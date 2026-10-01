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

Nos comandos abaixo, `DC` é um atalho para `docker compose --env-file .env -f infra/compose.yaml -f infra/compose.core.yaml -f infra/compose.obs.yaml`, e `DC_ALL` é o mesmo comando acrescido de `-f infra/compose.llm.yaml`.

## Setup

1. Validar a composição consolidada: `DC config --quiet` (sem erros).
2. Validar a configuração do Loki: `docker run --rm -v ./infra/loki:/c:ro grafana/loki:3.7.8 -config.file=/c/config.yaml -config.expand-env=true -verify-config` → `config is valid`.
3. Validar a sintaxe do Alloy: `docker run --rm -v ./infra/alloy:/c:ro grafana/alloy:v1.20.1 fmt /c/config.alloy` (exit 0).
4. Subir: `DC up -d --build`.

## Validation Scenarios

### Scenario 1: Subida saudável, sozinha e combinada (SC-007)

1. Só base + obs: `docker compose --env-file .env -f infra/compose.yaml -f infra/compose.obs.yaml up -d --build`, depois `docker compose --env-file .env -f infra/compose.yaml -f infra/compose.obs.yaml ps`.
2. Subir core e llm por cima, sem derrubar a obs: `DC_ALL up -d`, depois `DC_ALL ps`.
3. Ordem inversa: `DC_ALL down`, subir só base + core + llm e, por último, a obs com `DC_ALL up -d --build`.

**Expected outcome**: nas três execuções, `socket-proxy`, `loki` e `alloy` ficam `healthy` na primeira tentativa, e o `alloy` só inicia depois que `loki` e `socket-proxy` estão saudáveis. Os serviços das camadas iniciadas depois aparecem no Scenario 2 sem reiniciar a obs (FR-003).

### Scenario 2: Coleta de todos os contêineres (SC-001)

1. `curl -s http://127.0.0.1:${LOKI_PORT:-3100}/loki/api/v1/label/compose_service/values`.
2. `curl -s http://127.0.0.1:${LOKI_PORT:-3100}/loki/api/v1/label/container/values`.

**Expected outcome**: o passo 1 contém todos os serviços de `DC_ALL config --services` (incluindo `loki`, `alloy` e `socket-proxy`). O passo 2 contém também os contêineres avulsos ativos, fora do Compose (FR-002).

### Scenario 3: Contêiner novo, stdout × stderr e latência de linha (SC-003, SC-002)

1. `docker run -d --rm --name qs-probe busybox:1.37.0-musl sh -c 'echo qs-out; echo qs-err >&2; sleep 40; echo "qs-lat $(date +%s)"; sleep 60'`.
2. Em até 30 s após o passo 1, consultar `{container="qs-probe", stream="stdout"} |= "qs-out"` e `{container="qs-probe", stream="stderr"} |= "qs-err"` via `GET /loki/api/v1/query_range` (SC-003).
3. Com o contêiner já descoberto, consultar `{container="qs-probe"} |= "qs-lat"` a cada 1 s a partir do instante gravado na própria linha e anotar quando ela aparece (SC-002).

**Expected outcome**: no passo 2, cada consulta retorna exatamente a linha correspondente, em ≤ 30 s e sem reiniciar a camada (referência do protótipo: cerca de 10 s). No passo 3, a linha fica consultável em ≤ 10 s após o instante gravado nela.

### Scenario 4: Filtros por serviço, nível e trace (SC-005)

1. Iniciar um emissor JSON: `docker run -d --rm --name qs-json --label com.docker.compose.project=qs --label com.docker.compose.service=qs-json busybox:1.37.0-musl sh -c 'while true; do echo "{\"level\":\"ERROR\",\"trace_id\":\"qs-trace-1\",\"msg\":\"x\"}"; echo "{\"level\":\"INFO\",\"msg\":\"y\"}"; sleep 1; done'`.
2. Consultar `{compose_service="qs-json"} | level="ERROR"` e `{compose_project="qs"} | trace_id="qs-trace-1"`.
3. Consultar `GET /loki/api/v1/labels`.

**Expected outcome**: só linhas `ERROR` e só `qs-trace-1` são retornadas (0 falsos positivos). `level`, `trace_id` e `span_id` **não** aparecem na lista de rótulos.

### Scenario 5: Linha não-JSON e JSON malformado (FR-008)

1. `docker run --rm --name qs-bad busybox:1.37.0-musl sh -c 'echo "{broken json"; echo plain; sleep 15'`.

**Expected outcome**: as duas linhas são consultáveis por `{container="qs-bad"}`.

### Scenario 6: Reinício do coletor sem perda (SC-004)

1. Iniciar um emissor de sequência: `docker run -d --rm --name qs-seq busybox:1.37.0-musl sh -c 'i=0; while true; do i=$((i+1)); echo "seq=$i"; sleep 0.1; done'`.
2. Depois de ≥ 30 s, executar `DC restart alloy` e aguardar `healthy`; deixar rodar mais 30 s.
3. Consultar `{container="qs-seq"}` cobrindo toda a janela (`query_range` com `limit` suficiente), extrair os números `seq=N` e calcular os números únicos (`sort -n -u`).

**Expected outcome**: os números únicos formam uma sequência contínua, do primeiro ao último retornado, sem nenhum número faltando. Linhas duplicadas são aceitáveis.

### Scenario 7: Segurança do proxy (SC-008, SC-009)

