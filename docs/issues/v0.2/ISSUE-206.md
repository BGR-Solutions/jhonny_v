# 📌 Issue #206: Exposição do Servidor MCP via SSE / Stdio

* **Milestone:** `v0.2 - MCP Server & Skills`
* **Tipo:** Infra / Transport Layer
* **ADRs Vinculadas:** N/A

## 🎯 Descrição
Expor o servidor MCP nos transportes Server-Sent Events (SSE) e Stdio, permitindo sua utilização tanto em contêineres quanto localmente.

## 📥 Tarefas
- [ ] Configurar transporte SSE em FastAPI/Starlette dentro do `apps/mcp-server`.
- [ ] Manter suporte ao modo Stdio via parâmetro de inicialização CLI.
- [ ] Instrumentar logs de conexão e desconexão de clientes MCP.

## ✅ Critérios de Aceite
- Clientes MCP (como Inspector e Agent Orchestrator) conectam e descobrem as ferramentas via SSE.
