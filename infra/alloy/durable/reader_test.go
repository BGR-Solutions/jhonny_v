package durable

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"testing"
)

func frame(stream byte, text string) []byte {
	var header [8]byte
	header[0] = stream
	binary.BigEndian.PutUint32(header[4:], uint32(len(text)))
	return append(header[:], []byte(text)...)
}

func TestDockerReconstructionKeepsReceiveOrderAndTimestamp(t *testing.T) {
	wire := append(frame(1, "2026-10-16T10:00:02Z pass"), frame(2, "2026-10-16T10:00:01Z error\n")...)
	wire = append(wire, frame(1, "2026-10-16T10:00:02Z word=secret\n")...)
	var got []string
	err := readDocker(bytes.NewReader(wire), false, func(record rawRecord) error {
		got = append(got, fmt.Sprintf("%s %s %s", record.Stream, record.Time.Format("15:04:05"), record.Line))
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
	// A pending stdout fragment must not be persisted until reconstructed.
	want := "[stderr 10:00:01 error stdout 10:00:02 pass" + "word=secret]"
	if fmt.Sprint(got) != want {
		t.Fatal(got)
	}
}

func TestDockerLongLineExcludedButNextLinePreserved(t *testing.T) {
	wire := frame(1, "2026-10-16T10:00:00Z "+string(bytes.Repeat([]byte("x"), maxLineBytes+1))+"\n")
	wire = append(wire, frame(1, "2026-10-16T10:00:01Z next\n")...)
	var lines []string
	if err := readDocker(bytes.NewReader(wire), false, func(r rawRecord) error {
		lines = append(lines, r.Line)
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	if fmt.Sprint(lines) != "[next]" {
		t.Fatal("oversize line corrupted next record")
	}
}

func TestDockerIncompleteRawFragmentNotCommitted(t *testing.T) {
	calls := 0
	err := readDocker(bytes.NewReader(frame(1, "2026-10-16T10:00:00Z ******")), false, func(r rawRecord) error {
		calls++
		return nil
	})
	if err != nil || calls != 0 {
		t.Fatal("incomplete raw fragment must not reach durable queue", err, calls)
	}
}

func TestDockerTTYAndNonmonotonicTimestamps(t *testing.T) {
	input := "2026-10-16T10:00:02Z later\n2026-10-16T10:00:01Z earlier\n"
	var got []rawRecord
	err := readDocker(bytes.NewBufferString(input), true, func(r rawRecord) error {
		got = append(got, r)
		return nil
	})
	if err != nil || len(got) != 2 {
		t.Fatal(got, err)
	}
	if got[0].Line != "later" || got[1].Line != "earlier" || !got[1].Time.Before(got[0].Time) {
		t.Fatal("receive order and source timestamps must not be rewritten")
	}
}

func TestDockerTruncatedFrameIsNotCommitted(t *testing.T) {
	wire := frame(1, "2026-10-16T10:00:00Z incomplete")
	wire = wire[:len(wire)-1]
	calls := 0
	err := readDocker(bytes.NewReader(wire), false, func(r rawRecord) error {
		calls++
		return nil
	})
	if err == nil || calls != 0 {
		t.Fatal("truncated Docker frame must not commit", err, calls)
	}
}
