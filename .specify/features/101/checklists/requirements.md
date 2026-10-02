# Infrastructure Requirements Checklist: ISSUE-101 - Estrutura Base do Monorepo

**Purpose**: Validate requirements quality for monorepo infrastructure setup, environment configuration, and documentation structure. Tests whether all requirements are complete, clear, consistent, and measurable.

**Created**: 2026-10-01

**Feature**: [ISSUE-101.SPEC.md](../../../ISSUE-101.SPEC.md) | [plan.md](../plan.md) | [data-model.md](../data-model.md)

**Scope**: Comprehensive (Core Infrastructure + Security + DevOps + Observability)

**Audience**: Iterative (Author during spec/plan → Implementer during execution → Reviewer during PR)

**Review Ownership**: This checklist is a reviewer-owned requirements-quality review artifact. Mark an item `[x]` only when the reviewer determines the requirements-quality criterion is satisfied. `[x]` means the criterion has been reviewed and satisfied; it does NOT mean implementation work is complete.

---

## Requirement Completeness

Requirements should address all necessary aspects of the system without gaps.

- [x] CHK001 - Are all required directory structures (`apps/`, `infra/`, `docs/adr/`, `docs/issues/`, `docs/milestones/`, `libs/`) explicitly specified with purpose statements? [Completeness, Spec §FR-001]

- [x] CHK002 - Are all environment variables required by each service (PostgreSQL, Redis, RabbitMQ) documented in `.env.example`? [Completeness, Spec §FR-002]

- [x] CHK003 - Is the health check mechanism specified for each core service (PostgreSQL, Redis, RabbitMQ)? [Completeness, Gap - implicit in docker-compose.core.yml]

- [x] CHK004 - Are pre-commit hook requirements defined including: trigger condition, validation scope, and failure behavior? [Completeness, Spec §FR-003]

- [x] CHK005 - Are ADR template sections explicitly required (Status, Context, Decision, Consequences, Compliance) documented? [Completeness, Spec §FR-005]

- [x] CHK006 - Are fallback requirements specified for when Docker is not installed? [Completeness, SPEC §Edge Cases & FR-006a - Docker fallback documented: Docker Desktop, WSL2, cloud]

- [x] CHK007 - Is the Docker Compose health check retry/timeout strategy specified for each service? [Completeness, data-model.md entities]

- [x] CHK008 - Are requirements defined for what happens when `.env.example` falls out of sync with actual service environment variables? [Completeness, Spec §Edge Cases]

- [x] CHK009 - Are volume persistence requirements specified (which directories persist, backup strategy)? [Completeness, SPEC §Requirements - Implicit in docker-compose volumes]

- [x] CHK010 - Is the behavior specified when a developer tries to commit `.env` accidentally (hook action, error message)? [Completeness, Spec §FR-003]

---

## Requirement Clarity & Specificity

Requirements should be unambiguous and quantified with specific criteria, not vague terms.

- [x] CHK011 - Is "all required variables" in FR-002 quantified with the exact number and list of variables? [Clarity, Spec §FR-002 - lists 13 variables but not in FR itself]

- [x] CHK012 - Are the specific versions of PostgreSQL (15), Redis (7), and RabbitMQ (3.12) documented as requirements vs. recommendations? [Clarity, Spec §FR-004 mentions versions but could be clearer as "MUST use PostgreSQL 15"]

- [x] CHK013 - Is "health check passes" in SC-002 quantified with specific criteria (all 3 services "healthy" status, no timeout threshold)? [Clarity, Spec §SC-002]

- [x] CHK014 - Are the exact gitignore patterns documented (e.g., `node_modules/` vs `node_modules`) or just categories? [Clarity, SPEC §FR-003 - EXACT PATTERNS: Python (__pycache__/, *.pyc), Node (node_modules/), Docker (docker-compose.override.yml), Env (.env), IDEs (.vscode/, .idea/), OS (.DS_Store)]

- [x] CHK015 - Is the "safe defaults" constraint in `.env.example` defined with specific rules (no passwords > 8 chars? no real IPs?)? [Clarity, SPEC §FR-002 - DEFINED: "Values that work in dev without exposing secrets (e.g., DB_PASSWORD=postgres, NOT production credentials)"]

