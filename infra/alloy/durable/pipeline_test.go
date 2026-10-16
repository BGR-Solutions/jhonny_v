package durable

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log/slog"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/grafana/alloy/internal/component/common/loki"
	"github.com/grafana/alloy/internal/component/loki/process/stages"
	"github.com/grafana/alloy/internal/featuregate"
	"github.com/grafana/alloy/syntax"
	"github.com/grafana/loki/pkg/push"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/common/model"
)

func TestSynchronousMaskingBeforeDurableCommit(t *testing.T) {
	// Decode the actual deployed stage configuration, not a duplicate policy.
	data, err := os.ReadFile("/src/durable-config.alloy")
	if err != nil {
		t.Fatal(err)
	}
	text := string(data)
	start := strings.Index(text, "\tstage.replace")
	end := strings.LastIndex(text, "\n}")
	if start < 0 || end < start {
		t.Fatal("production masking stages not found")
	}
	var cfg struct {
		Stages []stages.StageConfig `alloy:"stage,enum,optional"`
	}
	if err := syntax.Unmarshal([]byte(text[start:end]), &cfg); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(t.TempDir(), "queue.db")
	q, err := openQueue(path, 4*1024*1024)
	if err != nil {
		t.Fatal(err)
	}
	consumer := &queueConsumer{queue: q, source: "producer/stdout"}
	pipeline, err := stages.NewPipelineConsumer(
		slog.New(slog.NewJSONHandler(io.Discard, nil)),
		prometheus.NewRegistry(), featuregate.StabilityGenerallyAvailable, cfg.Stages, consumer,
	)
	if err != nil {
		t.Fatal(err)
	}
	secrets := []string{
		"random-bearer-value-abcdef0123456789",
		"sk-abcdef01234567890123456789",
		"first second,third",
		"unquoted-abcdef0123456789",
	}
	lines := []string{
		"Authorization: Bearer " + secrets[0],
		"key " + secrets[1],
		fmt.Sprintf(`{"password":%q,"level":"ERROR","trace_id":"trace","span_id":"span"}`, secrets[2]),
		"access_token=" + secrets[3],
	}
	for _, line := range lines {
		batch := loki.NewBatch()
		batch.AddEntry(model.LabelSet{"container": "producer", "stream": "stdout"}, 0, push.Entry{
			Timestamp: time.Unix(1700000000, 123), Line: line,
		})
		if err := pipeline.Consume(context.Background(), batch); err != nil {
			t.Fatal(err)
		}
	}
	pipeline.Stop()
	for i := range lines {
		record, err := q.peek()
		if err != nil {
			t.Fatal(err)
		}
		var payload struct {
			Streams []struct {
				Values [][]json.RawMessage `json:"values"`
			} `json:"streams"`
		}
		if err := json.Unmarshal(record.Payload, &payload); err != nil {
			t.Fatal(err)
		}
		if !bytes.Contains(payload.Streams[0].Values[0][1], []byte(`\u003credacted\u003e`)) {
			t.Fatalf("record %d not masked", i)
		}
		if i == 2 && !bytes.Contains(record.Payload, []byte(`"trace_id":"trace"`)) {
			t.Fatal("structured metadata missing")
		}
		if err := q.ack(record.ID); err != nil {
			t.Fatal(err)
		}
	}
	if err := q.close(); err != nil {
		t.Fatal(err)
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	for _, secret := range secrets {
		if bytes.Contains(raw, []byte(secret)) {
			t.Fatal("raw secret leaked into bbolt pages, including freed pages")
		}
	}
}
