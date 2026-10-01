# Tasks: Agregação Centralizada de Logs de Contêineres (Grafana Alloy + Loki)

**Input**: Design documents from `/specs/003-agregacao-logs-loki/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: os testes são obrigatórios nesta feature. O FR-027 e o SC-014 exigem testes de aceite `pytest` em `infra/tests/`, rodados contra a stack em execução. Pela constituição 3.5.4, os testes de cada história são escritos **antes** da implementação e precisam falhar antes dela (a stack ainda não existe).

**Organization**: as tarefas estão agrupadas por história de usuário, para que cada uma possa ser implementada e testada de forma independente.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependências)
- **[Story]**: história de usuário à qual a tarefa pertence (US1, US2, US3)
- Toda descrição inclui o caminho exato do arquivo

## Path Conventions

- Overlay da camada: `infra/compose.obs.yaml`, combinado com `infra/compose.yaml`
- Configurações: `infra/loki/`, `infra/loki-gateway/`, `infra/alloy/`
- Testes de aceite: `infra/pyproject.toml` + `infra/tests/`
- Variáveis de ambiente: `.env.example`
- Comando base (`DC`): `docker compose --env-file .env -f infra/compose.yaml -f infra/compose.core.yaml -f infra/compose.obs.yaml` (ver [quickstart.md](./quickstart.md))
- Restrição de rede (research, Decision 12): nenhum serviço resolvido por nome ou com porta publicada pode estar em mais de uma rede

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: criar a estrutura de diretórios, o projeto de testes e o contrato de variáveis.

- [ ] T001 Criar os diretórios `infra/loki/`, `infra/loki-gateway/`, `infra/alloy/` e `infra/tests/` (estrutura do plan.md)
- [ ] T002 Criar `infra/pyproject.toml` (FR-027; constituição 3.1.2, 3.1.4, 3.5.1):
  - projeto `jhonny-v-infra-tests`, `requires-python = ">=3.12"`;
  - dependências `pytest` e `httpx`; extra `dev` com `black` e `ruff`;
  - `[tool.pytest.ini_options]` com `testpaths = ["tests"]` e os markers `disruptive` (reinicia ou recria serviços) e `slow`;
  - `[tool.ruff]` e `[tool.black]` com `line-length = 88` e `target-version` py312;
  - sem `requirements.txt`.
- [ ] T003 Gerar `infra/uv.lock` com `cd infra && uv lock`, e confirmar que `infra/.gitignore` (ou o `.gitignore` da raiz) ignora `infra/.venv/` e `__pycache__/` (constituição 3.4.7)
- [ ] T004 [P] Atualizar `.env.example`, na seção de observabilidade (FR-018):
  - `LOKI_RETENTION_PERIOD=7d`, `LOKI_LOG_LEVEL=info`, `DOCKER_LOG_MAX_SIZE=10m`, `DOCKER_LOG_MAX_FILE=3`;
  - `LOKI_GATEWAY_USER=` e `LOKI_GATEWAY_PASSWORD=` vazios, com comentário "obrigatório; segredo, não versionar";
  - `DOCKER_GID=`, com comentário "obrigatório; `stat -c %g /var/run/docker.sock`";
  - ajustar o comentário do `LOKI_PORT` para "porta do gateway autenticado do Loki".

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: fixtures de teste e esqueleto do overlay, que todas as histórias usam.

**⚠️ CRITICAL**: nenhuma história pode começar antes de esta fase terminar.

- [ ] T005 Criar `infra/tests/conftest.py` com fixtures de sessão, todas com type hints e docstrings estilo Google:
  - `env`: lê `LOKI_GATEWAY_USER`, `LOKI_GATEWAY_PASSWORD`, `LOKI_PORT` (default 3100) e `HOST_IP` (default 127.0.0.1) do ambiente; falha com mensagem clara se faltar credencial;
  - `loki`: um `httpx.Client` com `base_url` do gateway e `auth=(user, password)`;
  - `query_lines(logql, since)`: chama `/loki/api/v1/query_range` e devolve as linhas com seus labels e metadados;
  - `wait_for_lines(logql, predicate, timeout)`: polling de 1 s até o predicado valer ou o tempo esgotar;
  - `compose(*args)`: executa `docker compose --env-file ../.env -f compose.yaml -f compose.core.yaml -f compose.obs.yaml …` via `subprocess`;
  - `probe_container(name, script, labels=None)`: sobe `busybox:1.37.0-musl` com `docker run -d --rm`, faz cleanup no teardown e gera nomes únicos com o prefixo `qs-`;
  - `llm_env`: valida que `LITELLM_MASTER_KEY` está definido e define `OLLAMA_API_BASE=http://ollama-local-mock:11435` e `COMPOSE_PROFILES=core,validation` para a camada llm (SC-007). Se faltar algum pré-requisito, MUST falhar com mensagem explícita, nunca chamar `pytest.skip` (SC-014; constituição 6.3).
