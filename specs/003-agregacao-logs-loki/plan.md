# Implementation Plan: Agregação Centralizada de Logs de Contêineres (Grafana Alloy + Loki)

**Branch**: `[003-agregacao-logs-loki]` | **Date**: 2026-10-01 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-agregacao-logs-loki/spec.md`

**Redesenho aprovado (2026-10-16)**: o usuário aprovou substituir o descarte
do FR-026 por fila durável limitada, com confirmação transacional de registros
mascarados/checkpoint e remoção somente após aceitação do Loki. O gate de entrega
permanece bloqueado até a implementação e os testes abaixo; o WAL padrão isolado
não atende ao contrato.

## SDD Feature Selection

Os comandos Specify seguintes selecionam esta feature pelo `.specify/feature.json`, que agora é versionado (foi removido do `.specify/.gitignore`) e aponta para `specs/003-agregacao-logs-loki`. `SPECIFY_FEATURE_DIRECTORY` continua valendo como override.

## Summary

Criar o overlay `infra/compose.obs.yaml` com quatro serviços:

- **`socket-proxy`**: proxy de socket do Docker (`wollomatic/socket-proxy`), allowlist só leitura, sem root.
- **`alloy`**: distribuição local do Grafana Alloy com componente nativo de coleta e entrega durável; a compilação mantém a versão upstream fixada.
- **`loki`**: armazenamento, escutando só em loopback.
- **`loki-gateway`**: Caddy com autenticação HTTP básica. Compartilha o namespace de rede do `loki` e é o único caminho de consulta e de ingestão.

Juntos, eles ingerem o `stdout`/`stderr` de todos os contêineres do host:

- **Rótulos de origem** de baixa cardinalidade: projeto, serviço, contêiner e stream.
- **Mascaramento** de padrões conhecidos de segredo antes do envio.
- **Metadados estruturados**: `level`, `trace_id` e `span_id`. O filtro de nível usa o `detected_level` normalizado.
- **Truncamento** de linhas acima de 256 KB.
- **Retenção** configurável, com default de 7 dias.

A porta publicada é a do gateway, apenas em `${HOST_IP:-127.0.0.1}`. A feature também:

- aplica um limite comum de rotação de logs do Docker (10 MB × 3) a todos os serviços das camadas core, llm e obs;
- cria testes de aceite `pytest` em `infra/tests/`.

Toda a abordagem foi prototipada localmente com as versões fixadas abaixo (ver [research.md](./research.md)).

## Technical Context

**Language/Version**:
- YAML: Docker Compose v2 e configuração do Loki.
- Sintaxe de configuração do Alloy (`.alloy`).
- Caddyfile.
- Dockerfile: camada mínima de healthcheck do Loki.
- Python ≥ 3.12, só nos testes de aceite.
- Go, na extensão nativa compilada com o código-fonte fixado do Alloy e seu ferramental existente.
- Markdown.

**Primary Dependencies**:
- `grafana/loki:3.7.8`
- `grafana/alloy:v1.20.1`
- `wollomatic/socket-proxy:1.13.1`
- `caddy:2.11.4-alpine`
- `busybox:1.37.0-musl`: só como estágio de build, para obter um binário estático de probe.
- Nos testes: `pytest` e `httpx`, além de Black e Ruff como dependências de desenvolvimento.

**Storage**:
- Volume nomeado `loki-data`: chunks, índice TSDB e compactor.
- Volume nomeado `alloy-data`: banco transacional privado da fila e checkpoints, com sincronização durável habilitada. O limite padrão de 256 MiB refere-se ao conteúdo pendente serializado, não ao tamanho físico total do banco.

### Redesenho de entrega: fronteira transacional

1. Um único dono de decodificação por contêiner reconstrói as linhas de `stdout`/`stderr`. Conteúdo parcial fica somente em memória; não se confirma progresso além de linhas incompletas.
2. Os estágios síncronos existentes do Alloy fazem mascaramento, extração JSON e metadados. Somente estágios sem descarte/buffer são permitidos nesta fronteira; a configuração inválida falha antes da leitura.
3. Uma transação síncrona no banco privado (bbolt já presente no upstream) insere o registro processado e confirma seu recebimento/checkpoint. Erro ou falta de capacidade cancela a transação; não há confirmação durável nem avanço.
4. O emissor lê somente conteúdo persistido e envia pelo gateway autenticado. Nenhuma transação de escrita permanece aberta durante chamadas HTTP. Somente HTTP `204` autoriza remoção transacional. Resultado ambíguo, erro de rede e rejeição preservam o conteúdo; queda entre aceitação e remoção produz duplicatas, não perda.
5. Recuperação percorre toda a fila pendente sem depender de descoberta, nome ou existência do produtor. Ao reconectar ao Docker, relê conservadoramente o histórico retido: timestamps podem repetir ou retroceder e não são identidade para deduplicação.
6. `ALLOY_QUEUE_MAX_BYTES` limita globalmente os bytes serializados pendentes (default 268435456), compartilhados pelos alvos do host. Fila cheia/falha de armazenamento suspende leitura e confirmações; métricas de pendências e estado degradado tornam o bloqueio observável. Um produtor ruidoso pode suspender os demais; isolamento por quota individual não faz parte deste contrato. Reserva de disco deve incluir páginas/índices/transações e o histórico Docker. O arquivo bbolt não encolhe após drenar: as páginas livres são reutilizadas, não devolvidas ao sistema operacional.

**Implementação/build**: componente nativo aditivo em `infra/alloy/`, registrado e
compilado numa árvore upstream obtida por arquivo com versão/checksum fixados.
Não há plugin externo estável nem fork espelhado no repositório. A imagem local
declara `build` e versão própria no Compose; o estágio de testes usa o `go test`
do upstream. O binário resultante valida a configuração no CI.

**Riscos e limites**: APIs internas do Alloy exigem revisão a cada atualização;
fsync/transações não protegem contra destruição do volume; dados parciais ou
não confirmados dependem do Docker; fila cheia pode coincidir com rotação;
rejeição permanente exige intervenção e pode bloquear o envio FIFO. Não há
promessa de perda zero fora dessas fronteiras nem saída operacional em arquivo.

**Testing**:
- Testes de aceite `pytest` em `infra/tests/`, executados contra a stack em execução e cobrindo os SC-001 a SC-013 (SC-014).
- Projeto Python próprio em `infra/pyproject.toml`, gerenciado com `uv`.
- Validações estáticas complementares: `docker compose config`, `loki -verify-config`, `alloy fmt` e `caddy validate`.
- As evidências são registradas por ID de SC no [quickstart.md](./quickstart.md).
- CI: workflow `.github/workflows/infra-obs.yaml` (GitHub Actions) executa lint, validações estáticas e a suíte completa contra a stack em pull requests e pushes que tocam `infra/**` (FR-027).

**Target Platform**: host local com Docker Engine e Docker Compose v2 (Linux, macOS ou Windows com Docker Desktop).

**Project Type**: monorepo com infraestrutura em camadas (`infra/compose.yaml` + overlays `infra/compose.*.yaml`).

**Performance Goals**:
- Linha visível no Loki em ≤ 10 s, em condições normais: camada saudável e até 1000 linhas/s (SC-002).
- Contêiner novo coletado em ≤ 30 s (SC-003). No protótipo, um contêiner novo ficou consultável em cerca de 10 s com `refresh_interval = "5s"`; a implementação usa `"1s"` para cobrir contêineres de vida curta (research, Decision 2).

**Constraints**:
- O coletor não monta o socket.
- O proxy só aceita `GET` nos caminhos da allowlist (contêineres, logs, redes, `_ping`, `version`) e `HEAD /_ping`. O restante é negado com `403` (caminho) ou `405` (método).
- A rede proxy ↔ coletor é `internal`.
- O Loki escuta só em `127.0.0.1:3101`, dentro do namespace compartilhado com o gateway.
- Nenhuma porta é publicada além da do gateway.
- Versões fixadas.
- Nenhum log em arquivo.
- Os rótulos de indexação são limitados a `compose_project`, `compose_service`, `container`, `stream` e `service_name`.
- Nenhum contêiner que precise ser resolvido por nome pode estar em mais de uma rede (ver research, decisão 12).

**Scale/Scope**:
- 4 serviços novos, 2 volumes e 1 rede nova.
- 4 arquivos de configuração novos.
- Ajuste de logging em 2 overlays existentes.
- Projeto de testes de infra.
- 1 workflow de CI.
- Atualização de `.env.example`, `README.md`, ISSUE-103 e milestone v0.1.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Regra (constituição) | Avaliação | Status |
|----------------------|-----------|--------|
| 2.1 / 3.4.1 Separação `infra/` e orquestração local | Tudo fica em `infra/`: overlay, `infra/alloy/`, `infra/loki/`, `infra/loki-gateway/` e `infra/tests/` | PASS |
| 2.5 / 3.4.2 `build` × `image` declarado por serviço | `loki` e o Alloy estendido usam `build` local com versões fixadas; proxy e gateway usam imagens remotas. Nenhuma alteração de redes/portas é necessária | PASS (design) |
| 2.6 Convenção `compose.*.yaml` | `infra/compose.obs.yaml` (não `.yml`) | PASS |
| 3.1.2 / 3.1.4 `pyproject.toml` + `uv` | Testes de infra em `infra/pyproject.toml` com `uv`; sem `requirements.txt` | PASS |
| 3.3.1 / 3.3.2 Sem logs em disco; `stdout`/`stderr` em JSON | Os quatro serviços logam em JSON no stdout/stderr, sem arquivo: Loki (`log_format: json`), Alloy (`format = "json"`), socket-proxy (`-logjson`) e Caddy (`format json`). Verificado no protótipo | PASS |
| 3.3.4 Compatível com LGTMP | Loki é o "L" da stack; o Alloy é o agente oficial da Grafana para essa stack | PASS |
| 3.4.3 / 3.4.8 Sem segredos versionados | As credenciais do gateway vêm do `.env` (`${VAR:?}`, obrigatórias). O `.env.example` só tem placeholders. A senha é convertida em hash bcrypt na subida do gateway, e o texto puro é removido do ambiente do processo Caddy | PASS |
| 3.4.4 Versões fixadas, sem `:latest` | Todas as imagens com tag exata | PASS |
| 3.4.5 `healthcheck` + `depends_on: service_healthy` | Healthcheck nos 4 serviços. `loki-gateway` depende de `loki`; `alloy` depende de `loki-gateway` e `socket-proxy`; todos com `service_healthy` | PASS |
| 3.4.6 Volumes nomeados para persistência | `loki-data` e `alloy-data` declarados com `name:` prefixado pelo projeto | PASS |
| 3.4.7 `.dockerignore` | Contextos limitados aos diretórios Loki/Alloy; verificar exclusão de `.venv/`, `__pycache__/` e `secrets/` no contexto do coletor | A validar no build |
| 3.5.1 Black + Ruff | Configurados em `infra/pyproject.toml` para os testes de aceite | PASS |
| 3.5.3 / 3.5.4 pytest + CI | Testes de aceite `pytest` cobrem os SCs e rodam no workflow `.github/workflows/infra-obs.yaml`, que bloqueia o merge em caso de falha (decisão D1 do analyze) | PASS |
| Princípio V (segurança por padrão) | O Loki não é exposto sem autenticação; o proxy de socket é uma allowlist só leitura, sem root; segredos conhecidos são mascarados no coletor | PASS |
| 4.1 Ordem bottom-up | A feature pertence à v0.1 (Infra Core) | PASS |
| 5.1 Fluxo SDD | specify → clarify → plan → **checklist** (decisões aplicadas) → tasks → analyze → implement | PASS |
| 6.4 Bloqueios imediatos | Sem `requirements.txt`, sem logs em disco, sem segredos, sem rede implícita (todas declaradas) | PASS |

- **Status pré-pesquisa**: PASS.
- **Status pós-design (2026-10-16)**: o desenho respeita isolamento, segredos externos, JSON no stdout/stderr e volume nomeado; o banco é estado de transporte, não destino de logs operacionais. A política FR-026 foi explicitamente aprovada pelo usuário. Aprovação de entrega continua condicionada a testes de atomicidade, capacidade, falhas HTTP, recuperação abrupta e CI verde; evidência antiga de reinício gracioso não fecha T041.

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
│   ├── requirements.md
│   └── observability.md
└── tasks.md             # gerado por /speckit-tasks (não por este comando)
```

### Source Code (repository root)

```text
infra/
├── compose.yaml                 # inalterado (rede jhonny-core e volumes base)
├── compose.core.yaml            # + bloco x-logging e `logging: *default-logging` em cada serviço (FR-019)
├── compose.llm.yaml             # + bloco x-logging e `logging: *default-logging` em cada serviço (FR-019)
├── compose.obs.yaml             # NOVO: socket-proxy, alloy, loki, loki-gateway; rede docker-api; volumes loki-data/alloy-data
├── alloy/
│   ├── config.alloy             # discovery/relabel → componente durável com estágios síncronos
│   ├── Dockerfile               # overlay nativo; origem/checksum e imagens fixados; alvo de testes
│   └── durable/                 # componente Go, fila/checkpoint/emissor e testes unitários
├── loki/
│   ├── Dockerfile               # NOVO: FROM grafana/loki:3.7.8 + busybox estático para healthcheck
│   └── config.yaml              # NOVO: single-tenant, loopback :3101, TSDB v13, retenção por env, truncamento 256 KB, logs JSON
├── loki-gateway/
│   └── Caddyfile                # NOVO: :3100, basic_auth (exceto /ready), access log JSON sem push/ready
├── pyproject.toml               # NOVO: projeto de testes de aceite (pytest, httpx; dev: black, ruff)
└── tests/                       # NOVO: testes de aceite por SC (contra a stack em execução)
    ├── conftest.py
    └── test_*.py

.github/workflows/infra-obs.yaml  # NOVO: CI (lint, validações estáticas, stack + pytest)
.env.example                     # + LOKI_RETENTION_PERIOD, LOKI_LOG_LEVEL, DOCKER_LOG_MAX_SIZE, DOCKER_LOG_MAX_FILE,
                                 #   LOKI_GATEWAY_USER, LOKI_GATEWAY_PASSWORD, DOCKER_GID (LOKI_PORT já existe)
README.md                        # + comando de subida da camada obs e dos testes de aceite
docs/issues/v0.1/ISSUE-103.md    # Promtail → Grafana Alloy; tarefas e caminhos atualizados
docs/milestones/v0.1-infra-core.md  # Promtail → Grafana Alloy
```

**Structure Decision**: seguir o padrão de camadas já usado nas features 001/002. A observabilidade de logs ganha um overlay próprio, combinável com a base, e a configuração de cada componente fica num diretório próprio em `infra/`. As camadas core e llm só ganham o bloco de rotação de logs (FR-019), sem outras mudanças de comportamento. Os testes de aceite de infraestrutura ficam em `infra/tests/`, com `pyproject.toml` próprio (isolamento de dependências por componente, constituição 2.2/3.1.4).

## Ownership & Configuration Boundaries

### File Ownership

| File | Owner | Responsibility Boundary |
|------|-------|--------------------------|
| `infra/compose.obs.yaml` | Plataforma/Infra | Ciclo de vida, redes, volumes, portas, healthchecks, hardening e permissões do proxy |
| `infra/alloy/config.alloy` | Plataforma/Observabilidade | Descoberta, rótulos, mascaramento, parsing JSON, metadados estruturados e entrega autenticada |
| `infra/alloy/Dockerfile`, `infra/alloy/durable/` | Plataforma/Observabilidade | Build fixado da extensão nativa, atomicidade/durabilidade, limites de fila, replay e testes Go |
| `infra/loki/config.yaml` | Plataforma/Observabilidade | Schema, armazenamento, retenção, limites, truncamento, `discover_log_levels` e formato de log |
| `infra/loki/Dockerfile` | Plataforma/Infra | Só adiciona o binário de probe; nenhuma outra customização |
| `infra/loki-gateway/Caddyfile` | Plataforma/Segurança | Autenticação, exceção `/ready`, proxy para o Loki e access log |
| `infra/pyproject.toml`, `infra/tests/` | Plataforma/QA | Testes de aceite dos SCs; não fazem parte de nenhuma imagem |
| `.github/workflows/infra-obs.yaml` | Plataforma/QA | Gate de CI: lint, validações estáticas e suíte de aceite; gera um `.env` efêmero sem segredos versionados |
| `infra/compose.core.yaml`, `infra/compose.llm.yaml` | Plataforma/Infra | Só o bloco `x-logging` (FR-019) |
| `.env.example` | Plataforma | Contrato das novas variáveis, defaults e placeholders |

### Environment Variable Dependency Matrix

| Variable | Required | Default | Consumer | Validation |
|----------|----------|---------|----------|------------|
| `LOKI_PORT` | Não | `3100` | `compose.obs.yaml` (porta publicada do gateway) | Porta inválida falha no `compose up` |
| `LOKI_RETENTION_PERIOD` | Não | `7d` | `infra/loki/config.yaml` via `-config.expand-env` | Duração inválida aborta o start do Loki (fail-fast, verificado) |
| `LOKI_LOG_LEVEL` | Não | `info` | `infra/loki/config.yaml` | Valor inválido aborta o start |
| `LOKI_GATEWAY_USER` | **Sim** | — | `loki-gateway`, `alloy`, testes de aceite | `${VAR:?}`: ausência aborta o `compose up` |
| `LOKI_GATEWAY_PASSWORD` | **Sim** (segredo) | — | `loki-gateway` (hash bcrypt na subida), `alloy`, testes de aceite | `${VAR:?}`: ausência aborta o `compose up`; nunca versionado |
| `DOCKER_GID` | **Sim** | — | `socket-proxy` (`user: "65534:${DOCKER_GID}"`) | `${VAR:?}`; um GID errado deixa o proxy sem acesso ao socket e o healthcheck falha |
| `DOCKER_LOG_MAX_SIZE` | Não | `10m` | Bloco `x-logging` (core, llm, obs) | Formato do driver `json-file` |
| `DOCKER_LOG_MAX_FILE` | Não | `3` | Bloco `x-logging` (core, llm, obs) | Inteiro ≥ 1 |
| `ALLOY_QUEUE_MAX_BYTES` | Não | `268435456` | Componente durável do Alloy | Inteiro positivo; valor incapaz de comportar um registro suspende a aceitação, sem descarte |
| `HOST_IP` | Não | `127.0.0.1` | Porta do gateway | Já existente |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| `build` local para o Loki (`infra/loki/Dockerfile`) | A imagem oficial é distroless (sem shell nem cliente HTTP) e o binário não tem flag de health. Sem um probe, não dá para cumprir 3.4.5 nem o `depends_on: service_healthy` do FR-013 | `-verify-config` como healthcheck só valida o arquivo, não a prontidão. Um healthcheck externo (outro contêiner) não alimenta o `service_healthy` do próprio Loki |
| `build` local do Alloy com componente nativo | A confirmação de origem, o conteúdo mascarado e o checkpoint precisam de uma única fronteira transacional; a API de canais padrão não expõe essa confirmação | Habilitar só `loki.write.wal` perdeu 40/40 registros no experimento de SIGKILL. Um serviço coletor externo substituiria o Alloy e ampliaria a topologia |
| `loki-gateway` com `network_mode: service:loki` | O Docker Engine 28.0.4 do ambiente resolve por DNS o IP da rede errada em contêineres multi-rede, e portas publicadas nesses contêineres travaram (research, decisão 12). Compartilhar o namespace deixa o `loki` single-homed, com o Loki em loopback, inalcançável sem passar pelo gateway | Um gateway em contêiner próprio e multi-rede, com o Loki numa rede interna `loki-backend`, falhou no protótipo pelo bug de DNS |
| Proxy de socket com `-allowfrom=0.0.0.0/0` | O DNS embutido do Docker não responde dentro de um contêiner ligado só a uma rede `internal`, então a restrição por hostname (`-allowfrom=alloy`) bloqueia o próprio coletor | Fixar IPs (`ipam`) acopla a configuração a sub-redes. O isolamento real vem da topologia: a rede `docker-api` é interna e tem só dois membros (SC-009) |
| `DOCKER_GID` obrigatório | O proxy roda sem root e precisa do grupo dono do socket, cujo GID varia por host | Rodar o proxy como root contraria o hardening do Princípio V |
| Bloco `x-logging` repetido em cada arquivo Compose | Âncoras YAML não atravessam arquivos; o padrão `x-common-environment` já se repete pelo mesmo motivo | Um `include`/`extends` só para logging adicionaria complexidade sem ganho; o bloco é único **por arquivo** e não é duplicado por serviço (FR-019) |
