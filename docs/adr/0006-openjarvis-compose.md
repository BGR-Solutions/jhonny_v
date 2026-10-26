# 0006. Orquestração com OpenJarvis via imagem Docker

* **Status:** Aceito para planejamento; integração e homologação pendentes
* **Data:** 2026-10-25
* **Issues Relacionadas:** `#301` a `#306`, `#402`, `#501` a `#504`
* **Decisões relacionadas:** [ADR-0001](./0001-litellm-proxy-abstraction.md), [ADR-0002](./0002-human-in-the-loop-langgraph.md), [ADR-0003](./0003-opentelemetry-sampling-tracing.md), [ADR-0004](./0004-async-task-messaging-queue.md), [ADR-0005](./0005-database-postgresql-pgvector.md)

## Contexto e Problema

O planejamento anterior previa desenvolver uma aplicação própria em `apps/agent-orchestrator`, baseada em LangGraph. A nova direção é utilizar uma imagem Docker do OpenJarvis como motor de orquestração, reduzindo código próprio sem alterar intencionalmente a experiência nem os contratos funcionais do projeto.

## Opções Consideradas

1. **Manter o orquestrador próprio:** exige desenvolver e manter o motor de decisão e sua infraestrutura de aplicação.
2. **Integrar o OpenJarvis por imagem Docker:** reutiliza o motor externo e concentra a operação em Compose e arquivos de configuração. Exige homologar os contratos antes de substituir o componente anterior.

## Decisão e Escopo

- Planejar o OpenJarvis como serviço `openjarvis`, definido por `image` em `infra/compose.core.yaml`, combinado com a base `infra/compose.yaml`. Não criar um novo app Python nem assumir um build local do OpenJarvis.
- Reservar conceitualmente `infra/openjarvis/` para configurações versionadas sem segredos, seguindo o padrão de serviços como `infra/litellm/`. A pasta ainda não será criada nesta revisão.
- Manter MCP Server e Worker como aplicações próprias em `apps/`, e LiteLLM como gateway exclusivo de modelos no overlay `infra/compose.llm.yaml`.
- Preservar os nomes dos documentos, links e números das issues. O placeholder `apps/agent-orchestrator/` permanece fisicamente no repositório, identificado como legado; sua remoção ou migração fica para uma entrega posterior.
- Limitar esta entrega a Markdown: sem alterações em Compose, variáveis de ambiente, código, dependências ou estrutura de diretórios. Os comandos atuais do quickstart não passam a iniciar o OpenJarvis por esta revisão.

## Esclarecimentos e Contratos a Preservar

OpenJarvis é a escolha do motor, não evidência de compatibilidade já verificada. Repositório de origem, registro da imagem, versão ou digest, licença, portas, comandos, caminhos internos e opções de configuração serão identificados e homologados na [issue #301](../issues/v0.3/ISSUE-301.md); não há referência de imagem executável definida nesta decisão.

Os seguintes comportamentos continuam obrigatórios:

- descoberta e execução de ferramentas do MCP Server;
- chamadas de modelos exclusivamente pelo LiteLLM, preservando aliases e autenticação;
- aprovação ou rejeição explícita antes de ações sensíveis, sem execução em caso de rejeição;
- continuidade de sessões por `thread_id`, histórico e estado pendente após reinício;
- API compatível com OpenAI, incluindo `/v1/chat/completions` e streaming SSE para os clientes;
- despacho assíncrono de tarefas para RabbitMQ/Worker com o contrato `TaskEnvelope`;
- logs JSON em `stdout`/`stderr`, propagação de `trace_id` e `span_id` e integração à stack LGTMP.

LangGraph, `StateGraph`, `interrupt_before` e `PostgresSaver` deixam de ser imposições de implementação do projeto. PostgreSQL/pgvector continua como infraestrutura planejada; o mecanismo de persistência efetivamente suportado pela imagem precisa ser validado sem presumir compatibilidade de schema.

Qualquer lacuna nesses contratos bloqueia a homologação. Deve ser registrada para decisão arquitetural sobre configuração, integração mínima ou revisão explícita do contrato; não autoriza omitir funcionalidades nem reintroduzir silenciosamente o orquestrador próprio.

## Plano e Ordem de Execução Futura

Preservar a sequência bottom-up: v0.1 infraestrutura, v0.2 MCP Server, v0.3 integração do OpenJarvis, v0.4 Worker e v0.5 clientes. A definição no Compose core não antecipa a aprovação funcional da v0.3.

1. [#301](../issues/v0.3/ISSUE-301.md): identificar a distribuição, fixar a imagem e planejar configuração, segurança, saúde e telemetria.
2. [#302](../issues/v0.3/ISSUE-302.md) e [#303](../issues/v0.3/ISSUE-303.md): integrar MCP e LiteLLM e validar o ciclo de decisão.
3. [#304](../issues/v0.3/ISSUE-304.md) e [#306](../issues/v0.3/ISSUE-306.md): homologar aprovações e persistência, incluindo retomada após reinício.
4. [#305](../issues/v0.3/ISSUE-305.md): homologar os contratos HTTP/SSE consumidos pelos clientes.
5. [#402](../issues/v0.4/ISSUE-402.md) e [#501 a #504](../issues/README.md): validar mensageria, interfaces e regressão ponta a ponta.

Antes de implementar, concluir os gates SDD `specify`, `clarify`, `plan`, `checklist`, `tasks` e `analyze` com evidências da imagem escolhida. Escrever testes de contrato antes de qualquer adaptação funcional, conforme a constituição. Este registro documenta a direção e o escopo, não substitui a aprovação desses gates nem comprova execução do serviço.

## Checklist de Aceitação da Integração Futura

- [ ] Imagem de origem verificada, com versão/digest fixado, sem `latest` e sem build local implícito.
- [ ] Compose explicita ambiente, rede, volumes, dependências operacionais saudáveis e healthcheck suportado pela imagem.
- [ ] Configurações em `infra/openjarvis/`, segredos somente em `.env` ou secret manager e dados persistentes em volumes nomeados.
- [ ] Contratos MCP, LiteLLM, HitL, sessões, API/SSE, mensageria e telemetria validados por testes.
- [ ] Reinício preserva histórico e aprovações pendentes; rejeições não executam ferramentas.
- [ ] Nenhum cliente depende do antigo hostname nem de portas ou endpoints não homologados.

## Análise Constitucional e Riscos

A separação entre aplicações próprias e componente externo operado em `infra/` é mantida, assim como a opção explícita por `image`. A alteração documental não instala dependências, introduz segredos ou modifica o funcionamento atual.

Os principais riscos são incompatibilidade da imagem com MCP, API/SSE, aprovações, persistência, mensageria ou observabilidade. A mitigação é homologação verificável e bloqueio da entrega funcional enquanto houver lacunas. Logs em disco, ausência de contexto distribuído e acesso direto a provedores de modelos não são exceções autorizadas pela adoção de software externo.

## Consequências

- **Positivas:** menor manutenção de um motor próprio; operação declarativa junto aos demais serviços Docker.
- **Custos e limitações:** dependência do ciclo de versões e capacidades do OpenJarvis, necessidade de verificar procedência/licença e risco de adaptações de integração.
- **Rastreabilidade:** referências ao app antigo em tarefas concluídas permanecem como histórico, não como instrução para novo desenvolvimento.
