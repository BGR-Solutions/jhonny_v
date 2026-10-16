package durable

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"net/http"
)

func sendOldest(ctx context.Context, queue *diskQueue, client *http.Client, endpoint, user, password string) error {
	record, err := queue.peek()
	if err != nil {
		return err
	}
	// No database transaction remains open while waiting on the network.
	request, err := http.NewRequestWithContext(ctx, http.MethodPost, endpoint, bytes.NewReader(record.Payload))
	if err != nil {
		return errors.New("invalid Loki endpoint")
	}
	request.Header.Set("Content-Type", "application/json")
	request.SetBasicAuth(user, password)
	response, err := client.Do(request)
	if err != nil {
		return errors.New("Loki acknowledgement unavailable")
	}
	// Never read/log an unbounded or potentially secret response body.
	response.Body.Close()
	if response.StatusCode != http.StatusNoContent {
		return fmt.Errorf("Loki acknowledgement status %d", response.StatusCode)
	}
	return queue.ack(record.ID)
}
