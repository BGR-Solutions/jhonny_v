# 📌 Issue #305: Exposição da API OpenAI-Compatible e SSE Streaming

* **Milestone:** `v0.3 - Agent Orchestrator`
* **Tipo:** API / Client Layer
* **ADRs Vinculadas:** N/A

## 🎯 Descrição
Expor endpoint `/v1/chat/completions` no orquestrador compatível com o padrão OpenAI, transmitindo o raciocínio em tempo real via Server-Sent Events (SSE).

## 📥 Tarefas
- [ ] Implementar controlador compatível com os contratos de requisição/resposta da OpenAI.
- [ ] Implementar gerador de fluxo SSE retornando eventos do LangGraph (passos intermediários e texto final).
- [ ] Mapear `thread_id` a partir das requisições do cliente.

## ✅ Critérios de Aceite
- Clientes HTTP compatíveis recebem respostas em streaming SSE tratadas passo a passo.
