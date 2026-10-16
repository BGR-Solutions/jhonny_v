# Data Model: Agregação Centralizada de Logs de Contêineres

Modelo lógico das entidades da [spec](./spec.md). Não há banco de dados de aplicação; os dados ficam no Loki (volume `loki-data`) e no estado do coletor (volume `alloy-data`).

## Entity: Linha de log

| Campo | Tipo | Origem | Regras |
|-------|------|--------|--------|
| `timestamp` | instante (ns) | Docker (momento da escrita) | Obrigatório; usado na ordenação e na retenção; timestamps no conteúdo não o substituem (FR-024) |
| `line` | texto | `stdout`/`stderr` do contêiner | Preservado como foi emitido, exceto pelo mascaramento de segredos (FR-022) e pelo truncamento acima de 256 KB (FR-023); JSON inválido também é aceito (FR-008) |
| rótulos | conjunto de `Rótulo de origem` | Coletor | Sempre presentes (FR-005) |
| metadados | conjunto de `Atributo estruturado` | Coletor (`stage.json`) | Opcionais; só existem se a linha for JSON com o campo |

## Entity: Rótulo de origem (indexado)

| Rótulo | Fonte (meta do Docker) | Exemplo | Cardinalidade |
|--------|------------------------|---------|---------------|
| `compose_project` | `com.docker.compose.project` | `jhonny_v` | Baixa (nº de projetos) |
| `compose_service` | `com.docker.compose.service` | `postgres` | Baixa (nº de serviços) |
| `container` | nome do contêiner sem `/` | `jhonny_v-postgres-1` | Baixa (réplicas × serviços) |
| `stream` | stream do log | `stdout` \| `stderr` | 2 |
| `service_name` | atribuído pelo Loki a partir de `compose_service` | `postgres` | Igual a `compose_service` |

**Validação**: contêineres fora do Compose não têm `compose_project`/`compose_service`, mas continuam com `container` e `stream` (FR-002). Nenhum rótulo pode receber ID de contêiner, `trace_id`, `span_id` ou IDs de requisição (FR-006).

## Entity: Atributo estruturado (não indexado)

| Atributo | Chave JSON na linha | Uso |
|----------|---------------------|-----|
| `level` | `level` | Valor original preservado; busca `\| level="ERROR"` |
| `detected_level` | atribuído pelo Loki (`discover_log_levels`) | Filtro normalizado `\| detected_level="error"` (`debug`, `info`, `warn`, `error`, `critical`, `trace`, `unknown`) — FR-007 |
| `trace_id` | `trace_id` | Busca `\| trace_id="..."`; correlação futura com o Tempo (ISSUE-105) |
| `span_id` | `span_id` | Busca `\| span_id="..."` |

**Validação**: a ausência do campo não descarta a linha (edge case da spec, constituição 3.3.3).

## Entity: Proxy de socket do Docker

| Atributo | Valor |
|----------|-------|
| Imagem | `wollomatic/socket-proxy:1.13.1` |
| Endpoints permitidos (GET) | `/_ping`, `/version`, `/containers/json`, `/containers/{id}/json`, `/containers/{id}/logs`, `/networks`, `/networks/{id}` (com prefixo de versão opcional) |
| Outros métodos permitidos | `HEAD /_ping` |
| Caminho fora da allowlist | Negado (`403`) |
| Método não permitido | Negado (`405`) |
| Execução | UID 65534, GID `${DOCKER_GID}`, rootfs somente leitura, sem capabilities, `no-new-privileges` |
| Logs | JSON (`-logjson`) |
| Redes | Só `docker-api` (interna); `-allowfrom=0.0.0.0/0`, com isolamento pela topologia |
| Socket | `/var/run/docker.sock:ro` |

## Entity: Coletor (Alloy)

