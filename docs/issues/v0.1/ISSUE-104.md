# 📌 Issue #104: Setup do Prometheus e Grafana (Metrics & Dashboards)

* **Milestone:** `v0.1 - Infra Core & Observabilidade`
* **Tipo:** Observabilidade
* **ADRs Vinculadas:** N/A

## 🎯 Descrição
Implementar a infraestrutura central de coleta e visualização de métricas de serviços por meio do Prometheus e Grafana pré-configurados. A coleta de métricas de contêineres, host e aceleradores de hardware pertence à [`Issue #108`](./ISSUE-108.md), e os dashboards específicos sem dados serão tratados na [`Issue #109`](./ISSUE-109.md).

## 📥 Tarefas
- [x] Adicionar serviço `prometheus` no Compose com retenção e scrape targets definidos em `infra/prometheus/config.yml`.
- [x] Adicionar serviço `grafana` no Compose.
- [x] Provisionar datasources (Loki e Prometheus) automaticamente via `infra/grafana/provisioning/datasources/`.
- [x] Criar e provisionar o dashboard `Jhonny Core - Visão Global` com métricas nativas do Prometheus.

## ✅ Critérios de Aceite
- Painel do Grafana acessível em `http://localhost:3000` sem necessidade de setup manual de datasources.
- Prometheus acessível em `http://localhost:9090` e coletando as métricas dos serviços configurados que estiverem ativos.
- Dashboard `Jhonny Core - Visão Global` renderizando disponibilidade, memória, séries TSDB, requisições HTTP, ingestão de amostras e duração dos scrapes do Prometheus.