- [ ] T006 Criar `infra/tests/__init__.py` vazio e `infra/tests/README.md` com os pré-requisitos (`.env` preenchido, stack no ar) e os comandos `uv sync --extra dev`, `uv run pytest -v` e `uv run pytest -m "not disruptive"`
- [ ] T007 Criar o esqueleto de `infra/compose.obs.yaml` (FR-013, FR-019; research, Decisions 4, 8 e 9). No topo, um comentário que declara a política de `env_file` (constituição 3.4.2 / IV): nenhum serviço usa `env_file`, e as variáveis vêm de interpolação via `--env-file .env`, com default ou obrigatórias (`${VAR:?}`). Cada serviço declara seu bloco `environment` explicitamente. O esqueleto contém:
  - bloco `x-logging: &default-logging` com `driver: json-file`, `max-size: ${DOCKER_LOG_MAX_SIZE:-10m}` e `max-file: "${DOCKER_LOG_MAX_FILE:-3}"`;
  - a rede `docker-api` (`name: ${COMPOSE_PROJECT_NAME:-jhonny_v}-docker-api`, `internal: true`);
  - os volumes `loki-data` e `alloy-data`, com `name:` prefixado pelo projeto;
  - `services: {}` vazio, a preencher nas histórias.
- [ ] T008 Validar o esqueleto com `docker compose --env-file .env -f infra/compose.yaml -f infra/compose.obs.yaml config --quiet` (Setup 1 do quickstart)

**Checkpoint**: fixtures e esqueleto prontos; as histórias podem começar.

---

## Phase 3: User Story 1 - Consultar os logs de todos os contêineres em um único ponto (Priority: P1) 🎯 MVP

**Goal**: entregar a coleta de `stdout`/`stderr` de todos os contêineres do host, com segurança. Isso inclui o proxy de socket só leitura, o Loki em loopback, o gateway autenticado, o mascaramento de segredos, o truncamento, a retenção configurável e a entrega "ao menos uma vez".

**Independent Test**: subir base + core + obs, escrever uma linha conhecida num contêiner avulso e consultá-la pelo gateway com credenciais (Scenarios 1–3 e 6–9 do quickstart). Depois, rodar `uv run pytest tests/test_ingestion.py tests/test_gateway.py tests/test_socket_proxy.py`.

### Tests for User Story 1 ⚠️

> Escrever primeiro e confirmar que falham (`uv run pytest` → falha de conexão ou de asserção) antes de T019.

- [ ] T009 [P] [US1] Teste de ingestão em `infra/tests/test_ingestion.py`:
  - SC-001: todos os serviços de `compose config --services` aparecem em `label/compose_service/values`, e um contêiner avulso sem labels Compose aparece em `label/container/values` (FR-002);
  - SC-003: um probe novo fica consultável em ≤ 30 s;
  - edge case de vida curta: um contêiner que imprime uma linha e encerra em ~2 s (`docker run --rm`) tem a linha ingerida;
  - stdout × stderr distinguíveis pelo rótulo `stream`;
  - SC-002: uma linha com timestamp embutido fica consultável em ≤ 10 s.
