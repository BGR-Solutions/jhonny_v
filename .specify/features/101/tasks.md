# Tasks: ISSUE-101 - Estrutura Base do Monorepo e Documentação Inicial

**Input**: Specification from `ISSUE-101.SPEC.md` (95/95 items validated ✅)  
**Prerequisites**: plan.md, research.md, data-model.md, quickstart.md (ALL COMPLETE)  
**Phase**: Phase 3 Implementation  
**Target**: v0.1 - Infra Core & Observabilidade

---

## Format: `[ID] [P?] [Story] Description`

- **[ID]**: Task identifier (T001, T002, etc.)
- **[P]**: Can run in parallel (different files/folders, no interdependencies)
- **[Story]**: Which user story (US1, US2, US3, US4, US5)
- **Paths**: Relative to repository root

---

## Phase 1: Setup (Shared Infrastructure - 5 min)

**Purpose**: Initialize monorepo structure and Git configuration

### Directory Structure

- [ ] **T001** [P] [CORE] Create directory structure: `apps/`, `infra/`, `docs/`, `libs/`
  - **Deliverable**: Five directories with `.gitkeep` files
  - **Files**: `apps/`, `infra/`, `docs/`, `libs/` (mkdir)

- [ ] **T002** [P] [CORE] Create `docs/` subdirectories: `adr/`, `issues/`, `milestones/`
  - **Deliverable**: Three subdirectories within docs/
  - **Files**: `docs/adr/`, `docs/issues/`, `docs/milestones/`

- [ ] **T003** [P] [CORE] Create root configuration directory: `.husky/`
  - **Deliverable**: Hidden directory for pre-commit hooks
  - **Files**: `.husky/`

**Checkpoint**: All 8 directories created ✅

---

## Phase 2: Foundational Configuration (Blocking - 20 min)

**Purpose**: Core configuration files that MUST be complete before ANY user story implementation

⚠️ **CRITICAL**: NO story work can begin until this phase completes

### Configuration Files

- [ ] **T004** [CORE] Create `.gitignore` with comprehensive patterns
  - **Deliverable**: `.gitignore` file with all required patterns
  - **Content**:
    - Python: `__pycache__/`, `*.pyc`, `*.pyo`, `*.egg-info/`, `venv/`, `.venv/`, `dist/`, `build/`
    - Node.js: `node_modules/`, `npm-debug.log`, `yarn-error.log`, `dist/`, `.next/`
    - Docker: `docker-compose.override.yml`, `.dockerignore`
    - Environment: `.env`, `.env.local`, `.env.*.local`
    - IDEs: `.vscode/`, `.idea/`, `*.swp`, `*.swo`, `*.swn`
    - OS: `.DS_Store`, `Thumbs.db`, `.vagrant/`
  - **Reference**: SPEC §FR-003, research.md §.gitignore Patterns
  - **Acceptance**: File present, all patterns covered, no conflicts

- [ ] **T005** [CORE] Create `.env.example` with all required variables
  - **Deliverable**: `.env.example` file with 13 environment variables
  - **Content** (annotated):
    ```
    # PostgreSQL (database)
    DB_HOST=localhost
    DB_PORT=5432
    DB_USER=postgres
    DB_PASSWORD=postgres
    DB_NAME=app_db
    
    # Redis (cache)
    REDIS_URL=redis://localhost:6379
    REDIS_DB=0
    
    # RabbitMQ (message broker)
    RABBITMQ_HOST=localhost
    RABBITMQ_PORT=5672
    RABBITMQ_USER=guest
    RABBITMQ_PASSWORD=guest
    RABBITMQ_VHOST=/
    ```
  - **Reference**: SPEC §FR-002, data-model.md §Environment Variables
  - **Acceptance**: 13 variables present, safe defaults (no production secrets), comments explain each

- [ ] **T006** [CORE] Create `package.json` (root, for husky)
  - **Deliverable**: `package.json` file at repository root
  - **Content**:
    ```json
    {
      "name": "monorepo",
      "version": "0.1.0",
      "private": true,
      "scripts": {
        "prepare": "husky install"
      },
      "devDependencies": {
        "husky": "^8.0.0"
      }
    }
    ```
  - **Reference**: research.md §Pre-commit Hook Strategy
  - **Acceptance**: File present, husky dependency declared

- [ ] **T007** [CORE] Create `.husky/pre-commit` hook script
  - **Deliverable**: `.husky/pre-commit` executable script
  - **Content**: 
    - Check for `.env` files (except `.env.example`) being committed
    - Validate `.env.example` exists and has basic structure
    - Block commit if `.env` detected (error message)
    - Pass if checks succeed
  - **Reference**: research.md §Pre-commit Hook Strategy, SPEC §FR-003
  - **Acceptance**: Script exists, executable, blocks `.env` commits, passes on valid state

