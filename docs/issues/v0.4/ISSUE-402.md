# 📌 Issue #402: Contrato de Mensagens e Schemas de Tasks em Background

* **Milestone:** `v0.4 - Worker Assíncrono`
* **Tipo:** Arquitetura / Contratos
* **ADRs Vinculadas:** [`ADR-0004: Processamento Assíncrono via RabbitMQ`](../../adr/0004-async-task-messaging-queue.md)

## 🎯 Descrição
Definir contratos de payloads JSON padronizados (`TaskEnvelope`) transmitidos do `agent-orchestrator` para o `worker`.

## 📥 Tarefas
- [ ] Criar modelos Pydantic/Schemas para a estrutura de mensagens das filas.
- [ ] Incluir metadados obrigatórios nas mensagens: `task_id`, `thread_id`, `action`, `payload`, `timestamp`.
- [ ] Criar utilitário de validação e desempacotamento seguro de mensagens no Worker.

## ✅ Critérios de Aceite
- Mensagens fora do padrão do schema são rejeitadas com erro explicativo sem derrubar o serviço.
