# Implementation Plan: Agregação Centralizada de Logs de Contêineres (Grafana Alloy + Loki)

**Branch**: `[003-agregacao-logs-loki]` | **Date**: 2026-10-01 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-agregacao-logs-loki/spec.md`

## SDD Feature Selection

Os comandos Specify seguintes selecionam esta feature pelo `.specify/feature.json`, que agora é versionado (foi removido do `.specify/.gitignore`) e aponta para `specs/003-agregacao-logs-loki`. `SPECIFY_FEATURE_DIRECTORY` continua valendo como override.

## Summary

Criar o overlay `infra/compose.obs.yaml` com três serviços: um proxy de socket do Docker restrito a leitura, o coletor Grafana Alloy e o armazenamento Loki. Juntos, eles ingerem `stdout`/`stderr` de todos os contêineres do host com rótulos de origem de baixa cardinalidade (projeto, serviço, contêiner e stream). Os campos `level`, `trace_id` e `span_id` de logs JSON viram metadados estruturados. A retenção é configurável (default 7 dias) e a porta do Loki é publicada apenas em `${HOST_IP:-127.0.0.1}`. A feature também aplica um limite comum de rotação de logs do Docker (10 MB × 3) a todos os serviços das camadas core, llm e obs. Toda a abordagem foi prototipada localmente com as versões fixadas abaixo (ver [research.md](./research.md)).

## Technical Context

**Language/Version**: YAML (Docker Compose v2 e configuração do Loki), sintaxe de configuração do Alloy (`.alloy`), Dockerfile (camada mínima de healthcheck do Loki), Markdown

**Primary Dependencies**: `grafana/loki:3.7.8`, `grafana/alloy:v1.20.1`, `tecnativa/docker-socket-proxy:v0.5.0`, `busybox:1.37.0-musl` (só como estágio de build para obter um binário estático de probe)

**Storage**: volume nomeado `loki-data` (chunks, índice TSDB e compactor) e volume nomeado `alloy-data` (posições de leitura do coletor)

**Testing**: validação operacional reproduzível, como na feature 002: `docker compose config`, `loki -verify-config`, `alloy fmt`, consultas LogQL via HTTP no Loki publicado e chamadas negativas ao proxy. Todas as evidências são registradas por ID de SC no [quickstart.md](./quickstart.md). Não há código Python, então pytest não se aplica (ver Constitution Check).

**Target Platform**: host local com Docker Engine e Docker Compose v2 (Linux, macOS ou Windows com Docker Desktop)

**Project Type**: monorepo com infraestrutura em camadas (`infra/compose.yaml` + overlays `infra/compose.*.yaml`)

**Performance Goals**: linha visível no Loki em ≤ 10 s (SC-002); contêiner novo coletado em ≤ 30 s (SC-003). No protótipo, um contêiner novo ficou consultável em cerca de 10 s com `refresh_interval = "5s"`.

**Constraints**: o coletor não monta o socket; o proxy só aceita GET em `/containers`, `/networks`, `/_ping` e `/version` e nega o resto (POST desabilitado); a rede proxy ↔ coletor é `internal`; nenhuma porta publicada além da do Loki; versões fixadas; nenhum log em arquivo; rótulos de indexação limitados a `compose_project`, `compose_service`, `container`, `stream` e `service_name`

**Scale/Scope**: 3 serviços novos, 2 volumes, 1 rede nova, 3 arquivos de configuração novos, ajuste de logging em 2 overlays existentes, atualização de `.env.example`, `README.md`, ISSUE-103 e milestone v0.1

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Regra (constituição) | Avaliação | Status |
|----------------------|-----------|--------|
| 2.1 / 3.4.1 Separação `infra/` e orquestração local | Tudo fica em `infra/` (overlay + `infra/alloy/` + `infra/loki/`) | PASS |
| 2.5 / 3.4.2 `build` × `image` declarado por serviço | `loki` usa `build` (Dockerfile mínimo FROM imagem fixada); `alloy` e `socket-proxy` usam `image`; `env_file`, `volumes`, `networks` e `depends_on` são explícitos em cada serviço | PASS |
| 2.6 Convenção `compose.*.yaml` | `infra/compose.obs.yaml` (não `.yml`) | PASS |
| 3.3.1 / 3.3.2 Sem logs em disco; `stdout`/`stderr` em JSON | Loki (`log_format: json`) e Alloy (`logging { format = "json" }`) logam em JSON no stdout. O proxy (HAProxy) loga texto no stderr e não tem opção JSON | PASS com exceção justificada (ver Complexity Tracking) |
| 3.3.4 Compatível com LGTMP | Loki é o "L" da stack; o Alloy é o agente oficial da Grafana para essa stack | PASS |
| 3.4.3 / 3.4.8 Sem segredos versionados | Nenhuma credencial; o Loki é single-tenant local, restrito a `127.0.0.1` | PASS |
| 3.4.4 Versões fixadas, sem `:latest` | Todas as imagens com tag exata | PASS |
| 3.4.5 `healthcheck` + `depends_on: service_healthy` | Healthcheck nos 3 serviços; `alloy` depende de `loki` e `socket-proxy` como `service_healthy` | PASS |
| 3.4.6 Volumes nomeados para persistência | `loki-data` e `alloy-data` declarados com `name:` prefixado pelo projeto | PASS |
| 3.4.7 `.dockerignore` | O contexto de build é `infra/loki/` (só Dockerfile + config); o `.dockerignore` da raiz não muda | PASS |
| 3.5.3 / 3.5.4 pytest + CI | A feature não produz código Python e o repositório ainda não tem pipeline de CI (`.github/workflows` não existe). A validação segue a evidência objetiva dos itens 6.2.1 e 6.2.4: configuração versionada + resultados de `compose config`, `verify-config` e consultas | PASS com ressalva: evidência operacional, como na feature 002 |
| 4.1 Ordem bottom-up | A feature pertence à v0.1 (Infra Core) | PASS |
| 5.1 Fluxo SDD | specify → clarify → **plan** (este) → checklist → tasks → analyze → implement | PASS |
| 6.4 Bloqueios imediatos | Sem `requirements.txt`, sem logs em disco, sem segredos, sem rede implícita (todas declaradas) | PASS |

- **Status pré-pesquisa**: PASS (com 2 ressalvas registradas)
- **Status pós-design**: PASS. O design de Phase 1 manteve as escolhas; as ressalvas estão em Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/003-agregacao-logs-loki/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── logs-aggregation-contract.md
├── checklists/
│   └── requirements.md
└── tasks.md             # gerado por /speckit-tasks (não por este comando)
```

