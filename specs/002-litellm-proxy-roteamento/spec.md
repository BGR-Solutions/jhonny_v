# Feature Specification: Configuração do LiteLLM Proxy e Roteamento de Modelos

**Feature Branch**: `[002-litellm-proxy-roteamento]`

**Created**: 2026-09-28

**Status**: Draft

**Input**: User description: "Configurar o contêiner do LiteLLM Proxy no Compose, permitindo desacoplar a escolha dos modelos (Ollama local e Provedores Cloud) do código das aplicações."

## Clarifications

### Session 2026-09-29

- Q: Quando as chaves dos provedores cloud (OpenAI/Anthropic) não estiverem definidas, o proxy deve subir mantendo apenas as rotas locais ativas? → A: Subir normalmente e expor apenas rotas locais; rotas cloud ficam indisponíveis.
- Q: A autenticação por chave mestre deve ser obrigatória também no endpoint de listagem de modelos (`/v1/models`)? → A: Exigir chave mestre em todos os endpoints do proxy, incluindo `/v1/models` e `/v1/chat/completions`.
- Q: Quando uma rota cloud estiver configurada, mas indisponível por ausência de credenciais, qual resultado o proxy deve retornar na chamada de chat? → A: Tratar como rota indisponível por configuração/credencial (503).
- Q: Quando uma rota cloud falhar em runtime (timeout/erro do provedor), o proxy deve tentar fallback automático para uma rota local equivalente? → A: Não, retornar erro da rota solicitada sem fallback automático.

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

- Quando a configuração de rota apontar para provedor indisponível em runtime, o proxy deve retornar erro da rota alvo sem fallback automático para rota local.
- Quando uma rota solicitada não existir na configuração ativa, o proxy deve retornar erro de rota inexistente distinto do erro `503` de indisponibilidade por credencial.
- Quando a chave mestre não estiver definida ou estiver inválida, os endpoints protegidos devem negar acesso de forma consistente.
- Quando uma rota cloud existir, mas não tiver credencial disponível, o proxy deve responder com indisponibilidade (`503`) para chamadas dessa rota.
- Quando ocorrer falha runtime em rota cloud (timeout/erro do provedor), o proxy deve preservar o erro da rota solicitada sem redirecionamento implícito.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O ambiente MUST disponibilizar um serviço dedicado de proxy de modelos que possa ser iniciado junto da infraestrutura local compartilhada.
- **FR-002**: O proxy MUST expor uma listagem de modelos configurados que permita à equipe verificar as rotas disponíveis.
- **FR-003**: A configuração do proxy MUST definir rotas para pelo menos um modelo local e modelos alternativos de provedores cloud, mantendo o consumo uniforme pelas aplicações.
- **FR-004**: O proxy MUST aceitar solicitações de chat para rotas válidas e retornar resposta de sucesso quando os pré-requisitos de autenticação e rota forem atendidos.
- **FR-005**: O controle de acesso ao proxy MUST depender de uma chave mestre definida por variável de ambiente, sem hardcode de credenciais no versionamento.
- **FR-006**: O projeto MUST incluir uma configuração versionada do proxy separada do código das aplicações, para permitir evolução de rotas sem alterações no domínio das apps.
- **FR-007**: A configuração inicial MUST manter aliases de rotas locais e cloud documentados com versionamento explícito de configuração para evitar quebra de contrato entre revisões.
- **FR-008**: Quando credenciais cloud não estiverem definidas, o proxy MUST iniciar com rotas locais disponíveis e marcar rotas cloud como indisponíveis sem interromper o ambiente local.
- **FR-009**: O proxy MUST exigir autenticação por chave mestre em todos os endpoints expostos, incluindo listagem de modelos e execução de chat.
- **FR-010**: Quando uma rota cloud estiver configurada, mas indisponível por ausência de credenciais, o proxy MUST retornar status de indisponibilidade (503) nas chamadas de chat para essa rota.
- **FR-011**: Quando uma rota cloud falhar em runtime por timeout ou erro do provedor, o proxy MUST retornar erro da rota solicitada sem fallback automático para rota local.
- **FR-012**: Quando uma rota solicitada não existir na configuração ativa, o proxy MUST retornar erro de rota inexistente distinto do erro `503` de indisponibilidade por credencial.

### Key Entities *(include if feature involves data)*

- **Serviço de Proxy de Modelos**: Representa o ponto único de acesso para listagem e execução de chamadas de modelos no ambiente local.
- **Rota de Modelo**: Representa um alias funcional consumido pelas aplicações e vinculado a um destino de provedor/modelo.
- **Credencial Mestre do Proxy**: Representa o segredo de autenticação necessário para autorizar chamadas ao proxy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em uma janela de 10 inicializações locais consecutivas com configuração válida, o endpoint de listagem de modelos do proxy fica disponível com sucesso em 100% dos casos (10/10).
- **SC-002**: Na mesma janela de 10 inicializações consecutivas, o tempo até a primeira resposta bem-sucedida de listagem de modelos permanece em até 30 segundos em pelo menos 90% dos casos (9/10).
- **SC-003**: Em uma janela de 10 chamadas consecutivas autenticadas para rota válida, pelo menos 90% das requisições (9/10) retornam sucesso no endpoint de chat do proxy.
- **SC-004**: Em 20 chamadas consecutivas sem credencial válida, 100% das requisições para endpoints protegidos do proxy são bloqueadas.
- **SC-005**: Em uma janela de 10 chamadas consecutivas sem credenciais cloud configuradas, 100% das requisições para rotas locais seguem funcionais e os endpoints de aceite permanecem operacionais.
- **SC-006**: Em 20 chamadas consecutivas com chave ausente ou inválida distribuídas entre `/v1/models` e `/v1/chat/completions`, 100% das requisições são rejeitadas.
- **SC-007**: Em 10 chamadas consecutivas para rota cloud sem credencial, 100% das respostas retornam `503`, mantendo distinção explícita de erro para rota inexistente.
- **SC-008**: Em falhas runtime de rotas cloud, o retorno preserva o erro da rota alvo sem redirecionamento automático para rota local.

## Assumptions

- O ambiente local já dispõe dos pré-requisitos para executar os serviços de infraestrutura compartilhados do projeto.
- Credenciais de provedores cloud serão fornecidas por variáveis de ambiente quando a equipe optar por validar rotas externas.
- Quando credenciais cloud não forem fornecidas, a validação de aceite seguirá com rotas locais sem bloquear a inicialização do proxy.
- A entrega atual cobre a configuração inicial e validação operacional do proxy, não incluindo ajustes de código nas aplicações consumidoras.
- A validação manual por cURL ou ferramenta equivalente é suficiente para comprovar o aceite desta issue.
