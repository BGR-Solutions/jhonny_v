# Research: Agregação Centralizada de Logs de Contêineres (Grafana Alloy + Loki)

Todas as decisões abaixo foram validadas num protótipo descartável (em `/tmp`, fora do repositório) com Docker Engine 28 e as imagens fixadas. Nenhum `NEEDS CLARIFICATION` permanece.

## Decision 1: Versões das imagens

- **Decision**:
  - `grafana/loki:3.7.8`
  - `grafana/alloy:v1.20.1`
  - `wollomatic/socket-proxy:1.13.1`
  - `caddy:2.11.4-alpine`
  - `busybox:1.37.0-musl`, só como estágio de build.
- **Rationale**: são as releases estáveis mais recentes em 2026-10-01:
  - Loki 3.7.8, de 2026-09-17, com correções de segurança;
  - Alloy 1.20.1, de 2026-09-28;
  - socket-proxy 1.13.1, de 2026-08-15;
  - Caddy 2.11.4, de 2026-09-23.

  As tags foram verificadas no registro.
- **Alternatives considered**:
  - Tags flutuantes (`3`, `latest`): rejeitadas pela regra 3.4.4.
  - `tecnativa/docker-socket-proxy:v0.5.0`: substituído pela decisão do checklist Q7 (ver Decision 3).
## Decision 2: Coletor = Grafana Alloy com `loki.source.docker`

- **Decision**: pipeline `discovery.docker` → `discovery.relabel` → `loki.source.docker` → `loki.process` → `loki.write`, em `infra/alloy/config.alloy`, com `refresh_interval = "5s"`.
- **Rationale**: o `loki.source.docker` lê os logs pela API do Docker (`/containers/{id}/logs`), sem montar `/var/lib/docker/containers`. Isso combina com o proxy de socket (FR-009) e mantém a descoberta dinâmica (FR-003). No protótipo, um contêiner novo ficou consultável em cerca de 10 s (SC-003 ≤ 30 s).
- **Alternatives considered**: ler os arquivos `*-json.log` do host, rejeitado (exige montar o diretório do Docker, perde metadados do Compose e foi descartado na clarificação Q1); Promtail, rejeitado (EOL, clarificação Q3).

## Decision 3: Proxy de socket e permissões mínimas

- **Decision**: `wollomatic/socket-proxy:1.13.1`. O socket é montado `:ro` só nesse serviço.
  - **Execução**: sem root, com `user: "65534:${DOCKER_GID}"`, `read_only: true`, `cap_drop: [ALL]` e `no-new-privileges`.
  - **Flags**:
    - `-logjson -loglevel=INFO -listenip=0.0.0.0 -allowfrom=0.0.0.0/0 -allowhealthcheck`
    - `-allowGET=(/v1\.[0-9]{1,2})?/(_ping|version|containers/json|containers/[a-zA-Z0-9_.-]+/(json|logs)|networks|networks/[a-zA-Z0-9_.-]+)`
    - `-allowHEAD=(/v1\.[0-9]{1,2})?/_ping`
  - **Ancoragem**: o proxy aplica `^…$` às regexes automaticamente.
  - **Healthcheck**: `["CMD", "./healthcheck"]`. A imagem é `scratch` (sem shell nem `wget`), e o binário de healthcheck é embutido e habilitado por `-allowhealthcheck`.
- **Rationale**:
  - **Logs JSON**: o proxy loga em JSON nativo (`-logjson`), o que elimina a exceção à constituição 3.3.2 que existia com o HAProxy do tecnativa (checklist Q7).
  - **Allowlist explícita**: a allowlist por regex fica fixada no arquivo versionado.
  - **Respostas verificadas**:
    - `GET /containers/json` → `200`;
    - `GET /images/json` e `GET /info` → `403`;
    - `POST /containers/create` e `DELETE /containers/x` → `405` (SC-008).
  - **Requisitos do coletor**: o `discovery.docker` precisa de `/networks`, e o Alloy chama `HEAD /_ping` (verificado).
  - **GID**: o `DOCKER_GID` é necessário porque a imagem não roda como root. No runner de teste, o socket pertence ao GID 118.
