package durable

import (
	"net"
	"net/http"
	"time"
)

func boundedTransport() *http.Transport {
	return &http.Transport{
		DialContext:            (&net.Dialer{Timeout: 5 * time.Second, KeepAlive: 30 * time.Second}).DialContext,
		MaxResponseHeaderBytes: 64 * 1024,
		ResponseHeaderTimeout:  10 * time.Second,
		TLSHandshakeTimeout:    5 * time.Second,
		IdleConnTimeout:        30 * time.Second,
		MaxIdleConns:           2,
		MaxIdleConnsPerHost:    2,
		MaxConnsPerHost:        2,
	}
}