- [ ] T010 [P] [US1] Teste de gateway em `infra/tests/test_gateway.py` (SC-010, FR-015):
  - sem credencial → `401`; credencial inválida → `401`; credencial válida → `200` em `/loki/api/v1/labels`; `GET /ready` sem credencial → `200`;
  - a porta publicada está ligada só a `127.0.0.1` (`docker port`);
  - um acesso pelo IP não-loopback do host falha;
  - `http://loki:3101/ready` falha a partir de um busybox na rede `jhonny_v-core`.
- [ ] T011 [P] [US1] Teste do proxy em `infra/tests/test_socket_proxy.py` (SC-008, SC-009, FR-009):
  - via `docker compose exec alloy bash /dev/tcp`: `POST /containers/create` e `DELETE /containers/x` → `405`; `GET /images/json` e `GET /info` → `403`; asserções positivas para cada caminho da allowlist: `GET /_ping`, `HEAD /_ping`, `GET /version`, `GET /containers/json`, `GET /containers/<id>/json`, `GET /containers/<id>/logs?stdout=1&tail=1`, `GET /networks` e `GET /networks/<id>` → `200`, com e sem o prefixo `/v1.NN`;
  - os mounts do `alloy` não contêm `docker.sock`;
  - o proxy está só na rede `jhonny_v-docker-api`, e os membros dessa rede são exatamente `socket-proxy` e `alloy`;
  - um busybox em `jhonny_v-core` não alcança `socket-proxy:2375`;
  - `docker inspect` do proxy mostra o usuário `65534:<DOCKER_GID>` e `ReadonlyRootfs=true`.
- [ ] T012 [P] [US1] Teste de mascaramento em `infra/tests/test_masking.py` (SC-012, FR-022):
  - um probe emite uma linha de cada padrão (token `Bearer`, `sk-…`, `"password":"…"`, `token=…`, `api_key=…`), montando a palavra `Bearer` em runtime para evitar falso positivo de secret scanning;
  - todas as linhas aparecem com `<redacted>`;
  - uma busca `|~` pelos valores originais retorna 0 linhas.
- [ ] T013 [P] [US1] Teste de limites de linha em `infra/tests/test_line_limits.py` (SC-013, FR-023, FR-024):
  - uma linha de 300.000 `a` é armazenada com 262.144 caracteres;
  - o timestamp da entrada no Loki é igual ao de `docker logs -t`, com tolerância de 1 ms.
- [ ] T014 [P] [US1] Teste de retenção em `infra/tests/test_retention.py` (FR-012), via `docker run grafana/loki:3.7.8 -verify-config -print-config-stderr` montando `infra/loki/`:
  - `LOKI_RETENTION_PERIOD=72h` → `retention_period: 3d`;
  - sem a variável → `1w`;
  - `abc` → exit ≠ 0 com `not a valid duration string`.
- [ ] T015 [P] [US1] Teste de entrega em `infra/tests/test_delivery.py`, marker `disruptive`:
  - SC-004: um emissor de sequência `seq=N`; `compose restart alloy`; esperar `healthy`; os números únicos consultados formam uma sequência contínua;
  - FR-011: `compose rm -sf loki && compose up -d loki loki-gateway`; uma linha anterior continua consultável;
  - FR-025: um contêiner que logou antes de o `alloy` subir tem essas linhas ingeridas;
  - edge case de reinício do proxy: com o emissor de sequência ativo, `compose restart socket-proxy`; esperar `healthy`; 0 números faltando.
