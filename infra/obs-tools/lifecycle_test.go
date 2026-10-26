package main

import (
	"bytes"
	"context"
	"errors"
	"io"
	"os"
	"strings"
	"sync"
	"syscall"
	"testing"
	"time"
)

type observingWriter struct {
	ready chan struct{}
	once  sync.Once
	data  bytes.Buffer
}

func (w *observingWriter) Write(data []byte) (int, error) {
	if bytes.Contains(data, []byte(`"ready":true`)) {
		w.once.Do(func() { close(w.ready) })
	}
	return w.data.Write(data)
}

func TestLaunchForwardsSignalsAndDrains(t *testing.T) {
	for _, sig := range []syscall.Signal{syscall.SIGTERM, syscall.SIGINT, syscall.SIGQUIT} {
		t.Run(sig.String(), func(t *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 4*time.Second)
			defer cancel()
			output := &observingWriter{ready: make(chan struct{})}
			done := make(chan error, 1)
			script := `trap 'echo "{\"signal\":\"received\"}"; exit 0' TERM INT QUIT; echo '{"ready":true}'; while :; do sleep 0.05; done`
			go func() { done <- launch(ctx, []string{"/bin/sh", "-c", script}, output, output, "fixture") }()
			select {
			case <-output.ready:
			case <-ctx.Done():
				t.Fatal("child never became ready")
			}
			if err := syscall.Kill(os.Getpid(), sig); err != nil {
				t.Fatal(err)
			}
			if err := <-done; err != nil {
				t.Fatal(err)
			}
			if !strings.Contains(output.data.String(), `"signal":"received"`) {
				t.Fatal("signal not forwarded or final output not drained")
			}
		})
	}
}

type failedWriter struct{}

func (failedWriter) Write([]byte) (int, error) { return 0, errors.New("sentinel-private-error") }

type failedReader struct{}

func (failedReader) Read([]byte) (int, error) { return 0, errors.New("sentinel-private-error") }

func TestRelayIOFailure(t *testing.T) {
	if err := relay(failedReader{}, io.Discard, "fixture", false); err == nil || err.Error() != "native_stream_read_failed" {
		t.Fatalf("read failure not classified: %v", err)
	}
	if err := relay(strings.NewReader("message\n"), failedWriter{}, "fixture", false); err == nil || err.Error() != "output_failed" {
		t.Fatalf("write failure not classified: %v", err)
	}
	if err := relay(strings.NewReader(strings.Repeat("a", 1024*1024+1)), io.Discard, "fixture", false); err == nil {
		t.Fatal("over-limit line silently truncated")
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	if err := launch(ctx, []string{"/bin/sh", "-c", "echo diagnostic; sleep 60"}, failedWriter{}, io.Discard, "fixture"); err == nil {
		t.Fatal("output failure hidden")
	}
}

type blockedWriter struct{ release <-chan struct{} }

func (w blockedWriter) Write(data []byte) (int, error) {
	<-w.release
	return len(data), nil
}

func TestLaunchBlockedDrainIsBounded(t *testing.T) {
	release := make(chan struct{})
	defer close(release)
	begin := time.Now()
	err := launch(context.Background(), []string{"/bin/sh", "-c", "echo diagnostic"}, blockedWriter{release}, io.Discard, "fixture")
	if err == nil || err.Error() != "stream_drain_timeout" || time.Since(begin) > 8*time.Second {
		t.Fatalf("blocked drain not bounded and explicit: %v", err)
	}
}

func TestPrivateFileRejectsUnauthorizedOwner(t *testing.T) {
	path := t.TempDir() + "/secret"
	if err := os.WriteFile(path, []byte("sentinel"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.Chown(path, 12345, 12345); err != nil {
		t.Fatal("ownership test requires the fixed Linux builder root identity", err)
	}
	if _, err := privateFile(path); err == nil {
		t.Fatal("unauthorized secret owner accepted")
	}
}

func TestDiagnosticSeverityAndErrno(t *testing.T) {
	var output bytes.Buffer
	err := relay(strings.NewReader("2026 [warn] open() failed (13: Permission denied), secret-sentinel\n"), &output, "fixture", false)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(output.String(), `"level":"warn"`) || !strings.Contains(output.String(), `"errno":13`) {
		t.Fatal("diagnostic severity/errno missing", output.String())
	}
}
