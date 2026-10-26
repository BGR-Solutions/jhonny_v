# 0005. Utilização do PostgreSQL com pgvector para Checkpoints e Vetores

* **Status:** Aceito
* **Data:** 2026-08-08
* **Autores:** Equipe jhonny-core ([@cesarsuchoj](https://github.com/cesarsuchoj))
* **Issues Relacionadas:** `#106`, `#306`

---

## Contexto e Problema
O assistente requer persistência de longo prazo para históricos e estado de sessões por `thread_id`, incluindo ações aguardando aprovação. Além disso, evoluções futuras do sistema demandarão a capacidade de realizar buscas semânticas (RAG) sobre arquivos e dados do usuário[cite: 230].

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
Adotar o **PostgreSQL** com a extensão **`pgvector`** ativada como solução de persistência relacional e armazenamento vetorial do projeto **`jhonny-v`**. A integração de sessões/estado do OpenJarvis com esse backend precisa ser homologada, sem presumir schemas LangGraph.

**Revisão de 2026-10-25:** a [ADR-0006](./0006-openjarvis-compose.md) remove a imposição de `PostgresSaver` e `langgraph-checkpoint-postgres`. As opções acima preservam a análise original, não comprovam compatibilidade do OpenJarvis. A [issue #306](../issues/v0.3/ISSUE-306.md) deve validar backend, inicialização, migrações e retomada após reinício; incompatibilidades exigem decisão arquitetural antes de mudar a persistência planejada.

---

## Consequências

### Positivas
* **Flexibilidade Dev/Cloud:** Facilidade de migração do contêiner local para o Supabase apenas alterando o `.env`[cite: 228, 234].
* **Unificação de Storage:** Dados estruturados de sessões e embeddings armazenados em uma única engine de banco[cite: 230].
* **Robustez Relacional:** transações ACID e suporte a gravações concorrentes; a integração do motor externo permanece sujeita a homologação.

### Negativas / Mitigações
* **Uso de Recursos:** Consumo contínuo de RAM do contêiner PostgreSQL. *Mitigação:* Mapeamento de limites de recursos no Compose e ajustes de memória no `postgresql.conf`.
