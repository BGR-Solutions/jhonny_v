# 📋 Rastreamento de Issues & Tarefas — `jhonny_v`

Este diretório contém o detalhamento técnico e os critérios de aceite das issues do projeto **`jhonny_v`**, organizadas por milestones evolutivas.

## Como navegar

- Use a matriz de rastreabilidade para localizar a issue correta por milestone
- Consulte as ADRs vinculadas quando uma entrega depender de uma decisão arquitetural prévia
- Retorne ao [README principal](../../README.md) quando precisar da visão geral do monorepo

---

## 🔗 Matriz de Rastreabilidade (Issues vs ADRs)

| Milestone | Issue | Título | ADRs Vinculadas |
| :--- | :--- | :--- | :--- |
| **v0.1** | [**`#101`**](./v0.1/ISSUE-101.md) | Estrutura Base do Monorepo e Documentação inicial | N/A |
| **v0.1** | [**`#102`**](./v0.1/ISSUE-102.md) | Configuração do LiteLLM Proxy e Roteamento de Modelos | `ADR-0001` |
| **v0.1** | [**`#103`**](./v0.1/ISSUE-103.md) | Agregação de Logs de Contêineres com Grafana Alloy e Loki | [`0006`](../adr/0006-log-aggregation-socket-proxy-gateway.md) |
| **v0.1** | [**`#104`**](./v0.1/ISSUE-104.md) | Setup do Prometheus e Grafana (Metrics & Dashboards) | N/A |
| **v0.1** | [**`#105`**](./v0.1/ISSUE-105.md) | Setup do Grafana Tempo e Collector OpenTelemetry | `ADR-0003` |
| **v0.1** | [**`#106`**](./v0.1/ISSUE-106.md) | Provisionamento do PostgreSQL + pgvector | `ADR-0005` |
| **v0.1** | [**`#107`**](./v0.1/ISSUE-107.md) | Setup do Redis e Broker RabbitMQ | `ADR-0004` |
| **v0.1** | [**`#108`**](./v0.1/ISSUE-108.md) | Exporters de Contêineres, Host e Aceleradores de Hardware | N/A |
| **v0.1** | [**`#109`**](./v0.1/ISSUE-109.md) | Compatibilização dos Dashboards Específicos do Grafana | N/A |
| **v0.2** | [**`#201`**](./v0.2/ISSUE-201.md) | Estrutura Base do `apps/mcp-server` | N/A |
| **v0.2** | [**`#202`**](./v0.2/ISSUE-202.md) | Implementação da Skill System Filesystem | `ADR-0002` |
| **v0.2** | [**`#203`**](./v0.2/ISSUE-203.md) | Setup de Autenticação OAuth2 / Service Account Google API | N/A |
| **v0.2** | [**`#204`**](./v0.2/ISSUE-204.md) | Implementação da Skill Google Calendar | N/A |
| **v0.2** | [**`#205`**](./v0.2/ISSUE-205.md) | Implementação da Skill Gmail | `ADR-0002` |
| **v0.2** | [**`#206`**](./v0.2/ISSUE-206.md) | Exposição do Servidor MCP via SSE / Stdio | N/A |
| **v0.3** | [**`#301`**](./v0.3/ISSUE-301.md) | Estrutura Base do `apps/agent-orchestrator` | N/A |
| **v0.3** | [**`#302`**](./v0.3/ISSUE-302.md) | Integração do Orquestrador com Servidor MCP | N/A |
| **v0.3** | [**`#303`**](./v0.3/ISSUE-303.md) | Construção do Grafo LangGraph (ReAct Loop) | `ADR-0001`, `ADR-0002` |
| **v0.3** | [**`#304`**](./v0.3/ISSUE-304.md) | Implementação do Nó Human-in-the-Loop (HitL) | `ADR-0002` |
| **v0.3** | [**`#305`**](./v0.3/ISSUE-305.md) | Exposição da API OpenAI-Compatible e SSE Streaming | N/A |
| **v0.3** | [**`#306`**](./v0.3/ISSUE-306.md) | Persistência de Checkpoints com `PostgresSaver` | `ADR-0005` |
| **v0.4** | [**`#401`**](./v0.4/ISSUE-401.md) | Estrutura Base do `apps/worker` e Consumidor RabbitMQ | `ADR-0004` |
| **v0.4** | [**`#402`**](./v0.4/ISSUE-402.md) | Contrato de Mensagens e Schemas de Tasks em Background | `ADR-0004` |
| **v0.4** | [**`#403`**](./v0.4/ISSUE-403.md) | Implementação de Handlers para Resumo de E-mail e Agenda | N/A |
| **v0.4** | [**`#404`**](./v0.4/ISSUE-404.md) | Implementação de Dead Letter Queues (DLQ) e Retentativas | `ADR-0004` |
| **v0.4** | [**`#405`**](./v0.4/ISSUE-405.md) | Exportação de Métricas Prometheus e Traces no Worker | `ADR-0003` |
| **v0.5** | [**`#501`**](./v0.5/ISSUE-501.md) | Configuração do Open WebUI para o Agent Orchestrator | N/A |
| **v0.5** | [**`#502`**](./v0.5/ISSUE-502.md) | Homologação da Interface Human-in-the-Loop na UI | `ADR-0002` |
| **v0.5** | [**`#503`**](./v0.5/ISSUE-503.md) | Integração da Extensão VS Code ao Orquestrador | N/A |
| **v0.5** | [**`#504`**](./v0.5/ISSUE-504.md) | Testes de Integração End-to-End (E2E) | N/A |
