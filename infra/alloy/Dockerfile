# The component uses internal Alloy APIs: keep source, compiler and runtime pinned.
FROM golang:1.26.7-bookworm@sha256:e8c859f5632dcfde7b32d2012b4351728f6437930887c2f6a91ea242459e5514 AS source
WORKDIR /src
RUN curl -fsSL https://codeload.github.com/grafana/alloy/tar.gz/refs/tags/v1.20.1 -o alloy.tar.gz \
    && echo '8a1a2c4fd2f7179b606210b10fe3460fe315505194449524c60d0b6a7c2a8356  alloy.tar.gz' | sha256sum -c - \
    && tar -xzf alloy.tar.gz --strip-components=1 \
    && rm alloy.tar.gz
COPY durable/ internal/component/loki/source/docker_durable/
COPY config.alloy durable-config.alloy
RUN printf 'package all\nimport _ "github.com/grafana/alloy/internal/component/loki/source/docker_durable"\n' \
    > internal/component/all/docker_durable.go \
    && mkdir -p /src/.test-tmp
ENV TMPDIR=/src/.test-tmp

FROM node:24.16.0-bookworm-slim@sha256:2c87ef9bd3c6a3bd4b472b4bec2ce9d16354b0c574f736c476489d09f560a203 AS ui
WORKDIR /ui
COPY --from=source /src/internal/web/ui/ ./
RUN npm ci --no-audit --no-fund && npm run build

FROM source AS native-test
RUN --mount=type=cache,target=/go/pkg/mod --mount=type=cache,target=/root/.cache/go-build \
    go test -p 2 -race -count=1 ./internal/component/loki/source/docker_durable \
    && go vet -p 2 ./internal/component/loki/source/docker_durable \
    && test -z "$(gofmt -l internal/component/loki/source/docker_durable)"

FROM source AS build
RUN --mount=type=cache,target=/go/pkg/mod --mount=type=cache,target=/root/.cache/go-build \
    make download-beyla
COPY --from=ui /ui/dist/ internal/web/ui/dist/
WORKDIR /src/collector
RUN --mount=type=cache,target=/go/pkg/mod --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 go build -p 2 -tags "gore2regex embedalloyui" -ldflags="-s -w" -o /out/alloy .

FROM grafana/alloy:v1.20.1
COPY --from=build /out/alloy /bin/alloy
