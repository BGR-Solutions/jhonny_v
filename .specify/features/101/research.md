# Research Findings: ISSUE-101 Phase 0

**Date**: 2026-10-01 | **Status**: Complete

All clarification questions resolved in `/speckit-clarify`. This research document consolidates findings on infrastructure decisions.

---

## Research Topics & Findings

### 1. Service Health Checks

**Decision**: Implement Docker Compose health checks for all three core services.

**Rationale**: 
- Health checks enable Docker to mark containers as "healthy" vs. "unhealthy"
- `docker compose up` will wait for all services before returning
- Prerequisite for later observability (Prometheus scraping)

**Alternatives Considered**: 
- Manual health check scripts — Too fragile; requires polling
- No health checks — Can't detect service readiness; breaks DX

**Implementation**:

```yaml
# PostgreSQL
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U postgres"]
  interval: 10s
  timeout: 5s
  retries: 5

# Redis
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 10s
  timeout: 5s
  retries: 5

# RabbitMQ
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:15672/api/aliveness-test/%2F", "-u", "guest:guest"]
  interval: 10s
  timeout: 5s
  retries: 5
```

---

### 2. Environment Variable Naming Convention

**Decision**: NO global prefix. Use service-specific names (e.g., `DB_HOST`, `REDIS_URL`, `RABBITMQ_USER`).

**Rationale**: 
- Simpler to read and remember
- Aligns with common Docker Compose and service tooling conventions
- Namespace is implicit (each service has its own var set)

**Alternatives Considered**: 
- `APP_DB_HOST` (global `APP_` prefix) — More verbose; less common
- Fully qualified `DATABASE_CONNECTION_HOST` — Too long

**Implementation**: 

```env
# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=app_db

# Redis
REDIS_URL=redis://localhost:6379
REDIS_DB=0

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_VHOST=/
```

---

### 3. Pre-commit Hook Strategy

**Decision**: Use Husky + pre-commit hook to validate `.env.example` consistency.

**Rationale**: 
- Husky is industry standard for Node.js projects
- Pre-commit hooks prevent commits if validation fails
- Reduces CI/CD burden by catching issues early

**Alternatives Considered**: 
- CI/CD only validation — Slower feedback (PR stage)
- No validation — Risk of `.env.example` falling out of sync

**Implementation**:

```bash
#!/bin/bash
# .husky/pre-commit

# Check if any .env files (excluding .env.example) are being committed
if git diff --cached --name-only | grep -E '\.env$|\.env\.[a-z]+$' | grep -v '\.env\.example'; then
  echo "ERROR: Detected .env file in commit (secrets leak risk)"
  echo "Use .env.example for template; .env is gitignored"
  exit 1
fi

# Validate .env.example exists and has basic structure
if [ ! -f .env.example ]; then
  echo "WARNING: .env.example not found"
  exit 1
fi

echo "✅ Pre-commit checks passed"
exit 0
```

---

### 4. MADR (Markdown Architectural Decision Records) Format

**Decision**: Use MADR format with standard sections: Status, Context, Decision, Consequences, Compliance.

**Rationale**: 
- MADR is modern, lightweight, and widely adopted
- GitHub renders MADR naturally
- Structured format enables tooling and searchability

**Alternatives Considered**: 
- Y-Statements — Too brief for detailed decisions
- RFC format — Too verbose for v0.1

**Template Structure**:

```markdown
# ADR-NNN: [Title]

**Status**: Proposed | Accepted | Deprecated | Superseded

## Context

[What prompted this decision? What was the problem?]

## Decision

[What decision was made? (Declarative)]

## Consequences

[What are the positive and negative outcomes?]

[Positive]
- Benefit 1
- Benefit 2

[Negative]
- Risk 1
- Risk 2

## Compliance

[Does this comply with constitution/principles? Any dependencies on other ADRs?]
```

---

### 5. .gitignore Patterns for Polyglot Monorepo

**Decision**: Comprehensive `.gitignore` covering Node.js, Python, Docker, IDEs, OS files.

**Rationale**: 
- Prevents accidental commits of build artifacts, dependencies, secrets
- Reduces repo size and noise
- Critical for security (prevents `.env` commits)

**Coverage**:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/
.venv/
venv/

# Node.js
node_modules/
npm-debug.log
yarn-error.log
dist/
.next/

# Docker
docker-compose.override.yml
.dockerignore

# Environment
.env
.env.local
.env.*.local

# IDEs
.vscode/
.idea/
*.swp
*.swo
*.swn

# OS
.DS_Store
Thumbs.db
.vagrant/

# Build artifacts
*.o
*.a
*.so
*.egg

```

---

### 6. Docker Compose Split Strategy (Base vs. Core)

**Decision**: 
- `docker-compose.yml` — Base configuration (networks, volumes, defaults)
- `docker-compose.core.yml` — Services only (PostgreSQL, Redis, RabbitMQ)

**Rationale**: 
- Separates infrastructure config from service definitions
- Allows extending with `docker-compose.override.yml` later
- Clear responsibility: core contains what users "must have"

**Alternatives Considered**: 
- Single monolithic `docker-compose.yml` — Less modular
- Three separate files per service — Too fragmented

---

## Validation Results

✅ All unknowns resolved
✅ All design decisions justified
✅ Ready for Phase 1 artifact generation

---

**Next**: Generate `data-model.md` and `quickstart.md` (Phase 1)

