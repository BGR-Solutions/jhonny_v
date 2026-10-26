# Data Model: Configuração do LiteLLM Proxy e Roteamento de Modelos

## Entity: LiteLLM Proxy Service

- **Description**: Serviço de borda para descoberta e execução de modelos por contrato unificado.
- **Fields**:
  - `service_name`: identificador do serviço no Compose
  - `listen_port`: porta de exposição local
  - `auth_policy`: política de autenticação aplicada aos endpoints
  - `config_source`: caminho do arquivo versionado de configuração
- **Relationships**:
  - Possui múltiplas `Model Route`
  - Consome `Master Key Credential`
- **Validation Rules**:
  - Deve iniciar com configuração válida mesmo sem credenciais cloud
  - Deve exigir autenticação em endpoints de listagem e chat
  - Deve avaliar autenticação antes de qualquer decisão de roteamento

## Entity: Model Route

- **Description**: Alias consumível pelas aplicações para mapear chamadas a um modelo/provedor específico.
- **Fields**:
  - `route_name`: nome lógico da rota
  - `alias_format_rule`: regra de formato do alias aceito
  - `provider_type`: local ou cloud
  - `target_model`: identificador do modelo no provedor
  - `availability_state`: ativa, indisponível_por_credencial, erro_runtime
- **Relationships**:
  - Pertence a `LiteLLM Proxy Service`
  - Pode depender de `Provider Credential`
- **Validation Rules**:
  - Rotas locais devem permanecer ativas sem dependência de credenciais cloud
  - Rota cloud sem credencial deve responder indisponibilidade (`503`) quando invocada
  - Alias malformado ou não suportado deve retornar erro de requisição inválida

## Entity: Master Key Credential

- **Description**: Segredo único para autorização de acesso ao proxy.
- **Fields**:
  - `env_var_name`: nome da variável de ambiente da chave mestre
  - `required_endpoints`: lista de endpoints protegidos
  - `status`: definida ou ausente
  - `ownership`: área responsável pelo ciclo de vida
- **Relationships**:
  - Aplica-se a `LiteLLM Proxy Service`
- **Validation Rules**:
  - Deve ser exigida em `/v1/models` e `/v1/chat/completions`
  - Credencial inválida deve resultar em negação consistente de acesso
  - Chave ausente/malformada/inválida deve ter semântica explícita (`401`/`403`)

## Entity: Provider Credential

- **Description**: Credencial de integração para provedores cloud externos.
- **Fields**:
  - `provider_name`: identificador do provedor cloud
  - `env_var_name`: variável de ambiente esperada
  - `credential_state`: presente ou ausente
  - `ownership`: área responsável por provisionamento/rotação/revogação
- **Relationships**:
  - Habilita `Model Route` do tipo cloud
- **Validation Rules**:
  - Ausência de credencial não pode impedir startup do proxy
  - Rotas dependentes devem ser sinalizadas como indisponíveis
  - Falha transitória do provedor não deve alterar configuração de rota de forma manual

## Entity: Route Error Policy

- **Description**: Contrato de resposta para cenários negativos de roteamento.
- **Fields**:
  - `auth_missing_status`: código para autenticação ausente/malformada
  - `auth_invalid_status`: código para credencial inválida
  - `invalid_alias_status`: código para alias/payload inválido
  - `missing_route_status`: código para rota não existente
  - `missing_credential_status`: código para rota existente sem credencial
  - `runtime_failure_behavior`: política para erro de provedor
  - `precedence_order`: ordem determinística de avaliação de falhas
  - `fallback_mode`: habilitado ou desabilitado
- **Relationships**:
  - Aplica-se a `Model Route`
- **Validation Rules**:
  - `auth_missing_status` deve ser `401` e `auth_invalid_status` deve ser `403`
  - `invalid_alias_status` deve ser distinto de `404` e `503`
  - `missing_credential_status` deve ser `503`
  - `precedence_order` deve ser: auth → payload/alias → existência de rota → credencial → runtime
  - `fallback_mode` deve permanecer desabilitado nesta feature