- [ ] T016 [P] [US1] Teste de subida em `infra/tests/test_startup.py` (SC-007, FR-013), marker `disruptive` e `slow`:
  - as combinações base+obs, base+core+llm+obs, e obs por último, uma execução de cada (SC-007); a camada llm usa a fixture `llm_env` (perfil `validation`);
  - os quatro serviços obs ficam `healthy` sem restart (`RestartCount == 0`);
  - a ordem de `StartedAt` respeita `loki` → `loki-gateway` → `alloy`.

### Implementation for User Story 1

- [ ] T017 [P] [US1] Criar `infra/loki/Dockerfile`, com dois estágios (research, Decision 7):
  - `FROM busybox:1.37.0-musl AS probe`;
  - `FROM grafana/loki:3.7.8`;
  - `COPY --from=probe /bin/busybox /usr/bin/busybox`.
- [ ] T018 [P] [US1] Criar `infra/loki/config.yaml` (FR-011, FR-012, FR-020, FR-023; research, Decision 6):
  - `auth_enabled: false`;
  - `server`: `http_listen_address: 127.0.0.1`, `http_listen_port: 3101`, `log_format: json` e `log_level: ${LOKI_LOG_LEVEL:-info}`;
  - `common`, com `path_prefix /loki`, storage filesystem, `replication_factor 1` e ring inmemory;
  - `schema_config` TSDB v13 `from: "2026-01-01"` com `period: 24h`;
  - `compactor`, com `retention_enabled: true` e `delete_request_store: filesystem`;
  - `limits_config`, com `retention_period: ${LOKI_RETENTION_PERIOD:-7d}`, `allow_structured_metadata: true`, `discover_service_name: [compose_service]` (FR-005, exigido já na US1), `max_line_size: 256KB` e `max_line_size_truncate: true`;
  - `analytics.reporting_enabled: false`.
- [ ] T019 [P] [US1] Criar `infra/loki-gateway/Caddyfile` (FR-015, FR-020; research, Decisions 10 e 13):
  - global: `admin off` e `log { output stderr; format json }`;
  - site `:3100`, com access log JSON, matcher `@quiet path /ready /loki/api/v1/push` e `log_skip @quiet`;
  - `handle /ready { reverse_proxy 127.0.0.1:3101 }`;
  - `handle { basic_auth { {$LOKI_GATEWAY_USER} {$LOKI_GATEWAY_PASSWORD_HASH} } reverse_proxy 127.0.0.1:3101 }`;
  - validar com `caddy validate` (Setup 4 do quickstart).
- [ ] T020 [US1] Adicionar o serviço `socket-proxy` em `infra/compose.obs.yaml` (FR-009; research, Decision 3):
  - `image: wollomatic/socket-proxy:1.13.1` e `restart: unless-stopped`;
  - `user: "65534:${DOCKER_GID:?DOCKER_GID obrigatório}"`;
  - hardening: `read_only: true`, `cap_drop: [ALL]` e `security_opt: [no-new-privileges:true]`;
  - `command`: as flags `-logjson`, `-loglevel=INFO`, `-listenip=0.0.0.0`, `-allowfrom=0.0.0.0/0`, `-allowhealthcheck`, e os `-allowGET`/`-allowHEAD` exatos da Decision 3;
  - volume `/var/run/docker.sock:/var/run/docker.sock:ro` e `networks: [docker-api]`;
  - healthcheck `["CMD", "./healthcheck"]`;
  - `logging: *default-logging`.