1. `docker inspect $(DC ps -q alloy) --format '{{json .Mounts}}'` → sem `docker.sock`.
2. `DC exec alloy bash -c 'exec 3<>/dev/tcp/socket-proxy/2375; printf "POST /containers/create HTTP/1.0\r\nContent-Length: 2\r\n\r\n{}" >&3; head -1 <&3'` → `HTTP/1.0 403 Forbidden`.
3. Topologia: `docker inspect $(DC ps -q socket-proxy) --format '{{json .NetworkSettings.Networks}}'` → só a rede `jhonny_v-docker-api`. Depois, `docker network inspect jhonny_v-docker-api --format '{{range .Containers}}{{.Name}} {{end}}'` → só `socket-proxy` e `alloy`.
4. Amostra: `docker run --rm --network jhonny_v-core busybox:1.37.0-musl wget -qO- -T 3 http://socket-proxy:2375/_ping` → falha (nome não resolvido ou timeout).

**Expected outcome**: todas as verificações confirmam o isolamento. O passo 3 prova o SC-009 de forma exaustiva; o passo 4 é a amostra de conectividade.

### Scenario 8: Exposição do Loki (SC-010)

1. `docker port $(DC ps -q loki)` → `3100/tcp -> 127.0.0.1:3100`.
2. Linux: `curl -s --max-time 3 http://$(hostname -I | awk '{print $1}'):${LOKI_PORT:-3100}/ready` → falha (conexão recusada). Em macOS/Windows, use o IP da interface de rede principal.

**Expected outcome**: nenhum bind em `0.0.0.0` e nenhuma resposta por interface não-loopback. Os demais serviços da camada obs não publicam portas.

### Scenario 9: Retenção configurável (FR-012)

1. `docker run --rm -e LOKI_RETENTION_PERIOD=72h -v ./infra/loki:/c:ro grafana/loki:3.7.8 -config.file=/c/config.yaml -config.expand-env=true -print-config-stderr -verify-config 2>&1 | grep retention_period` → `3d`.
2. Repetir sem a variável → `1w` (default de 7 dias).
3. Repetir com `LOKI_RETENTION_PERIOD=abc` → erro `not a valid duration string`.

### Scenario 10: Rotação de logs em todas as camadas (SC-011)

1. `docker compose --env-file .env -f infra/compose.yaml -f infra/compose.core.yaml -f infra/compose.llm.yaml -f infra/compose.obs.yaml config --format json`, conferindo `services.*.logging` em todos os serviços.

**Expected outcome**: 100% dos serviços com `driver: json-file`, `max-size: 10m` e `max-file: "3"`.

### Scenario 11: Nenhum log em arquivo, logs próprios em JSON (SC-006, FR-016, FR-020)

1. Revisar `infra/compose*.yaml`, `infra/loki/config.yaml` e `infra/alloy/config.alloy`.
2. `DC logs --no-log-prefix --tail 5 loki alloy`.

**Expected outcome**: no passo 1, nenhum serviço configura saída de log para arquivo nem monta volume de logs. No passo 2, cada linha é um objeto JSON válido.

### Scenario 12: Persistência do armazenamento (FR-011)

1. Com dados já ingeridos (Scenario 3), executar `DC rm -sf loki` e `DC up -d loki`, e aguardar `healthy`.
2. Repetir a consulta `{container="qs-probe"} |= "qs-out"` sobre a janela original.

**Expected outcome**: a linha continua consultável depois da recriação do contêiner.

### Scenario 13: Revisão documental (FR-014, FR-017, FR-018, FR-021)

1. `ls infra/alloy/config.alloy infra/loki/config.yaml` → existem; `ls infra/promtail` → não existe.
2. `grep -nE 'LOKI_PORT|LOKI_RETENTION_PERIOD|LOKI_LOG_LEVEL|DOCKER_LOG_MAX_SIZE|DOCKER_LOG_MAX_FILE' .env.example` → as 5 variáveis, com os defaults do [contrato](./contracts/logs-aggregation-contract.md#5-variáveis-de-ambiente).
3. `grep -rni promtail infra docs/issues/v0.1/ISSUE-103.md docs/milestones/v0.1-infra-core.md` → nenhuma menção ao Promtail como componente adotado.

## Traceability Matrix (FR → evidência)

| FR | Evidência | FR | Evidência |
|----|-----------|----|-----------|
| FR-001 | Scenarios 2, 3 | FR-012 | Scenario 9 |
| FR-002 | Scenario 2 (passo 2) | FR-013 | Setup 1, Scenario 1 |
| FR-003 | Scenarios 1, 3 | FR-014 | Setup 2–3, Scenario 13 |
| FR-004 | Scenarios 2–4 | FR-015 | Scenario 8 |
| FR-005 | Scenarios 2, 4 | FR-016 | Scenario 11 |
| FR-006 | Scenario 4 (passo 3) | FR-017 | Scenario 13 |
| FR-007 | Scenario 4 | FR-018 | Scenario 13 |
| FR-008 | Scenario 5 | FR-019 | Scenario 10 |
| FR-009 | Scenario 7 | FR-020 | Scenario 11 |
| FR-010 | Scenario 6 | FR-021 | Scenario 13 |
| FR-011 | Scenario 12 | | |

## Teardown

- `DC down` (preserva os volumes) ou `DC down -v` (remove `loki-data` e `alloy-data`).
- `docker rm -f qs-json qs-probe qs-seq 2>/dev/null`.
