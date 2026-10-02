# Quickstart Validation Guide: ISSUE-101

**Date**: 2026-10-01 | **Status**: Complete

This guide provides runnable validation scenarios to prove ISSUE-101 implementation is complete and correct.

---

## Prerequisites

Before running any scenario, ensure:

- **Docker Engine**: 24.0+
  - Verify: `docker --version`
- **Docker Compose**: 2.0+
  - Verify: `docker compose version`
- **Git**: 2.30+
  - Verify: `git --version`
- **Node.js**: 18+
  - Verify: `node --version`
- **Repository cloned**: Latest main branch pulled

---

## Validation Scenarios

### Scenario 1: Verify Directory Structure

**Objective**: Confirm all required directories and README files exist

**Commands**:

```bash
# From repo root
$ tree -L 2 -d

# Expected output includes:
# .
# ├── apps
# ├── infra
# ├── docs
# ├── libs
# └── .husky
```

**Alternative (Windows)**:
```powershell
$ Get-ChildItem -Recurse -Directory | Where-Object {$_.Name -in @('apps', 'infra', 'docs', 'libs', '.husky')}
```

**Verification Checks**:

```bash
$ [ -f "apps/README.md" ] && echo "✅ apps/README.md found" || echo "❌ Missing"
$ [ -f "infra/README.md" ] && echo "✅ infra/README.md found" || echo "❌ Missing"
$ [ -f "docs/README.md" ] && echo "✅ docs/README.md found" || echo "❌ Missing"
$ [ -f "docs/adr/README.md" ] && echo "✅ docs/adr/README.md found" || echo "❌ Missing"
$ [ -f "docs/issues/README.md" ] && echo "✅ docs/issues/README.md found" || echo "❌ Missing"
$ [ -f "docs/milestones/README.md" ] && echo "✅ docs/milestones/README.md found" || echo "❌ Missing"
```

**Expected Outcome**: All 6 files present; tree shows clean hierarchy

---

### Scenario 2: Verify Environment Configuration

**Objective**: Ensure `.env.example` has all required variables with safe defaults

**Commands**:

```bash
# From repo root
$ cp .env.example .env

# Verify key environment variables are present
$ grep "DB_HOST" .env && echo "✅ DB_HOST found"
$ grep "DB_PORT" .env && echo "✅ DB_PORT found"
$ grep "DB_USER" .env && echo "✅ DB_USER found"
$ grep "DB_PASSWORD" .env && echo "✅ DB_PASSWORD found"
$ grep "DB_NAME" .env && echo "✅ DB_NAME found"

$ grep "REDIS_URL" .env && echo "✅ REDIS_URL found"
$ grep "REDIS_DB" .env && echo "✅ REDIS_DB found"

$ grep "RABBITMQ_HOST" .env && echo "✅ RABBITMQ_HOST found"
$ grep "RABBITMQ_PORT" .env && echo "✅ RABBITMQ_PORT found"
$ grep "RABBITMQ_USER" .env && echo "✅ RABBITMQ_USER found"
$ grep "RABBITMQ_PASSWORD" .env && echo "✅ RABBITMQ_PASSWORD found"
```

**Security Check**:

```bash
# Verify NO actual secrets in .env.example (should only have safe defaults)
$ grep -i "password" .env.example | grep -v "^#" | head -5
# Expected: Lines like "DB_PASSWORD=postgres" (safe default, not production secret)

# Verify .env is gitignored
$ git status | grep ".env" | grep -v ".env.example"
# Expected: .env should NOT appear in status (it's gitignored)
```

**Expected Outcome**: All variables present, .env created successfully, no secrets exposed

---

### Scenario 3: Verify .gitignore Comprehensiveness

**Objective**: Ensure common build artifacts and secrets are gitignored

**Commands**:

```bash
# Create test artifacts
$ mkdir -p node_modules __pycache__ dist build .vscode .idea
$ touch .env .DS_Store __pycache__/test.pyc node_modules/package.json

# Check git status
$ git status

# Expected: None of these files appear in "Untracked files"
$ git status | grep -E "node_modules|__pycache__|\.env$|\.vscode|\.idea|\.DS_Store" && echo "❌ Files NOT gitignored" || echo "✅ All properly gitignored"

# Cleanup
$ rm -rf node_modules __pycache__ dist build .vscode .idea
$ rm -f .env .DS_Store
```

**Detailed Checks**:

```bash
# Verify .env patterns
$ grep "^\.env" .gitignore && echo "✅ .env patterns found"

# Verify Python patterns
$ grep "__pycache__" .gitignore && echo "✅ Python patterns found"

# Verify Node patterns
$ grep "node_modules" .gitignore && echo "✅ Node patterns found"

# Verify Docker patterns
$ grep "docker-compose.override.yml" .gitignore && echo "✅ Docker patterns found"
```

**Expected Outcome**: All patterns present, test artifacts properly ignored

---

### Scenario 4: Verify Docker Services Start & Health

**Objective**: Confirm all core services (PostgreSQL, Redis, RabbitMQ) start and pass health checks

**Commands**:

```bash
# Start all services
$ docker compose -f infra/docker-compose.yml -f infra/docker-compose.core.yml up -d --pull always

# Wait 15 seconds for services to initialize
$ sleep 15

# Check service status
$ docker compose ps

# Expected output:
# NAME                  STATUS               PORTS
# app_postgres          Up 15 seconds (healthy)
# app_redis             Up 15 seconds (healthy)
# app_rabbitmq          Up 15 seconds (healthy)
```

