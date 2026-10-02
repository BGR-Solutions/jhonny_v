# Gap Resolution Plan: ISSUE-101 Checklist to 100%

**Objective**: Resolve all 20 unchecked items to achieve 95/95 (100%) validation coverage

**Date**: 2026-10-01

---

## 📋 Mapeamento dos 20 Itens Pendentes

### GRUPO 1: HIGH-PRIORITY GAPS (5 items) — MUST-FIX

#### CHK006 - Fallback para Docker não instalado
**Current Status**: Edge case mencionado mas sem requirement formal  
**Issue**: Spec §Edge Cases menciona "Documentação deve indicar alternativas" mas não há requisito explícito  
**Fix Strategy**: 
- Adicionar a FR-006 (ou criar FR-006a): "Sistema DEVE incluir documentação com procedimento quando Docker não está instalado"
- Adicionar seção em Edge Cases com procedimento específico
- Adicionar scenario em quickstart.md

**Artifact to Update**: ISSUE-101.SPEC.md, research.md, quickstart.md  
**Effort**: 15 min

---

#### CHK014 - Especificar padrões exatos de .gitignore
**Current Status**: Apenas categorias listadas ("Node.js, Python, Docker, IDEs")  
**Issue**: FR-003 não detalha patterns exatos (e.g., `__pycache__/` vs `__pycache__`)  
**Fix Strategy**:
- Estender FR-003 com tabela de patterns exatos
- Adicionar exemplos em data-model.md §Validation Rules
- Criar exemplo `.gitignore` concreto em research.md

**Artifact to Update**: ISSUE-101.SPEC.md (FR-003), research.md, data-model.md  
**Effort**: 20 min

---

#### CHK056 - Segurança: `--no-verify` como escape hatch
**Current Status**: research.md menciona mas não é requirement formal  
**Issue**: FR-003 (pre-commit obrigatório) precisa documentar bypass seguro  
**Fix Strategy**:
- Adicionar a FR-003 nota: "Pre-commit hooks podem ser desativados com `git commit --no-verify` em emergências (deve ser documentado em .husky/README.md)"
- Adicionar a Edge Cases scenario
- Adicionar a quickstart.md Troubleshooting

**Artifact to Update**: ISSUE-101.SPEC.md (FR-003), research.md, quickstart.md  
**Effort**: 10 min

---

#### CHK072 - MADR numbering scheme
**Current Status**: Não especificado (001 vs 1, global vs per-milestone)  
**Issue**: FR-005 menciona MADR mas não define numeração  
**Fix Strategy**:
- Estender FR-005: "ADR numbering: 001, 002, 003... (zero-padded 3-digit, global scope, independent of milestones)"
- Adicionar exemplos em data-model.md §ADR entity
- Criar template exemplo em research.md

**Artifact to Update**: ISSUE-101.SPEC.md (FR-005), research.md, data-model.md  
**Effort**: 15 min

---

#### CHK037 - Docker Compose scale scenario
**Current Status**: Não mencionado em lugar nenhum  
**Issue**: Scenario de "rodar múltiplos containers" não coberto  
**Fix Strategy**:
- NÃO implementar como requirement para v0.1
- APENAS adicionar a Assumptions clarificação: "v0.1 MVP assume single-instance containers; multi-instance orchestration (Kubernetes, Swarm) deferred to v0.2+"
- Adicionar nota em plan.md §Scope

**Artifact to Update**: ISSUE-101.SPEC.md (Assumptions), plan.md  
**Effort**: 5 min

---

### GRUPO 2: MEDIUM-PRIORITY GAPS (9 items) — DOCUMENT CLEARLY

#### CHK015 - "Safe defaults" rules — clarificar
**Current Status**: Vago: "valores defaults seguros"  
**Fix Strategy**:
- Adicionar regra específica: "Safe defaults = values that work in dev environment without exposing secrets (e.g., `DB_PASSWORD=postgres` for local dev, NOT production passwords)"
- Adicionar exemplo em .env.example template na research.md
- Adicionar constraint em data-model.md

**Artifact to Update**: ISSUE-101.SPEC.md (FR-002 constraint), research.md, data-model.md  
**Effort**: 10 min

---

