package main

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"golang.org/x/crypto/bcrypt"
)

func TestProbe(t *testing.T) {
	for _, status := range []int{200, 401, 500} {
		t.Run(http.StatusText(status), func(t *testing.T) {
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				w.WriteHeader(status)
			}))
			defer server.Close()
			err := probe(context.Background(), server.URL, 2*time.Second)
			if (err == nil) != (status == 200) {
				t.Fatalf("unexpected result: %v", err)
			}
		})
	}
}

func TestProbeTimeoutAndTransport(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		<-r.Context().Done()
	}))
	defer server.Close()
	if probe(context.Background(), server.URL, 20*time.Millisecond) == nil {
		t.Fatal("timeout must fail")
	}
	if probe(context.Background(), "http://127.0.0.1:1", time.Second) == nil {
		t.Fatal("transport failure must fail")
	}
}

func TestProbeCommandJSON(t *testing.T) {
	var out bytes.Buffer
	if command([]string{"probe", "http://127.0.0.1:1"}, &out) == 0 {
		t.Fatal("must fail")
	}
	var event map[string]any
	if err := json.Unmarshal(out.Bytes(), &event); err != nil {
		t.Fatal(err)
	}
	if strings.Contains(out.String(), "127.0.0.1") {
		t.Fatal("raw transport information leaked")
	}
}

func TestRetention(t *testing.T) {
	for _, value := range []string{"24h", "336h", "48h"} {
		if err := retention(value); err != nil {
			t.Fatal(value, err)
		}
	}
	for _, value := range []string{"", "0h", "23h", "25h", "-24h", "1d", "24.0h", " 24h", "999999999999999999999999h"} {
		if retention(value) == nil {
			t.Fatal("accepted", value)
		}
	}
}

func TestSecrets(t *testing.T) {
	dir := t.TempDir()
	if err := os.Chmod(dir, 0700); err != nil {
		t.Fatal(err)
	}
	password := strings.Repeat("s", 32)
	hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.MinCost)
	if err != nil {
		t.Fatal(err)
	}
	write := func(name, content string, mode os.FileMode) {
		t.Helper()
		if err := os.WriteFile(filepath.Join(dir, name), []byte(content), mode); err != nil {
			t.Fatal(err)
		}
	}
	write("read.htpasswd", "reader:"+string(hash)+"\n", 0600)
	write("write.htpasswd", "writer:"+string(hash)+"\n", 0600)
	write("write-password", password, 0600)
	if err := secrets(dir, "reader", "writer"); err != nil {
		t.Fatal(err)
	}
	write("write-password", strings.Repeat("x", 32), 0600)
	if secrets(dir, "reader", "writer") == nil {
		t.Fatal("accepted mismatch")
	}
	write("write-password", password, 0600)
	if secrets(dir, "reader", "reader") == nil {
		t.Fatal("accepted same identity")
	}
	if err := os.Chmod(filepath.Join(dir, "write-password"), 0644); err != nil {
		t.Fatal(err)
	}
	if secrets(dir, "reader", "writer") == nil {
		t.Fatal("accepted public file")
	}
	if err := os.Remove(filepath.Join(dir, "write-password")); err != nil {
		t.Fatal(err)
	}
	if secrets(dir, "reader", "writer") == nil {
		t.Fatal("accepted missing file")
	}
	if err := os.Symlink(filepath.Join(dir, "read.htpasswd"), filepath.Join(dir, "write-password")); err != nil {
		t.Fatal(err)
	}
	if secrets(dir, "reader", "writer") == nil {
		t.Fatal("accepted symlink")
	}
}

func TestPreflightRejectsInvalidRetention(t *testing.T) {
	t.Setenv("LOKI_RETENTION_PERIOD", "25h")
	var out bytes.Buffer
	if command([]string{"preflight", "--service", "loki"}, &out) == 0 {
		t.Fatal("accepted invalid retention")
	}

	if !strings.Contains(out.String(), "invalid_retention") {
		t.Fatal("missing diagnostic", out.String())
	}
}