### Environment & Dependencies

- [ ] **T008** [P] [CORE] Run `npm install` to install Node dependencies
  - **Deliverable**: `node_modules/` directory (ignored in git), `package-lock.json`
  - **Command**: `npm install` from repository root
  - **Reference**: SPEC §Assumptions
  - **Acceptance**: husky installed, hook framework ready

- [ ] **T009** [P] [CORE] Initialize husky
  - **Deliverable**: `.husky/_/husky.sh` framework files
  - **Command**: `npx husky install` from repository root
  - **Reference**: research.md §Pre-commit Hook Strategy
  - **Acceptance**: `.husky/` contains framework files, pre-commit hook linked

**Checkpoint**: Foundation complete - all prerequisites for user stories ready ✅

---

## Phase 3: User Story 1 - Estrutura de Diretórios (Priority: P1) 🎯 MVP

**Goal**: Directory structure created and validated with clear purpose statements in README files

**Independent Test**: Run `tree -L 2` → Confirm all directories exist with README files

### Documentation for Directory Structure

- [ ] **T010** [P] [US1] Create `apps/README.md`
  - **Deliverable**: README file explaining apps directory
  - **Content**:
    - Purpose: "Applications in this monorepo"
    - Guidelines: "Place application source code here (e.g., `backend/`, `workers/`, `cli/`)"
    - Structure example
  - **Acceptance**: File exists, clearly describes purpose

- [ ] **T011** [P] [US1] Create `infra/README.md`
  - **Deliverable**: README file explaining infra directory
  - **Content**:
    - Purpose: "Infrastructure configuration and Docker orchestration"
    - Files: docker-compose.yml, docker-compose.core.yml
    - How to use: `docker compose up`
  - **Acceptance**: File exists, clearly describes purpose

- [ ] **T012** [P] [US1] Create `docs/README.md` (master index)
  - **Deliverable**: README file with documentation index
  - **Content**:
    - Purpose: "Project documentation"
    - Index links to: ADRs, Issues, Milestones
    - Navigation: "See subdirectories for specific documentation types"
  - **Acceptance**: File exists with links to adr/, issues/, milestones/

- [ ] **T013** [P] [US1] Create `docs/adr/README.md`
  - **Deliverable**: ADR directory README with MADR template
  - **Content**:
    - Purpose: "Architectural Decision Records (MADR format)"
    - Template with sections: Status, Context, Decision, Consequences, Compliance
    - Numbering scheme: 001, 002, 003... (zero-padded, global scope)
    - Example link: `001-database-choice.md`
  - **Reference**: SPEC §FR-005, data-model.md §ADR entity
  - **Acceptance**: File exists with complete MADR template + numbering scheme

- [ ] **T014** [P] [US1] Create example ADR: `docs/adr/001-database-choice.md`
  - **Deliverable**: Example ADR in MADR format
  - **Content**:
    ```markdown
    # ADR-001: PostgreSQL as Primary Database
    
    **Status**: Accepted
    
    ## Context
    v0.1 requires a reliable database for application data.
    
    ## Decision
    Use PostgreSQL 15 as the primary database for all applications.
    
    ## Consequences
    [Positive]
    - ACID compliance
    - JSON support
    - Wide adoption
    
    [Negative]
    - Requires database client libraries
    
    ## Compliance
    Aligns with Infrastructure Core principle (v0.1 milestone).
    ```
  - **Reference**: research.md §MADR Format
  - **Acceptance**: File follows MADR structure with all 5 sections

- [ ] **T015** [P] [US1] Create `docs/issues/README.md`
  - **Deliverable**: Issues directory README with templates
  - **Content**:
    - Purpose: "Issue tracking guidelines"
    - Template structure (simple)
  - **Acceptance**: File exists, describes issue documentation approach

- [ ] **T016** [P] [US1] Create `docs/milestones/README.md`
  - **Deliverable**: Milestones directory README with templates
  - **Content**:
    - Purpose: "Roadmap and milestone definitions"
    - Milestone structure: Name, Objectives, Deliverables, Issues
    - Example: v0.1 milestone definition
  - **Acceptance**: File exists with milestone template

**Checkpoint**: All directories have clear README files; structure is self-documenting ✅

---

## Phase 4: User Story 2 - Arquivo `.env.example` Centralizado (Priority: P1) 🎯 MVP

**Goal**: Centralized environment configuration with safe defaults