- **Allowfrom**: a restrição por hostname (`-allowfrom=alloy`) falha. Dentro de um contêiner ligado só a uma rede `internal`, o DNS embutido (127.0.0.11) responde `network is unreachable` (verificado). O isolamento fica a cargo da topologia (Decision 4).
- **Risco residual**: `GET /containers/{id}/json` expõe as variáveis de ambiente dos contêineres. Mitigação: só o coletor alcança o proxy (Decision 4).
- **Alternatives considered**:
  - Socket direto no coletor: rejeitado (Q1 da clarificação).
  - `tecnativa/docker-socket-proxy`: rejeitado (logs só em texto, roda como root).
  - Proxy próprio: rejeitado (manutenção e superfície de ataque).
## Decision 4: Topologia de rede

- **Decision**: nova rede `docker-api` (nome `${COMPOSE_PROJECT_NAME:-jhonny_v}-docker-api`, `internal: true`), com apenas `socket-proxy` e `alloy`.
  - O `alloy` também fica na `jhonny-core`.
  - O `loki` fica só na `jhonny-core`.
  - O `loki-gateway` usa `network_mode: service:loki`.
- **Rationale**:
  - Um contêiner na `jhonny-core` não alcançou o proxy (verificado, SC-009).
  - `internal: true` também tira a saída para a internet.
  - O único contêiner multi-rede (`alloy`) não é resolvido por nome por ninguém, o que contorna o bug da Decision 12.
- **Alternatives considered**:
  - Proxy na `jhonny-core`: rejeitado (Q2).
  - Rede `jhonny-obs` única: rejeitada (Q2).
  - Rede interna `loki-backend` entre o gateway e o Loki: rejeitada (Decision 12).
## Decision 5: Rótulos e metadados estruturados

- **Decision**:
  - **Rótulos de indexação**: `compose_project`, `compose_service`, `container` (sem a `/` inicial) e `stream`.
  - **Rótulo automático do Loki**: `service_name`, derivado de `compose_service` via `discover_service_name`.
  - **Metadados estruturados**: `level`, `trace_id` e `span_id`, extraídos por `stage.json` + `stage.structured_metadata`.
- **Rationale**: atende FR-005/006/007 sem transformar campos de alta cardinalidade em rótulos. Consultas como `{compose_service="x"} | detected_level="error"` e `| trace_id="..."` funcionam (verificado). O filtro de nível usa o `detected_level` normalizado (Decision 15). Linhas que não são JSON passam intactas, só sem os metadados (FR-008, verificado com stderr em texto).
- **Alternatives considered**: `level` como rótulo, rejeitado (FR-007 pede atributo filtrável sem promoção a rótulo); ID do contêiner como rótulo, rejeitado (FR-006).

## Decision 6: Configuração do Loki

- **Decision**: modo monolítico single-tenant (`auth_enabled: false`), com:
  - `server.http_listen_address: 127.0.0.1` e `http_listen_port: 3101`, só loopback;
  - `common.path_prefix: /loki`, filesystem + TSDB `schema: v13`;
  - retenção: `compactor.retention_enabled: true` e `limits_config.retention_period: ${LOKI_RETENTION_PERIOD:-7d}`, com a flag `-config.expand-env=true`;
  - `allow_structured_metadata: true`;
  - `discover_service_name: [compose_service]` e `discover_log_levels: true`;
  - `max_line_size: 256KB` e `max_line_size_truncate: true`;
  - `server.log_format: json`, `log_level: ${LOKI_LOG_LEVEL:-info}`;
  - `analytics.reporting_enabled: false`.
- **Rationale**:
  - Atende FR-011, FR-012, FR-023 e a constituição 3.3.2.
  - Retenção: `7d` é aceito (normalizado para `1w`), e um valor inválido aborta o start com `not a valid duration string` (fail-fast, verificado).
  - Truncamento: uma linha de 300.000 caracteres foi armazenada com 262.144 (verificado, SC-013).
  - Taxa de ingestão: defaults do Loki (4 MB/s, burst 6 MB), conforme o checklist Q3.
  - Com o Loki em loopback, só o gateway o alcança (verificado: `loki:3101` a partir da `jhonny-core` falha).
- **Alternatives considered**:
  - Retenção por stream: rejeitada (não pedida).
  - Desativar a telemetria só por flag: rejeitado (melhor deixar explícito no arquivo versionado).
## Decision 7: Healthchecks

