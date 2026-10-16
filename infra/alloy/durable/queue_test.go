package durable

import (
	"bytes"
	"context"
	"errors"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestQueueCommitRecoveryAndReceipt(t *testing.T) {
	path := filepath.Join(t.TempDir(), "queue.db")
	q, err := openQueue(path, 4096)
	if err != nil {
		t.Fatal(err)
	}
	payload := []byte(`{"streams":[{"values":[["1","masked"]]}]}`)
	id, err := q.enqueue(context.Background(), payload, "producer/stdout")
	if err != nil {
		t.Fatal(err)
	}
	payload[0] = 'X'
	if err := q.close(); err != nil {
		t.Fatal(err)
	}
	q, err = openQueue(path, 4096)
	if err != nil {
		t.Fatal(err)
	}
	defer q.close()
	record, err := q.peek()
	if err != nil || record.ID != id || record.Payload[0] != '{' {
		t.Fatalf("immutable recovered record: %+v, %v", record, err)
	}
	if q.receipt() != id {
		t.Fatal("queue and receipt did not commit together")
	}
	if err := q.ack(id); err != nil {
		t.Fatal(err)
	}
	records, size := q.stats()
	if records != 0 || size != 0 || q.receipt() != id {
		t.Fatal("ack must remove only pending data, not the receipt sequence")
	}
}

func TestQueueBoundBlocksWithoutAdvancingReceipt(t *testing.T) {
	q, err := openQueue(filepath.Join(t.TempDir(), "queue.db"), 4)
	if err != nil {
		t.Fatal(err)
	}
	defer q.close()
	id, err := q.enqueue(context.Background(), []byte("full"), "source")
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Millisecond)
	defer cancel()
	if _, err := q.enqueue(ctx, []byte("next"), "source"); !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("full queue must block: %v", err)
	}
	if q.receipt() != id {
		t.Fatal("uncommitted record advanced receipt")
	}
	if err := q.ack(id); err != nil {
		t.Fatal(err)
	}
	if _, err := q.enqueue(context.Background(), []byte("next"), "source"); err != nil {
		t.Fatal(err)
	}
}

func TestQueueCorruptionFailsClosed(t *testing.T) {
	path := filepath.Join(t.TempDir(), "queue.db")
	if err := os.WriteFile(path, bytes.Repeat([]byte("not a database"), 1024), 0600); err != nil {
		t.Fatal(err)
	}
	if q, err := openQueue(path, 1024); err == nil {
		q.close()
		t.Fatal("must not recreate or ignore corrupt durable state")
	}
}

func TestQueueOversizeDoesNotSilentlyDrop(t *testing.T) {
	q, err := openQueue(filepath.Join(t.TempDir(), "queue.db"), 3)
	if err != nil {
		t.Fatal(err)
	}

	func TestFIFOAndCrashAfterAck(t *testing.T) {
		path := filepath.Join(t.TempDir(), "queue.db")
		q, err := openQueue(path, 4096)
		if err != nil {
			t.Fatal(err)
		}
		first, err := q.enqueue(context.Background(), []byte("first"), "one")
		if err != nil {
			t.Fatal(err)
		}
		second, err := q.enqueue(context.Background(), []byte("second"), "two")
		if err != nil {
			t.Fatal(err)
		}
		if err := q.ack(second); err == nil {
			t.Fatal("out-of-order ack must fail")
		}
		if err := q.ack(first); err != nil {
			t.Fatal(err)
		}
		q.close()
		q, err = openQueue(path, 4096)
		if err != nil {
			t.Fatal(err)
		}
		defer q.close()
		record, err := q.peek()
		if err != nil || record.ID != second {
			t.Fatal("committed ack was not recovered", record, err)
		}
	}
	defer q.close()
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Millisecond)
	defer cancel()
	if _, err := q.enqueue(ctx, []byte("oversize"), "source"); !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("oversize record must pause, not drop: %v", err)
	}
	if q.receipt() != 0 {
		t.Fatal("uncommitted record advanced receipt")
	}
}