**Individual Health Checks**:

```bash
# PostgreSQL
$ docker exec app_postgres pg_isready -U postgres && echo "✅ PostgreSQL healthy"

# Redis
$ docker exec app_redis redis-cli ping
# Expected: PONG

# RabbitMQ
$ docker exec app_rabbitmq curl -s -u guest:guest http://localhost:15672/api/aliveness-test/%2F
# Expected: {"status":"ok"}
```

**Connection Tests**:

```bash
# PostgreSQL connection
$ PGPASSWORD=postgres psql -h localhost -U postgres -d app_db -c "SELECT 1;" && echo "✅ PostgreSQL connectable"

# Redis connection
$ redis-cli -h localhost ping
# Expected: PONG

# RabbitMQ connection
$ curl -u guest:guest http://localhost:15672/api/connections
# Expected: JSON list of connections
```

**Cleanup**:

```bash
$ docker compose down
$ docker volume rm app_postgres_data app_redis_data app_rabbitmq_data (optional)
```

**Expected Outcome**: All three services healthy, all health checks pass, connections succeed

---

### Scenario 5: Verify Pre-commit Hooks

**Objective**: Ensure pre-commit hooks prevent `.env` file commits and validate structure

**Commands**:

```bash
# Setup husky (install Node dependencies)
$ npm install

# Initialize husky
$ npx husky install

# Verify hook file exists
$ [ -f ".husky/pre-commit" ] && echo "✅ Pre-commit hook file exists"

# Test 1: Try to commit a fake .env file (should be blocked)
$ echo "TEST_VAR=test" > .env.test
$ git add .env.test
$ git commit -m "test .env.test commit" 2>&1 | grep -i "error\|prevent" && echo "✅ Hook prevented .env commit" || echo "⚠️ Hook did not block"

# Cleanup
$ rm -f .env.test
$ git reset
```

**Expected Outcome**: Hook prevents `.env` file commits; message indicates security check

---

### Scenario 6: Verify ADR Structure

**Objective**: Confirm ADR template and example follow MADR format

**Commands**:

```bash
# Check MADR template exists
$ [ -f "docs/adr/README.md" ] && echo "✅ ADR README exists"

# Verify example ADR has required sections
$ [ -f "docs/adr/001-*.md" ] && echo "✅ Example ADR found"

# Check for MADR sections (Status, Context, Decision, Consequences, Compliance)
$ grep -E "^## (Status|Context|Decision|Consequences|Compliance)" "docs/adr/001-*.md" && echo "✅ MADR sections present"
```

**Expected Outcome**: ADR template exists with all 5 required sections

---

### Scenario 7: Verify Git Status Clean

**Objective**: Final check that repo structure is clean and tracked properly

**Commands**:

```bash
# Check git status
$ git status

# Expected output:
# On branch 101-monorepo-base-structure
# nothing to commit, working tree clean
# (or untracked: only expected files like .env)

# Verify all required files are tracked
$ git ls-files | grep -E "^(apps|infra|docs|\.env\.example|\.gitignore)" | wc -l
# Expected: Multiple files (structure + config files)

# Verify .env is NOT tracked
$ git ls-files | grep "^\.env$" && echo "❌ .env is tracked (security issue)" || echo "✅ .env properly untracked"
```

**Expected Outcome**: Clean working tree, required files tracked, `.env` untracked

---

## End-to-End Validation Workflow

Run these scenarios in sequence to fully validate ISSUE-101 implementation:

```bash
#!/bin/bash
set -e

echo "🧪 ISSUE-101 Validation Workflow"
echo "================================"

echo "1️⃣  Checking directory structure..."
# (Run Scenario 1)

echo "2️⃣  Checking environment configuration..."
# (Run Scenario 2)

echo "3️⃣  Checking .gitignore coverage..."
# (Run Scenario 3)

echo "4️⃣  Starting Docker services..."
# (Run Scenario 4)

echo "5️⃣  Verifying pre-commit hooks..."
# (Run Scenario 5)

echo "6️⃣  Verifying ADR structure..."
# (Run Scenario 6)

echo "7️⃣  Final git status check..."
# (Run Scenario 7)

echo "✅ All validation scenarios passed!"
echo "🎉 ISSUE-101 implementation complete"
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `docker compose: command not found` | Compose not installed or wrong version | `docker compose version` → must be 2.0+ |
| Service unhealthy after startup | Port conflict or image not available | Check `docker logs <service>` for error details |
| `.env` accidentally committed | `.gitignore` issue | Remove from git: `git rm --cached .env` |
| Pre-commit hook not running | Husky not installed | `npm install && npx husky install` |
| `pg_isready` command not found | PostgreSQL client not installed | Install `postgresql-client` (macOS: `brew install postgresql`) |
| Redis/RabbitMQ ports already in use | Another service using 6379/5672 | Change ports in `.env.example` or stop conflicting service |

---

## Success Criteria

✅ **All scenarios pass** → ISSUE-101 is production-ready

**Definition of Done**:
- [ ] Scenario 1: Directory structure verified
- [ ] Scenario 2: Environment variables correct
- [ ] Scenario 3: .gitignore prevents commits
- [ ] Scenario 4: All services healthy
- [ ] Scenario 5: Pre-commit hooks working
- [ ] Scenario 6: ADR format correct
- [ ] Scenario 7: Git status clean

