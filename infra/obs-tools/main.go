package main

import (
	"bufio"
	"context"
	"crypto/sha256"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"time"

	"golang.org/x/crypto/bcrypt"
)

func probe(ctx context.Context, url string, timeout time.Duration) error {
	request, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return errors.New("invalid_probe_url")
	}

	client := &http.Client{Timeout: timeout, CheckRedirect: func(*http.Request, []*http.Request) error {
		return http.ErrUseLastResponse
	}}
	response, err := client.Do(request)
	if err != nil {
		return errors.New("probe_transport_failed")
	}
	defer response.Body.Close()
	if response.StatusCode != http.StatusOK {
		return errors.New("probe_status_unexpected")
	}
	return nil
}

func command(args []string, output io.Writer) int {
	if len(args) == 3 && args[0] == "run" && args[1] == "--service" {
		service := args[2]
		err := preflight(service)
		if err == nil {
			var child []string
			child, err = engine(service)
			if err == nil {
				err = launch(context.Background(), child, os.Stdout, output, service)
			}
		}
		if err != nil {
			_ = json.NewEncoder(output).Encode(map[string]string{"level": "error", "service": service, "stage": "run", "code": safeError(err)})
			return 1
		}
		return 0
	}
	if len(args) == 3 && args[0] == "preflight" && args[1] == "--service" {
		if err := preflight(args[2]); err != nil {
			_ = json.NewEncoder(output).Encode(map[string]string{"level": "error", "service": args[2], "stage": "preflight", "code": err.Error()})
			return 1
		}
		return 0
	}
	if len(args) == 2 && args[0] == "probe" {
		if err := probe(context.Background(), args[1], 2*time.Second); err != nil {
			if json.NewEncoder(output).Encode(map[string]string{"level": "error", "stage": "probe", "code": err.Error()}) != nil {
				return 1
			}
			return 1
		}
		return 0
	}
	_ = json.NewEncoder(output).Encode(map[string]string{"level": "error", "code": "invalid_command"})
	return 1
}

func main() {
	os.Exit(command(os.Args[1:], os.Stderr))
}

func validateSources(ctx context.Context, endpoint, project string) error {
	filters, _ := json.Marshal(map[string][]string{
		"label": {"com.docker.compose.project=" + project}, "status": {"running"},
	})
	request, err := http.NewRequestWithContext(ctx, http.MethodGet, endpoint+"/containers/json?filters="+url.QueryEscape(string(filters)), nil)
	if err != nil {
		return errors.New("docker_inventory_unavailable")
	}
	client := &http.Client{Timeout: 2 * time.Second, Transport: &http.Transport{Proxy: nil}, CheckRedirect: func(*http.Request, []*http.Request) error {
		return http.ErrUseLastResponse
	}}
	defer client.CloseIdleConnections()
	response, err := client.Do(request)
	if err != nil {
		return errors.New("docker_inventory_unavailable")
	}
	defer response.Body.Close()
	if response.StatusCode != http.StatusOK {
		return errors.New("docker_inventory_unavailable")
	}
	data, err := io.ReadAll(io.LimitReader(response.Body, (4<<20)+1))
	if err != nil || len(data) > 4<<20 {
		return errors.New("docker_inventory_invalid")
	}
	var containers []struct{ Labels map[string]string }
	if json.Unmarshal(data, &containers) != nil || containers == nil {
		return errors.New("docker_inventory_invalid")
	}
	for _, container := range containers {
		if container.Labels["com.docker.compose.project"] == project && strings.TrimSpace(container.Labels["com.docker.compose.service"]) == "" {
			return errors.New("source_missing_compose_service")
		}
	}
	return nil
}

func retention(value string) error {
	if !regexp.MustCompile(`^[0-9]+h$`).MatchString(value) {
		return errors.New("invalid_retention")
	}
	hours, err := strconv.ParseUint(strings.TrimSuffix(value, "h"), 10, 32)
	if err != nil || hours < 24 || hours%24 != 0 {
		return errors.New("invalid_retention")
	}
	return nil
}

