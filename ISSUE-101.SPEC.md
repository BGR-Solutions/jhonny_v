# Feature Specification: ISSUE-101 - Estrutura Base do Monorepo e Documentação Inicial

**Feature Branch**: `101-monorepo-base-structure`  
**Created**: 2026-10-01  
**Status**: Approved for Phase 3 Implementation  
**Target Audience**: Developers, Platform Architects, DevOps Engineers  
**Milestone**: `v0.1 - Infra Core & Observabilidade`

---

## User Scenarios & Testing

### User Story 1 - Estrutura de Diretórios Base Criada (Priority: P1)

Um desenvolvedor novo no projeto clone o repositório e encontre uma estrutura de pastas clara, organizada por domínios, com cada diretório servindo um propósito específico.

**Por que esta prioridade**: É a base absoluta — sem estrutura, nada funciona. Bloqueia todas as outras histórias.

**Teste Independente**: Ao clonar o repo, rodar `git status` e verificar se todos os diretórios (`apps/`, `infra/`, `docs/`) existem com arquivos essenciais.

**Cenários de Aceitação**:

1. **Dado** o repositório clonado, **Quando** executo `tree -L 2`, **Então** vejo estrutura com `apps/`, `infra/`, `docs/adr/`, `docs/issues/`, `docs/milestones/`
2. **Dado** que abro `docs/README.md`, **Quando** leio o conteúdo, **Então** entendo o propósito de cada pasta
3. **Dado** que executo `git status`, **Quando** consulto o status, **Então** todos os arquivos tracked estão sincronizados

---

### User Story 2 - Arquivo `.env.example` Centralizado (Priority: P1)

Um desenvolvedor novo precisa configurar variáveis de ambiente padronizadas sem adivinhar quais são necessárias.

**Por que esta prioridade**: Essencial para DX (Developer Experience) — sem isso, cada dev inventa suas próprias variáveis.

**Teste Independente**: Copiar `.env.example` para `.env` e verificar que todas as variáveis necessárias estão presentes.

**Cenários de Aceitação**:

1. **Dado** o arquivo `.env.example` na raiz, **Quando** copio para `.env`, **Então** todas as variáveis necessárias estão presentes com valores defaults seguros
2. **Dado** que um dev carrega o `.env` na aplicação, **Quando** a app inicia, **Então** não há erros de variáveis não-definidas
3. **Dado** um novo serviço adicionado, **Quando** suas env vars são definidas, **Então** `.env.example` é atualizado

---

### User Story 3 - `.gitignore` Abrangente (Priority: P1)

Um desenvolvedor executa `git status` e vê apenas arquivos que devem ser versionados, evitando commits acidentais de arquivos sensíveis ou temporários.

**Por que esta prioridade**: Evita vazamento de dados e poluição do histórico do git. Crítico para segurança.

**Teste Independente**: Gerar artefatos (node_modules, __pycache__, containers, .env), executar `git status`, e verificar que nenhum deles aparece.

**Cenários de Aceitação**:

1. **Dado** que crio `node_modules/` ou `__pycache__/`, **Quando** executo `git status`, **Então** esses diretórios não aparecem
2. **Dado** que crio arquivo `.env`, `.DS_Store`, ou `docker-compose.override.yml`, **Quando** executo `git status`, **Então** nenhum deles é listado
3. **Dado** que crio artefatos de build (`.pyc`, `.o`, `dist/`), **Quando** executo `git status`, **Então** nenhum é listado

---

### User Story 4 - Configuração Base do Docker Compose (Priority: P2)

Um desenvolvedor executa `docker compose up --pull always` e vê todos os serviços core iniciando corretamente.

**Por que esta prioridade**: Não é bloqueante para ter estrutura de pastas, mas essencial para ambiente dev funcional.

**Teste Independente**: Executar `docker compose up` da raiz e verificar que todos os serviços ficam saudáveis.

**Cenários de Aceitação**:

1. **Dado** que executo `docker compose up --pull always`, **Quando** os containers iniciam, **Então** todos os serviços core estão healthy
2. **Dado** que abro `infra/docker-compose.yml`, **Quando** leio o arquivo, **Então** vejo configuração base com override de `.env.example`
3. **Dado** que um serviço falha ao iniciar, **Quando** executo `docker logs`, **Então** recebo mensagem de erro clara

