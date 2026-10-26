# jhonny_v

`jhonny_v` é um monorepo em construção para o ecossistema **`jhonny_v`**, reunindo aplicações, infraestrutura compartilhada e documentação técnica em uma única base versionada.

## Visão geral do monorepo

A estrutura inicial do repositório foi organizada para tornar o onboarding previsível e preparar as próximas milestones do projeto.

```text
.
├── apps/      # Aplicações próprias (MCP Server e Worker); placeholder legado preservado
├── infra/     # Orquestração local, serviços core e artefatos operacionais compartilhados
├── docs/      # ADRs, rastreamento de issues e roadmap de milestones
└── specs/     # Artefatos do fluxo Spec-Driven Development (SDD)
```

## Áreas principais

### `apps/`
Contém os espaços reservados para as aplicações próprias do ecossistema: MCP Server e Worker. O placeholder do antigo Agent Orchestrator permanece apenas como referência legada nesta revisão documental.

### `infra/`
Centraliza a configuração operacional compartilhada do ambiente local. É a área responsável pelos arquivos Compose base, serviços core e contratos de execução reutilizados pelas aplicações. O planejamento inclui o OpenJarvis por imagem Docker em `infra/compose.core.yaml`, com configurações próprias na futura pasta `infra/openjarvis/`.

### `docs/`
É o hub documental do projeto, com navegação para ADRs, backlog técnico e milestones arquiteturais. Use esta área como ponto de referência para entender decisões, roadmap e rastreabilidade.

### `specs/`
Armazena as especificações, planos, tarefas e demais artefatos produzidos pelo fluxo obrigatório de Spec-Driven Development.

## Estrutura de aplicações planejadas

- [`apps/mcp-server/`](./apps/mcp-server/README.md): base do servidor MCP e das skills do projeto
- [`apps/worker/`](./apps/worker/README.md): base para processamento assíncrono e tarefas em background

## Orquestração planejada com OpenJarvis

O OpenJarvis substituirá o desenvolvimento do `agent-orchestrator` próprio. Seu ciclo de execução será controlado pelo `infra/compose.core.yaml`, usando uma imagem Docker de versão fixada e configurações na futura pasta `infra/openjarvis/`, sem build local do motor.

A mudança preserva como requisitos as integrações com MCP Server, LiteLLM, RabbitMQ/Worker, persistência, aprovações humanas e API/streaming para clientes. A compatibilidade da imagem ainda precisa ser homologada; veja a [ADR-0006](./docs/adr/0006-openjarvis-compose.md) e a [milestone v0.3](./docs/milestones/v0.3-agent-orchestrator.md).

**Estado da adoção do OpenJarvis:** permanece somente documental, sem implementação do motor ou movimentação de aplicações. O [placeholder legado](./apps/agent-orchestrator/README.md) continua presente, e o quickstart abaixo ainda não inicia o OpenJarvis. A camada de logs da issue #103 é independente dessa adoção.

## Quickstart do ambiente local

1. Copie o contrato de ambiente compartilhado:
   ```bash
   cp .env.example .env
   ```
   No Windows PowerShell:
   ```powershell
   Copy-Item .env.example .env
   ```
2. Revise os valores locais necessários em `.env`.
3. Valide a composição consolidada:
   ```bash
   docker compose -f infra/compose.yaml -f infra/compose.core.yaml config
   ```
4. Inicie os serviços core:
   ```bash
   docker compose -f infra/compose.yaml -f infra/compose.core.yaml up -d
   ```

## Logs locais com Alloy e Loki

A [camada de observabilidade](./infra/compose.obs.yaml) contém Alloy, Loki, gateway autenticado e proxy restrito da API Docker. Ela é iniciada com o Compose base, sem depender de serviços core, Grafana, MCP Server, Worker ou OpenJarvis:

```powershell
docker compose --env-file .\.env -f .\infra\compose.yaml -f .\infra\compose.obs.yaml up -d --wait --wait-timeout 120
```

**Antes de executar:** construa as imagens locais e provisione os segredos privados seguindo o [quickstart da issue #103](./specs/003-alloy-loki-logs/quickstart.md). Não há credenciais padrão. O preflight recusa material ausente, inconsistente ou com permissões indevidas; no Windows, evidência de ACL do bind real é obrigatória.

- Consulta somente em `127.0.0.1:3100` por padrão, com Basic Auth; ingestão e administração não são publicadas.
- Descoberta restrita ao projeto Compose; stdout/stderr, mensagens originais e contexto preservados. IDs de contêiner/tracing não são labels indexadas.
- Retenção padrão de 14 dias, em volume nomeado, sem tratar retenção como quota de disco. Não usar `down -v` na stack do operador.
- Validação local: 29 testes de regressão e um cenário contínuo de limpeza física passaram. CI Linux remoto e ACL Windows do operador ainda estão pendentes; a issue não está encerrada.
- O [contrato operacional](./specs/003-alloy-loki-logs/contracts/logging-contract.md) descreve autenticação, retentativas, janela fora de ordem e limites; o [workflow](./.github/workflows/validate-issue-103.yml) exige integração e retenção sem skips implícitos.

## Navegação da documentação

- [Hub de documentação](./docs/README.md)
- [ADRs](./docs/adr/README.md)
- [Issues e tarefas](./docs/issues/README.md)
- [Milestones](./docs/milestones/README.md)

## Roadmap atual

A entrega inicial prioriza a milestone **v0.1 — Infra Core & Observabilidade**, preparando a base para infraestrutura, observabilidade e futuras aplicações do monorepo.

Consulte também:
- [Milestone v0.1](./docs/milestones/v0.1-infra-core.md)
- [Índice de issues](./docs/issues/README.md)
- [Especificação da feature](./specs/001-estrutura-base-monorepo/spec.md)
