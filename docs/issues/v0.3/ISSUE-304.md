# 📌 Issue #304: Implementação do Nó Human-in-the-Loop (HitL)

* **Milestone:** `v0.3 - Agent Orchestrator`
* **Tipo:** Feature / Segurança
* **ADRs Vinculadas:** [`ADR-0002: Padrão Human-in-the-Loop para Ações de Alto Risco`](../../adr/0002-human-in-the-loop-langgraph.md)

## 🎯 Descrição
Interromper o grafo do LangGraph usando `interrupt_before` sempre que uma ferramenta classificada como sensível (escrita de arquivo, envio de e-mail, etc.) for solicitada.

## 📥 Tarefas
- [ ] Mapear ferramentas críticas exigindo confirmação explícita.
- [ ] Configurar ponto de interrupção no grafo salvando o estado pausado.
- [ ] Criar endpoints `/threads/{thread_id}/approve` e `/threads/{thread_id}/reject`.

## ✅ Critérios de Aceite
- Ações críticas entram em estado pausado até o recebimento de comando de aprovação na API.