**Independent Test**: `cp .env.example .env` → Verify all 13 variables present, safe defaults used

**Status**: ✅ **ALREADY COMPLETED in T005**

**Validation**:
- [ ] **T017** [US2] Validate `.env.example` has all 13 required variables
  - **Deliverable**: Validation checklist
  - **Check**:
    - DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME (PostgreSQL)
    - REDIS_URL, REDIS_DB (Redis)
    - RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USER, RABBITMQ_PASSWORD, RABBITMQ_VHOST (RabbitMQ)
  - **Acceptance**: All 13 present, safe defaults, no production secrets

**Checkpoint**: `.env.example` complete and validated ✅

---

## Phase 5: User Story 3 - `.gitignore` Abrangente (Priority: P1) 🎯 MVP

**Goal**: Comprehensive gitignore with exact patterns (Python, Node, Docker, IDEs, OS)

**Independent Test**: `git status` shows NO build artifacts or `.env` files as untracked

**Status**: ✅ **ALREADY COMPLETED in T004**

### Validation

- [ ] **T018** [P] [US3] Validate `.gitignore` patterns
  - **Test Cases**:
    - Create `node_modules/` → Should be ignored
    - Create `__pycache__/` → Should be ignored
    - Create `.env` → Should be ignored
    - Create `.env.example` → Should NOT be ignored
    - Create `docker-compose.override.yml` → Should be ignored
    - Create `.vscode/` → Should be ignored
    - Create `.DS_Store` → Should be ignored
  - **Command**: `git status` after creating test files → Verify none appear as untracked
  - **Cleanup**: Remove test files
  - **Acceptance**: All artifacts properly ignored, `.env.example` NOT ignored

**Checkpoint**: `.gitignore` validated, gitignore behavior correct ✅

---

## Phase 6: User Story 4 - Configuração Base do Docker Compose (Priority: P2)

**Goal**: Docker Compose setup with core services (PostgreSQL, Redis, RabbitMQ) running healthily

**Independent Test**: `docker compose up --pull always` → All 3 services healthy within 30s

### Docker Compose Configuration

- [ ] **T019** [CORE] Create `infra/docker-compose.yml` (base configuration)
  - **Deliverable**: Base Docker Compose file
  - **Content**:
    - Version: 3.9+
    - Networks: default bridge network
    - Volumes: named volumes for persistence
    - Common environment variables sourced from `.env`
    - Services will be added via docker-compose.core.yml
  - **Reference**: research.md §Docker Compose Split Strategy, plan.md §Project Structure
  - **Acceptance**: File valid YAML, includes base network/volume definitions

- [ ] **T020** [CORE] Create `infra/docker-compose.core.yml` (core services)
  - **Deliverable**: Core services file (Postgres, Redis, RabbitMQ)
  - **Content** (3 services):
    
    **PostgreSQL 15**:
    ```yaml
    services:
      postgres:
        image: postgres:15
        container_name: app_postgres
        environment:
          POSTGRES_HOST_AUTH_METHOD: trust
          POSTGRES_USER: ${DB_USER}
          POSTGRES_PASSWORD: ${DB_PASSWORD}
          POSTGRES_DB: ${DB_NAME}
        ports:
          - "${DB_PORT}:5432"
        volumes:
          - postgres_data:/var/lib/postgresql/data
        healthcheck:
          test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
          interval: 10s
          timeout: 5s
          retries: 5
    ```
    
    **Redis 7**:
    ```yaml
      redis:
        image: redis:7
        container_name: app_redis
        ports:
          - "6379:6379"
        healthcheck:
          test: ["CMD", "redis-cli", "ping"]
          interval: 10s
          timeout: 5s
          retries: 5
    ```
    
    **RabbitMQ 3.12**:
    ```yaml
      rabbitmq:
        image: rabbitmq:3.12-management
        container_name: app_rabbitmq
        environment:
          RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER}
          RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD}
          RABBITMQ_DEFAULT_VHOST: ${RABBITMQ_VHOST}
        ports:
          - "${RABBITMQ_PORT}:5672"
          - "15672:15672"  # Management UI
        healthcheck:
          test: ["CMD", "curl", "-f", "http://localhost:15672/api/aliveness-test/%2F", "-u", "${RABBITMQ_USER}:${RABBITMQ_PASSWORD}"]
          interval: 10s
          timeout: 5s
          retries: 5
    
    volumes:
      postgres_data:
      redis_data:
      rabbitmq_data:
    ```
  - **Reference**: SPEC §FR-004, research.md §Service Health Checks
  - **Acceptance**: All 3 services defined, health checks present, environment vars from .env

### Service Verification

