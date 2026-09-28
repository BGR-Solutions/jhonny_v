# Quickstart: Estrutura Base do Monorepo e Documentação Inicial

## Purpose

Validar ponta a ponta que a base do monorepo ficou navegável, configurável e pronta para iniciar os serviços core planejados.

Consulte também:
- [Repository Bootstrap Contract](./contracts/repository-bootstrap-contract.md)
- [Data Model](./data-model.md)

## Prerequisites

- Repositório clonado localmente
- Git instalado
- Docker Compose disponível no ambiente
- Permissão para criar um arquivo local `.env` a partir de `.env.example`

## Setup

1. Abrir o `README.md` na raiz do repositório.
2. Copiar `.env.example` para `.env` na raiz do projeto.
3. Revisar `docs/README.md` para confirmar os caminhos de documentação.

## Validation Scenarios

### Scenario 1: Navegação inicial do repositório

1. Abrir `README.md`.
2. Confirmar que o documento descreve `apps/`, `infra/` e `docs/`.
3. Seguir os links para `docs/README.md`, ADRs, issues e milestones.

**Expected outcome**: Um novo colaborador entende a estrutura do monorepo e consegue chegar aos índices documentais corretos sem procurar manualmente pela árvore inteira.

### Scenario 2: Contrato de ambiente compartilhado

1. Abrir `.env.example`.
2. Confirmar que as variáveis estão agrupadas por contexto operacional.
3. Criar `.env` com ajustes locais mínimos.

**Expected outcome**: O contrato de configuração local fica explícito e nenhum segredo real vem versionado.

### Scenario 3: Validação da composição local

1. Executar `docker compose -f infra/compose.yml -f infra/compose.core.yml config`.
2. Revisar a composição gerada para redes, volumes e serviços core.

**Expected outcome**: A combinação dos arquivos Compose é válida e reflete a separação entre base compartilhada e serviços core.

### Scenario 4: Inicialização dos serviços core

1. Executar `docker compose -f infra/compose.yml -f infra/compose.core.yml up -d`.
2. Aguardar a criação dos serviços definidos como core.
3. Revisar `docker compose ps` para confirmar o estado dos containers.

**Expected outcome**: Os serviços core planejados iniciam a partir apenas dos artefatos versionados e do `.env` local.

### Scenario 5: Higiene do repositório

1. Após a validação local, executar `git status --short`.
2. Confirmar que somente alterações intencionais permanecem rastreáveis.

**Expected outcome**: Arquivos transitórios de Python, Node.js, containers e ambiente local não poluem o status do repositório.