#### CHK038 - Hook bypass scenario
**Current Status**: research.md menciona `--no-verify` mas não como requirement  
**Fix Strategy**:
- Integrar com CHK056 (mesma resolução)
- Confirmar como feature documentada (não bug)

**Artifact to Update**: Integrado em CHK056  
**Effort**: 0 min (covered by CHK056)

---

#### CHK039 - Partial failure scenario (1 de 3 services)
**Current Status**: Success Criteria assume "todos healthy"  
**Fix Strategy**:
- NÃO adicionar como requirement obrigatório para v0.1
- Adicionar edge case em quickstart.md Troubleshooting: "Se um serviço falha, docker-compose exit com código erro; dev deve verificar logs via `docker logs <service>`"
- Adicionar a plan.md §Risk Assessment

**Artifact to Update**: quickstart.md, plan.md  
**Effort**: 10 min

---

#### CHK040 - OSError/permission denied scenario
**Current Status**: Não endereçado  
**Fix Strategy**:
- Adicionar a Edge Cases em Spec: "Se .husky criação falha (permission denied), dev deve verificar permissões de escrita na pasta raiz e executar `chmod +x .husky/pre-commit`"
- Adicionar a quickstart.md Troubleshooting

**Artifact to Update**: ISSUE-101.SPEC.md (Edge Cases), quickstart.md  
**Effort**: 10 min

---

#### CHK044 - Node.js não instalado
**Current Status**: Não endereçado (husky requer Node.js)  
**Fix Strategy**:
- Adicionar a Dependencies em Spec: "Node.js 18+ required for husky pre-commit hooks; if not available, dev can skip hook setup (document in .husky/README.md)"
- Adicionar alternative em plan.md §Resource Requirements

**Artifact to Update**: ISSUE-101.SPEC.md (Assumptions ou FR-003), plan.md  
**Effort**: 10 min

---

#### CHK053 - Observability requirements (logging, metrics, tracing)
**Current Status**: Explicitamente deferred ("Gap - deferred to v0.1 observability phase")  
**Fix Strategy**:
- FORMALIZAR como "Out of Scope para ISSUE-101" em Spec
- Adicionar nota: "Observability (logging, metrics, tracing) is explicitly deferred to ISSUE-102 (v0.1 - Infra Core & Observability Phase 2)"
- Marcar como "Intentional Deferral" (não gap)

**Artifact to Update**: ISSUE-101.SPEC.md (Out of Scope section), plan.md  
**Effort**: 5 min

---

#### CHK063 - Transitive dependencies (husky → npm → Node.js)
**Current Status**: Implícito mas não explícito  
**Fix Strategy**:
- Adicionar a data-model.md §Dependencies: "Dependency Chain: husky (npm package) → npm (package manager) → Node.js 18+ (runtime)"
- Referência em plan.md

**Artifact to Update**: data-model.md, plan.md  
**Effort**: 10 min

---

#### CHK079 - Data model entities referenced in FRs
**Current Status**: Entities definidas em data-model.md mas não em Spec §Requirements  
**Fix Strategy**:
- Adicionar referência: "Vide data-model.md para definições formais de entities (Environment, Service, ADR, Documentation, Directory Structure)"
- Adicionar link cruzado em Spec

**Artifact to Update**: ISSUE-101.SPEC.md (Requirements section), data-model.md  
**Effort**: 5 min

---

#### CHK085 - Breaking changes policies (versioning)
**Current Status**: Não documentado  
**Fix Strategy**:
- NÃO implementar para v0.1
- Adicionar Assumptions: "Version upgrades (e.g., PostgreSQL 15 → 16) are OUT OF SCOPE for v0.1; versioning policy deferred to ISSUE-103 (v0.2 Upgrade Management)"
- Nota em plan.md

**Artifact to Update**: ISSUE-101.SPEC.md (Assumptions), plan.md  
**Effort**: 5 min

---

### GRUPO 3: LOW-PRIORITY GAPS (6 items) — DOCUMENT OR ACCEPT AS-IS

#### CHK042 - Port conflict behavior
**Current Status**: plan.md Risk Assessment menciona; quickstart.md tem troubleshooting  
**Status**: ✅ JÁ COBERTO (marcar como checked)  
**Ação**: Apenas confirmar que está em quickstart.md Troubleshooting

---

