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
- `.env` criado a partir de `.env.example`, com `LOKI_GATEWAY_USER`, `LOKI_GATEWAY_PASSWORD` (segredo forte, nunca versionado) e `DOCKER_GID` (`stat -c %g /var/run/docker.sock`) preenchidos; sem eles o `compose up` aborta
- `uv` instalado (testes de aceite, Scenario 16)
- Variáveis do `.env` carregadas no shell: `set -a; . ./.env; set +a`

Nos comandos abaixo, `DC` é um atalho para `docker compose --env-file .env -f infra/compose.yaml -f infra/compose.core.yaml -f infra/compose.obs.yaml`, e `DC_ALL` é o mesmo comando acrescido de `-f infra/compose.llm.yaml`. `LQ` é um atalho para `curl -s -u "$LOKI_GATEWAY_USER:$LOKI_GATEWAY_PASSWORD" http://127.0.0.1:${LOKI_PORT:-3100}`, que precede o caminho da API (ex.: `LQ/loki/api/v1/labels`). Consultas LogQL são feitas com `LQ/loki/api/v1/query_range -G --data-urlencode 'query=<LogQL>'`.

## Setup

1. Validar a composição consolidada: `DC config --quiet` (sem erros).
2. Validar a configuração do Loki: `docker run --rm -v ./infra/loki:/c:ro grafana/loki:3.7.8 -config.file=/c/config.yaml -config.expand-env=true -verify-config` → `config is valid`.
3. Validar a sintaxe do Alloy: `docker run --rm -v ./infra/alloy:/c:ro grafana/alloy:v1.20.1 fmt /c/config.alloy` (exit 0).
4. Validar o Caddyfile: `docker run --rm -e LOKI_GATEWAY_USER=x -e LOKI_GATEWAY_PASSWORD_HASH=x -v ./infra/loki-gateway:/c:ro caddy:2.11.4-alpine caddy validate --config /c/Caddyfile --adapter caddyfile` (exit 0).
5. Subir: `DC up -d --build`.

## Validation Scenarios

### Scenario 1: Subida saudável, sozinha e combinada (SC-007)

Para a camada llm, use `--profile validation`, com `OLLAMA_API_BASE=http://ollama-local-mock:11435` e `LITELLM_MASTER_KEY` definidos no `.env`.

1. Só base + obs: `docker compose --env-file .env -f infra/compose.yaml -f infra/compose.obs.yaml up -d --build`, depois `docker compose --env-file .env -f infra/compose.yaml -f infra/compose.obs.yaml ps`.
2. Subir core e llm por cima, sem derrubar a obs: `DC_ALL up -d`, depois `DC_ALL ps`.
3. Ordem inversa: `DC_ALL down`, subir só base + core + llm e, por último, a obs com `DC_ALL up -d --build`.

**Expected outcome**: nas três execuções, `socket-proxy`, `loki`, `loki-gateway` e `alloy` ficam `healthy` na primeira tentativa. O `loki-gateway` só inicia depois do `loki`, e o `alloy` só inicia depois que `loki-gateway` e `socket-proxy` estão saudáveis. Os serviços das camadas iniciadas depois aparecem no Scenario 2 sem reiniciar a obs (FR-003). No passo 3, as linhas que os serviços core/llm emitiram antes da subida da obs também são consultáveis, porque o histórico retido pelo Docker é ingerido quando não há posição salva (FR-025).

### Scenario 2: Coleta de todos os contêineres (SC-001)

1. `LQ/loki/api/v1/label/compose_service/values`.
2. `LQ/loki/api/v1/label/container/values`.

**Expected outcome**: o passo 1 contém todos os serviços de `DC_ALL config --services` (incluindo `loki`, `loki-gateway`, `alloy` e `socket-proxy`). O passo 2 contém também os contêineres avulsos ativos, fora do Compose (FR-002).

### Scenario 3: Contêiner novo, stdout × stderr e latência de linha (SC-003, SC-002)

1. `docker run -d --rm --name qs-probe busybox:1.37.0-musl sh -c 'echo qs-out; echo qs-err >&2; sleep 40; echo "qs-lat $(date +%s)"; sleep 60'`.
2. Em até 30 s após o passo 1, consultar `{container="qs-probe", stream="stdout"} |= "qs-out"` e `{container="qs-probe", stream="stderr"} |= "qs-err"` via `GET /loki/api/v1/query_range` (SC-003).
3. Com o contêiner já descoberto, consultar `{container="qs-probe"} |= "qs-lat"` a cada 1 s a partir do instante gravado na própria linha e anotar quando ela aparece (SC-002).