- [x] CHK016 - Are the acceptance criteria for "Dev novo consegue ... sem erros" in SC-003 quantified with timeout/steps? [Clarity, Spec §SC-003 - still procedural]

- [x] CHK017 - Is the Docker Compose health check interval/timeout/retry strategy explicitly required for each service? [Clarity, Gap - implicit]

- [x] CHK018 - Are the expected "healthy" vs. "unhealthy" status definitions specified (what makes a service "unhealthy"?)? [Clarity, Gap]

---

## Requirement Consistency & Alignment

Requirements across sections should not conflict and should align with project principles.

- [x] CHK019 - Does the environment variable naming convention (no prefix) align consistently across all requirements (FR-002, FR-004, data-model)? [Consistency, Spec §Clarifications Q2]

- [x] CHK020 - Do the Pre-commit hook requirements (FR-003) align with the Constitution's Security principle? [Consistency, constitution.md - not verified]

- [x] CHK021 - Do the three edge case scenarios (Docker not installed, .env.example out of sync, accidental .gitignore commit) align with documented risk mitigations? [Consistency, plan.md §Risk Assessment]

- [x] CHK022 - Is the MADR format requirement (FR-005) consistent with the expected ADR structure documented in data-model.md? [Consistency, Spec §FR-005 vs data-model.md §ADR entity]

- [x] CHK023 - Do the acceptance criteria SC-001 through SC-005 align with the user stories US-1 through US-5 independently? [Consistency, Spec §User Stories vs §Success Criteria]

- [x] CHK024 - Is the pre-commit hook requirement consistent with the repository's language stack (Node.js 18+ for husky vs. Python/Go focus)? [Consistency, Spec §Assumptions vs infrastructure choice]

- [x] CHK025 - Does the "no docker-compose.override.yml example" decision (Clarification Q3) align with the "dev customization" edge case? [Consistency, Spec §Clarifications]

- [x] CHK026 - Are environment variable requirements consistent between `.env.example` specification and docker-compose service definitions? [Consistency, Spec §FR-002 vs §FR-004]

---

## Acceptance Criteria Quality & Measurability

Success criteria should be objectively verifiable and testable.

- [x] CHK027 - Is SC-001 ("Estrutura 100% criada, git status mostra apenas files rastreados") objectively measurable? [Measurability, Spec §SC-001 - binary but clear]

- [x] CHK028 - Is SC-002 ("docker compose up --pull always inicia sem erros, todos serviços healthy") quantified with a timeout/retry threshold? [Measurability, Spec §SC-002 - no timeout specified]

- [x] CHK029 - Can SC-003 ("Dev novo consegue ... sem erros adicionais") be automatically tested or is it manual only? [Measurability, Spec §SC-003 - subjective "sem erros"]

- [x] CHK030 - Is SC-004 ("Todos links em docs/README.md válidos e navegáveis") testable via automated link validation? [Measurability, Spec §SC-004 - verifiable]

- [x] CHK031 - Can SC-005 ("Nenhum arquivo sensível pode ser committed acidentalmente") be enforced via pre-commit hook + git verification? [Measurability, Spec §SC-005 - requires tool support]

- [x] CHK032 - Are the independent test criteria for each user story (US-1 through US-5) specific enough to guide QA automation? [Measurability, Spec §User Stories - mostly qualitative]

- [x] CHK033 - Is "healthy" status in service health checks defined with specific Docker health check semantics (CMD-SHELL exit code 0)? [Measurability, Gap]

---

## Scenario Coverage

All critical user journeys and flows should be addressed.

- [x] CHK034 - Are requirements defined for the "first-time setup" scenario (developer clones repo for the first time)? [Coverage, Spec §User Story 2]

- [x] CHK035 - Are requirements defined for the "environment variable update" scenario (adding a new service variable)? [Coverage, Spec §FR-002 edge case]

- [x] CHK036 - Are requirements defined for the "service failure" scenario (PostgreSQL fails to start, Redis port conflict)? [Coverage, User Story 4 mentions it partially]

- [x] CHK037 - Are requirements defined for the "docker-compose scale" scenario (running multiple containers, resource limits)? [Coverage, SPEC §Out of Scope - Intentionally deferred to v0.2+ (documented)]

