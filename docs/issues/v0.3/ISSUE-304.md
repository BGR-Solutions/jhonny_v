# 📌 Issue #304: Homologação de Human-in-the-Loop (HitL) no OpenJarvis

* **Milestone:** `v0.3 - OpenJarvis`
* **Tipo:** Feature / Segurança
* **ADRs Vinculadas:** [`ADR-0002: Padrão Human-in-the-Loop para Ações de Alto Risco`](../../adr/0002-human-in-the-loop-langgraph.md)

## 🎯 Descrição
Configurar e validar a pausa antes de ferramentas sensíveis no OpenJarvis, exigindo aprovação ou rejeição explícita. Conforme a [ADR-0006](../../adr/0006-openjarvis-compose.md), não se presume o mecanismo LangGraph `interrupt_before` nem suporte já comprovado da imagem.

## 📥 Tarefas
- [ ] Mapear ferramentas críticas exigindo confirmação explícita.
- [ ] Identificar e configurar o mecanismo de aprovação suportado pela imagem, preservando ação, argumentos e sessão pendente.
- [ ] Homologar o contrato de aprovação/rejeição consumido pelos clientes; validar equivalência às rotas antes previstas `/threads/{thread_id}/approve` e `/threads/{thread_id}/reject`, sem presumir que existam na imagem.
- [ ] Testar aprovação, rejeição e retomada após reinício, em conjunto com a [issue #306](./ISSUE-306.md).

## ✅ Critérios de Aceite
- Ações críticas permanecem pendentes e não executam ferramentas antes da aprovação explícita.
- Rejeições impedem a execução; o estado pendente sobrevive a reinícios e pode ser retomado.
- Ausência de um mecanismo compatível bloqueia a integração e exige decisão arquitetural explícita.