**Expected outcome**: no passo 2, cada consulta retorna exatamente a linha correspondente, em ≤ 30 s e sem reiniciar a camada (referência do protótipo: cerca de 10 s). No passo 3, a linha fica consultável em ≤ 10 s após o instante gravado nela.

### Scenario 4: Filtros por serviço, nível e trace (SC-005)

1. Iniciar um emissor JSON: `docker run -d --rm --name qs-json --label com.docker.compose.project=qs --label com.docker.compose.service=qs-json busybox:1.37.0-musl sh -c 'while true; do echo "{\"level\":\"ERROR\",\"trace_id\":\"qs-trace-1\",\"msg\":\"x\"}"; echo "{\"level\":\"INFO\",\"msg\":\"y\"}"; sleep 1; done'`.
2. Consultar `{compose_service="qs-json"} | detected_level="error"` e `{compose_project="qs"} | trace_id="qs-trace-1"`.
3. Consultar `GET /loki/api/v1/labels`.

**Expected outcome**: só linhas `ERROR` e só `qs-trace-1` são retornadas (0 falsos positivos). `level`, `detected_level`, `trace_id` e `span_id` **não** aparecem na lista de rótulos.

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
2. `DC exec alloy bash -c 'exec 3<>/dev/tcp/socket-proxy/2375; printf "POST /containers/create HTTP/1.0\r\nContent-Length: 2\r\n\r\n{}" >&3; head -1 <&3'` → `HTTP/1.0 405 Method Not Allowed`. Repetir com `DELETE /containers/x` → `405`, e com `GET /images/json` e `GET /info` → `403 Forbidden`.
3. Topologia: `docker inspect $(DC ps -q socket-proxy) --format '{{json .NetworkSettings.Networks}}'` → só a rede `jhonny_v-docker-api`. Depois, `docker network inspect jhonny_v-docker-api --format '{{range .Containers}}{{.Name}} {{end}}'` → só `socket-proxy` e `alloy`.
4. Amostra: `docker run --rm --network jhonny_v-core busybox:1.37.0-musl wget -qO- -T 3 http://socket-proxy:2375/_ping` → falha (nome não resolvido ou timeout).

**Expected outcome**: todas as verificações confirmam o isolamento. O passo 3 prova o SC-009 de forma exaustiva; o passo 4 é a amostra de conectividade.

### Scenario 8: Exposição e autenticação do Loki (SC-010)

1. `docker port $(DC ps -q loki)` → `3100/tcp -> 127.0.0.1:3100`.
2. Linux: `curl -s --max-time 3 http://$(hostname -I | awk '{print $1}'):${LOKI_PORT:-3100}/ready` → falha (conexão recusada). Em macOS/Windows, use o IP da interface de rede principal.
3. `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:${LOKI_PORT:-3100}/loki/api/v1/labels` → `401`. Com `-u errado:errado` → `401`. Com `LQ/loki/api/v1/labels` → `200`.
4. `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:${LOKI_PORT:-3100}/ready` → `200` (exceção de liveness).
5. `docker run --rm --network jhonny_v-core busybox:1.37.0-musl wget -qO- -T 3 http://loki:3101/ready` → falha (Loki só em loopback).

**Expected outcome**: nenhum bind em `0.0.0.0` e nenhuma resposta por interface não-loopback. Toda consulta exige credencial válida, exceto `/ready`, e o Loki não é alcançável sem passar pelo gateway. Os demais serviços da camada obs não publicam portas.

### Scenario 9: Retenção configurável (FR-012)

1. `docker run --rm -e LOKI_RETENTION_PERIOD=72h -v ./infra/loki:/c:ro grafana/loki:3.7.8 -config.file=/c/config.yaml -config.expand-env=true -print-config-stderr -verify-config 2>&1 | grep retention_period` → `3d`.
2. Repetir sem a variável → `1w` (default de 7 dias).
3. Repetir com `LOKI_RETENTION_PERIOD=abc` → erro `not a valid duration string`.

### Scenario 10: Rotação de logs em todas as camadas (SC-011)

1. `docker compose --env-file .env -f infra/compose.yaml -f infra/compose.core.yaml -f infra/compose.llm.yaml -f infra/compose.obs.yaml config --format json`, conferindo `services.*.logging` em todos os serviços.

**Expected outcome**: 100% dos serviços com `driver: json-file`, `max-size: 10m` e `max-file: "3"`.

### Scenario 11: Nenhum log em arquivo, logs próprios em JSON (SC-006, FR-016, FR-020)

