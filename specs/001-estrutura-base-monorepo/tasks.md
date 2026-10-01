# Tasks: Estrutura Base do Monorepo e Documentação Inicial

**Input**: Design documents from `/specs/001-estrutura-base-monorepo/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Não há exigência explícita de TDD na specification. A validação desta feature será feita pelos fluxos manuais descritos em `specs/001-estrutura-base-monorepo/quickstart.md`.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Criar os artefatos-base que destravam a implementação das histórias sem ainda detalhar todo o comportamento final.

- [X] T001 Create application-area placeholders in `apps/README.md`, `apps/mcp-server/README.md`, `apps/agent-orchestrator/README.md`, and `apps/worker/README.md`
- [X] T002 [P] Create infrastructure bootstrap files in `infra/compose.yaml` and `infra/compose.core.yaml`
- [X] T003 [P] Create the shared environment template scaffold in `.env.example`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Definir contratos e padrões compartilhados que MUST estar prontos antes de qualquer user story.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Expand local-artifact coverage for Python, Node.js, and Docker state in `.gitignore`
- [X] T005 Define shared Compose metadata, networks, volumes, and extension anchors in `infra/compose.yaml`
- [X] T006 Align variable names, placeholder defaults, and service comments across `.env.example`, `infra/compose.yaml`, and `infra/compose.core.yaml`

**Checkpoint**: Foundation ready - user story implementation can now begin in priority order

---

## Phase 3: User Story 1 - Estruturar a base do repositório (Priority: P1) 🎯 MVP

**Goal**: Entregar uma estrutura inicial previsível do monorepo, com áreas de aplicações e infraestrutura descobertas facilmente a partir da raiz do repositório.

**Independent Test**: Em um clone limpo, um colaborador consegue abrir `README.md`, localizar `apps/`, `infra/` e `docs/`, identificar os placeholders das aplicações futuras e confirmar pelo `git status --short` que os artefatos locais esperados permanecem ignorados.

### Implementation for User Story 1

- [X] T007 [US1] Transform the repository map and onboarding summary in `README.md` to explain `apps/`, `infra/`, and `docs/`
- [X] T008 [P] [US1] Add purpose statements for the monorepo areas in `apps/README.md`, `apps/mcp-server/README.md`, `apps/agent-orchestrator/README.md`, and `apps/worker/README.md`
- [X] T009 [US1] Finalize structure-tracking and local-artifact guidance in `.gitignore` and `README.md`
- [X] T010 [US1] Verify structural discoverability for `README.md`, `apps/`, `infra/`, and `.gitignore` using the `git status --short` flow described in `specs/001-estrutura-base-monorepo/quickstart.md`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Entender a organização do projeto pela documentação (Priority: P2)

**Goal**: Tornar a documentação inicial renderizável e navegável, conectando a landing page do repositório ao hub documental e aos índices especializados.

**Independent Test**: Um colaborador novo consegue começar em `README.md`, navegar para `docs/README.md` e alcançar `docs/adr/README.md`, `docs/issues/README.md` e `docs/milestones/README.md` sem links quebrados nem ambiguidade sobre a finalidade de cada área.

### Implementation for User Story 2

- [X] T011 [US2] Expand the main onboarding narrative and quickstart sections in `README.md`
- [X] T012 [P] [US2] Update the documentation hub cross-links in `docs/README.md` to reflect the root README and the monorepo structure
- [X] T013 [P] [US2] Normalize introductory copy in `docs/adr/README.md`, `docs/issues/README.md`, and `docs/milestones/README.md` for first-time navigation clarity
- [X] T014 [US2] Validate rendered navigation paths across `README.md` and `docs/README.md` against the expected destinations in `docs/adr/README.md`, `docs/issues/README.md`, and `docs/milestones/README.md`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Preparar a execução local dos serviços centrais (Priority: P3)

**Goal**: Entregar o contrato inicial de ambiente local e a composição em camadas necessária para subir os serviços core compartilhados do monorepo.

**Independent Test**: A equipe consegue copiar `.env.example` para `.env`, executar `docker compose -f infra/compose.yaml -f infra/compose.core.yaml config` e subir a stack core definida sem arquivos adicionais fora do contrato documentado.

### Implementation for User Story 3

- [X] T015 [US3] Populate grouped bootstrap, core-service, observability, and future-integration variables in `.env.example`
- [X] T016 [US3] Implement the base Compose layer for shared project defaults in `infra/compose.yaml`
- [X] T017 [US3] Implement the core database, cache, and messaging service definitions in `infra/compose.core.yaml`
- [X] T018 [US3] Validate the local-stack contract for `.env.example`, `infra/compose.yaml`, and `infra/compose.core.yaml` using the configuration and startup flows in `specs/001-estrutura-base-monorepo/quickstart.md`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Reconciliar documentação, comandos e validações finais antes de concluir a issue.

- [X] T019 [P] Reconcile final command examples and file locations across `README.md`, `docs/README.md`, and `specs/001-estrutura-base-monorepo/quickstart.md`
- [X] T020 Run the final acceptance pass across `.env.example`, `.gitignore`, `README.md`, `infra/compose.yaml`, and `infra/compose.core.yaml`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion
- **User Story 2 (Phase 4)**: Depends on User Story 1 because the navigation copy must describe the final root structure accurately
- **User Story 3 (Phase 5)**: Depends on Foundational completion and can be finalized after User Story 1 establishes the repository structure
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - no dependency on other stories
- **User Story 2 (P2)**: Depends on User Story 1 for the final repository map and top-level navigation entry points
- **User Story 3 (P3)**: Depends on Foundational (Phase 2) and should be reconciled with the repository map from User Story 1 before final validation

### Parallel Opportunities

- `T002` and `T003` can run in parallel after `T001`
- `T004` and `T005` can run in parallel once Phase 1 is complete
- `T008` can run in parallel with `T007` after the root README structure is outlined
- `T012` and `T013` can run in parallel during User Story 2
- `T016` and `T017` should proceed sequentially, but `T015` can start in parallel with `T016`
- `T019` can run in parallel with the final acceptance review in `T020` once all story work is complete

---

## Parallel Example: User Story 1

```bash
Task: "Transform the repository map and onboarding summary in README.md to explain apps/, infra/, and docs/"
Task: "Add purpose statements for the monorepo areas in apps/README.md, apps/mcp-server/README.md, apps/agent-orchestrator/README.md, and apps/worker/README.md"
```

## Parallel Example: User Story 2

```bash
Task: "Update the documentation hub cross-links in docs/README.md to reflect the root README and the monorepo structure"
Task: "Normalize introductory copy in docs/adr/README.md, docs/issues/README.md, and docs/milestones/README.md for first-time navigation clarity"
```

## Parallel Example: User Story 3

```bash
Task: "Populate grouped bootstrap, core-service, observability, and future-integration variables in .env.example"
Task: "Implement the base Compose layer for shared project defaults in infra/compose.yaml"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Confirm the root structure and ignore behavior via the `git status --short` flow in `specs/001-estrutura-base-monorepo/quickstart.md`

### Incremental Delivery

1. Complete Setup + Foundational → foundation ready
2. Add User Story 1 → validate repository structure and onboarding map
3. Add User Story 2 → validate rendered documentation navigation
4. Add User Story 3 → validate local stack contract and Compose startup flow
5. Finish with Polish → reconcile commands and acceptance checks

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 root-structure and placeholder files
   - Developer B: User Story 2 documentation hub and section indexes (after US1 map is stable)
   - Developer C: User Story 3 environment template and Compose layers
3. Rejoin for final reconciliation and acceptance validation

---

## Notes

- Todos os itens seguem o formato obrigatório `- [X] Txxx ...` com caminhos explícitos
- Nenhuma tarefa de teste automatizado foi gerada porque a specification não exige TDD ou suíte nova nesta etapa
- As validações operacionais reutilizam `specs/001-estrutura-base-monorepo/quickstart.md`
- A entrega incremental recomendada para MVP é encerrar após a conclusão da User Story 1
