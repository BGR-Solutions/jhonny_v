# 📌 Issue #203: Setup de Autenticação OAuth2 / Service Account Google API

* **Milestone:** `v0.2 - MCP Server & Skills`
* **Tipo:** Integração / Segurança
* **ADRs Vinculadas:** N/A

## 🎯 Descrição
Configurar o mecanismo de autenticação e gerenciamento de tokens OAuth2 para chamadas às APIs do Google Workspace.

## 📥 Tarefas
- [x] Criar módulo de autenticação Google em `apps/mcp-server/src/auth/providers/google_auth.py`.
- [x] Implementar rotina de refresh token automático e armazenamento seguro de credenciais.
- [x] Mapear as variáveis e caminhos de credenciais do Google no `.env.example` e na documentação do subprojeto.

## ✅ Critérios de Aceite
- O servidor MCP consegue autenticar e renovar o token das APIs Google com sucesso.
- A documentação de setup referencia corretamente os arquivos locais de credenciais e token do provedor Google.
