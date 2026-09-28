# 📌 Issue #405: Exportação de Métricas Prometheus e Traces no Worker

* **Milestone:** `v0.4 - Worker Assíncrono`
* **Tipo:** Observabilidade
* **ADRs Vinculadas:** [`ADR-0003: Amostragem e Rastreamento Distribuído`](../../adr/0003-opentelemetry-sampling-tracing.md)

## 🎯 Descrição
Instrumentar o microserviço Worker para emitir métricas de consumo de filas e distributed traces OpenTelemetry.

## 📥 Tarefas
- [ ] Expor servidor HTTP de métricas do Prometheus no Worker (`/metrics`).
- [ ] Coletar métricas customizadas: `tasks_processed_total`, `task_duration_seconds`, `tasks_failed_total`.
- [ ] Propagar o contexto do Trace ID extraído dos cabeçalhos da mensagem AMQP no OpenTelemetry.

## ✅ Critérios de Aceite
- Traces iniciados no Agent Orchestrator continuam visíveis de forma contínua no Grafana Tempo durante a execução no Worker.
