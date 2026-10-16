package durable

import (
	"context"
	"fmt"
	"path/filepath"
	"testing"
	"time"

	bolt "go.etcd.io/bbolt"
)

func TestBlockedRecordResumesAfterAcknowledgement(t *testing.T) {
	q, err := openQueue(filepath.Join(t.TempDir(), "queue.db"), 4)
	if err != nil {
		t.Fatal(err)
	}
	defer q.close()
	id, err := q.enqueue(context.Background(), []byte("full"), "source")
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	done := make(chan error, 1)
	go func() { _, err := q.enqueue(ctx, []byte("next"), "source"); done <- err }()
	for q.paused.Load() == 0 {
		if ctx.Err() != nil {
			t.Fatal("source did not signal pause")
		}
		time.Sleep(time.Millisecond)
	}
	if q.receipt() != id {
		t.Fatal("paused record advanced durable source progress")
	}
	if err := q.ack(id); err != nil {
		t.Fatal(err)
	}
	if err := <-done; err != nil {
		t.Fatal("blocked record did not resume", err)
	}
	if q.paused.Load() != 0 || q.receipt() != id+1 {
		t.Fatal("source failed to resume after capacity became available")
	}
}

func TestCheckpointKeysDoNotAccumulateProducerHistory(t *testing.T) {
	q, err := openQueue(filepath.Join(t.TempDir(), "queue.db"), 4096)
	if err != nil {
		t.Fatal(err)
	}
	defer q.close()
	for i := 0; i < 200; i++ {
		id, err := q.enqueue(context.Background(), []byte("masked"), fmt.Sprint(i))
		if err != nil {
			t.Fatal(err)
		}
		if err := q.ack(id); err != nil {
			t.Fatal(err)
		}
	}
	err = q.db.View(func(tx *bolt.Tx) error {
		if tx.Bucket(metaBucket).Stats().KeyN != 5 || tx.Bucket(queueBucket).Stats().KeyN != 0 {
			return fmt.Errorf("historical checkpoint keys accumulated")
		}
		if tx.Size() > 256*1024 {
			return fmt.Errorf("bbolt did not reuse freed pages: %d", tx.Size())
		}
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
}

func TestStorageFailureDoesNotConfirmReceipt(t *testing.T) {
	q, err := openQueue(filepath.Join(t.TempDir(), "queue.db"), 4096)
	if err != nil {
		t.Fatal(err)
	}
	q.close()
	if _, err := q.enqueue(context.Background(), []byte("masked"), "source"); err == nil {
		t.Fatal("closed storage confirmed a record")
	}
	if !q.failed.Load() {
		t.Fatal("storage failure did not signal degradation")
	}
}
