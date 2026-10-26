# 📌 Issue #402: Contrato de Mensagens e Schemas de Tasks em Background

* **Milestone:** `v0.4 - Worker Assíncrono`
* **Tipo:** Arquitetura / Contratos
* **ADRs Vinculadas:** [`ADR-0004: Processamento Assíncrono via RabbitMQ`](../../adr/0004-async-task-messaging-queue.md)

## 🎯 Descrição
Definir contratos de payloads JSON padronizados (`TaskEnvelope`) para tarefas originadas no OpenJarvis e consumidas pelo `worker` via RabbitMQ. A [ADR-0006](../../adr/0006-openjarvis-compose.md) preserva esse contrato sem presumir publicação AMQP nativa da imagem.

## 📥 Tarefas
- [ ] Criar modelos Pydantic/Schemas para a estrutura de mensagens das filas.
- [ ] Incluir metadados obrigatórios nas mensagens: `task_id`, `thread_id`, `action`, `payload`, `timestamp`.
- [ ] Criar utilitário de validação e desempacotamento seguro de mensagens no Worker.
- [ ] Homologar o ponto de publicação da integração com OpenJarvis, preservando o schema e a correlação de sessão e tracing; lacunas exigem decisão arquitetural antes da implementação.

## ✅ Critérios de Aceite
- Mensagens fora do padrão do schema são rejeitadas com erro explicativo sem derrubar o serviço.