### Source Code (repository root)

```text
infra/
├── compose.yaml                 # inalterado (rede jhonny-core e volumes base)
├── compose.core.yaml            # + bloco x-logging e `logging: *default-logging` em cada serviço (FR-019)
├── compose.llm.yaml             # + bloco x-logging e `logging: *default-logging` em cada serviço (FR-019)
├── compose.obs.yaml             # NOVO: socket-proxy, alloy, loki; rede docker-api; volumes loki-data/alloy-data
├── alloy/
│   └── config.alloy             # NOVO: discovery → relabel → source.docker → process(json) → write
└── loki/
    ├── Dockerfile               # NOVO: FROM grafana/loki:3.7.8 + busybox estático para healthcheck
    └── config.yaml              # NOVO: single-tenant, TSDB v13, retenção por env, logs JSON

.env.example                     # + LOKI_RETENTION_PERIOD, LOKI_LOG_LEVEL, DOCKER_LOG_MAX_SIZE, DOCKER_LOG_MAX_FILE (LOKI_PORT já existe)
README.md                        # + comando de subida da camada obs
docs/issues/v0.1/ISSUE-103.md    # Promtail → Grafana Alloy; tarefas e caminhos atualizados
docs/milestones/v0.1-infra-core.md  # Promtail → Grafana Alloy
```

