# 📌 Issue #502: Homologação da Interface Human-in-the-Loop na UI

* **Milestone:** `v0.5 - Interfaces & Clients`
* **Tipo:** Feature / UX
* **ADRs Vinculadas:** [`ADR-0002: Padrão Human-in-the-Loop para Ações de Alto Risco`](../../adr/0002-human-in-the-loop-langgraph.md)

## 🎯 Descrição
Validar a experiência do usuário quando o agente solicita aprovação explícita para executar ferramentas sensíveis.

## 📥 Tarefas
- [ ] Formatar payload de interrupção enviado no SSE para apresentação limpa do pedido de aprovação na UI.
- [ ] Validar botões/comandos de Confirmação e Rejeição disparando a retomada no `agent-orchestrator`.

## ✅ Critérios de Aceite
- O usuário consegue aprovar ou rejeitar uma ação crítica diretamente pelo chat sem falhas de estado.
