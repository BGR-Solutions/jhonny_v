# Apps do Monorepo

Este diretório reúne as aplicações do ecossistema `jhonny_v`.

## Objetivo

Separar cada aplicação em um espaço próprio, com responsabilidade explícita e evolução independente, mantendo a infraestrutura compartilhada e a documentação fora do código de aplicação.

## Áreas previstas

- [`mcp-server/`](./mcp-server/README.md): servidor MCP e catálogo de skills
- [`worker/`](./worker/README.md): processamento assíncrono, filas e jobs de longa duração

Enquanto as implementações completas não existem, estes subdiretórios funcionam como placeholders navegáveis para orientar a expansão do monorepo.

## Orquestração externa e placeholder legado

O motor de orquestração será o OpenJarvis, operado por imagem Docker em `infra/compose.core.yaml`, com configurações na futura pasta `infra/openjarvis/`. Ele não será uma aplicação própria em `apps/`.

O diretório [`agent-orchestrator/`](./agent-orchestrator/README.md) permanece como placeholder legado, sem previsão de desenvolver nele um motor LangGraph. Esta revisão altera apenas documentação, não a estrutura física. Consulte a [ADR-0006](../docs/adr/0006-openjarvis-compose.md).
