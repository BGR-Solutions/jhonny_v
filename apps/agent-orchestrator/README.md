# apps/agent-orchestrator

Placeholder legado do antigo planejamento de um orquestrador próprio para o ecossistema `jhonny_v`.

## Substituição planejada pelo OpenJarvis

O motor de decisão e orquestração passará a ser fornecido por uma imagem Docker do OpenJarvis, controlada em `infra/compose.core.yaml`. As configurações ficarão na futura pasta `infra/openjarvis/`, seguindo o padrão dos demais serviços Docker.

Não está previsto desenvolver uma aplicação FastAPI/LangGraph neste diretório. As responsabilidades de integrar modelos, ferramentas MCP, aprovações humanas e workers continuam no escopo da [milestone v0.3](../../docs/milestones/v0.3-agent-orchestrator.md), agora como integração e homologação do OpenJarvis.

Este diretório permanece fisicamente inalterado: sua eventual remoção ou migração será tratada em uma entrega posterior. A revisão atual é exclusivamente documental. Consulte a [ADR-0006](../../docs/adr/0006-openjarvis-compose.md).
