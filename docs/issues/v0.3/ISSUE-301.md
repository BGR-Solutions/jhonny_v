# 📌 Issue #301: Estrutura Base do `apps/agent-orchestrator`

* **Milestone:** `v0.3 - Agent Orchestrator`
* **Tipo:** Desenvolvimento App
* **ADRs Vinculadas:** N/A

## 🎯 Descrição
Inicializar a aplicação FastAPI responsável pela orquestração de estados do agente LangGraph.

## 📥 Tarefas
- [x] Criar estrutura base em `apps/agent-orchestrator/` (`src/`, `tests/`, `README.md`).
- [x] Configurar `pyproject.toml` / `requirements.txt` com FastAPI, LangGraph e OpenTelemetry SDK.
- [x] Configurar middleware de logs JSON e captura de trace-ids.

## ✅ Critérios de Aceite
- Servidor HTTP responde em `http://localhost:8000/health`.
