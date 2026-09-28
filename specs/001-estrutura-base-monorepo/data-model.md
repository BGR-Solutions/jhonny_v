# Data Model: Estrutura Base do Monorepo e Documentação Inicial

## Entity: Monorepo Bootstrap

- **Description**: Representa a base compartilhada do repositório, responsável por expor a estrutura física, a documentação de entrada e os artefatos operacionais mínimos.
- **Fields**:
  - `root_readme`: ponto de entrada documental do repositório
  - `apps_directory`: área reservada às aplicações do monorepo
  - `infra_directory`: área reservada à infraestrutura compartilhada
  - `docs_directory`: hub navegável de documentação
  - `env_template`: contrato central de variáveis de ambiente
  - `ignore_policy`: conjunto de regras para arquivos locais/gerados
- **Relationships**:
  - Agrega múltiplas entidades do tipo `Repository Area`
  - Depende de uma entidade `Compose Layer` para validação operacional local
- **Validation Rules**:
  - Deve conter referências claras às três áreas principais do monorepo
  - Deve incluir documentação suficiente para onboarding inicial

## Entity: Repository Area

- **Description**: Define uma área principal do monorepo e sua finalidade organizacional.
- **Fields**:
  - `name`: identificador da área (`apps`, `infra`, `docs`)
  - `purpose`: objetivo da área dentro do monorepo
  - `expected_contents`: tipos de artefatos que a área deve conter
  - `navigation_entry`: arquivo ou índice usado para descoberta do conteúdo
- **Relationships**:
  - Pertence a `Monorepo Bootstrap`
  - Pode conter múltiplos `Documentation Index` ou `Application Placeholder`
- **Validation Rules**:
  - Cada área deve ter finalidade única e não sobreposta
  - A descoberta de cada área deve ser possível a partir do README principal

## Entity: Environment Template Group

- **Description**: Agrupa variáveis de ambiente por domínio operacional.
- **Fields**:
  - `group_name`: nome da seção (global, core services, observabilidade, integrações futuras)
  - `variables`: lista de nomes padronizados
  - `secret_policy`: regra de preenchimento (placeholder apenas ou valor padrão não sensível)
  - `consumers`: quais áreas ou serviços reutilizam o grupo
- **Relationships**:
  - Pertence a `Monorepo Bootstrap`
  - É referenciado por `Core Service Definition`
- **Validation Rules**:
  - Nenhuma variável secreta pode conter valor real versionado
  - Nomes devem seguir convenção consistente e descritiva

## Entity: Compose Layer

- **Description**: Representa um arquivo Compose e sua responsabilidade na orquestração local.
- **Fields**:
  - `file_name`: nome do arquivo (`compose.yml` ou `compose.core.yml`)
  - `role`: responsabilidade do arquivo (base compartilhada ou serviços core)
  - `invocation_order`: ordem esperada na execução combinada
  - `shared_resources`: redes, volumes ou defaults definidos pela camada
- **Relationships**:
  - Pertence à área `infra`
  - Pode agrupar múltiplas entidades `Core Service Definition`
- **Validation Rules**:
  - `compose.yml` deve ser o ponto de entrada base
  - `compose.core.yml` deve complementar, não substituir, a camada base

## Entity: Core Service Definition

- **Description**: Descreve um serviço central compartilhado entre futuras aplicações do monorepo.
- **Fields**:
  - `service_name`: identificador do serviço
  - `category`: banco de dados, cache ou mensageria
  - `purpose`: capacidade compartilhada fornecida ao ecossistema local
  - `configuration_sources`: grupos de variáveis de ambiente necessários
  - `persistence_requirement`: necessidade de volume persistente ou estado descartável
- **Relationships**:
  - É definido dentro de `Compose Layer`
  - Consome `Environment Template Group`
- **Validation Rules**:
  - Deve ser reutilizável por mais de uma aplicação futura
  - Deve poder ser inicializado sem arquivos locais adicionais além de `.env`

## Entity: Documentation Index

- **Description**: Índice navegável que direciona o colaborador para a área correta da documentação.
- **Fields**:
  - `location`: caminho do índice (`README.md` ou `docs/README.md`)
  - `audience`: público primário (novo colaborador, mantenedor, equipe técnica)
  - `linked_sections`: áreas e páginas referenciadas
  - `onboarding_goal`: decisão ou ação que o índice ajuda a destravar
- **Relationships**:
  - Pertence a `Monorepo Bootstrap`
  - Referencia múltiplas `Repository Area`
- **Validation Rules**:
  - Deve evitar links órfãos ou sem contexto
  - Deve tornar explícita a finalidade de ADRs, issues e milestones
