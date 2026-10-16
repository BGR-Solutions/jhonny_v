package durable

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"testing"
)

func TestSenderOnly204Acknowledges(t *testing.T) {
	for _, status := range []int{200, 202, 400, 401, 429, 500, 503, 204} {
		t.Run(fmt.Sprint(status), func(t *testing.T) {
			q, err := openQueue(filepath.Join(t.TempDir(), "queue.db"), 4096)
			if err != nil {
				t.Fatal(err)
			}
			defer q.close()
			if _, err := q.enqueue(context.Background(), []byte(`{"streams":[]}`), "removed-producer"); err != nil {
				t.Fatal(err)
			}
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				if user, pass, ok := r.BasicAuth(); !ok || user != "user" || pass != "credential" {
					t.Error("missing gateway authentication")
				}
				w.WriteHeader(status)
				w.Write([]byte("never log response payload"))
			}))
			defer server.Close()
			err = sendOldest(context.Background(), q, server.Client(), server.URL, "user", "credential")
			count, _ := q.stats()
			if status == 204 && (err != nil || count != 0) {
				t.Fatalf("204 not acknowledged: %v, %d", err, count)
			}
			if status != 204 && (err == nil || count != 1) {
				t.Fatalf("non204 must remain pending: %v, %d", err, count)
			}
		})
	}
}

func TestSenderDisconnectRetainsCommittedRecord(t *testing.T) {
	q, err := openQueue(filepath.Join(t.TempDir(), "queue.db"), 4096)
	if err != nil {
		t.Fatal(err)
	}
	defer q.close()
	q.enqueue(context.Background(), []byte(`{"streams":[]}`), "source")
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		conn, _, err := w.(http.Hijacker).Hijack()
		if err != nil {
			t.Fatal(err)
		}
		conn.Close()
	}))
	defer server.Close()
	if err := sendOldest(context.Background(), q, server.Client(), server.URL, "", ""); err == nil {
		t.Fatal("lost acknowledgement must retry")
	}
	if count, _ := q.stats(); count != 1 {
		t.Fatal("record lost on disconnected acknowledgement")
	}
}
