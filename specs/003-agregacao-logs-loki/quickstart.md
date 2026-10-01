# Quickstart: Agregação Centralizada de Logs de Contêineres (Grafana Alloy + Loki)

## Purpose

Validar ponta a ponta que a camada `infra/compose.obs.yaml` coleta `stdout`/`stderr` de todos os contêineres, indexa no Loki com os rótulos esperados, respeita as garantias de segurança e aplica a rotação de logs em todas as camadas.

Consulte também:
- [Contrato da camada de logs](./contracts/logs-aggregation-contract.md)
- [Data Model](./data-model.md)

Cada cenário referencia os IDs de SC da [spec](./spec.md). Registre a saída de cada comando como evidência (constituição 6.2.4).

## Prerequisites

- Docker Engine + Docker Compose v2
- `curl` no host
- `.env` criado a partir de `.env.example` (opcional; todas as variáveis desta camada têm default)

Nos comandos abaixo, `DC` é um atalho para `docker compose --env-file .env -f infra/compose.yaml -f infra/compose.core.yaml -f infra/compose.obs.yaml`.

## Setup

1. Validar a composição consolidada: `DC config --quiet` (sem erros).
2. Validar a configuração do Loki: `docker run --rm -v ./infra/loki:/c:ro grafana/loki:3.7.8 -config.file=/c/config.yaml -config.expand-env=true -verify-config` → `config is valid`.
3. Validar a sintaxe do Alloy: `docker run --rm -v ./infra/alloy:/c:ro grafana/alloy:v1.20.1 fmt /c/config.alloy` (exit 0).
4. Subir: `DC up -d --build`.

## Validation Scenarios

### Scenario 1: Subida saudável (SC-007)

1. `DC ps`.

**Expected outcome**: `socket-proxy`, `loki` e `alloy` em `healthy` na primeira tentativa. O `alloy` só inicia depois que `loki` e `socket-proxy` estão saudáveis.

### Scenario 2: Coleta de todos os contêineres (SC-001, SC-002)

1. `curl -s http://127.0.0.1:${LOKI_PORT:-3100}/loki/api/v1/label/compose_service/values`.

**Expected outcome**: contém `postgres`, `redis`, `rabbitmq`, `loki`, `alloy` e `socket-proxy`.

### Scenario 3: Contêiner novo, stdout × stderr (SC-002, SC-003)

1. `docker run -d --rm --name qs-probe busybox:1.37.0-musl sh -c 'echo qs-out; echo qs-err >&2; sleep 60'`.
2. Em até 30 s, consultar `{container="qs-probe", stream="stdout"} |= "qs-out"` e `{container="qs-probe", stream="stderr"} |= "qs-err"` via `GET /loki/api/v1/query_range`.

**Expected outcome**: cada consulta retorna exatamente a linha correspondente, sem reiniciar a camada. Referência do protótipo: cerca de 10 s.

### Scenario 4: Filtros por serviço, nível e trace (SC-005)

1. Iniciar um emissor JSON: `docker run -d --rm --name qs-json --label com.docker.compose.project=qs --label com.docker.compose.service=qs-json busybox:1.37.0-musl sh -c 'while true; do echo "{\"level\":\"ERROR\",\"trace_id\":\"qs-trace-1\",\"msg\":\"x\"}"; echo "{\"level\":\"INFO\",\"msg\":\"y\"}"; sleep 1; done'`.
2. Consultar `{compose_service="qs-json"} | level="ERROR"` e `{compose_project="qs"} | trace_id="qs-trace-1"`.
3. Consultar `GET /loki/api/v1/labels`.

**Expected outcome**: só linhas `ERROR` e só `qs-trace-1` são retornadas (0 falsos positivos). `level`, `trace_id` e `span_id` **não** aparecem na lista de rótulos.

### Scenario 5: Linha não-JSON e JSON malformado (FR-008)

1. `docker run --rm --name qs-bad busybox:1.37.0-musl sh -c 'echo "{broken json"; echo plain; sleep 15'`.

**Expected outcome**: as duas linhas são consultáveis por `{container="qs-bad"}`.

### Scenario 6: Reinício do coletor sem lacuna (SC-004)

1. Com `qs-json` ativo, executar `DC restart alloy` e aguardar `healthy`.
2. Contar as linhas `qs-json` por segundo no intervalo do reinício (`query_range` com `step=1s` sobre `count_over_time`).

**Expected outcome**: nenhum segundo sem linhas; duplicação residual é aceitável.

### Scenario 7: Segurança do proxy (SC-008, SC-009)

1. `docker inspect $(DC ps -q alloy) --format '{{json .Mounts}}'` → sem `docker.sock`.
2. `DC exec alloy bash -c 'exec 3<>/dev/tcp/socket-proxy/2375; printf "POST /containers/create HTTP/1.0\r\nContent-Length: 2\r\n\r\n{}" >&3; head -1 <&3'` → `HTTP/1.0 403 Forbidden`.
3. `docker run --rm --network jhonny_v-core busybox:1.37.0-musl wget -qO- -T 3 http://socket-proxy:2375/_ping` → falha (nome não resolvido ou timeout).

**Expected outcome**: as três verificações confirmam o isolamento.

### Scenario 8: Exposição do Loki (SC-010)

1. `docker port $(DC ps -q loki)` → `3100/tcp -> 127.0.0.1:3100`.

**Expected outcome**: nenhum bind em `0.0.0.0`. Os demais serviços da camada obs não publicam portas.

### Scenario 9: Retenção configurável (FR-012)

1. `docker run --rm -e LOKI_RETENTION_PERIOD=72h -v ./infra/loki:/c:ro grafana/loki:3.7.8 -config.file=/c/config.yaml -config.expand-env=true -print-config-stderr -verify-config 2>&1 | grep retention_period` → `3d`.
2. Repetir sem a variável → `1w` (default de 7 dias).
3. Repetir com `LOKI_RETENTION_PERIOD=abc` → erro `not a valid duration string`.

### Scenario 10: Rotação de logs em todas as camadas (SC-011)

1. `docker compose --env-file .env -f infra/compose.yaml -f infra/compose.core.yaml -f infra/compose.llm.yaml -f infra/compose.obs.yaml config --format json`, conferindo `services.*.logging` em todos os serviços.

**Expected outcome**: 100% dos serviços com `driver: json-file`, `max-size: 10m` e `max-file: "3"`.

### Scenario 11: Nenhum log em arquivo (SC-006)

1. Revisar `infra/compose*.yaml`, `infra/loki/config.yaml` e `infra/alloy/config.alloy`.

**Expected outcome**: nenhum serviço configura saída de log para arquivo nem monta volume de logs.

## Teardown

- `DC down` (preserva os volumes) ou `DC down -v` (remove `loki-data` e `alloy-data`).
- `docker rm -f qs-json qs-probe 2>/dev/null`.
