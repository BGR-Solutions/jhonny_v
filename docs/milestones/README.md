# 🗺️ Planejamento de Milestones — `jhonny-v`

Este diretório contém o roadmap cronológico e arquitetural do projeto **`jhonny-v`**. O desenvolvimento é guiado por marcos (milestones) evolutivos, onde cada milestone representa uma camada funcional completa e testável do ecossistema.

---

## 📍 Visão Geral do Roadmap

```Plaintext
+-----------------------------------------------------------------------------------+
|  v0.1: Infra Core & Observabilidade                                               |
|  - Docker Compose, LiteLLM, Ollama, PostgreSQL (pgvector), Redis, RabbitMQ        |
|  - Stack LGTMP (Loki, Grafana, Tempo, Prometheus, Promtail)                       |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|  v0.2: MCP Server & Skills (Protocolo MCP)                                        |
|  - Servidor MCP em Python                                                         |
|  - Toolkits: Filesystem Local, Google Workspace (Calendar/Gmail), VS Code         |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|  v0.3: Agent Orchestrator (LangGraph Engine)                                      |
|  - Motor de Decisão ReAct & Persistência PostgresSaver                            |
|  - Suporte a Human-in-the-Loop (Aprovação de Ações Sensíveis)                     |
|  - Exposição de API OpenAI-Compatible                                             |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|  v0.4: Worker Assíncrono & Processamento em Fila                                  |
|  - Consumidor RabbitMQ para Tarefas Longas (Background Jobs)                      |
|  - Notificações de Status e Callbacks de Execução                                 |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|  v0.5: Interfaces & Integrações de Cliente                                        |
|  - Homologação no Open WebUI                                                      |
|  - Extensão Customizada / Integração VS Code                                      |
+-----------------------------------------------------------------------------------+
```

---

## 🎯 Resumo das Milestones

| Milestone | Nome | Foco Principal | Entregáveis Chave |
| :--- | :--- | :--- | :--- |
| **`v0.1`** | **Infra Core & Observabilidade** | Base de Execução e Telemetria | Compose completo, Proxy LLM, Postgres+pgvector, Stack LGTMP de logs e traces. |
| **`v0.2`** | **MCP Server & Skills** | Capacidades de Execução | Servidor MCP estendido, ferramentas de SO, Google Calendar/Gmail e VS Code. |
| **`v0.3`** | **Agent Orchestrator** | Cérebro / Orquestração ReAct | Grafo LangGraph, checkpointing no Postgres, Human-in-the-Loop, API REST. |
| **`v0.4`** | **Worker Assíncrono** | Resiliência & Background Jobs | Worker RabbitMQ, processamento de e-mails em lote, relatórios e agendamentos. |
| **`v0.5`** | **Interfaces & Clients** | Experiência de Uso | Integração com Open WebUI, extensão VS Code e testes E2E. |

---

## 📂 Detalhamento por Arquivo

* [**v0.1 - Infra Core & Observabilidade**](./v0.1-infra-core.md)
* [**v0.2 - MCP Server & Skills**](./v0.2-mcp-server.md)
* [**v0.3 - Agent Orchestrator**](./v0.3-agent-orchestrator.md)
* [**v0.4 - Worker Assíncrono**](./v0.4-worker-async.md)
* [**v0.5 - Interfaces & Clients**](./v0.5-clients-integration.md)
