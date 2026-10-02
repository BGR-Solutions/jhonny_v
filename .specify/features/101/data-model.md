# Data Model: ISSUE-101 - Estrutura Base do Monorepo

**Date**: 2026-10-01 | **Status**: Complete

---

## Entities & Relationships

### 1. Environment Variables Entity

**Purpose**: Centralized configuration for development environment

**Fields**:

| Field | Type | Example | Constraint |
|-------|------|---------|-----------|
| `DB_HOST` | string | `localhost` | Required; must resolve to active PostgreSQL |
| `DB_PORT` | integer | `5432` | Required; 1024-65535 |
| `DB_USER` | string | `postgres` | Required; minimum 3 chars |
| `DB_PASSWORD` | string | `postgres` | Required; NO default in production |
| `DB_NAME` | string | `app_db` | Required; valid PostgreSQL identifier |
| `REDIS_URL` | URL | `redis://localhost:6379` | Required; valid Redis URL format |
| `REDIS_DB` | integer | `0` | Optional; 0-15 |
| `RABBITMQ_HOST` | string | `localhost` | Required; resolvable hostname |
| `RABBITMQ_PORT` | integer | `5672` | Required; 1024-65535 |
| `RABBITMQ_USER` | string | `guest` | Required |
| `RABBITMQ_PASSWORD` | string | `guest` | Required |
| `RABBITMQ_VHOST` | string | `/` | Required; valid RabbitMQ vhost |

**Validation Rules**:

- All required fields must be present in `.env.example`
- No secret values in `.env.example` (use safe defaults or placeholder comments)
- Format: `KEY=value` (one per line, no spaces around `=`)
- Comments start with `#` and describe purpose
- Pre-commit hook validates no `.env` file (only `.env.example`) committed

---

### 2. Service Entity

**Purpose**: Docker Compose service definition

**Fields**:

| Field | Type | Allowed Values | Purpose |
|-------|------|----------------|---------|
| `name` | string | `postgresql`, `redis`, `rabbitmq` | Unique service identifier |
| `image` | string | `postgres:15`, `redis:7`, `rabbitmq:3.12` | Docker image reference |
| `container_name` | string | `app_postgres`, etc. | Optional; for debugging |
| `ports` | [port:port] | `["5432:5432"]` | Port mappings (host:container) |
| `environment` | map | `DB_USER: postgres` | Environment from `.env` |
| `healthcheck.test` | array | `["CMD-SHELL", "pg_isready ..."]` | Health check command |
| `healthcheck.interval` | string | `10s` | Interval between checks |
| `healthcheck.retries` | integer | `5` | Failed retries before unhealthy |
| `volumes` | [path] | `["postgres_data:/var/lib/postgresql/data"]` | Data persistence |

**Relationships**:
- Service → Environment (1:many) — Each service references multiple env vars
- Service → Volume (1:many) — Each service may mount multiple volumes

---

### 3. Architectural Decision Record (ADR)

**Purpose**: Document major design decisions for future reference

**Fields**:

| Field | Type | Cardinality | Purpose |
|-------|------|-------------|---------|
| `number` | integer | 1:1 | Unique identifier (001, 002, etc.) |
| `title` | string | 1:1 | Decision title |
| `status` | enum | 1:1 | Proposed \| Accepted \| Deprecated \| Superseded |
| `context` | text | 1:1 | Problem statement & constraints |
| `decision` | text | 1:1 | What was decided (declarative) |
| `consequences.positive` | [string] | 0:many | Benefits & advantages |
| `consequences.negative` | [string] | 0:many | Risks & downsides |
| `compliance` | text | 1:1 | Constitution alignment check |
| `created_at` | timestamp | 1:1 | Creation date |
| `superseded_by` | reference | 0:1 | Link to newer ADR (if deprecated) |

**Location**: `docs/adr/NNN-title.md`

**Relationships**:
- ADR → Milestone (0:many) — ADR may relate to milestone(s)
- ADR → Issue (0:many) — ADR may explain decisions made in issue(s)

---

### 4. Documentation Root Entity

**Purpose**: Main entry point for all project documentation

**Structure**:

```
docs/
├── README.md              # Index + navigation
├── adr/                   # Architecture decisions
├── issues/                # Issue tracking templates
└── milestones/            # Roadmap & deliverables
```

**Navigation Model**:
- `docs/README.md` → Links to all subdirectories
- Each subdirectory has own `README.md` with templates & examples
- All .md files are GitHub-rendered (no build step)

---

### 5. Directory Structure Entity

**Purpose**: Define canonical folder layout

**Hierarchy**:

```
repo_root/
├── apps/                  # Application containers
│   └── README.md          # Apps guide: "Place app code here"
├── infra/                 # Infrastructure & orchestration
│   ├── docker-compose.yml
│   ├── docker-compose.core.yml
│   └── README.md
├── docs/                  # Documentation (described above)
├── libs/                  # Shared libraries (pre-existing)
├── .env.example           # Environment template
├── .gitignore             # Git rules
├── .husky/                # Pre-commit hooks
└── package.json           # Root package (husky)
```

**Constraints**:
- Each folder must have `README.md` explaining its purpose
- No arbitrary files in root except `.env.example`, `.gitignore`, `package.json`, `.husky`
- `apps/` and `libs/` may have arbitrary structure (project-specific)

---

## State Transitions

### Service Lifecycle (Docker Compose)

```
State: "stopped"
  ↓ (docker compose up)
State: "starting"
  ↓ (health check passes)
State: "healthy"
  ↓ (docker compose stop)
State: "stopped"
```

### ADR Lifecycle

```
Status: "Proposed"
  ↓ (team approval)
Status: "Accepted"
  ↓ (superseding new ADR)
Status: "Superseded" (links to newer ADR)
```

---

## Validation & Invariants

**Invariant 1**: All environment variables referenced in `docker-compose.core.yml` must be defined in `.env.example`

**Invariant 2**: No `.env` file (untracked) can be committed; only `.env.example` (tracked)

**Invariant 3**: All ADRs must follow MADR format with all 5 sections (Status, Context, Decision, Consequences, Compliance)

**Invariant 4**: All services in `docker-compose.core.yml` must have health checks

**Invariant 5**: Directory structure must match defined hierarchy; no folders at root except those listed

---

## Data Dictionary

| Term | Definition | Context |
|------|-----------|---------|
| **Monorepo** | Single Git repository containing multiple apps/services | Architecture |
| **Core Services** | PostgreSQL, Redis, RabbitMQ (mandatory for v0.1) | Infrastructure |
| **Health Check** | Automated test verifying service is responsive | Docker Compose |
| **Pre-commit Hook** | Git hook executed before each commit | Security |
| **MADR** | Markdown Architectural Decision Record format | Documentation |
| **12-Factor** | Configuration via environment variables (methodology) | DevOps |

