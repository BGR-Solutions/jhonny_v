# 📌 Issue #202: Implementação da Skill System Filesystem

* **Milestone:** `v0.2 - MCP Server & Skills`
* **Tipo:** Feature / Skills
* **ADRs Vinculadas:** [`ADR-0002: Padrão Human-in-the-Loop para Ações de Alto Risco`](../../adr/0002-human-in-the-loop-langgraph.md)

## 🎯 Descrição
Implementar conjunto de ferramentas para leitura, listagem e manipulação segura de arquivos locais dentro de diretórios autorizados.

## 📥 Tarefas
- [x] Criar ferramenta `read_file`, `write_file`, `list_directory` e `search_files`.
- [x] Aplicar validação de sandbox para impedir navegação fora do diretório delimitado (*path traversal protection*).
- [x] Marcar metadados de ferramentas de escrita/exclusão com flag de ação crítica.

## ✅ Critérios de Aceite
- Leitura e escrita de arquivos funcionais com limites de permissão validados por testes unitários.
- Erro amigável retornado caso ocorra tentativa de acesso fora da sandbox.
