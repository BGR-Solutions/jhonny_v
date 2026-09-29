# Tasks: Configuração do LiteLLM Proxy e Roteamento de Modelos

**Input**: Design documents from `/specs/002-litellm-proxy-roteamento/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Testes automatizados não foram explicitamente solicitados na especificação; a validação desta feature será por cenários operacionais e chamadas HTTP de aceite.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Infraestrutura: `infra/compose.yaml` + overlays `infra/compose.*.yaml`
- Configuração LiteLLM: `infra/litellm/config.yaml`
- Variáveis de ambiente: `.env.example`
- Validação documental: `specs/002-litellm-proxy-roteamento/quickstart.md`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preparar base de arquivos e pontos de integração para a stack LiteLLM.

- [ ] T001 Criar diretório de configuração do proxy em `infra/litellm/`
- [ ] T002 Criar arquivo base de configuração em `infra/litellm/config.yaml`
- [ ] T003 Criar overlay de infraestrutura LLM em `infra/compose.llm.yaml`
- [ ] T004 Atualizar contrato de variáveis em `.env.example` com campos necessários para chave mestre do proxy e credenciais opcionais cloud

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Definir contratos compartilhados que bloqueiam todas as histórias de usuário.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Definir serviço `litellm` em `infra/compose.llm.yaml` com integração à rede compartilhada e fonte de configuração versionada
- [ ] T006 Definir política de inicialização do serviço `litellm` em `infra/compose.llm.yaml` para execução local estável
- [ ] T007 Definir estrutura de roteamento inicial em `infra/litellm/config.yaml` (aliases, provedores e destinos)
- [ ] T008 Definir política de autenticação por chave mestre no `infra/litellm/config.yaml` para todos os endpoints do proxy
- [ ] T009 Validar consistência entre `infra/compose.yaml` e `infra/compose.llm.yaml` quanto a convenções de nomes, rede e variáveis
- [ ] T010 Validar sintaxe consolidada do Compose para stack LLM com `docker compose -f infra/compose.yaml -f infra/compose.llm.yaml config`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Disponibilizar o proxy de modelos no ambiente local (Priority: P1) 🎯 MVP

**Goal**: Subir o LiteLLM no ambiente local e expor listagem de modelos via endpoint do proxy.

**Independent Test**: Com a stack LLM em execução, chamada autenticada a `GET /v1/models` retorna sucesso e lista de modelos configurados.

### Implementation for User Story 1

- [ ] T011 [US1] Declarar mapeamento de porta e endpoint do proxy em `infra/compose.llm.yaml` para acesso local em `localhost:4000`
- [ ] T012 [US1] Registrar rotas de modelos locais no `infra/litellm/config.yaml`
- [ ] T013 [US1] Garantir montagem/leitura do arquivo `infra/litellm/config.yaml` pelo serviço `litellm` em `infra/compose.llm.yaml`
- [ ] T014 [US1] Validar subida do serviço e disponibilidade básica com `docker compose -f infra/compose.yaml -f infra/compose.llm.yaml up -d`
- [ ] T015 [US1] Validar aceite do endpoint `GET /v1/models` conforme cenário descrito em `specs/002-litellm-proxy-roteamento/quickstart.md`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Consumir modelos sem alterar código da aplicação (Priority: P2)

**Goal**: Permitir seleção de rotas local/cloud por configuração do proxy sem mudanças no código consumidor.

**Independent Test**: Chamadas autenticadas em `POST /v1/chat/completions` funcionam para rota local e respeitam comportamento de rota cloud sem credencial.

### Implementation for User Story 2

- [ ] T016 [US2] Definir rotas cloud (OpenAI e Anthropic) no `infra/litellm/config.yaml` com aliases explícitos
- [ ] T017 [US2] Configurar referências de credenciais cloud por variável de ambiente no `infra/litellm/config.yaml`
- [ ] T018 [US2] Implementar política de indisponibilidade de rota cloud sem credencial (retorno `503`) no `infra/litellm/config.yaml`
- [ ] T019 [US2] Garantir distinção de semântica entre rota inexistente e rota indisponível no `infra/litellm/config.yaml`
- [ ] T020 [US2] Validar cenário de chat em rota local com `POST /v1/chat/completions` conforme `specs/002-litellm-proxy-roteamento/quickstart.md`
- [ ] T021 [US2] Validar cenário de rota cloud sem credencial e retorno `503` conforme `specs/002-litellm-proxy-roteamento/quickstart.md`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Proteger acesso ao proxy por chave mestre (Priority: P3)

**Goal**: Assegurar autenticação obrigatória em endpoints de modelos e chat com comportamento consistente de negação.

**Independent Test**: Sem chave válida, chamadas para `/v1/models` e `/v1/chat/completions` são negadas; com chave válida, fluxos autorizados funcionam.

### Implementation for User Story 3

- [ ] T022 [US3] Definir variável de chave mestre e documentação de uso em `.env.example`
- [ ] T023 [US3] Configurar injeção da chave mestre no serviço `litellm` em `infra/compose.llm.yaml`
- [ ] T024 [US3] Reforçar política de autenticação obrigatória para `/v1/models` e `/v1/chat/completions` no `infra/litellm/config.yaml`
- [ ] T025 [US3] Validar cenários de acesso negado com chave ausente/inválida conforme `specs/002-litellm-proxy-roteamento/quickstart.md`
- [ ] T026 [US3] Validar cenários de acesso autorizado com chave válida conforme `specs/002-litellm-proxy-roteamento/quickstart.md`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Consolidar qualidade operacional, documentação e validação final da feature.

- [ ] T027 [P] Revisar consistência entre `specs/002-litellm-proxy-roteamento/spec.md`, `specs/002-litellm-proxy-roteamento/contracts/litellm-proxy-contract.md` e configurações em `infra/`
- [ ] T028 Atualizar `specs/002-litellm-proxy-roteamento/quickstart.md` se os comandos finais de validação divergirem do executado
- [ ] T029 Executar checklist de validação manual final da feature em `specs/002-litellm-proxy-roteamento/quickstart.md`
- [ ] T030 [P] Validar que nenhum segredo real foi versionado em `.env.example` e `infra/litellm/config.yaml`
- [ ] T031 Executar validação temporal de startup/listagem em `specs/002-litellm-proxy-roteamento/quickstart.md` para comprovar janela de 10 inicializações e limite de 30 segundos
- [ ] T032 Adicionar cenário de edge case no `specs/002-litellm-proxy-roteamento/quickstart.md` para rota inexistente com erro distinto de `503`
- [ ] T033 Adicionar cenário de edge case no `specs/002-litellm-proxy-roteamento/quickstart.md` para rota cloud sem credencial com retorno `503`
- [ ] T034 Adicionar cenário de edge case no `specs/002-litellm-proxy-roteamento/quickstart.md` para chave mestre ausente/inválida em endpoints protegidos
- [ ] T035 Adicionar cenário de edge case no `specs/002-litellm-proxy-roteamento/quickstart.md` para falha runtime em rota cloud sem fallback automático
- [ ] T036 Adicionar cenário de edge case no `specs/002-litellm-proxy-roteamento/quickstart.md` para indisponibilidade de provedor mantendo erro da rota alvo

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - no dependency on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - depends conceitualmente em rotas e endpoint do proxy já disponíveis
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - valida controle de acesso em endpoints já definidos

### Within Each User Story

- Estrutura/configuração de rota antes da validação operacional
- Configuração de autenticação antes de testes de negação/autorização
- Critérios de aceite validados com os cenários independentes da história

### Parallel Opportunities

- **Polish**: T027 e T030 em paralelo

---

## Parallel Example: User Story 2

```bash
# US2 usa o mesmo arquivo de configuração e deve seguir execução sequencial
Task: "Definir rotas cloud (OpenAI e Anthropic) no infra/litellm/config.yaml"
Task: "Após concluir a task anterior, configurar referências de credenciais cloud por variável de ambiente no infra/litellm/config.yaml"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Confirmar `GET /v1/models` com autenticação

### Incremental Delivery

1. Setup + Foundational
2. Entregar US1 (proxy local e listagem)
3. Entregar US2 (roteamento híbrido e semântica de indisponibilidade)
4. Entregar US3 (hardening de autenticação)
5. Consolidar Polish

### Parallel Team Strategy

1. Time A: Compose/infra (`infra/compose.llm.yaml`)
2. Time B: Configuração de rotas (`infra/litellm/config.yaml`) com execução sequencial interna no mesmo arquivo
3. Time C: Validação e documentação (`specs/002-litellm-proxy-roteamento/quickstart.md`)
4. Integrar resultados por fase e checkpoints independentes

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at checkpoints to validate story independently
- Avoid same-file conflicts during parallel execution
