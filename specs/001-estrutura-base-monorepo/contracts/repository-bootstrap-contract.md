# Repository Bootstrap Contract

## Purpose

Definir o contrato visível para colaboradores da primeira entrega estrutural do monorepo: quais artefatos precisam existir, qual o papel de cada um e como validar a base local compartilhada.

## Top-Level Artifact Contract

| Path | Contract | Validation Expectation |
|------|----------|------------------------|
| `README.md` | Landing page do repositório com visão geral, mapa do monorepo, quickstart e links para `docs/` | O colaborador entende a estrutura principal sem abrir arquivos adicionais primeiro |
| `apps/` | Área reservada para aplicações do monorepo e seus placeholders iniciais | A árvore do repositório evidencia onde novas aplicações devem nascer |
| `infra/compose.yaml` | Ponto de entrada base da orquestração local, contendo definições compartilhadas | Pode ser combinado com `infra/compose.core.yaml` sem ambiguidade |
| `infra/compose.core.yaml` | Camada de serviços core compartilhados entre aplicações futuras | Os serviços core podem ser avaliados por `docker compose config` e inicializados em conjunto com a base |
| `.env.example` | Contrato central das variáveis de ambiente locais e dos placeholders de configuração | Um colaborador consegue gerar `.env` sem adivinhar nomes de variáveis |
| `.gitignore` | Política de exclusão para ambientes Python, Node.js e estados locais de containers | `git status` não deve incluir artefatos locais esperados após o bootstrap |
| `docs/README.md` | Índice secundário da documentação | Direciona o colaborador para ADRs, issues e milestones |
| `docs/adr/`, `docs/issues/`, `docs/milestones/` | Estruturas documentais navegáveis para decisões, backlog e roadmap | Cada diretório é descoberto a partir dos READMEs principais |

## Operational Contract

1. O colaborador deve conseguir copiar `/.env.example` para `/.env` e entender quais campos precisam de ajuste local.
2. O colaborador deve conseguir validar a configuração combinada com `docker compose -f infra/compose.yaml -f infra/compose.core.yaml config`.
3. O colaborador deve conseguir subir a stack compartilhada com `docker compose -f infra/compose.yaml -f infra/compose.core.yaml up -d`.
4. O colaborador deve conseguir confirmar, por `git status`, que a política de ignore cobre os artefatos gerados pelo ambiente local.

## Scope Boundaries

- Este contrato cobre apenas a base estrutural e operacional inicial do monorepo.
- APIs de aplicação, contratos de mensageria e observabilidade detalhada ficam para issues posteriores.
- O contrato não autoriza versionar segredos reais; apenas placeholders e defaults não sensíveis são permitidos.
