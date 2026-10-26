package main

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestSourceAdmission(t *testing.T) {
	for _, scenario := range []struct {
		name, body, code string
		status           int
	}{
		{"valid", `[{"Labels":{"com.docker.compose.project":"selected","com.docker.compose.service":"api"}}]`, "", 200},
		{"missing-service", `[{"Labels":{"com.docker.compose.project":"selected"}}]`, "source_missing_compose_service", 200},
		{"foreign", `[{"Labels":{"com.docker.compose.project":"different"}}]`, "", 200},
		{"invalid-response", `invalid`, "docker_inventory_invalid", 200},
		{"denied", `{}`, "docker_inventory_unavailable", 403},
	} {
		t.Run(scenario.name, func(t *testing.T) {
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				var filters map[string][]string
				if r.URL.Path != "/containers/json" || json.Unmarshal([]byte(r.URL.Query().Get("filters")), &filters) != nil ||
					len(filters["label"]) != 1 || filters["label"][0] != "com.docker.compose.project=selected" {
					t.Error("inventory not restricted to selected project")
				}
				w.WriteHeader(scenario.status)
				_, _ = w.Write([]byte(scenario.body))
			}))
			defer server.Close()
			err := validateSources(context.Background(), server.URL, "selected")
			if scenario.code == "" && err != nil {
				t.Fatal(err)
			}
			if scenario.code != "" && (err == nil || err.Error() != scenario.code) {
				t.Fatalf("expected %s, received %v", scenario.code, err)
			}
		})
	}
}
