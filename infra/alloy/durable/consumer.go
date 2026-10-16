package durable

import (
	"context"
	"encoding/json"
	"strconv"

	"github.com/grafana/alloy/internal/component/common/loki"
	"github.com/prometheus/common/model"
)

type queueConsumer struct {
	queue   *diskQueue
	source  string
	receipt func(model.LabelSet)
}

func (c *queueConsumer) Consume(ctx context.Context, batch loki.Batch) error {
	return batch.ConsumeStreams(func(stream loki.Stream) error {
		labels := make(map[string]string, len(stream.Labels))
		for name, value := range stream.Labels {
			labels[string(name)] = string(value)
		}
		for _, entry := range stream.Entries {
			metadata := make(map[string]string, len(entry.StructuredMetadata))
			for _, pair := range entry.StructuredMetadata {
				metadata[pair.Name] = pair.Value
			}
			line := entry.Line
			if len(line) > maxStoredLineBytes {
				line = line[:maxStoredLineBytes]
			}
			payload, err := json.Marshal(map[string]any{
				"streams": []any{map[string]any{
					"stream": labels,
					"values": [][]any{{strconv.FormatInt(entry.Timestamp.UnixNano(), 10), line, metadata}},
				}},
			})
			if err != nil {
				return err
			}
			if _, err := c.queue.enqueue(ctx, payload, c.source+"/"+labels["stream"]); err != nil {
				return err
			}
			if c.receipt != nil {
				c.receipt(stream.Labels)
			}
		}
		return nil
	})
}