- [ ] T021 [US1] Adicionar os serviços `loki` e `loki-gateway` em `infra/compose.obs.yaml` (FR-013, FR-015; research, Decisions 7, 12 e 13):
  - `loki`:
    - `build: ./loki`;
    - `command` com `-config.file=/etc/loki/config.yaml` e `-config.expand-env=true`;
    - `environment` com `LOKI_RETENTION_PERIOD` e `LOKI_LOG_LEVEL`;
    - volumes `./loki/config.yaml:/etc/loki/config.yaml:ro` e `loki-data:/loki`;
    - `networks: [jhonny-core]` (só essa rede);
    - `ports: ["${HOST_IP:-127.0.0.1}:${LOKI_PORT:-3100}:3100"]`;
    - healthcheck `/usr/bin/busybox wget -qO- http://127.0.0.1:3101/ready`, com `start_period: 40s`.
  - `loki-gateway`:
    - `image: caddy:2.11.4-alpine` e `network_mode: service:loki`;
    - `environment` com `LOKI_GATEWAY_USER: ${LOKI_GATEWAY_USER:?…}` e `LOKI_GATEWAY_PASSWORD: ${LOKI_GATEWAY_PASSWORD:?…}`;
    - entrypoint `sh -c` que gera o hash com `caddy hash-password --plaintext`, faz `unset` da senha e executa `exec caddy run`;
    - volume `./loki-gateway/Caddyfile:/etc/caddy/Caddyfile:ro`;
    - `depends_on: loki: service_healthy`;
    - healthcheck `wget -qO- http://127.0.0.1:3100/ready`.
  - Ambos com `restart: unless-stopped` e `logging: *default-logging`.
- [ ] T022 [US1] Criar `infra/alloy/config.alloy`, na parte de coleta e entrega (FR-001 a FR-005, FR-010, FR-022, FR-026; research, Decisions 2, 5 e 14):
  - `logging { level = "info" format = "json" }`;
  - `discovery.docker` com `host = "tcp://socket-proxy:2375"` e `refresh_interval = "5s"`;
  - `discovery.relabel`, com as regras para `compose_project`, `compose_service`, `container` (regex `/(.*)`) e `stream`;
  - `loki.source.docker` com `relabel_rules`;
  - `loki.process` com os 3 `stage.replace` da Decision 14, todos com `<redacted>`;
  - `loki.write` com `url = "http://loki:3100/loki/api/v1/push"` e `basic_auth` via `sys.env`, sem sobrescrever os defaults de backoff (FR-026);
  - validar com `alloy fmt` (Setup 3 do quickstart).
- [ ] T023 [US1] Adicionar o serviço `alloy` em `infra/compose.obs.yaml` (FR-010, FR-013):
  - `image: grafana/alloy:v1.20.1`;
  - `command`: `run /etc/alloy/config.alloy --storage.path=/var/lib/alloy/data`;
  - `environment` com as credenciais do gateway (`${VAR:?}`);
  - volumes `./alloy/config.alloy:/etc/alloy/config.alloy:ro` e `alloy-data:/var/lib/alloy/data`;
  - `networks: [jhonny-core, docker-api]`;
  - `depends_on`: `loki-gateway` e `socket-proxy`, ambos `service_healthy`;
  - healthcheck bash via `/dev/tcp` em `127.0.0.1:12345/-/ready`;
  - sem portas publicadas e sem montar `docker.sock`;
  - `restart: unless-stopped` e `logging: *default-logging`.
- [ ] T024 [US1] Subir com `DC up -d --build` e rodar `cd infra && uv run pytest tests/test_ingestion.py tests/test_gateway.py tests/test_socket_proxy.py tests/test_masking.py tests/test_line_limits.py tests/test_retention.py tests/test_delivery.py tests/test_startup.py -v` até passar 100%; registrar a saída como evidência (Scenarios 1–3 e 6–9 do quickstart)

**Checkpoint**: a US1 está funcional e entrega o MVP: logs de todos os contêineres consultáveis com autenticação.

---

## Phase 4: User Story 2 - Filtrar logs por origem e por atributos estruturados (Priority: P2)

**Goal**: extrair `level`, `trace_id` e `span_id` como metadados estruturados, normalizar o nível (`detected_level`) e derivar `service_name`, sem aumentar a cardinalidade dos rótulos.

**Independent Test**: um emissor JSON com `level`/`trace_id` e um emissor de texto. Os filtros por `detected_level` e `trace_id` retornam 0 falsos positivos, e `/labels` lista só os rótulos permitidos (Scenarios 4–5 do quickstart).

