# Loki + busybox estático, só para o healthcheck (a imagem oficial é distroless).
FROM busybox:1.37.0-musl AS probe

FROM grafana/loki:3.7.8
COPY --from=probe /bin/busybox /usr/bin/busybox
