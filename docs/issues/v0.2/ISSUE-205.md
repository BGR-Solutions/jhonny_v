# 📌 Issue #205: Implementação da Skill Gmail

* **Milestone:** `v0.2 - MCP Server & Skills`
* **Tipo:** Feature / Skills
* **ADRs Vinculadas:** [`ADR-0002: Padrão Human-in-the-Loop para Ações de Alto Risco`](../../adr/0002-human-in-the-loop-langgraph.md)

## 🎯 Descrição
Desenvolver a skill de gerenciamento de e-mails para busca, leitura e escrita de rascunhos ou envios.

## 📥 Tarefas
- [ ] Implementar ferramenta `Google Gmail`, com manipulação de `Users`, `Drafts`, `History`, `Labels`, `Messages`, `Messages Attachments`, `Settings`, `Settings CSE Identities`, `Settings CSE Keypairs`, `Settings Delegates`, `Settings Filters`, `Settings Forwarding Addresses`, `Settings SendAs`, `Settings SendAs S/MIME Info` e `Threads`.
- [ ] Marcar `create_delegate`, `delete_delegate`, `list_delegates`, `create_send_as`, `verify_send_as`, `insert_smime_info`, `disable_cse_keypair`, `obliterate_cse_keypair`, `create_forwarding_address`, `update_auto_forwarding`, `send_email` como ferramenta crítica exigindo confirmação de envio.

## ✅ Critérios de Aceite
- E-mails listados e rascunhos criados no Gmail com sucesso.
