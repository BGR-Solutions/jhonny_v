# Documentação do jhonny_v

Este diretório é o hub central de documentação do monorepo **`jhonny_v`**. Aqui ficam as decisões arquiteturais, o planejamento incremental das entregas e os índices que orientam o roadmap técnico do projeto.

## Como usar esta documentação

1. Comece pelo [README principal](../README.md) para entender a visão geral do monorepo e o quickstart local.
2. Use os índices abaixo para navegar até o tipo de contexto que você precisa.
3. Consulte as milestones e issues para conectar cada entrega às decisões arquiteturais correspondentes.

## Índices

- [Architecture Decision Records (ADRs)](./adr/README.md)
- [Issues e tarefas](./issues/README.md)
- [Milestones](./milestones/README.md)

## Relação com a estrutura do monorepo

- `apps/`: aplicações próprias (MCP Server e Worker), com o placeholder legado do orquestrador ainda preservado
- `infra/`: infraestrutura compartilhada, serviços core e operação local; inclui o planejamento do OpenJarvis via imagem em `compose.core.yaml` e configurações na futura pasta `openjarvis/`
- `docs/`: contexto arquitetural, backlog técnico e roadmap
- `specs/`: artefatos do fluxo Spec-Driven Development

Consulte também o [README principal](../README.md) para a visão geral da arquitetura e as instruções de desenvolvimento.

## Direção arquitetural: OpenJarvis

A [ADR-0006](./adr/0006-openjarvis-compose.md) substitui o planejamento de um motor próprio em LangGraph pela integração do OpenJarvis. Os requisitos funcionais continuam como critérios de homologação, não como capacidades já comprovadas da imagem. Esta revisão é somente documental e preserva diretórios, Compose e código atuais.
