package durable

import (
	"bufio"
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
)

func TestQueueCrashWorker(t *testing.T) {
	path := os.Getenv("DURABLE_CRASH_STATE")
	if path == "" {
		return
	}
	q, err := openQueue(path, 4096)
	if err != nil {
		t.Fatal(err)
	}
	id, err := q.enqueue(context.Background(), []byte("masked-record"), "removed-producer")
	if err != nil {
		t.Fatal(err)
	}
	if os.Getenv("DURABLE_CRASH_ACK") == "1" {
		if err := q.ack(id); err != nil {
			t.Fatal(err)
		}
	}
	os.Stdout.Write([]byte("durable\n"))
	select {}
}

func TestSIGKILLBeforeAndAfterAcknowledgement(t *testing.T) {
	for _, ack := range []string{"0", "1"} {
		t.Run("ack="+ack, func(t *testing.T) {
			path := filepath.Join(t.TempDir(), "queue.db")
			process := exec.Command(os.Args[0], "-test.run=^TestQueueCrashWorker$")
			process.Env = append(os.Environ(), "DURABLE_CRASH_STATE="+path, "DURABLE_CRASH_ACK="+ack)
			output, err := process.StdoutPipe()
			if err != nil {
				t.Fatal(err)
			}
			if err := process.Start(); err != nil {
				t.Fatal(err)
			}
			t.Cleanup(func() { process.Process.Kill(); process.Wait() })
			line, err := bufio.NewReader(output).ReadString('\n')
			if err != nil || line != "durable\n" {
				t.Fatal("worker did not confirm fsync", line, err)
			}
			process.Process.Kill()
			process.Wait()
			q, err := openQueue(path, 4096)
			if err != nil {
				t.Fatal(err)
			}
			defer q.close()
			count, _ := q.stats()
			expected := uint64(1)
			if ack == "1" {
				expected = 0
			}
			if count != expected || q.receipt() != 1 {
				t.Fatal(fmt.Sprintf("recovered count=%d receipt=%d", count, q.receipt()))
			}
		})
	}
}
