# 📌 Issue #404: Implementação de Dead Letter Queues (DLQ) e Retentativas

* **Milestone:** `v0.4 - Worker Assíncrono`
* **Tipo:** Resiliência
* **ADRs Vinculadas:** [`ADR-0004: Processamento Assíncrono via RabbitMQ`](../../adr/0004-async-task-messaging-queue.md)

## 🎯 Descrição
Configurar politica de retentativa automática com Exponential Backoff e roteamento de mensagens falhas para uma Dead Letter Queue (DLQ).

## 📥 Tarefas
- [ ] Configurar política de NACK e requeue no RabbitMQ com limite de retentativas (ex: 3 tentativas).
- [ ] Criar e vincular a fila `jhonny.tasks.dlq` para descarte de mensagens com falha persistente.
- [ ] Adicionar logs de alerta ao encaminhar mensagens para a DLQ.

## ✅ Critérios de Aceite
- Mensagens que falham repetidamente são isoladas na DLQ sem travar o processamento da fila principal.
