FROM golang:1.27.2@sha256:820153096fda4de6ac1b7194d12e416b7dd8f4e9a33d17e0345b111b945162d8 AS builder
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download && go mod verify
COPY *.go ./
RUN go test ./... && CGO_ENABLED=0 go build -trimpath -o /obs-tools .

FROM grafana/loki:3.7.9@sha256:0db216b630ae1f348a1584c67f3cead8b4c1fc839169a39501db664744158e28 AS loki
COPY --from=builder /obs-tools /usr/local/bin/obs-tools
ENTRYPOINT ["/usr/local/bin/obs-tools", "run", "--service", "loki"]
CMD []

FROM grafana/alloy:v1.21.2@sha256:89a5a320168387336b9ac3c850609c3ba7757eadd4ae5f1d819deb35e9854b18 AS alloy
COPY --from=builder /obs-tools /usr/local/bin/obs-tools
ENTRYPOINT ["/usr/local/bin/obs-tools", "run", "--service", "alloy"]
CMD []

FROM nginx:1.30.6-alpine@sha256:47928bf67eb62a1863cb08d9ecb52d3e704304ba614eaee17884204677702951 AS nginx
COPY --from=builder /obs-tools /usr/local/bin/obs-tools
ENTRYPOINT ["/usr/local/bin/obs-tools"]
CMD []
