# 📌 Issue #103: Setup do Promtail e Loki para Agregação de Logs

* **Milestone:** `v0.1 - Infra Core & Observabilidade`
* **Tipo:** Observabilidade
* **ADRs Vinculadas:** N/A

## 🎯 Descrição
Configurar a coleta unificada de logs de contêineres capturando saídas `stdout`/`stderr` e enviando para o Loki através do Promtail.

## 📥 Tarefas
- [ ] Adicionar serviço `loki` no `infra/compose.obs.yml`.
- [ ] Adicionar serviço `promtail` no `infra/compose.obs.yml` montando o socket do Docker (`/var/run/docker.sock`).
- [ ] Criar arquivo `infra/promtail/config.yaml` mapeando labels dinâmicos de contêiner.
- [ ] Criar arquivo `infra/loki/config.yaml`.

## ✅ Critérios de Aceite
- Os logs de qualquer contêiner ativo são ingeridos e indexados no Loki.
- Nenhuma aplicação grava logs em arquivos locais; uso estrito de `stdout`/`stderr`.
