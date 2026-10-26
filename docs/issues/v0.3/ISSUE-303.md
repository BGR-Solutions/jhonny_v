# 📌 Issue #303: Configuração do Ciclo de Decisão do OpenJarvis via LiteLLM

* **Milestone:** `v0.3 - OpenJarvis`
* **Tipo:** Feature / Agent Architecture
* **ADRs Vinculadas:** [`ADR-0001: Abstração de Provedores de LLM`](../../adr/0001-litellm-proxy-abstraction.md), [`ADR-0002: Human-in-the-Loop`](../../adr/0002-human-in-the-loop-langgraph.md)

## 🎯 Descrição
Homologar o ciclo iterativo de decisão e execução de ferramentas do OpenJarvis, com chamadas de modelos exclusivamente pelo LiteLLM Proxy. A [ADR-0006](../../adr/0006-openjarvis-compose.md) substitui a construção de um grafo LangGraph próprio pela configuração do motor externo.

## 📥 Tarefas
- [ ] Configurar endpoint, autenticação e aliases de modelos do LiteLLM nos mecanismos suportados pela imagem, mantendo o proxy em `infra/compose.llm.yaml`.
- [ ] Validar chamadas de ferramentas MCP e continuidade do contexto até a resposta final.
- [ ] Validar limites de execução, condições de parada e tratamento explícito de falhas, sem exigir `AgentState` ou nós LangGraph próprios.
- [ ] Demonstrar que o OpenJarvis não acessa diretamente Ollama ou provedores cloud e preserva os contratos de erro do proxy.

## ✅ Critérios de Aceite
- O agente responde a solicitações simples e completa uma tarefa iterativa com ferramentas MCP e modelos via LiteLLM.
- O comportamento é validado na versão selecionada; incompatibilidades bloqueiam o aceite em vez de alterar silenciosamente o contrato.
