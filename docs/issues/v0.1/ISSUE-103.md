# 📌 Issue #103: Agregação de Logs de Contêineres com Grafana Alloy e Loki

* **Milestone:** `v0.1 - Infra Core & Observabilidade`
* **Tipo:** Observabilidade
* **ADRs Vinculadas:** [`0006`](../../adr/0006-log-aggregation-socket-proxy-gateway.md)
* **Especificação (SDD):** [`specs/003-agregacao-logs-loki/`](../../../specs/003-agregacao-logs-loki/)

## 🎯 Descrição
Configurar a coleta unificada de logs de contêineres, capturando as saídas `stdout`/`stderr` e enviando-as ao Loki pelo **Grafana Alloy**. O Promtail, citado na versão original desta issue, está em fim de vida e foi substituído pelo Alloy na clarificação da especificação.

## 📥 Tarefas
- [x] Adicionar o serviço `loki` em `infra/compose.obs.yaml`, ouvindo só no loopback, com config em `infra/loki/config.yaml`.
- [x] Adicionar o gateway autenticado `loki-gateway` (Caddy, basic auth), único ponto de consulta e push.
- [x] Adicionar o proxy `socket-proxy` (`wollomatic/socket-proxy`), o único serviço que monta `/var/run/docker.sock`, somente leitura e com allowlist de leitura.
- [x] Adicionar o coletor `alloy`, com config em `infra/alloy/config.alloy`, mapeando rótulos dinâmicos de contêiner (`compose_project`, `compose_service`, `container`, `stream`).
- [x] Aplicar a rotação `json-file` (10m × 3) em todas as camadas Compose.
- [x] Testes de aceite `pytest` em `infra/tests/` e workflow de CI `.github/workflows/infra-obs.yaml`.

## ✅ Critérios de Aceite
- Os logs de qualquer contêiner ativo são ingeridos e indexados no Loki.
- Nenhuma aplicação grava logs em arquivos locais; uso estrito de `stdout`/`stderr`.