### Tests for User Story 2 ⚠️

- [ ] T025 [P] [US2] Teste de filtros em `infra/tests/test_filters.py` (SC-005, FR-005 a FR-008):
  - dois emissores JSON com labels Compose distintos;
  - `| detected_level="error"` retorna só as linhas `ERROR` (testar também `warning` → `warn` e `Info` → `info`);
  - `| trace_id="…"` retorna só o trace esperado;
  - o filtro por `compose_service` isola o serviço;
  - `GET /labels` ⊆ {`compose_project`, `compose_service`, `container`, `stream`, `service_name`}, sem `level`, `detected_level`, `trace_id` nem `span_id`;
  - as linhas `{broken json` e `plain` são consultáveis por `container`.

### Implementation for User Story 2

- [ ] T026 [US2] Acrescentar ao `loki.process` de `infra/alloy/config.alloy`, depois dos `stage.replace`, os estágios `stage.json { expressions = { level = "", trace_id = "", span_id = "" } }` e `stage.structured_metadata { values = { level = "", trace_id = "", span_id = "" } }` (FR-007; research, Decision 5)
- [ ] T027 [US2] Acrescentar a `limits_config` de `infra/loki/config.yaml` a chave `discover_log_levels: true` (FR-007; research, Decision 15). O `discover_service_name` já entra no T018.
- [ ] T028 [US2] Recriar `alloy` e `loki` (`DC up -d --build alloy loki`) e rodar `uv run pytest tests/test_filters.py -v` até passar; registrar a evidência (Scenarios 4–5 do quickstart)

**Checkpoint**: US1 e US2 funcionam de forma independente.

---

## Phase 5: User Story 3 - Garantir conformidade com a política de logs apenas em `stdout`/`stderr` (Priority: P3)

**Goal**: provar que nenhum serviço grava logs em arquivo, que os serviços da camada obs logam em JSON sem laço de realimentação e que todas as camadas aplicam o limite comum de rotação.

**Independent Test**: com `compose config --format json` de todas as camadas, 100% dos serviços têm `json-file` 10m×3; os logs dos quatro serviços obs são JSON válido; a camada ociosa não cresce em volume (Scenarios 10–11 do quickstart).

### Tests for User Story 3 ⚠️

- [ ] T029 [P] [US3] Teste de conformidade em `infra/tests/test_compliance.py` (SC-006, SC-011, SC-015, FR-016, FR-019, FR-020):
  - `config --format json` das 4 camadas: todo serviço tem `logging.driver == "json-file"`, `max-size == "10m"` e `max-file == "3"`;
  - nenhum volume ou bind mount com destino em diretórios de log (`/var/log`, `*.log`);
  - as últimas 20 linhas de `compose logs --no-log-prefix` de `loki`, `loki-gateway`, `alloy` e `socket-proxy` são JSON válido;
  - SC-015: com a camada ociosa por 5 min, contar por minuto as linhas novas de `{compose_service=~"loki|loki-gateway|alloy|socket-proxy"}` (`count_over_time` por janela de 1 m); o total precisa ser ≤ 60 linhas/min, e a contagem do 5º minuto ≤ 1,2× a do 2º; marker `slow`;
  - SC-011: para cada contêiner das camadas, somar o tamanho de `<id>-json.log*` com um contêiner auxiliar sem sudo (`docker run --rm -v /var/lib/docker/containers:/c:ro busybox:1.37.0-musl du -cb /c/<id>/<id>-json.log*`), que deve ser ≤ 30 MB (31.457.280 bytes) com os defaults. Sem `skip`: se a medição falhar, o teste falha (constituição 6.3).

### Implementation for User Story 3