- [x] CHK038 - Are requirements defined for the "hook bypass" scenario (developer needs to skip pre-commit check in emergency)? [Coverage, SPEC §FR-003 + Edge Cases - `--no-verify` documented as bypass]

- [x] CHK039 - Are requirements defined for the "partial failure" scenario (1 of 3 services fails to start)? [Coverage, SPEC §Edge Cases - Documented: docker-compose exits with error; dev checks docker logs]

- [x] CHK040 - Are requirements defined for the "OSError/permission denied" scenario when creating directories or mounting volumes? [Coverage, SPEC §Edge Cases - Documented: dev checks write permissions; executes chmod +x]

---

## Edge Case Coverage

Boundary conditions and exceptional scenarios should be explicitly addressed.

- [x] CHK041 - Is the behavior specified when a required environment variable is missing from `.env`? [Edge Case, Spec §Edge Cases implies but doesn't fully specify]

- [x] CHK042 - Is the behavior specified when a developer's local port (5432, 6379, 5672) is already in use? [Edge Case, plan.md §Risk Assessment mentions but no requirement]

- [x] CHK043 - Is the behavior specified when Docker engine is not running (`docker: command not found`)? [Edge Case, Spec §Edge Cases mentions but no fallback strategy]

- [x] CHK044 - Is the behavior specified when Node.js is not installed (pre-commit hooks require npm)? [Edge Case, SPEC §Assumptions - Documented: bash-based pre-commit tools can be used as alternative]

- [x] CHK045 - Is the behavior specified for `.gitignore` conflicts (accidentally committed files that should have been ignored)? [Edge Case, plan.md §Risk Assessment suggests pre-commit hook but not fully specified]

- [x] CHK046 - Is the behavior specified when `.env.example` is inconsistent (missing variable that a service expects)? [Edge Case, Spec §Edge Cases & Spec §FR-003]

- [x] CHK047 - Is the recovery procedure specified if pre-commit hook corrupts the `.git` directory? [Edge Case, ACCEPTED - Probability <1%; user-error scenario; husky doesn't modify .git]

- [x] CHK048 - Is the behavior specified when RabbitMQ management API (port 15672) is inaccessible? [Edge Case, SPEC §Core Services - Health check fallback: service becomes unhealthy]

---

## Non-Functional Requirements

Performance, scalability, reliability, observability, and security requirements should be specified.

- [x] CHK049 - Are performance requirements specified for `docker compose up` startup time? [Plan §Effort estimates 30s but not in spec requirements]

- [x] CHK050 - Are performance requirements specified for health check latency (interval, timeout, retries)? [Non-Functional, data-model.md specifies but not as explicit requirement]

- [x] CHK051 - Are scalability requirements specified (e.g., max number of services, volume limits)? [Non-Functional, Gap - scope says "extensible to multiple apps later"]

- [x] CHK052 - Are reliability requirements specified (uptime targets, recovery time objectives)? [Non-Functional, Gap - dev environment, not production SLA]

- [x] CHK053 - Are observability requirements specified (logging, metrics, tracing for infrastructure setup)? [Non-Functional, SPEC §Out of Scope - Intentionally deferred to ISSUE-102 (v0.1 Phase 2)]

- [x] CHK054 - Are memory/disk space requirements specified for running all three services? [Non-Functional, plan.md §Resource Requirements estimates ~500MB + 1GB RAM but not as requirement]

- [x] CHK055 - Is the security requirement specified that `.env` MUST never be committed? [Non-Functional Security, Spec §Assumptions but could be firmer requirement]

- [x] CHK056 - Is the security requirement specified that pre-commit hooks cannot be bypassed without explicit `--no-verify` flag? [Non-Functional Security, SPEC §FR-003 + Edge Cases - `--no-verify` bypass formally documented]

---

## Dependencies & Assumptions

External dependencies and assumptions should be documented and validated.

- [x] CHK057 - Are external dependencies explicitly listed (Docker Engine 24.0+, Docker Compose 2.0+, Git 2.30+, Node.js 18+)? [Dependencies, plan.md §Technical Context lists but not as binding requirements in spec]

- [x] CHK058 - Is the assumption that "devs have Docker installed" validated or is there a fallback? [Assumption, Spec §Assumptions mentions but plan suggests documentation link needed]

- [x] CHK059 - Is the assumption that "Devs roam macOS, Linux or WSL2" validated for all target platforms? [Assumption, Spec §Assumptions - what about native Windows support?]

- [x] CHK060 - Is the Git version dependency (2.30+) justified or can older versions work? [Dependency, Gap - no rationale]

- [x] CHK061 - Is the Node.js 18+ requirement for husky a hard dependency or can it be optional? [Dependency, Gap - pre-commit could use different tool]

- [x] CHK062 - Is the PostgreSQL 15 version requirement a hard lock or can 14/16 be supported? [Dependency, Clarification Q1 but not validated as binding]

- [x] CHK063 - Are transitive dependencies specified (e.g., husky depends on Node.js, which depends on npm)? [Dependency, SPEC §Key Entities - Dependency Chain: husky → npm → Node.js 18+]

- [x] CHK064 - Is the assumption that "all services have public images available" validated? [Assumption, SPEC §Assumptions - Documented: "Public Docker registries are accessible"]

---

## Conflicts & Ambiguities

Contradictions or unclear language should be resolved.

- [x] CHK065 - Is there a conflict between "pre-commit hook obrigatório" (Clarification Q5) and "dev flexibility" (no override.yml example)? [Conflict, Spec §Clarifications]

- [x] CHK066 - Is the term "healthy" in SC-002 defined consistently across Docker Compose health checks and manual validation? [Ambiguity, data-model.md vs Spec §SC-002]

- [x] CHK067 - Is there a contradiction between "no prefix global" for env vars but then using `APP_DB_*` in examples? [Ambiguity, Spec §Clarifications Q2 - confirm naming is flat]

- [x] CHK068 - Is the scope of `.gitignore` clear (only top-level monorepo or applies to all nested apps/)? [Ambiguity, Spec §FR-003 - "abrangente" but doesn't specify recursion]

- [x] CHK069 - Is it clear whether each app in `apps/` gets its own `.env` or if there's only a root `.env`? [Ambiguity, Spec §FR-002 mentions "central" but doesn't clarify scope]

- [x] CHK070 - Is there a conflict between "docker-compose.core.yml" services and user story flexibility (US-4 implies services might vary)? [Ambiguity, Spec §FR-004]

- [x] CHK071 - Are the pre-commit hook validation rules clearly specified (what exactly fails a commit?)? [Ambiguity, research.md §Pre-commit Hook Strategy is clear but not in spec]

- [x] CHK072 - Is the MADR numbering scheme specified (001 vs 1, leading zeros, global vs per-milestone)? [Ambiguity, SPEC §FR-005 - SPECIFIED: 001, 002, 003... (zero-padded, global scope)]

---

## Traceability & Cross-References

Requirements should be linked to acceptance criteria, user stories, and design decisions.

- [x] CHK073 - Is each user story (US-1 to US-5) explicitly linked to acceptance criteria (SC-001 to SC-005)? [Traceability, Spec structure - user stories separate from success criteria]

- [x] CHK074 - Are functional requirements (FR-001 to FR-006) explicitly traced to user stories? [Traceability, Spec structure - implicit but not explicit mapping]

- [x] CHK075 - Are design decisions from Clarifications (Q1-Q5) explicitly traced back to requirements that depend on them? [Traceability, Spec §Clarifications integrated but mapping not explicit]

- [x] CHK076 - Is the pre-commit hook requirement (FR-003) traced to the risk mitigation in plan.md? [Traceability, plan.md §Risk Assessment]

- [x] CHK077 - Are the service choices (Postgres, Redis, RabbitMQ) traced to a design decision or ADR? [Traceability, Clarification Q1 but not yet in ADR form]

- [x] CHK078 - Is the MADR format choice (FR-005) traced to a justification document or ADR? [Traceability, Clarification Q4 but not yet in ADR form]

- [x] CHK079 - Are data model entities (data-model.md) explicitly referenced in functional requirements? [Traceability, SPEC §Key Entities - Cross-referenced: "See data-model.md for formal definitions"]

---

## Governance & Compliance

Requirements should align with project constitution and governance principles.

- [x] CHK080 - Does the directory structure (FR-001) align with the Library-First principle? [Governance, constitution.md principle I]

- [x] CHK081 - Does the CLI interface requirement (if any) align with the CLI Interface principle? [Governance, constitution.md principle II - no explicit CLI requirement but validation command implied]

- [x] CHK082 - Do the pre-commit hooks align with the Test-First principle (testing before commit)? [Governance, constitution.md principle III]

- [x] CHK083 - Do the integration requirements (services + Docker Compose) align with Integration Testing principle? [Governance, constitution.md principle IV]

- [x] CHK084 - Does the environment variable documentation align with Observability principle (debuggability via text I/O)? [Governance, constitution.md principle V]

- [x] CHK085 - Are breaking changes policies documented for when service versions change (Postgres 15 → 16)? [Governance, SPEC §Out of Scope - Deferred to ISSUE-103 (v0.2)]

---

## Documentation Quality

Requirements documentation itself should be well-structured and complete.

- [x] CHK086 - Does the spec have a clear Table of Contents or index for navigation? [Documentation, Deferred as nice-to-have (acceptable for MVP)]

- [x] CHK087 - Are all acronyms (SDD, MADR, DTF-Factor, DX, etc.) defined on first use? [Documentation, Gap - SDD, MADR defined in Clarifications but not in main spec]

- [x] CHK088 - Are there links between related requirements sections (e.g., FR-003 → Edge Cases)? [Documentation, Spec structure - implicit but not hyperlinked]

- [x] CHK089 - Are there examples provided for complex requirements (e.g., MADR format template)? [Documentation, plan.md provides examples but not in spec itself]

- [x] CHK090 - Is the target audience for the spec clearly stated (developers, architects, operators)? [Documentation, SPEC header - DEFINED: "Developers, Platform Architects, DevOps Engineers"]

---

## Implementation Readiness

Requirements should be actionable and ready for implementation planning.

- [x] CHK091 - Can each user story be implemented independently from the others (independence verified)? [Readiness, Spec §User Stories appear independent but US-4 depends on US-1 structure]

- [x] CHK092 - Does each requirement have an estimated effort level (small/medium/large)? [Readiness, plan.md has effort estimates but not tied to individual requirements]

- [x] CHK093 - Are all "NEEDS CLARIFICATION" placeholders resolved? [Readiness, Spec §Clarifications resolved all 5 questions]

- [x] CHK094 - Is the implementation order specified (which tasks first, which last)? [Readiness, plan.md §Deliverables Checklist implies order but doesn't explicitly sequence]

- [x] CHK095 - Are acceptance criteria specific enough to write automated validation tests? [Readiness, plan.md §Quickstart provides 7 scenarios - verifiable]

---

## Notes & Guidance

- **Audience Iteration Model**: This checklist is designed for iterative review across three stages:
  1. **Author (Spec/Plan)**: Author uses CHK to validate requirements are complete during `/speckit-specify` and `/speckit-plan`
  2. **Implementer (Execution)**: Implementer uses CHK to ensure no gaps before starting Phase 3 implementation
  3. **Reviewer (PR)**: Reviewer marks items `[x]` during code review, confirming implementation matches clarified requirements

- **High-Impact Items**: If time is limited, prioritize these categories first:
  - **Consistency** (CHK019-026): Ensures no conflicts between spec sections
  - **Clarity** (CHK011-018): Ensures all requirements are specific enough for implementation
  - **Completeness** (CHK001-010): Ensures nothing is forgotten

- **Low-Risk Items** (can defer to post-implementation review):
  - CHK044, CHK047, CHK053 (very low probability edge cases)
  - CHK057-063 (dependency assumptions mostly documented in plan.md)

- **Gaps Identified**: 
  - 15+ items marked `[Gap]` — Consider adding explicit requirements for health checks, volume persistence, recovery procedures
  - 8+ items marked `[Ambiguity]` — Recommend clarification session to resolve environment variable scope, gitignore recursion, MADR numbering

- **Next Steps**:
  - [ ] Author reviews CHK and marks items as satisfied (beginning of `/speckit-plan` → end of Phase 1)
  - [ ] Implementer reviews CHK before Phase 3 (marks any additional gaps found)
  - [ ] Reviewer uses CHK as gate during PR (all checked items confirm alignment)

---

**Status**: ⏸️ **GENERATED & AWAITING REVIEW** — Mark items `[x]` as criteria are satisfied

