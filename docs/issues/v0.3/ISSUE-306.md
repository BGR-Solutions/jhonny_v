# 📌 Issue #306: Persistência de Sessões e Estado do OpenJarvis

* **Milestone:** `v0.3 - OpenJarvis`
* **Tipo:** Banco de Dados / Persistência
* **ADRs Vinculadas:** [`ADR-0005: Utilização do PostgreSQL com pgvector`](../../adr/0005-database-postgresql-pgvector.md)

## 🎯 Descrição
Configurar o mecanismo de persistência suportado pela imagem do OpenJarvis para preservar histórico, sessões por `thread_id` e aprovações pendentes. A [ADR-0006](../../adr/0006-openjarvis-compose.md) remove a imposição de `PostgresSaver`, sem remover o requisito de durabilidade.

## 📥 Tarefas
- [ ] Identificar backend, schema e procedimentos de inicialização/migração oficialmente suportados pela versão escolhida.
- [ ] Homologar a integração com PostgreSQL; eventual incompatibilidade exige decisão arquitetural antes de adotar outro backend, sem alterar o banco compartilhado silenciosamente.
- [ ] Declarar configurações de persistência em `infra/openjarvis/` e mounts/volumes nomeados no Compose; credenciais ficam em `.env` ou secret manager.
- [ ] Testar histórico, isolamento de sessões e pausa/retomada de aprovações após reinício.
- [ ] Documentar backup, restauração e atualização de versão sem presumir compatibilidade com tabelas LangGraph.

## ✅ Critérios de Aceite
- Conversas e estado pendente sobrevivem ao reinício completo do contêiner do OpenJarvis.
- Uma sessão pode ser retomada pelo mesmo `thread_id` sem perder contexto ou executar novamente uma ação rejeitada.
