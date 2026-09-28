# 📌 Issue #302: Integração do Orquestrador com Servidor MCP

* **Milestone:** `v0.3 - Agent Orchestrator`
* **Tipo:** Integration / Feature
* **ADRs Vinculadas:** N/A

## 🎯 Descrição
Implementar o cliente MCP dentro do orquestrador para carregar dinamicamente as definições de ferramentas oferecidas pelo `mcp-server`.

## 📥 Tarefas
- [x] Criar cliente de conexão SSE para o `mcp-server`.
- [x] Implementar conversor de schemas do MCP para o formato nativo de `Tools` do LangChain/LangGraph.
- [x] Tratar reconexões automáticas e falhas de comunicação com o MCP.

## ✅ Critérios de Aceite
- O orquestrador carrega com sucesso as ferramentas do MCP Server na inicialização.
