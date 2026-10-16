package durable

import (
	"context"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"testing"
	"time"

	"github.com/grafana/alloy/internal/component"
	"github.com/grafana/alloy/internal/component/discovery"
	"github.com/grafana/alloy/internal/featuregate"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/common/model"
)

func TestOneReaderPerContainerAndCancellationUnderBackpressure(t *testing.T) {
	var connections atomic.Int64
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, request *http.Request) {
		switch {
		case strings.HasSuffix(request.URL.Path, "/json"):
			w.Write([]byte(`{"Config":{"Tty":false}}`))
		case strings.HasSuffix(request.URL.Path, "/logs"):
			connections.Add(1)
			w.Write(frame(1, "2026-10-16T10:00:00Z token=raw-value\n"))
			w.(http.Flusher).Flush()
			<-request.Context().Done()
		default:
			w.WriteHeader(503)
		}
	}))
	defer server.Close()
	args := deployedArguments(t)
	args.Host, args.Endpoint, args.QueueMaxBytes = server.URL, server.URL+"/push", "1"
	target := discovery.NewTargetFromLabelSet(model.LabelSet{
		"__meta_docker_container_id": "producer", "__meta_docker_container_name": "/producer",
	})
	args.Targets = []discovery.Target{target, target}
	c, err := New(component.Options{
		DataPath: t.TempDir(), Registerer: prometheus.NewRegistry(),
		Logger: slog.New(slog.NewJSONHandler(io.Discard, nil)), MinStability: featuregate.StabilityGenerallyAvailable,
	}, args)
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	done := make(chan error, 1)
	go func() { done <- c.Run(ctx) }()
	for c.queue.paused.Load() == 0 {
		if ctx.Err() != nil {
			t.Fatal("source never reached backpressure")
		}
		time.Sleep(time.Millisecond)
	}
	if connections.Load() != 1 || c.queue.receipt() != 0 ||
		c.CurrentHealth().Health != component.HealthTypeUnhealthy {
		t.Fatal("reader ownership, uncommitted receipt, or health invalid")
	}
	cancel()
	select {
	case err := <-done:
		if err != nil {
			t.Fatal(err)
		}
	case <-time.After(time.Second):
		t.Fatal("source shutdown deadlocked under backpressure")
	}
}
