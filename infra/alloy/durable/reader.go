package durable

import (
	"bufio"
	"encoding/binary"
	"errors"
	"io"
	"strings"
	"time"
)

const maxLineBytes = 1024 * 1024
const maxStoredLineBytes = 262144

type rawRecord struct {
	Stream string
	Time   time.Time
	Line   string
}

type partialLine struct {
	data []byte
	time time.Time
	drop bool
}

func (p *partialLine) consume(reader io.Reader, stream string, timestamp time.Time, emit func(rawRecord) error) error {
	buffer := bufio.NewReaderSize(reader, 16384)
	for {
		part, err := buffer.ReadSlice('\n')
		if len(p.data) == 0 && !p.drop {
			p.time = timestamp
		}
		newline := len(part) > 0 && part[len(part)-1] == '\n'
		body := part
		if newline {
			body = part[:len(part)-1]
		}
		if len(p.data)+len(body) > maxLineBytes {
			p.drop = true
			p.data = nil
		}
		if !p.drop {
			p.data = append(p.data, body...)
		}
		if newline {
			if !p.drop {
				if err := emit(rawRecord{Stream: stream, Time: p.time, Line: string(p.data)}); err != nil {
					return err
				}
			}
			p.data, p.drop = p.data[:0], false
		}
		if err == io.EOF {
			return nil
		}
		if err != nil && err != bufio.ErrBufferFull {
			return errors.New("Docker log read failed")
		}
	}
}

func readDocker(reader io.Reader, tty bool, emit func(rawRecord) error) error {
	if tty {
		// TTY has one combined stdout stream and no Docker multiplex headers.
		var partial partialLine
		return partial.consume(reader, "stdout", time.Time{}, func(record rawRecord) error {
			timestamp, text, ok := strings.Cut(record.Line, " ")
			if !ok {
				return errors.New("missing Docker timestamp")
			}
			ts, err := time.Parse(time.RFC3339Nano, timestamp)
			if err != nil {
				return errors.New("invalid Docker timestamp")
			}
			record.Time, record.Line = ts, text
			return emit(record)
		})
	}
	var stdout, stderr partialLine
	for {
		var header [8]byte
		_, err := io.ReadFull(reader, header[:])
		if err == io.EOF {
			return nil
		}
		if err != nil {
			return errors.New("truncated Docker frame")
		}
		if (header[0] != 1 && header[0] != 2) || header[1] != 0 || header[2] != 0 || header[3] != 0 {
			return errors.New("invalid Docker frame header")
		}
		length := int64(binary.BigEndian.Uint32(header[4:]))
		if length == 0 {
			continue
		}
		limited := &io.LimitedReader{R: reader, N: length}
		frameReader := bufio.NewReaderSize(limited, 64)
		prefix, err := frameReader.ReadSlice(' ')
		if err != nil || len(prefix) > 40 {
			return errors.New("invalid Docker frame timestamp")
		}
		ts, err := time.Parse(time.RFC3339Nano, string(prefix[:len(prefix)-1]))
		if err != nil {
			return errors.New("invalid Docker frame timestamp")
		}
		partial, stream := &stdout, "stdout"
		if header[0] == 2 {
			partial, stream = &stderr, "stderr"
		}
		if err := partial.consume(frameReader, stream, ts, emit); err != nil {
			return err
		}
		if limited.N != 0 {
			return errors.New("truncated Docker frame payload")
		}
	}
}
