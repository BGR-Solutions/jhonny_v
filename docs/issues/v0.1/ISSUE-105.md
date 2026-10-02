# 📌 Issue #105: Setup do Grafana Tempo e Collector OpenTelemetry

* **Milestone:** `v0.1 - Infra Core & Observabilidade`
* **Tipo:** Observabilidade
* **ADRs Vinculadas:** [`ADR-0003: Amostragem e Rastreamento Distribuído via OpenTelemetry`](../../adr/0003-opentelemetry-sampling-tracing.md)

## 🎯 Descrição
Instalar e configurar o Grafana Tempo para recepção e consulta de distributed traces das aplicações e grafos de agentes. A integração usa OTLP gRPC/HTTP para ingestão, armazenamento local persistente e o dashboard global do Grafana para consulta via TraceQL.

## 📥 Tarefas
- [x] Adicionar serviço `tempo` no `infra/docker-compose.obs.yml`.
- [x] Criar arquivo de configuração `infra/tempo/config.yaml` para receber traces gRPC/HTTP OTLP.
- [x] Incluir Tempo, Grafana, Loki e Prometheus no profile `issue-105` e Tempo no profile `v0.1`.
- [x] Persistir WAL e blocos no volume `tempodata`.
- [x] Vincular o Tempo como datasource no Grafana habilitando a integração Trace-to-Logs com o Loki.
- [x] Adicionar o painel `Traces recentes` ao dashboard global `Jhonny Core - Visão Global`.
- [x] Validar em CI o envio de um span OTLP/HTTP, sua consulta no Tempo e o provisionamento no Grafana.

## ✅ Critérios de Aceite
- Endpoints OTLP gRPC (`4317`) e HTTP (`4318`) expostos pelo Tempo.
- Span enviado para `POST /v1/traces` recuperável pela API do Tempo usando seu Trace ID.
- Datasource `tempo` provisionado com UID estável e correlação Trace-to-Logs apontando para o datasource `loki`.
- Dashboard global provisionado com um painel de traces que executa consultas TraceQL no Tempo.
- Job `validate-issue-105` executável localmente com `act pull_request -j validate-issue-105`.