---

### User Story 5 - Documentação Estruturada e Navegável (Priority: P2)

Um desenvolvedor novo acessa `docs/` e encontra guias claros para entender ADRs, issues, e roadmap.

**Por que esta prioridade**: Importante para onboarding e governance, mas secundário à estrutura física funcionar.

**Teste Independente**: Abrir `docs/README.md`, seguir links para `docs/adr/`, `docs/issues/`, `docs/milestones/` e verificar conteúdo.

**Cenários de Aceitação**:

1. **Dado** que abro `docs/README.md`, **Quando** leio o conteúdo, **Então** vejo índice com links para ADRs, Issues, Milestones
2. **Dado** que clico em link para `docs/adr/`, **Quando** a página carrega, **Então** vejo template de ADR com exemplo
3. **Dado** que acesso `docs/milestones/`, **Quando** abro um milestone, **Então** vejo objectives e deliverables

---

### Edge Cases & Fallbacks

- O que acontece se um dev não tiver Docker instalado? → Documentação aponta para instalação (Docker Desktop, WSL2, cloud placement)
- E se um `.env.example` estiver desatualizado? → Pre-commit hook valida sincronismo
- E se alguém commitar arquivo em `.gitignore`? → Pre-commit hook previne
- E se uma porta (5432, 6379, 5672) já está em uso? → docker-compose exit com erro; dev verifica `docker logs`; alterna porta em `.env`
- E se 1 de 3 serviços falha ao iniciar? → docker-compose exit com erro; pre-commit hook valida; dev verifica logs
- E se `.husky/` criação falha com permission denied? → Dev verifica permissões de escrita; executa `chmod +x .husky/pre-commit`
- Qual é o procedimento se preciso fazer commit mesmo com hook falhando? → Use `git commit --no-verify` (documentado em `.husky/README.md`)

---

## Requirements

### Functional Requirements

- **FR-001**: Sistema DEVE criar estrutura de diretórios com `apps/`, `infra/`, `docs/` (com sub-pastas `adr/`, `issues/`, `milestones/`, `libs/`). Cada pasta DEVE ter `README.md` explicando seu propósito.

- **FR-002**: Sistema DEVE incluir `.env.example` com todas as variáveis necessárias (13 total: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, REDIS_URL, REDIS_DB, RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USER, RABBITMQ_PASSWORD, RABBITMQ_VHOST). **Naming**: Sem prefix global (ex: `DB_HOST`, `REDIS_URL`, `RABBITMQ_URL`). **Safe Defaults Definition**: Values that work in dev environment without exposing secrets (e.g., `DB_PASSWORD=postgres` for local dev, NEVER production credentials). Arquivo commentado e com valores defaults seguros.

- **FR-003**: Sistema DEVE incluir `.gitignore` abrangente com padrões exatos:
  - **Python**: `__pycache__/`, `*.pyc`, `*.pyo`, `*.egg-info/`, `venv/`, `.venv/`, `*.egg`, `dist/`, `build/`
  - **Node.js**: `node_modules/`, `npm-debug.log`, `yarn-error.log`, `dist/`, `.next/`
  - **Docker**: `docker-compose.override.yml`, `.dockerignore`
  - **Environment**: `.env`, `.env.local`, `.env.*.local`
  - **IDEs**: `.vscode/`, `.idea/`, `*.swp`, `*.swo`, `*.swn`
  - **OS**: `.DS_Store`, `Thumbs.db`, `.vagrant/`
  
  **Validation**: Pre-commit hook obrigatório via husky que valida sincronismo entre `.env.example` e variáveis de ambiente. Bloqueia commit de arquivos `.env` (não `.env.example`). **Bypass**: Developers can use `git commit --no-verify` in emergencies (documented in `.husky/README.md`).

- **FR-004**: Sistema DEVE incluir `infra/docker-compose.yml` com configuração base e `infra/docker-compose.core.yml` com serviços core: **PostgreSQL 15**, **Redis 7**, **RabbitMQ 3.12** (message broker). Todos serviços DEVEM ter health checks com interval 10s, timeout 5s, retries 5. **No compose override example provided** — devs criam seu próprio `.override.yml` conforme necessidade.

