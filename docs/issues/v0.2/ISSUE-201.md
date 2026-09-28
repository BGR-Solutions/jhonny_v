# 📌 Issue #201: Estrutura Base do `apps/mcp-server`

* **Milestone:** `v0.2 - MCP Server & Skills`
* **Tipo:** Desenvolvimento App
* **ADRs Vinculadas:** N/A

## 🎯 Descrição
Inicializar o subrepositório do servidor MCP em Python, configurando dependências do SDK oficial e estrutura básica do projeto.

## 📥 Tarefas
- [x] Criar estrutura interna em `apps/mcp-server/` (`src/`, `tests/`, `README.md`).
- [x] Configurar `pyproject.toml` / `requirements.txt` com SDK do MCP e Pytest.
- [x] Implementar entrypoint inicial com logging estruturado direcionado para `stdout`.

## ✅ Critérios de Aceite
- Execução do servidor MCP via CLI sem falhas de importação.
- Suíte de testes iniciais executando via `pytest apps/mcp-server/tests`.