- [ ] **T021** [P] [US4] Test Docker Compose syntax validation
  - **Command**: `docker compose -f infra/docker-compose.yml -f infra/docker-compose.core.yml config` (validate)
  - **Acceptance**: No YAML errors, config valid

- [ ] **T022** [US4] Start services and verify health
  - **Commands**:
    ```bash
    docker compose -f infra/docker-compose.yml -f infra/docker-compose.core.yml up -d --pull always
    sleep 15
    docker compose ps
    ```
  - **Acceptance**: All 3 services show "Up" and "healthy" status

- [ ] **T023** [P] [US4] Individual service health checks
  - **PostgreSQL**: `docker exec app_postgres pg_isready -U postgres` → Exit code 0
  - **Redis**: `docker exec app_redis redis-cli ping` → Response: PONG
  - **RabbitMQ**: `curl -u guest:guest http://localhost:15672/api/aliveness-test/%2F` → {"status":"ok"}
  - **Acceptance**: All checks pass

- [ ] **T024** [P] [US4] Connection tests
  - **PostgreSQL**: `psql -h localhost -U postgres -d app_db -c "SELECT 1;"` → Returns 1
  - **Redis**: `redis-cli -h localhost ping` → PONG
  - **RabbitMQ**: `curl -u guest:guest http://localhost:15672/api/connections` → JSON response
  - **Acceptance**: All connections successful

- [ ] **T025** [US4] Cleanup
  - **Command**: `docker compose down`
  - **Acceptance**: All containers stopped

**Checkpoint**: Docker Compose fully functional, all services healthy ✅

---

## Phase 7: User Story 5 - Documentação Estruturada (Priority: P2)

**Goal**: Navigation and templates for ADRs, issues, and milestones

**Independent Test**: All links in `docs/README.md` valid and navigable; MADR format clear

**Status**: ✅ **ALREADY COMPLETED in T010-T016**

### Documentation Validation

- [ ] **T026** [P] [US5] Verify all documentation files exist
  - **Files**:
    - `docs/README.md` ✅
    - `docs/adr/README.md` ✅
    - `docs/adr/001-database-choice.md` ✅
    - `docs/issues/README.md` ✅
    - `docs/milestones/README.md` ✅
  - **Acceptance**: All 5 files present

- [ ] **T027** [P] [US5] Validate markdown formatting
  - **Check**:
    - All files render in GitHub/GitLab
    - No broken links (internal references valid)
    - Headers correctly formatted
  - **Acceptance**: All markdown valid, links functional

- [ ] **T028** [US5] Verify MADR template completeness
  - **Sections**: Status, Context, Decision, Consequences, Compliance
  - **Numbering**: 001-database-choice.md example
  - **Acceptance**: Template complete, example follows format

**Checkpoint**: Documentation complete, navigable, templates clear ✅

---

## Phase 8: Integration & Validation (10 min)

**Purpose**: End-to-end validation using quickstart.md scenarios

### Git Status & Tracking

- [ ] **T029** [CORE] Verify git status clean
  - **Command**: `git status`
  - **Acceptance**: No untracked files except `.env` (gitignored)

- [ ] **T030** [P] [CORE] Add files to git
  - **Commands**:
    ```bash
    git add .
    git status
    ```
  - **Acceptance**: All required files staged (directories, configs, docs)

- [ ] **T031** [CORE] Commit initial structure
  - **Command**: `git commit -m "ISSUE-101: Initial monorepo structure, Docker Compose, documentation"`
  - **Acceptance**: Commit succeeds, pre-commit hook passes

### Run Quickstart Validation Scenarios

- [ ] **T032** [P] [US1-US5] Scenario 1: Directory structure
  - **Reference**: quickstart.md §Scenario 1
  - **Command**: `tree -L 2`
  - **Acceptance**: Confirms all directories present with READMEs

- [ ] **T033** [P] [US2] Scenario 2: Environment configuration
  - **Reference**: quickstart.md §Scenario 2
  - **Commands**: `cp .env.example .env` + grep checks
  - **Acceptance**: All 13 variables found, safe defaults

- [ ] **T034** [P] [US3] Scenario 3: .gitignore coverage
  - **Reference**: quickstart.md §Scenario 3
  - **Commands**: Create test artifacts + `git status`
  - **Acceptance**: All properly ignored

- [ ] **T035** [US4] Scenario 4: Docker services
  - **Reference**: quickstart.md §Scenario 4
  - **Commands**: `docker compose up`, health checks, connection tests
  - **Acceptance**: All 3 services healthy