- **FR-005**: Sistema DEVE incluir documentação em `docs/README.md` com navegação para ADRs, Issues, Milestones. **ADR Format: MADR** (Markdown Architectural Decision Records) com seções Status, Context, Decision, Consequences, Compliance. **Numbering Scheme**: ADRs numbered 001, 002, 003... (zero-padded 3-digit, global scope, independent of milestones).

- **FR-006**: Desenvolvedores DEVEM conseguir validar estrutura com comando único verificando: diretórios, arquivos, sintaxe YAML, health checks Docker.

- **FR-006a** (NEW): Sistema DEVE incluir documentação com procedimento alternativo quando Docker não está instalado (opções: instalação Docker Desktop, WSL2, Docker em nuvem).

### Core Services Defined

- **PostgreSQL 15**: Database principal para aplicações. Health check: `pg_isready -U postgres`
- **Redis 7**: Cache distribuído + Session Store + Pub/Sub. Health check: `redis-cli ping`
- **RabbitMQ 3.12**: Message broker para async tasks. Health check: `curl -f http://localhost:15672/api/aliveness-test/%2F -u guest:guest`

### Key Entities

- **Monorepo Root**: Diretório raiz com configuração global (`.env.example`, `.gitignore`, `package.json`)
- **App**: Aplicação dentro de `apps/`
- **Service**: Serviço containerizado em Docker Compose (PostgreSQL, Redis, RabbitMQ)
- **Environment Variable**: Configuração em `.env` (sem prefix, 13 variáveis core)
- **Documentation Page**: Arquivo markdown em `docs/` navegável
- **Dependency Chain**: husky → npm → Node.js 18+

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: Estrutura 100% criada, `git status` mostra apenas files rastreados
- **SC-002**: `docker compose up --pull always` inicia sem erros, todos 3 serviços healthy (timeout <= 30s)
- **SC-003**: Dev novo consegue: clonar → copiar `.env.example` → `docker compose up` → acessar docs, sem erros adicionais
- **SC-004**: Todos links em `docs/README.md` válidos e navegáveis
- **SC-005**: Nenhum arquivo sensível (`.env`, `*.key`, credentials) pode ser committed acidentalmente (pre-commit hook previne)

---

## Out of Scope (Deferred)

- **Observability** (logging, metrics, tracing): Deferred to ISSUE-102 (v0.1 Phase 2)
- **Version Upgrade Management**: Deferred to ISSUE-103 (v0.2)
- **Multi-instance Orchestration** (Kubernetes, Swarm): Deferred to v0.2+
- **Native Windows Support** (Docker Desktop only): Deferred to v0.2

---

## Clarifications

### Session 2026-10-01

- **Q1**: Quais serviços core? → **A: PostgreSQL 15 + Redis 7 + RabbitMQ 3.12**
- **Q2**: Qual prefix de env vars? → **A: Sem prefix global (DB_HOST, REDIS_URL, RABBITMQ_URL, etc.)**
- **Q3**: Docker Compose override example? → **A: Não incluir — cada dev cria seu próprio conforme necessidade**
- **Q4**: Formato de ADRs? → **A: MADR (Markdown Architectural Decision Records), numbered 001, 002, ...**
- **Q5**: Pre-commit hooks para validar `.env.example`? → **A: Sim, obrigatório com husky; bypass via `--no-verify` documented**

## Assumptions

- **Tecnologia**: Docker + Docker Compose (v2.0+) é padrão para dev; Node.js 18+ para pre-commit hooks (husky)
- **Ambiente**: Devs rodam em macOS, Linux ou WSL2; native Windows support TBD
- **Git**: Repo em Git com modelo de branches
- **Registry**: Public Docker registries (Docker Hub, etc.) são acessíveis
- **Scope v0.1**: Infra + core; multi-instance (Kubernetes) deferred to v0.2+
- **Segurança**: `.env` NUNCA committed; `.env.example` é template público
- **Linguagens**: Python 3.11+ e Node.js 18+ inicialmente; Go pode vir depois
- **Pre-commit Hooks**: Node.js 18+ required for husky; alternative pre-commit tools (bash-based) can be used if Node unavailable
- **Performance**: Dev environment startup < 30 seconds; health check all services < 5 seconds