func secrets(dir, reader, writer string) error {
	name := regexp.MustCompile(`^[A-Za-z0-9_-]{1,64}$`)
	if reader == writer || !name.MatchString(reader) || !name.MatchString(writer) {
		return errors.New("invalid_identities")
	}
	info, err := os.Lstat(dir)
	if err != nil || !info.IsDir() || info.Mode().Perm()&0027 != 0 || !authorizedOwner(info) {
		return errors.New("unsafe_secrets_directory")
	}
	hashes := make(map[string][]byte)
	for _, identity := range []struct{ file, user string }{{"read.htpasswd", reader}, {"write.htpasswd", writer}} {
		data, err := privateFile(filepath.Join(dir, identity.file))
		if err != nil {
			return err
		}
		line := strings.TrimSuffix(string(data), "\n")
		parts := strings.Split(line, ":")
		if len(parts) != 2 || parts[0] != identity.user || strings.ContainsAny(parts[1], "\r\n") {
			return errors.New("invalid_htpasswd")
		}
		if _, err := bcrypt.Cost([]byte(parts[1])); err != nil {
			return errors.New("invalid_bcrypt")
		}
		hashes[identity.user] = []byte(parts[1])
	}
	password, err := privateFile(filepath.Join(dir, "write-password"))
	if err != nil {
		return err
	}
	if len(password) < 32 || len(password) > 72 {
		return errors.New("invalid_password_length")
	}
	for _, b := range password {
		if b < 33 || b > 126 {
			return errors.New("invalid_password_encoding")
		}
	}
	if bcrypt.CompareHashAndPassword(hashes[writer], password) != nil {
		return errors.New("inconsistent_write_password")
	}
	return nil
}

func privateFile(path string) ([]byte, error) {
	info, err := os.Lstat(path)
	if err != nil || !info.Mode().IsRegular() || info.Mode().Perm()&0007 != 0 || info.Mode().Perm()&0022 != 0 || info.Size() == 0 || info.Size() > 4096 || !authorizedOwner(info) {
		return nil, errors.New("unsafe_secret_file")
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, errors.New("secret_unreadable")
	}
	return data, nil
}

func authorizedOwner(info os.FileInfo) bool {
	stat, ok := info.Sys().(*syscall.Stat_t)
	if !ok || (stat.Uid != 0 && stat.Uid != uint32(os.Geteuid())) {
		return false
	}
	return info.Mode().Perm()&0070 == 0 || stat.Gid == 0 || stat.Gid == uint32(os.Getegid())
}

func writableDirectory(path string) error {
	info, err := os.Stat(path)
	if err != nil || !info.IsDir() {
		return errors.New("volume_unavailable")
	}
	probe, err := os.CreateTemp(path, ".obs-write-check-")
	if err != nil {
		return errors.New("volume_not_writable")
	}
	name := probe.Name()
	closeErr := probe.Close()
	removeErr := os.Remove(name)
	if closeErr != nil || removeErr != nil {
		return errors.New("volume_check_cleanup_failed")
	}
	return nil
}

func preflight(service string) error {
	switch service {
	case "loki":
		if err := retention(os.Getenv("LOKI_RETENTION_PERIOD")); err != nil {
			return err
		}
		if err := writableDirectory("/loki"); err != nil {
			return err
		}
	case "logs-gateway":
		if err := secrets("/run/secrets", os.Getenv("OBS_READ_USER"), os.Getenv("OBS_WRITE_USER")); err != nil {
			return err
		}
	case "alloy":
		if strings.TrimSpace(os.Getenv("COMPOSE_PROJECT_NAME")) == "" {
			return errors.New("missing_project")
		}
		if _, err := privateFile("/run/secrets/write-password"); err != nil {
			return err
		}
		if err := writableDirectory("/var/lib/alloy"); err != nil {
			return err
		}
	case "docker-log-proxy":
		info, err := os.Stat("/var/run/docker.sock")
		if err != nil || info.Mode()&os.ModeSocket == 0 {
			return errors.New("docker_socket_unavailable")
		}
	default:
		return errors.New("unknown_service")
	}
	configs := map[string]string{"loki": "/etc/loki/config.yaml", "alloy": "/etc/alloy/config.alloy", "logs-gateway": "/etc/nginx/templates/nginx.conf.template", "docker-log-proxy": "/etc/nginx/nginx.conf"}
	if data, err := os.ReadFile(configs[service]); err != nil || len(data) == 0 {
		return errors.New("config_unavailable")
	}
	if service == "alloy" {
		return validateSources(context.Background(), "http://docker-log-proxy:2375", os.Getenv("COMPOSE_PROJECT_NAME"))
	}
	return nil
}

func relay(input io.Reader, output io.Writer, service string, access bool) error {
	scanner := bufio.NewScanner(input)
	scanner.Buffer(make([]byte, 4096), 1024*1024)
	for scanner.Scan() {
		line := scanner.Bytes()
		if access {
			var value map[string]json.RawMessage
			if json.Unmarshal(line, &value) == nil && value != nil {
				if _, err := fmt.Fprintln(output, string(line)); err != nil {
					return errors.New("output_failed")
				}
				continue
			}
		}
		code := "native_diagnostic_unrecognized"
		for _, category := range []struct{ match, code string }{
			{"Permission denied", "permission_denied"},
			{"connect() failed", "upstream_connect_failed"},
			{"No such file", "file_missing"},
			{"unknown directive", "config_invalid"},
			{"invalid", "config_invalid"},
			{"exiting", "process_exiting"},
			{"signal", "process_signal"},
		} {
			if strings.Contains(string(line), category.match) {
				code = category.code
				break
			}
		}
		level := "error"
		for marker, severity := range map[string]string{"[warn]": "warn", "[notice]": "info", "[info]": "info", "[debug]": "debug"} {
			if strings.Contains(string(line), marker) {
				level = severity
				break
			}
		}
		event := map[string]any{"level": level, "service": service, "stage": "native", "code": code, "size": len(line), "digest": fmt.Sprintf("%x", sha256.Sum256(line))}
		if match := regexp.MustCompile(`\(([0-9]+):`).FindSubmatch(line); len(match) == 2 {
			if number, err := strconv.Atoi(string(match[1])); err == nil {
				event["errno"] = number
			}
		}
		if err := json.NewEncoder(output).Encode(event); err != nil {
			return errors.New("output_failed")
		}
	}
	if scanner.Err() != nil {
		return errors.New("native_stream_read_failed")
	}
	return nil
}

