# 📌 Issue #106: Provisionamento do PostgreSQL + pgvector

* **Milestone:** `v0.1 - Infra Core & Observabilidade`
* **Tipo:** Banco de Dados
* **ADRs Vinculadas:** [`ADR-0005: Utilização do PostgreSQL com pgvector para Checkpoints e Vetores`](../../adr/0005-database-postgresql-pgvector.md)

## 🎯 Descrição
Provisionar o contêiner do PostgreSQL 16 com a extensão `pgvector` para persistência de checkpoints do LangGraph e armazenamento de embeddings. A inicialização é automática, idempotente e validada por um profile isolado da issue.

## 📥 Tarefas
- [ ] Adicionar serviço `postgres` utilizando a imagem `pgvector/pgvector:pg16` no Compose.
- [ ] Configurar volume persistente `pgdata`.
- [ ] Criar script de inicialização SQL em `infra/postgres/init.sql` garantindo a execução de `CREATE EXTENSION IF NOT EXISTS vector;`.
- [ ] Montar o script em `/docker-entrypoint-initdb.d/10-pgvector.sql` como somente leitura.
- [ ] Configurar healthcheck com `pg_isready` no Compose.
- [ ] Adicionar o profile isolado `issue-106`.
- [ ] Validar em CI a extensão, operações vetoriais e persistência após reinício.

## ✅ Critérios de Aceite
- PostgreSQL operacional e saudável na porta `5432`.
- Profile `issue-106` inicia somente o serviço `postgres`.
- Extensão `vector` criada automaticamente no banco configurado.
- Coluna `vector(3)` aceita inserção e cálculo de distância vetorial.
- Dados permanecem disponíveis após reinício do contêiner por meio do volume `pgdata`.
- Job `validate-issue-106` executável localmente com `act pull_request -j validate-issue-106`.
