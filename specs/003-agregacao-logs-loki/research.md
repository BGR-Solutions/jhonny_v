# Research: Agregação Centralizada de Logs de Contêineres (Grafana Alloy + Loki)

Todas as decisões abaixo foram validadas num protótipo descartável (em `/tmp`, fora do repositório) com Docker Engine 28 e as imagens fixadas. Nenhum `NEEDS CLARIFICATION` permanece.

## Decision 1: Versões das imagens

- **Decision**: `grafana/loki:3.7.8`, `grafana/alloy:v1.20.1`, `tecnativa/docker-socket-proxy:v0.5.0` e `busybox:1.37.0-musl` (só como estágio de build).
- **Rationale**: são as releases estáveis mais recentes em 2026-10-01 (Loki 3.7.8 de 2026-09-17, com correções de segurança; Alloy 1.20.1 de 2026-09-28). As tags foram verificadas no Docker Hub; o proxy publica tags com prefixo `v`, e `0.5.0` sem `v` não existe.
- **Alternatives considered**: tags flutuantes (`3`, `latest`), rejeitadas pela regra 3.4.4.

## Decision 2: Coletor = Grafana Alloy com `loki.source.docker`

- **Decision**: pipeline `discovery.docker` → `discovery.relabel` → `loki.source.docker` → `loki.process` → `loki.write`, em `infra/alloy/config.alloy`, com `refresh_interval = "5s"`.
- **Rationale**: o `loki.source.docker` lê os logs pela API do Docker (`/containers/{id}/logs`), sem montar `/var/lib/docker/containers`. Isso combina com o proxy de socket (FR-009) e mantém a descoberta dinâmica (FR-003). No protótipo, um contêiner novo ficou consultável em cerca de 10 s (SC-003 ≤ 30 s).
- **Alternatives considered**: ler os arquivos `*-json.log` do host, rejeitado (exige montar o diretório do Docker, perde metadados do Compose e foi descartado na clarificação Q1); Promtail, rejeitado (EOL, clarificação Q3).

## Decision 3: Proxy de socket e permissões mínimas

- **Decision**: `tecnativa/docker-socket-proxy:v0.5.0` com `CONTAINERS=1`, `NETWORKS=1`, `PING=1`, `VERSION=1`, `EVENTS=0`, `POST=0` e todas as demais seções em `0`. O socket é montado `:ro` só nesse serviço.
- **Rationale**: o `discovery.docker` também consulta `/networks` para montar rótulos de rede; sem `NETWORKS=1`, a descoberta falha com `403` (verificado). `EVENTS` não é necessário (verificado). Com `POST=0`, o HAProxy nega todo método que não seja GET: um `POST /containers/create` retornou `403 Forbidden` (verificado, SC-008).
- **Risco residual**: GET em `/containers/{id}/json` expõe as variáveis de ambiente dos contêineres. Mitigação: a rede dedicada (Decision 4) faz com que só o coletor alcance o proxy.
- **Alternatives considered**: socket direto no coletor, rejeitado (Q1); proxy próprio, rejeitado (manutenção e superfície de ataque).

## Decision 4: Topologia de rede

- **Decision**: nova rede `docker-api` (nome `${COMPOSE_PROJECT_NAME:-jhonny_v}-docker-api`, `internal: true`) com só `socket-proxy` e `alloy`. `alloy` e `loki` também ficam na `jhonny-core`.
- **Rationale**: um contêiner na `jhonny-core` não alcançou o proxy (timeout, verificado, SC-009). `internal: true` também tira a saída para a internet.
- **Alternatives considered**: proxy na `jhonny-core`, rejeitado (Q2); rede `jhonny-obs` única, rejeitada (Q2).

## Decision 5: Rótulos e metadados estruturados

- **Decision**:
  - **Rótulos de indexação**: `compose_project`, `compose_service`, `container` (sem a `/` inicial) e `stream`.
  - **Rótulo automático do Loki**: `service_name`, derivado de `compose_service` via `discover_service_name`.
  - **Metadados estruturados**: `level`, `trace_id` e `span_id`, extraídos por `stage.json` + `stage.structured_metadata`.