func launch(ctx context.Context, args []string, stdout, stderr io.Writer, service string) error {
	if len(args) == 0 {
		return errors.New("missing_engine")
	}
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()
	child := exec.CommandContext(ctx, args[0], args[1:]...)
	signals := make(chan os.Signal, 4)
	signal.Notify(signals, syscall.SIGTERM, syscall.SIGINT, syscall.SIGQUIT)
	defer signal.Stop(signals)
	var lock sync.Mutex
	output := &lockedWriter{writer: stdout, lock: &lock}
	diagnostics := &lockedWriter{writer: stderr, lock: &lock}
	outR, outW, err := os.Pipe()
	if err != nil {
		return errors.New("pipe_failed")
	}
	defer outR.Close()
	errR, errW, err := os.Pipe()
	if err != nil {
		outW.Close()
		return errors.New("pipe_failed")
	}
	defer errR.Close()
	child.Stdout, child.Stderr = outW, errW
	if err := child.Start(); err != nil {
		outW.Close()
		errW.Close()
		return errors.New("engine_start_failed")
	}
	outW.Close()
	errW.Close()
	results := make(chan error, 2)
	go func() {
		e := relay(outR, output, service, true)
		if e != nil {
			cancel()
		}
		results <- e
	}()
	go func() {
		e := relay(errR, diagnostics, service, service == "loki" || service == "alloy")
		if e != nil {
			cancel()
		}
		results <- e
	}()
	done := make(chan struct{})
	defer close(done)
	go func() {
		for {
			select {
			case sig := <-signals:
				if e := child.Process.Signal(sig); e != nil && !errors.Is(e, os.ErrProcessDone) {
					cancel()
				}
			case <-done:
				return
			}
		}
	}()
	waitErr := child.Wait()
	timer := time.AfterFunc(5*time.Second, func() { outR.Close(); errR.Close() })
	defer timer.Stop()
	for range 2 {
		select {
		case result := <-results:
			if result != nil {
				return result
			}
		case <-time.After(6 * time.Second):
			return errors.New("stream_drain_timeout")
		}
	}
	if waitErr != nil {
		return errors.New("engine_exit_failed")
	}
	return nil
}

type lockedWriter struct {
	writer io.Writer
	lock   *sync.Mutex
}

func (w *lockedWriter) Write(data []byte) (int, error) {
	w.lock.Lock()
	defer w.lock.Unlock()
	return w.writer.Write(data)
}

func safeError(err error) string {
	if regexp.MustCompile(`^[a-z_]+$`).MatchString(err.Error()) {
		return err.Error()
	}
	return "operation_failed"
}

func engine(service string) ([]string, error) {
	switch service {
	case "loki":
		return []string{"/usr/bin/loki", "-config.file=/etc/loki/config.yaml", "-config.expand-env=true", "-log.format=json"}, nil
	case "alloy":
		return []string{"/bin/alloy", "run", "--storage.path=/var/lib/alloy", "--server.http.listen-addr=127.0.0.1:12345", "/etc/alloy/config.alloy"}, nil
	case "docker-log-proxy":
		return []string{"/usr/sbin/nginx", "-c", "/etc/nginx/nginx.conf", "-g", "daemon off;"}, nil
	case "logs-gateway":
		content, err := os.ReadFile("/etc/nginx/templates/nginx.conf.template")
		if err != nil {
			return nil, errors.New("template_unreadable")
		}
		for _, name := range []string{"OBS_READ_USER", "OBS_WRITE_USER"} {
			content = []byte(strings.ReplaceAll(string(content), "${"+name+"}", os.Getenv(name)))
		}
		if err := os.WriteFile("/run/obs/nginx.conf", content, 0600); err != nil {
			return nil, errors.New("template_render_failed")
		}
		return []string{"/usr/sbin/nginx", "-c", "/run/obs/nginx.conf", "-g", "daemon off;"}, nil
	default:
		return nil, errors.New("unknown_service")
	}
}
