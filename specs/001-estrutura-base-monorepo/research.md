# Research: Estrutura Base do Monorepo e Documentação Inicial

## Decision 1: Topologia raiz do monorepo

- **Decision**: Estruturar o repositório com `apps/`, `infra/` e `docs/` na raiz, mantendo `docs/` como hub de navegação e antecipando subdiretórios de aplicações previstos no roadmap.
- **Rationale**: Essa divisão espelha diretamente os requisitos da issue e evita ambiguidade entre código de aplicação, infraestrutura compartilhada e documentação. Também reduz retrabalho nas próximas issues, que já projetam aplicações separadas para `mcp-server`, `agent-orchestrator` e `worker`.
- **Alternatives considered**:
  - Adicionar `packages/` ou `libs/` já nesta issue — rejeitado por falta de necessidade imediata.
  - Concentrar tudo em `docs/` até existirem apps reais — rejeitado porque não resolve a estrutura física pedida pela issue.

## Decision 2: Contrato do `.env.example`

- **Decision**: Usar um `.env.example` central na raiz com seções agrupadas por contexto: bootstrap global, serviços core, portas/URLs locais, observabilidade e placeholders para integrações futuras.
- **Rationale**: Um único arquivo de referência simplifica onboarding e deixa explícito quais parâmetros fazem parte do contrato operacional comum do monorepo. Segredos devem aparecer apenas como placeholders vazios ou valores sentinela, nunca como dados reais.
- **Alternatives considered**:
  - Arquivos de ambiente separados por serviço já na base — rejeitado por aumentar a complexidade antes da existência de múltiplos módulos implementados.
  - Não criar placeholders para serviços futuros — rejeitado porque reduz a utilidade do arquivo como referência central para expansão do monorepo.

## Decision 3: Estratégia de ignore multi-ecossistema

- **Decision**: Manter a cobertura atual para Python e estados de containers, adicionando regras explícitas para Node.js, workspaces e caches locais, preservando `.env.example` como arquivo rastreado.
- **Rationale**: A issue exige suporte simultâneo a Python, Node e Docker. Complementar a política atual evita ruído no `git status` e prepara o repositório para apps heterogêneas sem alterar o comportamento esperado para o ecossistema Python já contemplado.
- **Alternatives considered**:
  - Substituir o `.gitignore` atual por um template novo — rejeitado para evitar perda de regras úteis já presentes.
  - Ignorar todos os arquivos `.env*` sem exceções — rejeitado porque esconderia o próprio contrato `.env.example`.

## Decision 4: Modelo de Docker Compose em camadas

- **Decision**: Definir `infra/compose.yaml` como arquivo base e `infra/compose.core.yaml` como overlay obrigatório dos serviços centrais, com execução prevista via `docker compose -f infra/compose.yaml -f infra/compose.core.yaml up -d`.
- **Rationale**: Esse modelo separa configuração compartilhada (nome do projeto, redes, volumes, defaults) da definição efetiva dos serviços core, o que torna a base extensível para overlays futuros sem acoplar tudo a um único arquivo. Também facilita validação por `docker compose config` usando a mesma ordem de arquivos.
- **Alternatives considered**:
  - Concentrar tudo em um único `compose.yaml` — rejeitado por conflitar com a exigência explícita de um arquivo dedicado aos serviços core.
  - Usar `include` já nesta etapa — rejeitado por ser mais complexo do que o necessário para o bootstrap inicial.

## Decision 5: Escopo dos serviços core

- **Decision**: Planejar `compose.core.yaml` para conter apenas os serviços compartilhados de base local do ecossistema — banco de dados, cache e mensageria — deixando LLM proxy, observabilidade e outras stacks especializadas para arquivos e issues futuras.
- **Rationale**: A milestone já separa esses temas em entregas independentes. Limitar o escopo dos serviços core evita inflar a primeira configuração operacional do monorepo e preserva clareza sobre o que toda aplicação futura poderá reutilizar.
- **Alternatives considered**:
  - Incluir observabilidade e serviços de IA já no core — rejeitado para manter a issue pequena e coerente com o roadmap.
  - Não definir nenhum serviço core concreto nesta fase — rejeitado porque a issue exige que os serviços core possam rodar no Docker Compose.

## Decision 6: Navegação documental

- **Decision**: Transformar `README.md` na landing page do repositório, com visão geral, mapa do monorepo, quickstart operacional e links para `docs/README.md`, ADRs, issues e milestones.
- **Rationale**: O `docs/README.md` já atua como índice secundário; a página principal precisa complementar isso com contexto inicial para novos colaboradores. Essa combinação atende ao critério de documentação renderizada e navegável.
- **Alternatives considered**:
  - Deixar o README principal minimalista e transferir todo onboarding para `docs/` — rejeitado porque dificultaria a descoberta inicial.
  - Duplicar integralmente o conteúdo entre README raiz e `docs/README.md` — rejeitado por gerar manutenção desnecessária.
