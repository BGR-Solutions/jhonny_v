# 📌 Issue #306: Persistência de Checkpoints com `PostgresSaver`

* **Milestone:** `v0.3 - Agent Orchestrator`
* **Tipo:** Banco de Dados / Persistência
* **ADRs Vinculadas:** [`ADR-0005: Utilização do PostgreSQL com pgvector`](../../adr/0005-database-postgresql-pgvector.md)

## 🎯 Descrição
Configurar o `PostgresSaver` (`langgraph-checkpoint-postgres`) para gravar automaticamente todos os estados do grafo e históricos de conversas por `thread_id`.

## 📥 Tarefas
- [ ] Integrar biblioteca `langgraph-checkpoint-postgres` no orquestrador.
- [ ] Configurar conexão com o PostgreSQL do Compose usando `DATABASE_URL`.
- [ ] Executar migrations automáticas na startup da aplicação para criação das tabelas de checkpoints.

## ✅ Critérios de Aceite
- As conversas e estados do agente sobrevivem ao reinício completo do contêiner do orquestrador.
