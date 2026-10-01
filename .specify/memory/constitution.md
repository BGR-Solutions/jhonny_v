# Jhonny-V Constitution

## Core Principles

### I. Monorepo Architecture Consistency (MUST)
- O projeto MUST ser tratado como monorepo com separação clara entre `apps/`, `libs/` e `infra/`.
- Cada app MUST ter responsabilidade explícita e limites claros de dependência.
- Serviços de infraestrutura locais e externos MUST ser declarados explicitamente por ambiente.

### II. Observability and Logging (MUST)
- Aplicações MUST enviar logs para `stdout`/`stderr` em JSON estruturado.
- Logs em arquivos locais são PROIBIDOS.
- Telemetria distribuída MUST manter `trace_id` e `span_id` propagados.

### III. Python Packaging and App Structure (MUST)
- `requirements.txt` é PROIBIDO; dependências MUST ser geridas por `pyproject.toml`.
- Apps Python em `apps/` MUST separar código em `src/` e testes em `tests/`.
- Ferramental de qualidade MUST incluir lint/format/tipagem e testes automatizados quando aplicável.

### IV. Compose and Infrastructure Contracts (MUST)
- Compose MUST usar convenção `compose.yaml` e `compose.override.yaml` (ou overlays `compose.*.yaml` em `infra/`).
- Definições de serviço MUST explicitar `build`/`image`, `env_file`, `volumes`, `network`, `depends_on` e políticas de restart conforme necessário.
- Segredos MUST permanecer fora do versionamento e ser fornecidos por `.env`/secret manager.

### V. Security and Operational Safety (MUST)
- Credenciais e dados sensíveis NEVER podem ser hardcoded no repositório.
- Acesso a serviços MUST usar autenticação forte e controles explícitos.
- Alterações MUST preservar documentação operacional e rastreabilidade das decisões.

## Workflow Governance

- Fluxo SDD MUST seguir ordem: `specify` → `clarify` → `plan` → `checklist` → `tasks` → `analyze` → `implement`.
- Nenhuma implementação deve começar antes dos artefatos de planejamento estarem aprovados.
- Conflitos com esta constituição são CRÍTICOS e devem ser corrigidos em spec/plan/tasks antes de implementação.

## Compliance Notes

- Esta constituição está alinhada às diretrizes operacionais atuais do projeto em `.github/copilot-instructions.md`.
- Em caso de divergência futura, a atualização da constituição deve ocorrer explicitamente com versionamento e revisão.

**Version**: 1.0.0 | **Ratified**: 2026-09-29 | **Last Amended**: 2026-09-29
