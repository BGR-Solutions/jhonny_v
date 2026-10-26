# 📌 Issue #103: Setup do Grafana Alloy e Loki para Agregação de Logs

* **Milestone:** `v0.1 - Infra Core & Observabilidade`
* **Tipo:** Observabilidade
* **ADRs Vinculadas:** N/A

## 🎯 Descrição
Configurar a coleta unificada de logs dos contêineres do projeto, capturando saídas `stdout`/`stderr` e enviando para o Loki através do Grafana Alloy. Contêineres de outros projetos no mesmo host ficam fora da coleta por padrão.

**Decisão de 2026-10-25:** substituir Promtail por Grafana Alloy, conforme confirmação do usuário. A [documentação oficial](https://grafana.com/docs/loki/latest/send-data/promtail/) informa que Promtail chegou ao fim de vida em 2026-03-02, sem novas atualizações.

**Especificação:** [003 — Agregação de Logs com Alloy e Loki](../../../specs/003-alloy-loki-logs/spec.md). Esta etapa apenas especifica a entrega; implementação depende dos próximos gates SDD.

## 📥 Tarefas
- [ ] Adicionar serviço `loki` no `infra/compose.obs.yaml`.
- [ ] Adicionar serviço `alloy` no `infra/compose.obs.yaml`, com descoberta Docker e controles explícitos para o acesso aos logs; avaliar o acesso ao socket Docker no planejamento.
- [ ] Criar arquivo `infra/alloy/config.alloy` mapeando labels dinâmicos de baixa cardinalidade e restringindo a coleta ao projeto.
- [ ] Criar arquivo `infra/loki/config.yaml`.

## ✅ Critérios de Aceite
- Os logs de stdout/stderr de qualquer contêiner ativo do projeto com mecanismo de logs suportado são ingeridos e consultáveis no Loki, incluindo contêineres descobertos após a inicialização.
- A origem, mensagem e contexto distribuído dos eventos são preservados, sem ingerir logs de outros projetos.
- Nenhuma aplicação grava logs em arquivos locais; uso estrito de `stdout`/`stderr`.
- Reinício, persistência e diagnóstico de falhas atendem aos cenários e critérios mensuráveis da especificação.
