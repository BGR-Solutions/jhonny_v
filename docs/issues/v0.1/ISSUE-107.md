# 📌 Issue #107: Setup do Redis, RabbitMQ e Compose Secrets

* **Milestone:** `v0.1 - Infra Core & Observabilidade`
* **Tipo:** Infraestrutura / Mensageria
* **ADRs Vinculadas:** [`ADR-0004: Processamento Assíncrono e Filas Persistentes via RabbitMQ`](../../adr/0004-async-task-messaging-queue.md)

## 🎯 Descrição
Configurar o Redis para cache persistente e o RabbitMQ como mensageria de alta confiabilidade com suporte a filas duráveis. Centralizar também o consumo de credenciais da infraestrutura por meio de Docker Compose Secrets, evitando valores sensíveis no ambiente dos contêineres.

## 📥 Tarefas
- [x] Adicionar serviço `redis` no Compose habilitando persistência RDB periódica.
- [x] Adicionar serviço `rabbitmq` (imagem `rabbitmq:3-management`).
- [x] Configurar usuário e virtual host do RabbitMQ via `.env` e senha via Compose Secret.
- [x] Mapear portas AMQP (`5672`) e de gerência web (`15672`) do RabbitMQ.
- [x] Proteger o Redis com senha fornecida via Compose Secret.
- [x] Declarar no Compose os secrets de PostgreSQL, Redis, RabbitMQ, LiteLLM, OpenAI, Anthropic, Grafana e Open WebUI.
- [x] Fazer PostgreSQL e Grafana consumirem secrets por interfaces nativas baseadas em arquivo.
- [x] Fazer Redis, RabbitMQ, LiteLLM e Open WebUI carregarem suas credenciais de `/run/secrets` no processo de inicialização, sem persisti-las em `services.*.environment`.
- [x] Adicionar o profile isolado `issue-107` e validação de secrets em CI.

## 🔐 Configuração dos Secrets
Os valores continuam sendo fornecidos pelo ambiente do host ou pelo arquivo `.env`, mas o Compose os materializa como arquivos somente leitura em `/run/secrets` dentro de cada contêiner. Use `.env.example` como referência e substitua todos os valores de desenvolvimento antes de executar a stack fora do ambiente local.

Secrets declarados em `infra/docker-compose.yml`:

| Secret | Variável de origem | Consumidor |
|---|---|---|
| `postgres_password` | `POSTGRES_PASSWORD` | PostgreSQL |
| `redis_password` | `REDIS_PASSWORD` | Redis |
| `rabbitmq_password` | `RABBITMQ_DEFAULT_PASS` | RabbitMQ |
| `litellm_master_key` | `LITELLM_MASTER_KEY` | LiteLLM |
| `openai_api_key` | `OPENAI_API_KEY` | LiteLLM |
| `anthropic_api_key` | `ANTHROPIC_API_KEY` | LiteLLM |
| `grafana_admin_password` | `GRAFANA_PASSWORD` | Grafana |
| `open_webui_api_key` | `OPEN_WEBUI_API_KEY` | Open WebUI |

## ✅ Critérios de Aceite
- Profile `issue-107` inicia somente Redis e RabbitMQ.
- Redis rejeita comandos anônimos e responde `PONG` com a senha montada em `/run/secrets/redis_password`.
- RabbitMQ fica saudável, cria o virtual host configurado e autentica a API de gerência na porta `15672`.
- Senhas e chaves não aparecem no campo `Config.Env` dos contêineres.
- Serviços implementados nas issues anteriores consomem os secrets explicitamente declarados no Compose.
- Job `validate-issue-107` executável localmente com `act pull_request -j validate-issue-107`.
