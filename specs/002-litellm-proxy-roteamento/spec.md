# Feature Specification: Configuração do LiteLLM Proxy e Roteamento de Modelos

**Feature Branch**: `[002-litellm-proxy-roteamento]`

**Created**: 2026-09-28

**Status**: Draft

**Input**: User description: "Configurar o contêiner do LiteLLM Proxy no Compose, permitindo desacoplar a escolha dos modelos (Ollama local e Provedores Cloud) do código das aplicações."

## Clarifications

### Session 2026-09-29

- Q: Quando as chaves dos provedores cloud (OpenAI/Anthropic) não estiverem definidas, o proxy deve subir mantendo apenas as rotas locais ativas? → A: Subir normalmente e expor apenas rotas locais; rotas cloud ficam indisponíveis.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Disponibilizar o proxy de modelos no ambiente local (Priority: P1)

Como integrante da equipe, quero iniciar o proxy de modelos no ambiente compartilhado para que as aplicações tenham um ponto único de acesso aos modelos sem configuração manual adicional.

**Why this priority**: Sem o proxy disponível, não existe desacoplamento entre aplicações e provedores de modelo, bloqueando a adoção do padrão proposto.

**Independent Test**: Pode ser testada de forma independente iniciando o ambiente local e validando que o endpoint de listagem de modelos responde com sucesso e retorna os modelos esperados.

**Acceptance Scenarios**:

1. **Given** o ambiente local configurado, **When** o proxy é iniciado, **Then** um endpoint de listagem de modelos responde com sucesso.
2. **Given** o proxy em execução, **When** um integrante consulta os modelos disponíveis, **Then** a resposta inclui os modelos roteados previstos para uso local e alternativo.

---

### User Story 2 - Consumir modelos sem alterar código da aplicação (Priority: P2)

Como desenvolvedor de aplicações do monorepo, quero selecionar modelos por meio de rotas do proxy para alternar entre execução local e provedores cloud sem mudanças no código de negócio.

**Why this priority**: O principal valor da entrega é separar a decisão de provedor/modelo da implementação das aplicações.

**Independent Test**: Pode ser testada enviando uma solicitação de chat para o proxy e confirmando que a chamada é aceita para uma rota configurada, sem exigir ajuste no cliente além do endpoint do proxy.

**Acceptance Scenarios**:

1. **Given** rotas de modelos configuradas no proxy, **When** uma chamada de chat é enviada para uma rota válida, **Then** o proxy processa a solicitação com resposta de sucesso.
2. **Given** múltiplas rotas configuradas, **When** a equipe alterna a rota alvo da solicitação, **Then** a integração continua funcional sem mudanças no código de domínio da aplicação.

---

### User Story 3 - Proteger acesso ao proxy por chave mestre (Priority: P3)

Como responsável por operação do ambiente, quero controlar o acesso ao proxy por chave mestre para evitar uso não autorizado dos modelos configurados.

**Why this priority**: A proteção por credencial reduz risco de uso indevido e prepara o ambiente para evolução com provedores externos.

**Independent Test**: Pode ser testada validando que chamadas autenticadas funcionam e chamadas sem credencial válida são rejeitadas.

**Acceptance Scenarios**:

1. **Given** a chave mestre configurada no ambiente, **When** uma solicitação autenticada é enviada ao proxy, **Then** a solicitação é processada normalmente.
2. **Given** uma solicitação sem autenticação válida, **When** ela é enviada ao proxy, **Then** o acesso é negado.

---

### Edge Cases

- Como o sistema deve se comportar quando a configuração de rota aponta para um provedor indisponível?
- Como o proxy deve responder quando uma rota solicitada não existe na configuração ativa?
- Como garantir comportamento previsível quando a chave mestre não estiver definida no ambiente?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O ambiente MUST disponibilizar um serviço dedicado de proxy de modelos que possa ser iniciado junto da infraestrutura local compartilhada.
- **FR-002**: O proxy MUST expor uma listagem de modelos configurados que permita à equipe verificar as rotas disponíveis.
- **FR-003**: A configuração do proxy MUST definir rotas para pelo menos um modelo local e modelos alternativos de provedores cloud, mantendo o consumo uniforme pelas aplicações.
- **FR-004**: O proxy MUST aceitar solicitações de chat para rotas válidas e retornar resposta de sucesso quando os pré-requisitos de autenticação e rota forem atendidos.
- **FR-005**: O controle de acesso ao proxy MUST depender de uma chave mestre definida por variável de ambiente, sem hardcode de credenciais no versionamento.
- **FR-006**: O projeto MUST incluir uma configuração versionada do proxy separada do código das aplicações, para permitir evolução de rotas sem alterações no domínio das apps.
- **FR-007**: A configuração inicial MUST contemplar rotas para execução local e alternativas cloud em uma única fonte de configuração.
- **FR-008**: Quando credenciais cloud não estiverem definidas, o proxy MUST iniciar com rotas locais disponíveis e marcar rotas cloud como indisponíveis sem interromper o ambiente local.

### Key Entities *(include if feature involves data)*

- **Serviço de Proxy de Modelos**: Representa o ponto único de acesso para listagem e execução de chamadas de modelos no ambiente local.
- **Rota de Modelo**: Representa um alias funcional consumido pelas aplicações e vinculado a um destino de provedor/modelo.
- **Credencial Mestre do Proxy**: Representa o segredo de autenticação necessário para autorizar chamadas ao proxy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das inicializações locais do ambiente, com configuração válida, disponibilizam com sucesso o endpoint de listagem de modelos do proxy.
- **SC-002**: A equipe consegue listar os modelos configurados no proxy em até 30 segundos após a inicialização do serviço.
- **SC-003**: A equipe consegue executar com sucesso uma chamada de chat para uma rota válida do proxy durante a validação da entrega.
- **SC-004**: Chamadas sem credencial válida são bloqueadas de forma consistente durante os testes de acesso ao proxy.
- **SC-005**: Em ausência de credenciais cloud, o ambiente local mantém disponibilidade de rotas locais e permanece operacional para validação dos endpoints de aceite.

## Assumptions

- O ambiente local já dispõe dos pré-requisitos para executar os serviços de infraestrutura compartilhados do projeto.
- Credenciais de provedores cloud serão fornecidas por variáveis de ambiente quando a equipe optar por validar rotas externas.
- Quando credenciais cloud não forem fornecidas, a validação de aceite seguirá com rotas locais sem bloquear a inicialização do proxy.
- A entrega atual cobre a configuração inicial e validação operacional do proxy, não incluindo ajustes de código nas aplicações consumidoras.
- A validação manual por cURL ou ferramenta equivalente é suficiente para comprovar o aceite desta issue.