1. Revisar `infra/compose*.yaml`, `infra/loki/config.yaml`, `infra/alloy/config.alloy` e `infra/loki-gateway/Caddyfile`.
2. `DC logs --no-log-prefix --tail 5 loki loki-gateway alloy socket-proxy`.
3. Com a camada ociosa por 5 min, contar por minuto as linhas novas de `{compose_service=~"loki|loki-gateway|alloy|socket-proxy"}`.

**Expected outcome**: no passo 1, nenhum serviço configura saída de log para arquivo nem monta volume de logs. No passo 2, cada linha é um objeto JSON válido. No passo 3, com a camada ociosa por 5 min, o total é ≤ 60 linhas/min, e o 5º minuto não passa de 1,2× o 2º (SC-015): não há linha por push nem por healthcheck.

### Scenario 12: Persistência do armazenamento (FR-011)

1. Com dados já ingeridos (Scenario 3), executar `DC rm -sf loki` e `DC up -d loki`, e aguardar `healthy`.
2. Repetir a consulta `{container="qs-probe"} |= "qs-out"` sobre a janela original.

**Expected outcome**: a linha continua consultável depois da recriação do contêiner.

### Scenario 13: Revisão documental (FR-014, FR-017, FR-018, FR-021)

1. `ls infra/alloy/config.alloy infra/loki/config.yaml infra/loki-gateway/Caddyfile` → existem; `ls infra/promtail` → não existe.
2. `grep -nE 'LOKI_PORT|LOKI_RETENTION_PERIOD|LOKI_LOG_LEVEL|DOCKER_LOG_MAX_SIZE|DOCKER_LOG_MAX_FILE|LOKI_GATEWAY_USER|LOKI_GATEWAY_PASSWORD|DOCKER_GID' .env.example` → as 8 variáveis, com os defaults ou placeholders do [contrato](./contracts/logs-aggregation-contract.md#5-variáveis-de-ambiente).
3. `grep -rni promtail infra docs/issues/v0.1/ISSUE-103.md docs/milestones/v0.1-infra-core.md` → nenhuma menção ao Promtail como componente adotado.

### Scenario 14: Mascaramento de segredos (SC-012, FR-022)

1. `docker run -d --rm --name qs-secret busybox:1.37.0-musl sh -c 'B=Bea; echo "Authorization: ${B}rer qsTOKENabc123"; echo "{\"password\":\"qsPass1\"}"; echo "token=qsTok2 api_key=qsKey3"; echo "key sk-qsABCDEFGHIJKLMNOP end"; sleep 60'`.
2. Consultar `{container="qs-secret"}`.
3. Consultar `{container="qs-secret"} |~ "qsTOKENabc123|qsPass1|qsTok2|qsKey3|sk-qsABCDEFGHIJKLMNOP"`.

**Expected outcome**: no passo 2, as 4 linhas aparecem com os valores substituídos por `<redacted>`. No passo 3, a consulta retorna 0 linhas.

### Scenario 15: Truncamento e timestamp (SC-013, FR-023, FR-024)

1. `docker run -d --rm --name qs-long busybox:1.37.0-musl sh -c 'head -c 300000 /dev/zero | tr "\0" a; echo; sleep 30'`.
2. Consultar `{container="qs-long"}` e medir o tamanho da linha retornada; comparar o timestamp com `docker logs -t qs-long`.

**Expected outcome**: a linha é armazenada com 262.144 caracteres, e o timestamp é igual ao do Docker.

### Scenario 16: Testes de aceite automatizados (SC-014, FR-027)

1. `cd infra && uv sync --extra dev && uv run ruff check . && uv run black --check .`.
2. Com a stack no ar e o `.env` carregado: `uv run pytest -v`.

**Expected outcome**: lint sem erros e 100% dos testes aprovados, sem testes pulados, cobrindo os SC-001 a SC-013 e o SC-015. O mesmo resultado precisa aparecer no workflow `.github/workflows/infra-obs.yaml` do pull request (FR-027).

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
| FR-011 | Scenario 12 | FR-022 | Scenario 14 |
| FR-023 | Scenario 15 | FR-024 | Scenario 15 |
| FR-025 | Scenario 1 (passo 3) | FR-026 | Contrato §6; revisão de `infra/alloy/config.alloy` (defaults do `loki.write`) |
| FR-027 | Scenario 16 | | |

## Teardown

- `DC down` (preserva os volumes) ou `DC down -v` (remove `loki-data` e `alloy-data`).
- `docker rm -f qs-json qs-probe qs-seq qs-secret qs-long 2>/dev/null`.
