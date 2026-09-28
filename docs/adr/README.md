# 🏛️ Architecture Decision Records (ADRs) — `jhonny_v`

Este diretório contém os Registros de Decisões de Arquitetura (ADRs) do projeto **`jhonny_v`**. Cada documento registra uma escolha arquitetural relevante, com o contexto do problema, alternativas avaliadas, racional da decisão e suas consequências.

## Quando consultar esta área

- Para entender decisões estruturais que impactam múltiplas milestones
- Para relacionar escolhas de infraestrutura, observabilidade e aplicações futuras
- Para rastrear o motivo de padrões já aceitos no roadmap

---

## 📌 Índice de Decisões

| ID | Título | Status | Data | ADR Contextualizada em |
| :--- | :--- | :--- | :--- | :--- |
| [**`0001`**](./0001-litellm-proxy-abstraction.md) | Abstração de Provedores de LLM via LiteLLM Proxy | **Aceito** | 2026-08-08 | Infra / Orquestração |
| [**`0002`**](./0002-human-in-the-loop-langgraph.md) | Padrão Human-in-the-Loop para Ações de Alto Risco | **Aceito** | 2026-08-08 | Orquestrador / MCP |
| [**`0003`**](./0003-opentelemetry-sampling-tracing.md) | Amostragem e Rastreamento Distribuído via OpenTelemetry | **Aceito** | 2026-08-08 | Observabilidade |
| [**`0004`**](./0004-async-task-messaging-queue.md) | Processamento Assíncrono e Filas Persistentes via RabbitMQ | **Aceito** | 2026-08-08 | Worker / Mensageria |
| [**`0005`**](./0005-database-postgresql-pgvector.md) | Utilização do PostgreSQL com `pgvector` para Checkpoints e Vetores | **Aceito** | 2026-08-08 | Banco de Dados |

---

## 📐 Estrutura do Formato MADR

Cada ADR adota o seguinte modelo:
- **Status**: *Proposto*, *Aceito*, *Depreciado* ou *Substituído*
- **Contexto**: o problema ou desafio técnico enfrentado
- **Opções Consideradas**: as alternativas analisadas
- **Decisão**: a escolha realizada e o motivo determinante
- **Consequências**: os impactos positivos, negativos e mitigantes resultantes