| Estado | Persistência | Regras |
|--------|--------------|--------|
| Alvos descobertos | Memória (renovados a cada 5 s) | Contêiner novo vira alvo; contêiner encerrado sai depois de drenado |
| Registro pendente | Banco transacional em `alloy-data` (`/var/lib/alloy/data`) | ID sequencial, timestamp Docker em ns, linha já mascarada, rótulos e metadados imutáveis; remoção somente após HTTP `204` |
| Checkpoint de recebimento | Mesma transação do registro | Confirma recebimento durável, nunca mera entrega a canal em memória; timestamp não é identidade única nem autorização para pular histórico |
| Bytes pendentes | Mesma transação de inserção/remoção | Inclui representação serializada persistida; limitado por `ALLOY_QUEUE_MAX_BYTES` |
| Diagnósticos/saúde | Métricas e JSON no stdout/stderr | Fila cheia, armazenamento indisponível e reenvio bloqueado não expõem linhas ou credenciais |

### Invariantes transacionais

- Ou registro mascarado e checkpoint são confirmados juntos, ou nenhum é confirmado. A confirmação exige sincronização durável do banco, não só flush de buffers de aplicação.
- Nunca persistir conteúdo bruto ou fragmentos anteriores ao mascaramento. O banco pode conservar páginas livres contendo versões antigas, mas todas elas já passaram pelo mascaramento.
- O envio lê apenas dados confirmados; não depende de o produtor continuar existindo. Não mantém transação de escrita durante HTTP.
- HTTP `204` permite retirar o registro; queda antes da retirada permite duplicatas. Qualquer outro resultado mantém a pendência sem limite de tentativas/idade.
- Inserção que exceda capacidade ou falhe não avança checkpoint. A fila drena independentemente dos leitores suspensos; capacidade liberada permite retomar.
- O limite de bytes pendentes não inclui páginas, índices e espaço temporário de transações. O operador deve reservar folga; o banco reutiliza páginas liberadas. Remover o volume para liberar disco destrói a garantia.

### Ciclo de vida de um alvo

`descoberto` → `lendo` → (`contêiner encerrado`) → `drenado` → `removido`

Se o proxy cair, a reconexão relê conservadoramente o histórico retido pelo
Docker, aceitando duplicatas e timestamps repetidos/não monotônicos. Se o Loki
cair, os registros confirmados permanecem pendentes, com backoff de 500 ms a
5 min e sem expiração por tentativas. Atingir a capacidade/falhar uma gravação
leva o alvo a `suspenso`, sem confirmação de novas linhas; após liberação de
capacidade volta a `lendo`. Dados ainda não confirmados podem desaparecer no
Docker por rotação/remoção. A fila sobrevive mesmo ao estado `removido` do alvo.

### Pipeline de processamento

Decodificação ordenada → `stage.replace` × 4 (mascaramento, FR-022) →
`stage.json` (`level`, `trace_id`, `span_id`) → `stage.structured_metadata` →
transação registro/checkpoint → emissor persistente (basic auth via gateway) →
confirmação HTTP `204` → remoção transacional. Os estágios nessa fronteira
devem ser síncronos, sem descarte nem buffers que separem progresso e conteúdo.

## Entity: Armazenamento central (Loki)

| Atributo | Valor |
|----------|-------|
| Tenancy | Single-tenant (`auth_enabled: false`) |
| Retenção | `LOKI_RETENTION_PERIOD` (default `7d`), aplicada pelo compactor |
| Persistência | Volume nomeado `loki-data` |
| Escuta | `127.0.0.1:3101` (loopback do namespace compartilhado com o gateway) |
| Limites | Defaults de taxa; `max_line_size: 256KB` com truncamento |
| Normalização de nível | `discover_log_levels: true` |
| Logs próprios | JSON, nível `LOKI_LOG_LEVEL` (default `info`) |

## Entity: Gateway de consulta (Caddy)

| Atributo | Valor |
|----------|-------|
| Imagem | `caddy:2.11.4-alpine`, `network_mode: service:loki` |
| Interface | HTTP `:3100`, publicada em `${HOST_IP:-127.0.0.1}:${LOKI_PORT:-3100}` (porta declarada no serviço `loki`) e `http://loki:3100` na `jhonny-core` |
| Autenticação | HTTP básica com `LOKI_GATEWAY_USER`/`LOKI_GATEWAY_PASSWORD` (hash bcrypt na subida); exceção: `GET /ready` |
| Respostas sem credencial válida | `401` |
| Logs | JSON em stderr; o access log omite `/ready` e `/loki/api/v1/push` |
