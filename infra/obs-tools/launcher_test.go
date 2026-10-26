package main

import (
	"bytes"
	"context"
	"encoding/json"
	"strings"
	"testing"
	"time"
)

func TestDiagnosticSanitization(t *testing.T) {
	for _, input := range []string{
		`2026/10/26 [error] connect() failed (13: Permission denied), request: "secret-sentinel"`,
		`unknown secret-sentinel Authorization password`,
		strings.Repeat("x", 128*1024),
	} {
		var out bytes.Buffer
		if err := relay(strings.NewReader(input+"\n"), &out, "logs-gateway", false); err != nil {
			t.Fatal(err)
		}
		var event map[string]any
		if err := json.Unmarshal(out.Bytes(), &event); err != nil {
			t.Fatal(err)
		}
		if strings.Contains(out.String(), "secret-sentinel") {
			t.Fatal("credential leaked")
		}
		if event["code"] == nil {
			t.Fatal("missing explicit category")
		}
	}
}

func TestAccessRelay(t *testing.T) {
	line := `{"level":"info","status":200}`
	var out bytes.Buffer
	if err := relay(strings.NewReader(line+"\n"), &out, "logs-gateway", true); err != nil {
		t.Fatal(err)
	}
	if strings.TrimSpace(out.String()) != line {
		t.Fatal("valid access JSON changed")
	}
}

func TestLaunchFailureStatus(t *testing.T) {
	var out bytes.Buffer
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	if err := launch(ctx, []string{"/bin/sh", "-c", "echo 'secret-sentinel' >&2; exit 7"}, &out, &out, "fixture"); err == nil {
		t.Fatal("child failure hidden")
	}
	if strings.Contains(out.String(), "secret-sentinel") {
		t.Fatal("child secret leaked")
	}
}
