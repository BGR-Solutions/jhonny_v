# 📌 Issue #103: Setup do Grafana Alloy e Loki para Agregação de Logs

* **Milestone:** `v0.1 - Infra Core & Observabilidade`
* **Tipo:** Observabilidade
* **ADRs Vinculadas:** N/A

## 🎯 Descrição
Configurar a coleta unificada de logs dos contêineres do projeto, capturando saídas `stdout`/`stderr` e enviando para o Loki através do Grafana Alloy. Contêineres de outros projetos no mesmo host ficam fora da coleta por padrão.

**Decisão de 2026-10-25:** substituir Promtail por Grafana Alloy, conforme confirmação do usuário. A [documentação oficial](https://grafana.com/docs/loki/latest/send-data/promtail/) informa que Promtail chegou ao fim de vida em 2026-03-02, sem novas atualizações.

**Especificação:** [003 — Agregação de Logs com Alloy e Loki](../../../specs/003-alloy-loki-logs/spec.md). Os gates SDD foram executados e a implementação local foi validada. **Aceite completo bloqueado:** execução remota da CI Linux e comprovação de ACL/permissões do bind Windows/WSL2 do operador continuam pendentes; a issue não deve ser fechada com base apenas no smoke local.

## 📥 Tarefas
- [x] Adicionar serviço `loki` no [Compose de observabilidade](../../../infra/compose.obs.yaml).
- [x] Adicionar Alloy com descoberta restrita ao projeto e proxy Docker privado de GET/HEAD allowlisted, sem socket montado no coletor.
- [x] Criar [configuração Alloy](../../../infra/alloy/config.alloy), preservando linhas e usando metadados estruturados para IDs de instância.
- [x] Criar [configuração Loki](../../../infra/loki/config.yaml), WAL/compactor em volume persistente e retenção padrão de 336h.
- [x] Validar localmente autenticação, diagnóstico JSON, descoberta, parsing, recuperação e limpeza física contínua.
- [ ] Executar [CI obrigatória](../../../.github/workflows/validate-issue-103.yml) em Linux remoto e registrar evidência de ACL Windows do operador.

## Operação e evidência

Seguir o [quickstart](../../../specs/003-alloy-loki-logs/quickstart.md) para construir as imagens locais, provisionar três arquivos privados e iniciar somente o Compose base com observabilidade. Gateway publica apenas consulta loopback autenticada; Loki/Alloy/admin/ingestão permanecem privados. As redes de dados são internas; `obs-edge` pertence exclusivamente ao gateway para a publicação loopback comprovada no Docker Desktop.

No ambiente local documentado, 29 testes passaram em 881,85s e o teste contínuo de retenção passou em 1227,19s, sem restart/flush forçado. Quatro timestamps antigos foram cobertos por dois chunks físicos; maior remoção observada ocorreu 509,66s após a expiração individual, abaixo do limite de 1800s. Controles válidos foram preservados. Isso não certifica todas as fases de rotação TSDB ou os mounts de outro operador.

O [plano revisado](../../../specs/003-alloy-loki-logs/plan.md) conserva deadline individual de 30m e explicita custo de I/O e janela fora de ordem aproximada de 90s. Retentativas podem duplicar eventos; posições do Alloy não são WAL de envio, não há garantia de exactly-once ou de recuperação ilimitada. Nunca remover volumes do operador para simular recuperação/limpeza.

## ✅ Critérios de Aceite
- Os logs de stdout/stderr de qualquer contêiner ativo do projeto com mecanismo de logs suportado são ingeridos e consultáveis no Loki, incluindo contêineres descobertos após a inicialização.
- A origem, mensagem e contexto distribuído dos eventos são preservados, sem ingerir logs de outros projetos.
- Nenhuma aplicação grava logs em arquivos locais; uso estrito de `stdout`/`stderr`.
- Reinício, persistência e diagnóstico de falhas atendem aos cenários e critérios mensuráveis da especificação.