**Structure Decision**: seguir o padrão de camadas já usado nas features 001/002. A observabilidade de logs ganha um overlay próprio, combinável com a base, e a configuração de cada componente fica num diretório próprio em `infra/`. As camadas core e llm só ganham o bloco de rotação de logs (FR-019), sem outras mudanças de comportamento.

## Ownership & Configuration Boundaries

### File Ownership

| File | Owner | Responsibility Boundary |
|------|-------|--------------------------|
| `infra/compose.obs.yaml` | Plataforma/Infra | Ciclo de vida, redes, volumes, portas, healthchecks e permissões do proxy |
| `infra/alloy/config.alloy` | Plataforma/Observabilidade | Descoberta, rótulos, parsing JSON, metadados estruturados e entrega ao Loki |
| `infra/loki/config.yaml` | Plataforma/Observabilidade | Schema, armazenamento, retenção, limites e formato de log do Loki |
| `infra/loki/Dockerfile` | Plataforma/Infra | Só adiciona o binário de probe; nenhuma outra customização |
| `infra/compose.core.yaml`, `infra/compose.llm.yaml` | Plataforma/Infra | Só o bloco `x-logging` (FR-019) |
| `.env.example` | Plataforma | Contrato das novas variáveis e defaults |

### Environment Variable Dependency Matrix

| Variable | Required | Default | Consumer | Validation |
|----------|----------|---------|----------|------------|
| `LOKI_PORT` | Não | `3100` | `compose.obs.yaml` (porta publicada) | Porta inválida falha no `compose up` |
| `LOKI_RETENTION_PERIOD` | Não | `7d` | `infra/loki/config.yaml` via `-config.expand-env` | Duração inválida aborta o start do Loki (fail-fast, verificado) |
| `LOKI_LOG_LEVEL` | Não | `info` | `infra/loki/config.yaml` | Valor inválido aborta o start |
| `DOCKER_LOG_MAX_SIZE` | Não | `10m` | Bloco `x-logging` (core, llm, obs) | Formato do driver `json-file` |
| `DOCKER_LOG_MAX_FILE` | Não | `3` | Bloco `x-logging` (core, llm, obs) | Inteiro ≥ 1 |
| `HOST_IP` | Não | `127.0.0.1` | Porta do Loki | Já existente |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| `build` local para o Loki (`infra/loki/Dockerfile`) | A imagem oficial é distroless (sem shell nem cliente HTTP) e o binário não tem flag de health. Sem um probe, não dá para cumprir 3.4.5 nem o `depends_on: service_healthy` do FR-013 | `-verify-config` como healthcheck só valida o arquivo, não a prontidão. Um healthcheck externo (outro contêiner) não alimenta o `service_healthy` do próprio Loki |
| Proxy de socket loga em texto (HAProxy), não em JSON (3.3.2) | Componente de segurança de terceiros, exigido pela clarificação Q1; não tem opção de log JSON | Escrever um proxy próprio em Python, com logs JSON, aumentaria a superfície de ataque e o escopo. Os logs continuam em stderr, sem arquivo, e são coletados como texto (FR-008) |
| Bloco `x-logging` repetido em cada arquivo Compose | Âncoras YAML não atravessam arquivos; o padrão `x-common-environment` já se repete pelo mesmo motivo | Um `include`/`extends` só para logging adicionaria complexidade sem ganho; o bloco é único **por arquivo** e não é duplicado por serviço (FR-019) |
| Sem pytest/CI (3.5.3) | A feature não tem código Python e o repositório não tem pipeline | Criar a infraestrutura de CI está fora do escopo da ISSUE-103; a evidência operacional segue o mesmo padrão aceito na feature 002 |
