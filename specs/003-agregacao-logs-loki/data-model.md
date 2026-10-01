# Data Model: Agregação Centralizada de Logs de Contêineres

Modelo lógico das entidades da [spec](./spec.md). Não há banco de dados de aplicação; os dados ficam no Loki (volume `loki-data`) e no estado do coletor (volume `alloy-data`).

## Entity: Linha de log

| Campo | Tipo | Origem | Regras |
|-------|------|--------|--------|
| `timestamp` | instante (ns) | Docker (momento da escrita) | Obrigatório; usado na ordenação e na retenção |
| `line` | texto | `stdout`/`stderr` do contêiner | Preservado como foi emitido; JSON inválido também é aceito (FR-008) |
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
| `level` | `level` | Filtro `\| level="ERROR"` |
| `trace_id` | `trace_id` | Busca `\| trace_id="..."`; correlação futura com o Tempo (ISSUE-105) |
| `span_id` | `span_id` | Busca `\| span_id="..."` |

**Validação**: a ausência do campo não descarta a linha (edge case da spec, constituição 3.3.3).

## Entity: Proxy de socket do Docker

| Atributo | Valor |
|----------|-------|
| Endpoints permitidos (GET) | `/containers/*`, `/networks/*`, `/_ping`, `/version` |
| Métodos não-GET | Negados (`403`) |
| Redes | Só `docker-api` (interna) |
| Socket | `/var/run/docker.sock:ro` |

## Entity: Coletor (Alloy)

| Estado | Persistência | Regras |
|--------|--------------|--------|
| Alvos descobertos | Memória (renovados a cada 5 s) | Contêiner novo vira alvo; contêiner encerrado sai depois de drenado |
| Posição de leitura por contêiner | `alloy-data` (`/var/lib/alloy/data`) | Retomada após reinício; entrega ao menos uma vez (FR-010) |

### Ciclo de vida de um alvo

`descoberto` → `lendo` → (`contêiner encerrado`) → `drenado` → `removido`

Se o proxy ou o Loki ficarem indisponíveis, o alvo permanece em `lendo` e o envio é retentado com backoff, sem afetar o contêiner de origem.

## Entity: Armazenamento central (Loki)

| Atributo | Valor |
|----------|-------|
| Tenancy | Single-tenant (`auth_enabled: false`) |
| Retenção | `LOKI_RETENTION_PERIOD` (default `7d`), aplicada pelo compactor |
| Persistência | Volume nomeado `loki-data` |
| Interface de consulta | HTTP `:3100`, publicada em `${HOST_IP:-127.0.0.1}:${LOKI_PORT:-3100}` |