#### CHK047 - Pre-commit hook corrupts .git
**Current Status**: Extremely unlikely edge case  
**Decision**: ACCEPT AS-IS (não implementar)  
**Rationale**: Probability << 1%; husky não modifica .git diretamente; user error seria causa raiz  
**Ação**: Marcar como intentional non-requirement

---

#### CHK048 - RabbitMQ management API inaccessible
**Current Status**: Health check fallback existe  
**Decision**: COVERED BY HEALTH CHECKS (marcar como checked)  
**Rationale**: Se API (port 15672) está down, health check falha e serviço fica "unhealthy"  
**Ação**: Adicionar nota em quickstart.md Troubleshooting

---

#### CHK064 - Public image availability (registry down)
**Current Status**: Standard Docker assumption  
**Decision**: ACCEPT AS-IS  
**Rationale**: MVP assumes standard Docker Hub access; offline scenarios out of scope  
**Ação**: Adicionar Assumption: "Public Docker registries (Docker Hub, etc.) are accessible"

---

#### CHK086 - Table of Contents in spec
**Current Status**: Nicety; não crítico  
**Decision**: DEFER to Phase 3 (implementer can add)  
**Ação**: Adicionar como "nice-to-have" em plan.md

---

#### CHK090 - Target audience stated
**Current Status**: Implícito (developers + architects)  
**Decision**: FORMALIZE em Spec intro  
**Ação**: Adicionar ao início de ISSUE-101.SPEC.md: "**Target Audience**: Developers, Platform Architects, DevOps Engineers"

---

## 🎯 Plano de Execução

### Fase 1: Atualizar ISSUE-101.SPEC.md (10-15 min)

**Edits**:
1. Reforçar FR-002 com "safe defaults" definition
2. Expand FR-003 com `.gitignore` patterns table + `--no-verify` documentation
3. Expand FR-005 com "MADR numbering: 001, 002, 003..."
4. Adicionar FR-006a: Docker not installed fallback requirement
5. Adicionar Out of Scope section: "Observability (deferred to ISSUE-102), Versioning (ISSUE-103), Multi-instance (v0.2+)"
6. Adicionar Assumptions: "Registry accessible", "Node.js alternative for pre-commit"
7. Expand Edge Cases: OSError permission denied, partial failure, hook bypass
8. Adicionar Target Audience statement

---

### Fase 2: Atualizar research.md (5-10 min)

**Additions**:
1. Add section: "7. .gitignore Patterns Detail"
2. Add section: "8. Pre-commit Hook Bypass Strategy"
3. Add section: "9. Partial Failure Handling"
4. Expand MADR template com numbering scheme

---

### Fase 3: Atualizar data-model.md (5 min)

**Additions**:
1. Expand Environment Variables constraints: "safe defaults" definition
2. Expand ADR entity: numbering scheme (001, 002, ...)
3. Add Dependencies Chain section
4. Cross-reference quickstart.md scenarios

---

### Fase 4: Atualizar quickstart.md (10 min)

**Additions**:
1. Expand Scenario 3 (.gitignore) com patterns exatos
2. Adicionar "Scenario 8: Partial Service Failure"
3. Expand Troubleshooting: "Port already in use", "Permission denied", "Node.js missing", "RabbitMQ API down"
4. Adicionar "Scenario 9: Pre-commit Hook Bypass"

---

### Fase 5: Atualizar plan.md (5 min)

**Additions**:
1. Adicionar "Out of Scope" section
2. Expand Assumptions com new items
3. Update Risk Assessment com new scenarios

---

### Fase 6: Validar e marcar 95/95 items ✅ (5 min)

**Final checklist validation**

---

## 📊 Summary

**Total Effort**: ~60 minutes  
**Result**: 95/95 items checked (100%)  
**Artifacts Updated**: 5 (spec, research, data-model, quickstart, plan)  
**New Requirements Added**: 2 (FR-006a Docker fallback, CHK056 --no-verify)  
**New Sections Added**: 3 (Out of Scope, Safe Defaults definition, Dependency Chain)  

---

## ✅ Sucesso Esperado

- [x] Todos os 20 itens pendentes resolvidos
- [x] Spec completo e sem ambiguidades
- [x] 100% traceability entre requirements, plan, research
- [x] Pronto para Phase 2 (/speckit-tasks)

