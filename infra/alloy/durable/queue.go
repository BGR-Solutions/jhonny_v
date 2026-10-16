// Package durable implements an acknowledged, masked Docker log source for Alloy.
package durable

import (
	"bytes"
	"context"
	"encoding/binary"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sync/atomic"
	"time"

	bolt "go.etcd.io/bbolt"
)

var (
	queueBucket = []byte("pending")
	metaBucket  = []byte("progress")
	errEmpty    = errors.New("durable queue empty")
)

type queuedRecord struct {
	ID      uint64
	Source  string
	Payload []byte
}

type diskQueue struct {
	db     *bolt.DB
	limit  uint64
	wake   chan struct{}
	paused atomic.Int64
	failed atomic.Bool
}

func number(n uint64) []byte {
	var b [8]byte
	binary.BigEndian.PutUint64(b[:], n)
	return b[:]
}

func integer(b []byte) uint64 {
	if len(b) != 8 {
		return 0
	}
	return binary.BigEndian.Uint64(b)
}

func openQueue(path string, limit uint64) (*diskQueue, error) {
	if limit == 0 {
		return nil, errors.New("queue limit must be positive")
	}
	if err := os.MkdirAll(filepath.Dir(path), 0750); err != nil {
		return nil, errors.New("cannot create durable state directory")
	}
	db, err := bolt.Open(path, 0600, &bolt.Options{Timeout: time.Second, NoSync: false})
	if err != nil {
		return nil, errors.New("cannot open durable state; manual recovery required")
	}
	q := &diskQueue{db: db, limit: limit, wake: make(chan struct{}, 1)}
	err = db.Update(func(tx *bolt.Tx) error {
		meta := tx.Bucket(metaBucket)
		pending := tx.Bucket(queueBucket)
		if meta == nil && pending == nil {
			var err error
			meta, err = tx.CreateBucket(metaBucket)
			if err != nil {
				return err
			}
			if _, err = tx.CreateBucket(queueBucket); err != nil {
				return err
			}
			return meta.Put([]byte("schema"), []byte("1"))
		}
		if meta == nil || pending == nil || !bytes.Equal(meta.Get([]byte("schema")), []byte("1")) {
			return errors.New("invalid durable state schema")
		}
		return nil
	})
	if err == nil {
		err = db.View(func(tx *bolt.Tx) error {
			bad := false
			for check := range tx.Check() {
				bad = bad || check != nil
			}
			if bad {
				return errors.New("durable state integrity failure")
			}
			var count, size uint64
			bucket := tx.Bucket(queueBucket)
			if err := bucket.ForEach(func(k, v []byte) error {
				if len(k) != 8 || len(v) < 2 || int(binary.BigEndian.Uint16(v[:2])) > len(v)-2 {
					return errors.New("invalid durable record")
				}
				offset := 2 + int(binary.BigEndian.Uint16(v[:2]))
				if offset > 258 || offset == len(v) || integer(k) > bucket.Sequence() {
					return errors.New("invalid durable receipt")
				}
				count++
				size += uint64(len(v) - offset)
				return nil
			}); err != nil {
				return err
			}
			meta := tx.Bucket(metaBucket)
			if count != integer(meta.Get([]byte("count"))) || size != integer(meta.Get([]byte("bytes"))) ||
				bucket.Sequence() != integer(meta.Get([]byte("receipt"))) {
				return errors.New("durable checkpoint mismatch")
			}
			return nil
		})
	}
	if err != nil {
		db.Close()
		return nil, errors.New("invalid durable state; refusing to discard it")
	}
	return q, nil
}

func (q *diskQueue) signal() {
	select {
	case q.wake <- struct{}{}:
	default:
	}
}

func (q *diskQueue) enqueue(ctx context.Context, payload []byte, source string) (uint64, error) {
	if len(source) > 256 || len(payload) == 0 {
		return 0, errors.New("invalid durable record")
	}
	var waiting bool
	defer func() {
		if waiting {
			q.paused.Add(-1)
		}
	}()
	for {
		if err := ctx.Err(); err != nil {
			return 0, err
		}
		var id uint64
		err := q.db.Update(func(tx *bolt.Tx) error {
			meta := tx.Bucket(metaBucket)
			size := integer(meta.Get([]byte("bytes")))
			if uint64(len(payload)) > q.limit || size > q.limit-uint64(len(payload)) {
				return nil
			}
			bucket := tx.Bucket(queueBucket)
			var err error
			id, err = bucket.NextSequence()
			if err != nil {
				return err
			}
			value := make([]byte, 2+len(source)+len(payload))
			binary.BigEndian.PutUint16(value, uint16(len(source)))
			copy(value[2:], source)
			copy(value[2+len(source):], payload)
			if err := bucket.Put(number(id), value); err != nil {
				return err
			}
			for key, value := range map[string][]byte{
				"receipt": number(id),
				"source":  []byte(source),
				"bytes":   number(size + uint64(len(payload))),
				"count":   number(integer(meta.Get([]byte("count"))) + 1),
			} {
				if err := meta.Put([]byte(key), value); err != nil {
					return err
				}
			}
			return nil
		})
		if err != nil {
			q.failed.Store(true)
			return 0, errors.New("durable commit failed; source receipt not confirmed")
		}
		if id != 0 {
			q.signal()
			return id, nil
		}
		if !waiting {
			q.paused.Add(1)
			waiting = true
		}
		select {
		case <-ctx.Done():
			return 0, ctx.Err()
		case <-q.wake:
		case <-time.After(100 * time.Millisecond):
		}
	}
}

func (q *diskQueue) peek() (queuedRecord, error) {
	var record queuedRecord
	err := q.db.View(func(tx *bolt.Tx) error {
		key, value := tx.Bucket(queueBucket).Cursor().First()
		if key == nil {
			return errEmpty
		}
		offset := 2 + int(binary.BigEndian.Uint16(value[:2]))
		record = queuedRecord{ID: integer(key), Source: string(value[2:offset]), Payload: bytes.Clone(value[offset:])}
		return nil
	})
	return record, err
}

func (q *diskQueue) ack(id uint64) error {
	err := q.db.Update(func(tx *bolt.Tx) error {
		bucket := tx.Bucket(queueBucket)
		key, value := bucket.Cursor().First()
		if key == nil || integer(key) != id {
			return errors.New("acknowledgement is not the oldest receipt")
		}
		offset := 2 + int(binary.BigEndian.Uint16(value[:2]))
		meta := tx.Bucket(metaBucket)
		if err := meta.Put([]byte("bytes"), number(integer(meta.Get([]byte("bytes")))-uint64(len(value)-offset))); err != nil {
			return err
		}
		if err := meta.Put([]byte("count"), number(integer(meta.Get([]byte("count")))-1)); err != nil {
			return err
		}
		return bucket.Delete(key)
	})
	if err != nil {
		q.failed.Store(true)
		return fmt.Errorf("durable acknowledgement failed")
	}
	q.signal()
	return nil
}

func (q *diskQueue) stats() (count, size uint64) {
	q.db.View(func(tx *bolt.Tx) error {
		meta := tx.Bucket(metaBucket)
		count, size = integer(meta.Get([]byte("count"))), integer(meta.Get([]byte("bytes")))
		return nil
	})
	return
}

func (q *diskQueue) receipt() (id uint64) {
	q.db.View(func(tx *bolt.Tx) error {
		id = integer(tx.Bucket(metaBucket).Get([]byte("receipt")))
		return nil
	})
	return
}

func (q *diskQueue) close() error { return q.db.Close() }
