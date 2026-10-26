# 📌 Issue #503: Integração da Extensão VS Code ao Orquestrador

* **Milestone:** `v0.5 - Interfaces & Clients`
* **Tipo:** Integration / Editor
* **ADRs Vinculadas:** N/A

## 🎯 Descrição
Configurar a comunicação do plugin/extensão do VS Code com o OpenJarvis, preservando o contexto do workspace ativo e os contratos de sessão e aprovação, conforme a [ADR-0006](../../adr/0006-openjarvis-compose.md).

## 📥 Tarefas
- [ ] Configurar cliente HTTP/SSE no VS Code apontando para a URL homologada do OpenJarvis, com autenticação e sem depender do antigo hostname.
- [ ] Passar metadados do workspace atual no cabeçalho das requisições para controle do `thread_id`.
- [ ] Validar leitura e modificação de arquivos de código via agentes do MCP.

## ✅ Critérios de Aceite
- O desenvolvedor conversa com a IA pelo VS Code e visualiza as alterações no código em tempo real.
