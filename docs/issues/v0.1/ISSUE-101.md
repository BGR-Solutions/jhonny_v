# 📌 Issue #101: Estrutura Base do Monorepo e Documentação Inicial

* **Milestone:** `v0.1 - Infra Core & Observabilidade`
* **Tipo:** Setup / Documentação
* **ADRs Vinculadas:** N/A

## 🎯 Descrição
Criar a estrutura física do Monorepo com a definição das pastas principais, arquivos de ambiente e documentação macro (`README.md` master e `docs/`).

## 📥 Tarefas
- [x] Criar diretórios `apps/`, `infra/`, `docs/` (`adr`, `issues`, `milestones`).
- [x] Criar arquivo `.env.example` central com parâmetros padronizados.
- [x] Criar `.gitignore` contemplando ambientes Python, Node e arquivos de estado do Docker.
- [x] Adicionar configuração base no `infra/compose.yaml`.
- [x] Adicionar serviços core no `infra/compose.core.yaml`.

## ✅ Critérios de Aceite
- Estrutura de diretórios criada e validada pelo git status.
- Documentação inicial totalmente renderizada e navegável no repositório.
- Serviços core rodando no Docker Compose.
