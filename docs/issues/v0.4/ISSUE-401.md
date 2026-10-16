# 📌 Issue #401: Estrutura Base do `apps/worker` e Consumidor RabbitMQ

* **Milestone:** `v0.4 - Worker Assíncrono`
* **Tipo:** Desenvolvimento App / Mensageria
* **ADRs Vinculadas:** [`ADR-0004: Processamento Assíncrono via RabbitMQ`](../../adr/0004-async-task-messaging-queue.md)

## 🎯 Descrição
Estruturar o serviço `apps/worker` responsável por escutar eventos do RabbitMQ e executar tarefas em background.

## 📥 Tarefas
- [ ] Criar estrutura interna em `apps/worker/` (`src/`, `tests/`, `README.md`).
- [ ] Implementar cliente consumidor assíncrono para RabbitMQ com reconexão automática.
- [ ] Configurar tratamento gracioso de encerramento (*graceful shutdown*).

## ✅ Critérios de Aceite
- O Worker conecta na fila do RabbitMQ e permanece ativo em loop de escuta sem estourar conexões.
