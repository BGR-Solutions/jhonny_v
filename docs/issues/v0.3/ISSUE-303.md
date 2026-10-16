# 📌 Issue #303: Construção do Grafo LangGraph (ReAct Loop)

* **Milestone:** `v0.3 - Agent Orchestrator`
* **Tipo:** Feature / Agent Architecture
* **ADRs Vinculadas:** [`ADR-0001: Abstração de Provedores de LLM`](../../adr/0001-litellm-proxy-abstraction.md), [`ADR-0002: Human-in-the-Loop`](../../adr/0002-human-in-the-loop-langgraph.md)

## 🎯 Descrição
Construir a estrutura do `StateGraph` no LangGraph com o loop ReAct (Reasoning + Acting), conectando-o ao LiteLLM Proxy.

## 📥 Tarefas
- [ ] Definir o schema do `AgentState` (mensagens, plano atual, chamadas pendentes).
- [ ] Criar nós `agent` (decisão da LLM via LiteLLM) e `tools` (execução do MCP).
- [ ] Definir bordas condicionais para avaliação de parada ou continuação do loop.

## ✅ Critérios de Aceite
- O agente responde a solicitações simples e executa ferramentas sequencialmente em loop ReAct.
