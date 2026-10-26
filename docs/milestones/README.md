# 🗺️ Planejamento de Milestones — `jhonny_v`

Este diretório contém o roadmap cronológico e arquitetural do projeto **`jhonny_v`**. Cada milestone representa uma camada funcional completa e testável do ecossistema, conectando infraestrutura, aplicações e integrações.

## Como usar este índice

- Comece por este arquivo para entender a sequência geral de entregas
- Abra o arquivo da milestone correspondente para ver o foco e os entregáveis
- Cruze o roadmap com [issues](../issues/README.md) e [ADRs](../adr/README.md) quando precisar de contexto adicional

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
|  v0.3: OpenJarvis (Imagem Docker no Compose Core)                                 |
|  - Decisão, ferramentas MCP e persistência de sessões a homologar                 |
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
| **`v0.3`** | **OpenJarvis** | Integração do motor de orquestração | Imagem Docker no Compose core, configurações em `infra/openjarvis/`, homologação de MCP, LiteLLM, persistência, HitL e API/SSE. |
| **`v0.4`** | **Worker Assíncrono** | Resiliência & Background Jobs | Worker RabbitMQ, processamento de e-mails em lote, relatórios e agendamentos. |
| **`v0.5`** | **Interfaces & Clients** | Experiência de Uso | Integração com Open WebUI, extensão VS Code e testes E2E. |

---

## 📂 Detalhamento por Arquivo

- [**v0.1 - Infra Core & Observabilidade**](./v0.1-infra-core.md)
- [**v0.2 - MCP Server & Skills**](./v0.2-mcp-server.md)
- [**v0.3 - OpenJarvis**](./v0.3-agent-orchestrator.md)
- [**v0.4 - Worker Assíncrono**](./v0.4-worker-async.md)
- [**v0.5 - Interfaces & Clients**](./v0.5-clients-integration.md)

A [ADR-0006](../adr/0006-openjarvis-compose.md) registra a substituição do orquestrador próprio pelo OpenJarvis. A revisão é documental: o serviço e a pasta de configurações ainda não foram adicionados. A ordem das fases permanece inalterada, e as funcionalidades são requisitos a homologar, não capacidades presumidas da imagem.
