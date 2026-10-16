# Apps do Monorepo

Este diretório reúne as aplicações do ecossistema `jhonny_v`.

## Objetivo

Separar cada aplicação em um espaço próprio, com responsabilidade explícita e evolução independente, mantendo a infraestrutura compartilhada e a documentação fora do código de aplicação.

## Áreas previstas

- [`mcp-server/`](./mcp-server/README.md): servidor MCP e catálogo de skills
- [`agent-orchestrator/`](./agent-orchestrator/README.md): coordenação de agentes, decisões e fluxos LangGraph
- [`worker/`](./worker/README.md): processamento assíncrono, filas e jobs de longa duração

Enquanto as implementações completas não existem, estes subdiretórios funcionam como placeholders navegáveis para orientar a expansão do monorepo.