- **Decision**:
  - **Loki**: `build` de `infra/loki/Dockerfile` (FROM `grafana/loki:3.7.8` + `/bin/busybox` estático de `busybox:1.37.0-musl`). Healthcheck `/usr/bin/busybox wget -qO- http://127.0.0.1:3101/ready` com `start_period: 40s`.
  - **Gateway**: `wget -qO- http://127.0.0.1:3100/ready`. Verifica o gateway e o Loki juntos; o `/ready` dispensa autenticação.
  - **Alloy**: probe em bash puro via `/dev/tcp` em `GET /-/ready` na porta interna `127.0.0.1:12345`.
  - **Proxy**: `./healthcheck`, binário embutido na imagem.
- **Rationale**:
  - A imagem do Loki é distroless, sem shell e sem flag de health (verificado).
  - O Alloy roda sobre Ubuntu e tem `bash`, mas não `curl` nem `wget` (verificado).
  - A imagem do proxy é `scratch`.
  - O Loki só fica pronto depois de cerca de 30 s, porque o ring tem espera inicial (verificado).
- **Alternatives considered**: ver a linha do `build` local em Complexity Tracking, no [plan.md](./plan.md).
## Decision 8: Persistência e posição de leitura

- **Decision**: o volume nomeado `alloy-data` montado em `/var/lib/alloy/data` (`--storage.path`) guarda as posições do `loki.source.docker`. O volume nomeado `loki-data` fica em `/loki`.
- **Rationale**: FR-010/011 e SC-004 (entrega ao menos uma vez após reinício). A imagem já cria `/loki` com dono `10001`, e um volume nomeado novo herda essa propriedade.

## Decision 9: Rotação de logs do Docker (FR-019)

- **Decision**: em cada arquivo `compose.core.yaml`, `compose.llm.yaml` e `compose.obs.yaml`, um bloco `x-logging: &default-logging` com `driver: json-file`, `max-size: ${DOCKER_LOG_MAX_SIZE:-10m}` e `max-file: "${DOCKER_LOG_MAX_FILE:-3}"`. Cada serviço usa `logging: *default-logging`.
- **Rationale**: âncoras YAML valem só dentro do próprio arquivo, que é o mesmo motivo pelo qual o `x-common-environment` se repete. A interpolação foi verificada em `docker compose config`.
- **Alternatives considered**: `daemon.json` do host, rejeitado (Q4); `include` com fragmento comum, rejeitado (não é suportado para trechos de serviço).

## Decision 10: Logs dos próprios componentes

- **Decision**: os quatro serviços logam em JSON no stdout/stderr:
  - Alloy: `logging { level = "info" format = "json" }`;
  - Loki: `server.log_format: json`;
  - proxy: `-logjson`;
  - Caddy: `log { format json }` global e no site.

  Os quatro são coletados como qualquer outro contêiner.
- **Rationale**:
  - Formato verificado no protótipo para os quatro serviços.
  - No nível `info`, nem o Alloy nem o Loki registram um log por linha ou por push.
  - O access log do Caddy usa `log_skip` para `/ready` e `/loki/api/v1/push`. Assim não há laço de realimentação (FR-020, checklist Q11). Requisições de consulta, inclusive as `401`, continuam registradas (verificado).
## Decision 11: Carregamento do `.env`

- **Decision**: o quickstart usa `docker compose --env-file .env -f infra/compose.yaml -f infra/compose.obs.yaml ...`.
- **Rationale**: o diretório do projeto Compose é o do primeiro `-f` (`infra/`), então o `.env` da raiz não é lido automaticamente. As variáveis `LOKI_GATEWAY_USER`, `LOKI_GATEWAY_PASSWORD` e `DOCKER_GID` são obrigatórias (`${VAR:?}`); as demais têm default.

## Decision 12: Bug de DNS multi-rede do Docker Engine 28.0.4

- **Finding**: no Docker Engine 28.0.4 do ambiente de prototipação, quando um contêiner é criado já ligado a várias redes (Compose ou `docker run --network a --network b`), o DNS embutido devolve o IP da rede errada. Os pares então não o alcançam pelo nome.
  - Portas publicadas nesses contêineres também travaram.
  - `priority`/`gw_priority` não resolveram.
- **Decision**: nenhum contêiner que precise ser resolvido por nome ou ter porta publicada fica em mais de uma rede.
  - O `alloy` é multi-rede, mas ninguém o resolve por nome.
  - O gateway compartilha o namespace do `loki` (`network_mode: service:loki`), que é single-homed na `jhonny-core` e publica a porta.
- **Alternatives considered**: gateway multi-rede com o Loki numa rede `loki-backend`, que falhou no protótipo.