- [ ] T030 [P] [US3] Adicionar o bloco `x-logging: &default-logging`, idêntico ao de T007, em `infra/compose.core.yaml`, e `logging: *default-logging` em `postgres`, `redis` e `rabbitmq`, sem nenhuma outra mudança (FR-019)
- [ ] T031 [P] [US3] Adicionar o mesmo bloco `x-logging` em `infra/compose.llm.yaml`, e `logging: *default-logging` em `ollama-local-mock`, `ollama`, `litellm-cloud-unavailable` e `litellm`, sem nenhuma outra mudança (FR-019)
- [ ] T032 [US3] Recriar as camadas com `DC_ALL up -d` e rodar `uv run pytest tests/test_compliance.py -v` até passar; registrar a evidência (Scenarios 10–11 do quickstart)

**Checkpoint**: as três histórias estão funcionais e verificadas.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: documentação, CI, lint e validação ponta a ponta. O T040 aparece antes do T037 porque o CI precisa existir para a validação final; o ID foi acrescentado no analyze para não renumerar as tarefas.

- [ ] T033 [P] Atualizar `docs/issues/v0.1/ISSUE-103.md` (FR-021):
  - Grafana Alloy no lugar do Promtail;
  - `infra/compose.obs.yaml` no lugar de `compose.obs.yml`;
  - `infra/alloy/config.alloy` no lugar de `infra/promtail/config.yaml`;
  - proxy de socket e gateway autenticado;
  - link para `specs/003-agregacao-logs-loki/`.
- [ ] T034 [P] Atualizar `docs/milestones/v0.1-infra-core.md`: Promtail → Grafana Alloy, com o proxy de socket e o gateway autenticado, sem citar o Promtail como componente adotado (FR-021)
- [ ] T035 [P] Atualizar `README.md`:
  - comando de subida da camada obs (`--env-file .env -f infra/compose.yaml -f infra/compose.obs.yaml`);
  - variáveis obrigatórias (`LOKI_GATEWAY_*`, `DOCKER_GID`);
  - como rodar os testes de aceite (`cd infra && uv run pytest`).
- [ ] T036 [P] Registrar em `docs/adr/` um ADR curto sobre o gateway autenticado com namespace compartilhado e o proxy `wollomatic/socket-proxy` (research, Decisions 3, 12 e 13), e indexá-lo em `docs/README.md`
- [ ] T040 Criar `.github/workflows/infra-obs.yaml` (FR-027, SC-014; research, Decision 18; constituição 3.5.3):
  - `on`: `pull_request` e `push` com `paths` (`infra/**`, `.env.example`, `.github/workflows/infra-obs.yaml`);
  - `permissions: contents: read`, `concurrency` por ref com `cancel-in-progress: true`;
  - job `acceptance` em `ubuntu-24.04`, com `timeout-minutes: 40`;
  - actions fixadas por SHA de commit (`actions/checkout`, `astral-sh/setup-uv`);
  - passos:
    1. Gerar o `.env` a partir de `.env.example`, com `LOKI_GATEWAY_USER=ci`, `LOKI_GATEWAY_PASSWORD` e `LITELLM_MASTER_KEY` gerados com `openssl rand -hex 24` e mascarados com `::add-mask::`, `DOCKER_GID=$(stat -c %g /var/run/docker.sock)` e `OLLAMA_API_BASE=http://ollama-local-mock:11435`;
    2. `cd infra && uv sync --extra dev && uv run ruff check . && uv run black --check .`;
    3. Validações estáticas (Setup 1–4 do quickstart);
    4. `DC up -d --build --wait`;
    5. `uv run pytest -v`;
    6. `if: failure()`: `DC logs --no-color` (stdout do job, sem artefato em arquivo);
    7. `if: always()`: `DC_ALL down -v`.