- **Rationale**: atende FR-005/006/007 sem transformar campos de alta cardinalidade em rótulos. Consultas como `{compose_service="x"} | level="ERROR"` e `| trace_id="..."` funcionam (verificado). Linhas que não são JSON passam intactas, só sem os metadados (FR-008, verificado com stderr em texto).
- **Alternatives considered**: `level` como rótulo, rejeitado (FR-007 pede atributo filtrável sem promoção a rótulo); ID do contêiner como rótulo, rejeitado (FR-006).

## Decision 6: Configuração do Loki

- **Decision**: modo monolítico single-tenant (`auth_enabled: false`), `common.path_prefix: /loki`, filesystem + TSDB `schema: v13`, `compactor.retention_enabled: true`, `limits_config.retention_period: ${LOKI_RETENTION_PERIOD:-7d}` com a flag `-config.expand-env=true`, `allow_structured_metadata: true`, `server.log_format: json` e `analytics.reporting_enabled: false`.
- **Rationale**: atende FR-011/012 e a constituição 3.3.2. `7d` é aceito (normalizado para `1w`), e um valor inválido aborta o start com `not a valid duration string` (fail-fast, verificado). O arquivo passa em `loki -verify-config`.
- **Alternatives considered**: retenção por stream, rejeitada (não pedida); desativar a telemetria só por flag, rejeitado (melhor deixar explícito no arquivo versionado).

## Decision 7: Healthchecks

- **Decision**:
  - **Loki**: `build` de `infra/loki/Dockerfile` (FROM `grafana/loki:3.7.8` + `/bin/busybox` estático de `busybox:1.37.0-musl`). Healthcheck `busybox wget -qO- http://127.0.0.1:3100/ready` com `start_period` ≥ 30 s.
  - **Alloy**: probe em bash puro via `/dev/tcp` em `GET /-/ready` na porta interna `127.0.0.1:12345`.
  - **Proxy**: `wget -qO- http://127.0.0.1:2375/_ping`.
- **Rationale**: a imagem do Loki é distroless, sem shell e sem flag de health (verificado). O Alloy roda sobre Ubuntu e tem `bash`, mas não `curl` nem `wget` (verificado). O proxy tem `wget`. O Loki só fica pronto depois de cerca de 30 s (o ring tem espera inicial; verificado).
- **Alternatives considered**: ver a linha do `build` local em Complexity Tracking, no [plan.md](./plan.md).

## Decision 8: Persistência e posição de leitura

- **Decision**: o volume nomeado `alloy-data` montado em `/var/lib/alloy/data` (`--storage.path`) guarda as posições do `loki.source.docker`. O volume nomeado `loki-data` fica em `/loki`.
- **Rationale**: FR-010/011 e SC-004 (entrega ao menos uma vez após reinício). A imagem já cria `/loki` com dono `10001`, e um volume nomeado novo herda essa propriedade.

## Decision 9: Rotação de logs do Docker (FR-019)

- **Decision**: em cada arquivo `compose.core.yaml`, `compose.llm.yaml` e `compose.obs.yaml`, um bloco `x-logging: &default-logging` com `driver: json-file`, `max-size: ${DOCKER_LOG_MAX_SIZE:-10m}` e `max-file: "${DOCKER_LOG_MAX_FILE:-3}"`. Cada serviço usa `logging: *default-logging`.
- **Rationale**: âncoras YAML valem só dentro do próprio arquivo, que é o mesmo motivo pelo qual o `x-common-environment` se repete. A interpolação foi verificada em `docker compose config`.
- **Alternatives considered**: `daemon.json` do host, rejeitado (Q4); `include` com fragmento comum, rejeitado (não é suportado para trechos de serviço).

## Decision 10: Logs dos próprios componentes

- **Decision**: o Alloy usa `logging { level = "info" format = "json" }`, o Loki usa `server.log_format: json` e o proxy mantém o padrão (texto em stderr). Os três são coletados como qualquer outro contêiner.
- **Rationale**: o Alloy não registra um log por linha encaminhada, então não há laço de realimentação (edge case da spec).

## Decision 11: Carregamento do `.env`

- **Decision**: o quickstart usa `docker compose --env-file .env -f infra/compose.yaml -f infra/compose.obs.yaml ...`.
- **Rationale**: o diretório do projeto Compose é o do primeiro `-f` (`infra/`), então o `.env` da raiz não é lido automaticamente. Todas as variáveis novas têm default, e a camada sobe mesmo sem `.env`.