## Decision 13: Gateway de consulta com autenticação (checklist Q9)

- **Decision**: `caddy:2.11.4-alpine` com `network_mode: service:loki` e `depends_on: loki (service_healthy)`. Configuração em `infra/loki-gateway/Caddyfile`:
  - global `admin off` e log JSON em stderr;
  - site `:3100` com access log JSON e `log_skip` para `/ready` e push;
  - `handle /ready` sem autenticação;
  - os demais caminhos com `basic_auth {$LOKI_GATEWAY_USER} {$LOKI_GATEWAY_PASSWORD_HASH}` e `reverse_proxy 127.0.0.1:3101`.
- **Inicialização**: o entrypoint `sh -c` gera o hash com `caddy hash-password --plaintext "$LOKI_GATEWAY_PASSWORD"`, faz `unset` da senha em texto e executa `caddy run`.
  - A leitura do hash por stdin falha com `EOF` (verificado), por isso o `--plaintext`.
  - O hash é bcrypt e é gerado a cada subida.
- **Rationale**:
  - Verificado: sem credenciais → `401`; credenciais inválidas → `401`; credenciais válidas → `200`; `/ready` sem autenticação → `200`.
  - O Alloy envia por `http://loki:3100/loki/api/v1/push` com `basic_auth` lido de `sys.env` (verificado).
- **Alternatives considered**:
  - Nginx com `htpasswd`: exige gerar e versionar ou montar o arquivo de hash.
  - Autenticação multi-tenant do Loki: o Loki não autentica, apenas lê o cabeçalho `X-Scope-OrgID`.

## Decision 14: Mascaramento de segredos (checklist Q2)

- **Decision**: três `stage.replace` no `loki.process`, antes do `stage.json`, todos com `replace = "<redacted>"`:
  1. `(?i)bearer\s+([A-Za-z0-9._~+/=-]+)`
  2. `\b(sk-[A-Za-z0-9_-]{16,})`
  3. `(?i)(?:password|passwd|pwd|secret|token|api_key|apikey)"?\s*[:=]\s*"?([^"\s,&}]+)`
- **Rationale**: o `stage.replace` substitui só os grupos de captura e preserva a chave e a estrutura do JSON. Verificado:
  - `"password":"<redacted>"`;
  - `token=<redacted>`;
  - `api_key=<redacted>`;
  - `Bearer <redacted>` (token após `Bearer`);
  - `key <redacted> end`.
- **Limitação**: é uma lista de padrões conhecidos, não uma detecção genérica. A responsabilidade primária continua com as apps.

## Decision 15: Nível normalizado (checklist Q4)

- **Decision**: o filtro usa `detected_level` (`discover_log_levels: true`), e o `level` original continua como metadado estruturado.
- **Rationale**: verificado no protótipo:
  - `ERROR` → `error`;
  - `warning` → `warn`;
  - `Info` → `info`;
  - JSON sem nível → `unknown`.

  Em texto puro o nível é heurístico (`plain error happened here` → `error`), por isso o SC-005 é medido com logs JSON.

## Decision 16: Política de entrega e histórico (checklist Q1, Q5, Q6)

- **Decision**:
  - **Reenvio**: defaults do `loki.write`: `min_backoff` 500 ms, `max_backoff` 5 min e `max_backoff_retries` 10, cerca de 8–9 min no total. Depois disso o lote é descartado.
  - **Fila e lote**: fila de 10 MiB e lote de 1 MiB.
  - **Timestamp**: o do Docker.
  - **Sem posição salva**: ingestão do histórico retido pelo Docker.
- **Rationale**:
  - O leitor salva a posição ao enfileirar a entrada, não ao confirmar o push. Por isso, um lote descartado é perdido, o que foi aceito para o ambiente local.
  - Linhas acima de cerca de 1 MiB são descartadas pelo leitor do Alloy (`line too big, skipping`). É uma limitação conhecida.

## Decision 17: Testes de aceite (checklist Q8)

- **Decision**: projeto `infra/pyproject.toml`, gerenciado com `uv`:
  - dependências: `pytest` e `httpx`;
  - desenvolvimento: `black` e `ruff`.

  Os testes ficam em `infra/tests/` e rodam contra a stack em execução. Um teste por SC, com credenciais lidas do ambiente (`.env`).
- **Rationale**: atende a constituição 3.1.2, 3.1.4, 3.5.1 e 3.5.3. O CI fica como follow-up porque `.github/workflows` não existe.
