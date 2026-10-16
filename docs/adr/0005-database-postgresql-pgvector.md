# 0005. Utilização do PostgreSQL com pgvector para Checkpoints e Vetores

* **Status:** Aceito
* **Data:** 2026-08-08
* **Autores:** Equipe jhonny-core ([@cesarsuchoj](https://github.com/cesarsuchoj))
* **Issues Relacionadas:** `#106`, `#306`

---

## Contexto e Problema
O assistente requer persistência de longo prazo para os históricos e checkpoints do LangGraph por `thread_id`[cite: 209, 231, 238]. Além disso, evoluções futuras do sistema demandarão a capacidade de realizar buscas semânticas (RAG) sobre arquivos e dados do usuário[cite: 230].

---

## Opções Consideradas

1. **SQLite Local (`langgraph-checkpoint-sqlite`):**
   * *Prós:* Arquivo único em disco, sem necessidade de contêiner ou consumo de memória adicional[cite: 215].
   * *Contras:* Limitação para concorrência de escrita; falta de suporte nativo a buscas vetoriais eficientes[cite: 230, 232].

2. **Bancos Vetoriais Dedicados (Qdrant / Chroma) + Banco Relacional Separado:**
   * *Prós:* Alta especialização para busca por vetores.
   * *Contras:* Operação de múltiplos contêineres de banco de dados aumentando a complexidade e o uso de recursos de hardware[cite: 230].

3. **PostgreSQL com Extensão `pgvector`:**
   * *Prós:* Suporte nativo e oficial via `langgraph-checkpoint-postgres` (`PostgresSaver`) [cite: 231, 238]; capacidade de realizar busca relacional e vetorial no mesmo banco [cite: 230]; total paridade entre o contêiner local e serviços gerenciados na nuvem como Supabase ou AWS RDS (bastando alterar a `DATABASE_URL`)[cite: 228, 234].
   * *Contras:* Requer gerenciamento de contêiner e volume persistente no Docker Compose[cite: 232].

---

## Decisão
Adotar o **PostgreSQL** com a extensão **`pgvector`** ativada como solução unificada de persistência relacional (checkpoints do LangGraph) e armazenamento vetorial do projeto **`jhonny-v`**[cite: 9, 10, 230, 238].

---

## Consequências

### Positivas
* **Flexibilidade Dev/Cloud:** Facilidade de migração do contêiner local para o Supabase apenas alterando o `.env`[cite: 228, 234].
* **Unificação de Storage:** Dados estruturados de sessões e embeddings armazenados em uma única engine de banco[cite: 230].
* **Robustez no LangGraph:** Suporte total a transações ACID e gravações concorrentes de checkpoints[cite: 231, 232].

### Negativas / Mitigações
* **Uso de Recursos:** Consumo contínuo de RAM do contêiner PostgreSQL. *Mitigação:* Mapeamento de limites de recursos no Compose e ajustes de memória no `postgresql.conf`.