- [ ] **T036** [P] [CORE] Scenario 5: Pre-commit hooks
  - **Reference**: quickstart.md §Scenario 5
  - **Commands**: `npm install`, try committing `.env.test`
  - **Acceptance**: Hook blocks `.env` commits

- [ ] **T037** [P] [US5] Scenario 6: ADR structure
  - **Reference**: quickstart.md §Scenario 6
  - **Check**: MADR sections present in 001-database-choice.md
  - **Acceptance**: All 5 sections found

- [ ] **T038** [CORE] Scenario 7: Git status final
  - **Reference**: quickstart.md §Scenario 7
  - **Command**: `git status`
  - **Acceptance**: Clean working tree, required files tracked

**Checkpoint**: All 7 quickstart scenarios pass ✅

---

## Phase 9: Documentation & Closure (5 min)

### Implementation Summary

- [ ] **T039** [CORE] Create IMPLEMENTATION-LOG.md
  - **Deliverable**: Log of all tasks completed
  - **Content**:
    - Date completed
    - All tasks T001-T038 status
    - Total time: ~60 minutes
    - Validation: 7/7 quickstart scenarios pass
    - Git commit: [hash]
  - **Acceptance**: File exists with complete log

- [ ] **T040** [CORE] Verify checklist 95/95 items satisfied
  - **Reference**: `.specify/features/101/checklists/requirements.md`
  - **Check**: All 95 items marked `[x]`
  - **Acceptance**: Confirmed 95/95 coverage

**Checkpoint**: Implementation complete, documented, validated ✅

---

## Dependencies & Sequencing

### Critical Path (Blocker Sequence)

```
T001-T003 (Create directories)
    ↓
T004-T009 (Foundational config + Node setup)
    ↓
T010-T025 (All user story implementations - can be PARALLEL after T009)
    ↓
T029-T038 (Integration & validation)
    ↓
T039-T040 (Documentation & closure)
```

### Parallelization Opportunities

**After T009** (Foundational complete), run in parallel:
- **T010-T016** (All documentation - different files)
- **T017-T025** (Docker Compose - different files)

**Within Phase**: 
- **T010, T011, T012, T013, T015, T016** (Documentation) — [P] tasks
- **T021, T023, T024** (Service verification) — [P] tasks
- **T032-T034, T036-T037** (Quickstart scenarios) — [P] tasks

### Minimum Time (Full Parallelization)

- T001-T003: 5 min (setup)
- T004-T009: 10 min (foundation)
- T010-T025: 15 min (all in parallel)
- T029-T040: 10 min (validation + closure)
- **TOTAL: ~40 minutes** (with full parallelization)

### Conservative Time (Sequential)

- All phases sequential: ~60 minutes
- See plan.md §Estimated Timeline

---

## Implementation Readiness Gates

### Pre-Implementation Gate

- [x] Specification complete (95/95 items validated)
- [x] Plan reviewed and approved
- [x] Research findings integrated
- [x] Architecture documented
- [x] All prerequisites met

### Post-Implementation Gate (Definition of Done)

- [ ] All 40 tasks completed (T001-T040)
- [ ] All 7 quickstart scenarios pass
- [ ] 95/95 checklist items confirmed satisfied
- [ ] Git status clean, all changes committed
- [ ] IMPLEMENTATION-LOG.md completed
- [ ] Pre-commit hooks functional
- [ ] Docker services verified healthy

### Sign-Off

- [ ] Developer: "All tasks complete, validation passed" ___________
- [ ] Reviewer: "Implementation matches spec, ready for Phase 4+" ___________
- [ ] Date: ___________

---

## Success Criteria Mapping

| SC | Task(s) | Verification |
|----|----|---|
| SC-001 | T001-T003, T029 | Directory structure 100%, git clean |
| SC-002 | T019-T025 | Docker compose up, all services healthy |
| SC-003 | T005-T009, T032-T033 | Dev can clone → copy .env → docker compose up |
| SC-004 | T012-T016, T027 | All docs links valid and navigable |
| SC-005 | T004, T007, T036 | No `.env` can be committed (hook prevents) |

---

## Next Steps After Implementation

1. ✅ Complete all 40 tasks (this document)
2. ✅ Validate all 7 quickstart scenarios pass
3. ✅ Run pre-commit hooks on final commit
4. 📋 **Next Issue**: ISSUE-102 (v0.1 Observability Phase 2)
   - Add Prometheus, Grafana, logging setup
   - Extend docker-compose with observability services

---

**Total Estimated Effort**: 40-60 minutes (depending on parallelization)  
**Start Date**: [TBD]  
**Target Completion**: [TBD]  
**Status**: 🚀 **READY FOR PHASE 3 IMPLEMENTATION**

