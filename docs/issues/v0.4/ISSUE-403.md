# 📌 Issue #403: Implementação de Handlers para Resumo de E-mail e Agenda

* **Milestone:** `v0.4 - Worker Assíncrono`
* **Tipo:** Feature / Worker Jobs
* **ADRs Vinculadas:** N/A

## 🎯 Descrição
Criar os processadores de tarefas em segundo plano para relatórios diários de compromissos e consolidação de e-mails.

## 📥 Tarefas
- [ ] Criar handler `daily_schedule_summary` (chamada ao MCP Calendar + sumarização LLM).
- [ ] Criar handler `unhandled_emails_digest` (busca e resumo de mensagens pendentes).
- [ ] Atualizar estado da task concluída no banco PostgreSQL.

## ✅ Critérios de Aceite
- Tarefas enfileiradas pelo orquestrador são processadas assincronamente pelo Worker registrando resultado final no banco.