- [ ] T037 Rodar `cd infra && uv run ruff check . && uv run black --check .` e corrigir até zerar (constituição 3.5.1)
- [ ] T038 Rodar a suíte completa com a stack no ar: `cd infra && uv run pytest -v` (SC-014), sem testes pulados, e confirmar que o workflow do T040 passou no pull request. Executar os Scenarios 13–16 do [quickstart.md](./quickstart.md) e registrar a saída de cada um como evidência (constituição 6.2)
- [ ] T039 Varredura final de conformidade:
  - `grep -rn ':latest' infra/` → vazio;
  - `git ls-files | grep requirements.txt` → vazio;
  - `grep -nE 'min_backoff|max_backoff|max_backoff_retries' infra/alloy/config.alloy` → vazio, o que confirma os defaults de reenvio do FR-026;
  - `grep -rniE 'password|secret' infra/ .env.example` só retorna referências a variáveis, sem valores;
  - `grep -rni promtail infra docs/issues/v0.1/ISSUE-103.md docs/milestones/v0.1-infra-core.md` → nenhuma adoção.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências.
- **Foundational (Phase 2)**: depende do Setup. **Bloqueia todas as histórias.**
- **US1 (Phase 3)**: depende da Foundational. É o MVP.
- **US2 (Phase 4)**: depende da Foundational e, na execução, da stack da US1 (`config.alloy` e `loki/config.yaml` já existentes). Os testes de US2 são independentes dos de US1.
- **US3 (Phase 5)**: T030/T031 dependem só da Foundational (só tocam `compose.core.yaml`/`compose.llm.yaml`). O T029 precisa dos quatro serviços obs no ar (US1).
- **Polish (Phase 6)**: depende das histórias desejadas.

### Within Each User Story

- Testes (T009–T016, T025, T029) são escritos primeiro e falham antes da implementação.
- US1: T017, T018 e T019 são paralelos (arquivos distintos) → T020 → T021 → T022 → T023 → T024. T020, T021 e T023 são sequenciais porque editam o mesmo `compose.obs.yaml`.
- US2: T026 e T027 editam arquivos diferentes e podem ser paralelos, mas ambos dependem de T018 e T022 → T028.
- US3: T030 ∥ T031 → T032.

### Parallel Opportunities

- Setup: T004 em paralelo com T001–T003.
- US1: os 8 testes (T009–T016) em paralelo; T017, T018 e T019 em paralelo.
- US3: T030 e T031 em paralelo, e podem começar junto com a US1.
- Polish: T033–T036 e T040 em paralelo. T038 depende do T040 (CI verde no PR).

---

## Parallel Example: User Story 1

```bash
# Testes (arquivos distintos):
Task: "Teste de ingestão em infra/tests/test_ingestion.py"
Task: "Teste de gateway em infra/tests/test_gateway.py"
Task: "Teste do proxy em infra/tests/test_socket_proxy.py"
Task: "Teste de mascaramento em infra/tests/test_masking.py"

# Configurações independentes:
Task: "Criar infra/loki/Dockerfile"
Task: "Criar infra/loki/config.yaml"
Task: "Criar infra/loki-gateway/Caddyfile"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 (Setup) e Phase 2 (Foundational).
2. Phase 3 (US1): escrever os testes, confirmar que falham, implementar e chegar a 100% verde.
3. **Parar e validar**: com logs de todos os contêineres consultáveis com autenticação, o critério de aceite principal da ISSUE-103 está cumprido.

### Incremental Delivery

1. Setup + Foundational → fixtures e esqueleto.
2. US1 → ingestão segura (MVP).
3. US2 → filtros estruturados e normalização de nível.
4. US3 → conformidade e rotação em todas as camadas.
5. Polish → documentação, CI, lint e suíte completa (SC-014).

---

## Notes

- [P] = arquivos diferentes, sem dependência de tarefa incompleta.
- Testes marcados `disruptive` reiniciam ou recriam serviços; rode-os isolados (`-m disruptive`).
- Faça commit a cada tarefa ou grupo lógico, via `report_progress`.
- Nunca versionar `.env` nem credenciais reais. Nos testes, monte strings parecidas com segredos em runtime.
