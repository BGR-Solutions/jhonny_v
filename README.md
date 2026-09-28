# jhonny_v

`jhonny_v` é um monorepo em construção para a stack do ecossistema **jhonny-v**, reunindo aplicações, infraestrutura compartilhada e documentação técnica em uma única base versionada.

## Visão geral do monorepo

A estrutura inicial do repositório foi organizada para tornar o onboarding previsível e preparar as próximas milestones do projeto.

```text
.
├── apps/      # Aplicações do ecossistema (MCP Server, Agent Orchestrator, Worker)
├── infra/     # Orquestração local, serviços core e artefatos operacionais compartilhados
├── docs/      # ADRs, rastreamento de issues e roadmap de milestones
└── specs/     # Artefatos do fluxo Spec-Driven Development (SDD)
```

## Áreas principais

### `apps/`
Contém os espaços reservados para as aplicações do ecossistema. Cada subdiretório representa uma frente evolutiva do roadmap e documenta sua finalidade antes da implementação completa.

### `infra/`
Centraliza a configuração operacional compartilhada do ambiente local. É a área responsável pelos arquivos Compose base, serviços core e contratos de execução reutilizados pelas aplicações.

### `docs/`
É o hub documental do projeto, com navegação para ADRs, backlog técnico e milestones arquiteturais. Use esta área como ponto de referência para entender decisões, roadmap e rastreabilidade.

### `specs/`
Armazena as especificações, planos, tarefas e demais artefatos produzidos pelo fluxo obrigatório de Spec-Driven Development.

## Estrutura de aplicações planejadas

- [`apps/mcp-server/`](./apps/mcp-server/README.md): base do servidor MCP e das skills do projeto
- [`apps/agent-orchestrator/`](./apps/agent-orchestrator/README.md): espaço reservado ao motor de orquestração e decisão
- [`apps/worker/`](./apps/worker/README.md): base para processamento assíncrono e tarefas em background

## Quickstart do ambiente local

1. Copie o contrato de ambiente compartilhado:
   ```bash
   cp .env.example .env
   ```
2. Revise os valores locais necessários em `.env`.
3. Valide a composição consolidada:
   ```bash
   docker compose -f infra/compose.yml -f infra/compose.core.yml config
   ```
4. Inicie os serviços core:
   ```bash
   docker compose -f infra/compose.yml -f infra/compose.core.yml up -d
   ```

## Navegação da documentação

- [Hub de documentação](./docs/README.md)
- [ADRs](./docs/adr/README.md)
- [Issues e tarefas](./docs/issues/README.md)
- [Milestones](./docs/milestones/README.md)

## Roadmap atual

A entrega inicial prioriza a milestone **v0.1 — Infra Core & Observabilidade**, preparando a base para infraestrutura, observabilidade e futuras aplicações do monorepo.

Consulte também:
- [Milestone v0.1](./docs/milestones/v0.1-infra-core.md)
- [Issue #101](./docs/issues/v0.1/ISSUE-101.md)
- [Especificação da feature](./specs/001-estrutura-base-monorepo/spec.md)
