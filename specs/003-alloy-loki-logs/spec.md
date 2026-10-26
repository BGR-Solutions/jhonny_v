# Feature Specification: Agregação de Logs com Alloy e Loki

**Feature Branch**: `feature/with-jarvis` (branch atual; nenhuma branch criada neste fluxo)

**Created**: 2026-10-25

**Status**: Draft

**Input**: User description: "Executar /speckit-specify para a ISSUE-103: coleta unificada de stdout/stderr dos contêineres e agregação de logs, adotando Grafana Alloy no lugar do Promtail conforme confirmação do usuário."

**Issue**: [#103 — Agregação de Logs](../../docs/issues/v0.1/ISSUE-103.md)

## Clarifications

### Session 2026-10-25

- Q: Manter Promtail, que está fora de suporte, ou adotar Grafana Alloy? → A: Usar Grafana Alloy, preservando Loki e a coleta de stdout/stderr; atualizar o escopo documental da #103.
- Q: Como os operadores devem acessar as consultas de logs no ambiente local? → A: Somente pela máquina local (loopback), com autenticação obrigatória; ingestão restrita à rede interna e a componentes autorizados.
- Q: Por quanto tempo os logs devem permanecer disponíveis para consulta por padrão? → A: 14 dias por padrão, com prazo configurável; o planejamento definirá o tempo técnico de limpeza após expirar o prazo.
- Q: Na falha simulada de 30 segundos do destino de logs, os eventos emitidos durante a interrupção também devem ser recuperados? → A: Sim; com coletor e contêineres de origem ativos, recuperar a amostra em até 60 segundos após o destino voltar, tolerando duplicatas.
- Evidência: a [documentação oficial do Grafana](https://grafana.com/docs/loki/latest/send-data/promtail/) informa fim de vida do Promtail em 2026-03-02 e recomenda um coletor suportado. A escolha não autoriza implementação antes dos demais gates SDD.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Localizar logs dos serviços em um ponto central (Priority: P1)

Como responsável pelo ambiente local, quero consultar em um único lugar as saídas dos contêineres do projeto para investigar problemas sem abrir cada serviço separadamente.

**Why this priority**: A coleta centralizada é o resultado principal da issue e a base para diagnóstico das próximas fases.

**Independent Test**: Iniciar apenas a camada de logs com dois contêineres de teste do projeto e consultar seus eventos pelo mecanismo de consulta do agregador, sem depender de interface gráfica, modelos ou aplicações futuras.

**Acceptance Scenarios**:

1. **Given** a camada de logs saudável e dois contêineres ativos do projeto, **When** cada um emite eventos identificáveis em stdout e stderr, **Then** todos os eventos ficam consultáveis centralmente com a origem e o fluxo preservados.
2. **Given** a coleta ativa, **When** um novo contêiner do projeto é iniciado, **Then** sua saída passa a ser coletada sem editar manualmente a lista de alvos.
3. **Given** outro projeto em execução no mesmo ambiente Docker, **When** ele emite eventos, **Then** esses eventos não aparecem nas consultas do projeto Jhonny-V.

---

### User Story 2 - Filtrar eventos e preservar o contexto de diagnóstico (Priority: P2)

Como desenvolvedor, quero filtrar eventos por serviço e encontrar o contexto de uma operação para relacionar erros sem perder a mensagem original.

**Why this priority**: A agregação só é útil quando a origem e os campos de diagnóstico continuam recuperáveis.

**Independent Test**: Emitir eventos estruturados e mensagens não estruturadas em contêineres de teste; consultar por serviço, conferir campos e comparar o conteúdo recuperado com o emitido.

**Acceptance Scenarios**:

1. **Given** eventos estruturados de serviços distintos, **When** a consulta seleciona um serviço, **Then** retorna apenas os eventos desse serviço e preserva mensagem, severidade e horário quando presentes.
2. **Given** um evento com contexto distribuído, **When** ele é coletado, **Then** `trace_id` e `span_id` permanecem consultáveis com seus valores originais.
3. **Given** uma mensagem não estruturada ou com estrutura inválida, **When** é coletada, **Then** seu conteúdo original e sua origem continuam consultáveis, com a condição de parsing identificável, sem interromper a coleta das demais mensagens.

---

### User Story 3 - Reiniciar e diagnosticar a camada de logs (Priority: P2)

Como responsável pela operação, quero reconhecer falhas da coleta e reiniciar seus componentes sem perder os eventos já armazenados.

**Why this priority**: Uma falha silenciosa da observabilidade impede distinguir falta de eventos de indisponibilidade do pipeline.

**Independent Test**: Confirmar a ingestão de eventos, reiniciar os componentes preservando seus dados, simular uma indisponibilidade breve do destino e verificar diagnósticos e retomada para novos eventos.

**Acceptance Scenarios**:

1. **Given** eventos confirmados no agregador, **When** o serviço é reiniciado sem apagar seus dados persistentes, **Then** os eventos anteriormente confirmados continuam consultáveis.
2. **Given** o destino de logs indisponível por 30 segundos, com coletor e contêineres de origem ativos, **When** são emitidos 20 eventos únicos durante a interrupção, **Then** a falha é sinalizada explicitamente, sem indicar sucesso de entrega; após a recuperação, os 20 eventos e novos eventos ficam consultáveis em até 60 segundos, tolerando duplicatas.
3. **Given** configuração inválida ou acesso ao Docker negado, **When** a coleta é iniciada, **Then** seu estado indica falha com diagnóstico suficiente para localizar a causa, sem expor credenciais.
4. **Given** um reinício do coletor, **When** são emitidos novos eventos após sua recuperação, **Then** a descoberta e coleta dos contêineres do projeto são retomadas sem reconfiguração manual.

### Edge Cases

- Contêineres iniciados, recriados ou parados durante a coleta devem manter origem distinguível; um nome reutilizado não deve misturar a identidade das instâncias.
- Eventos idênticos emitidos legitimamente mais de uma vez não devem ser descartados apenas por terem o mesmo texto.
- Campos ausentes ou JSON inválido não autorizam descarte silencioso da mensagem nem fabricação de identificadores de tracing.
- Ausência de `trace_id` ou `span_id` em evento que declare contexto distribuído é falha de instrumentação a identificar na validação, não um valor a inventar no coletor.
- Identificadores de execução, requisições, usuários e conteúdo livre não devem gerar dimensões de indexação de alta cardinalidade.
- Sem permissão para acessar o mecanismo de logs do Docker, o pipeline deve apresentar erro explícito; não deve ampliar permissões automaticamente.
- Contêiner sem suporte à leitura de seus logs pelo mecanismo escolhido deve ser identificado como incompatível, sem ser anunciado como coletado.
- Eventos emitidos antes da ativação da coleta e entrega sem perdas durante indisponibilidade prolongada não são garantias desta especificação; limites de recuperação e buffers devem ser definidos no planejamento.
- A recuperação da amostra durante a interrupção de 30 segundos pressupõe coletor e contêineres de origem ativos, sem rotação que torne a origem indisponível. Falha simultânea desses componentes e interrupções mais longas não possuem garantia de recuperação nesta entrega; duplicatas por retentativa são toleradas.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O ambiente MUST disponibilizar uma camada de agregação de logs que possa ser habilitada sem exigir aplicações futuras ou outras camadas de observabilidade.
- **FR-002**: A coleta MUST descobrir automaticamente contêineres ativos do projeto e capturar stdout e stderr, incluindo contêineres criados após a inicialização do coletor.
- **FR-003**: A coleta MUST ser restrita ao projeto selecionado; logs de outros projetos ou contêineres sem associação ao projeto MUST NOT ser ingeridos por padrão.
- **FR-004**: Cada evento MUST manter a identidade do projeto, serviço e instância do contêiner, o fluxo de origem e um horário de coleta ou emissão identificável.
- **FR-005**: Operadores MUST conseguir consultar eventos por intervalo de tempo e filtrar por serviço e contêiner, preservando a mensagem original.
- **FR-006**: O pipeline MUST preservar os campos JSON das aplicações, incluindo severidade, `trace_id` e `span_id` quando presentes, sem substituir o contexto distribuído por valores artificiais.
- **FR-007**: Mensagens de infraestrutura em texto ou com parsing inválido MUST continuar recuperáveis com origem e indicação da condição de parsing. Essa tolerância MUST NOT ser considerada autorização para aplicações próprias violarem a política de logs JSON.
- **FR-008**: A classificação indexada MUST limitar-se a dimensões operacionais controladas; conteúdo livre e identificadores de tracing MUST permanecer consultáveis sem se tornarem labels de indexação.
- **FR-009**: Eventos cuja ingestão foi confirmada MUST continuar consultáveis após reinício do agregador com seus dados persistentes preservados. A retenção MUST ser de 14 dias por padrão, configurável; eventos expirados MUST ser elegíveis para remoção automática, com prazo técnico de limpeza definido e validado no planejamento.
- **FR-010**: O pipeline MUST tornar falhas de configuração, acesso, descoberta e entrega identificáveis por estado operacional e diagnóstico explícitos, sem expor segredos nem reportar entrega bem-sucedida quando houve falha.
- **FR-011**: Após recuperação de indisponibilidade transitória, o coletor MUST retomar a descoberta e entrega de novos eventos sem exigir edição de configurações. No teste de interrupção do destino por 30 segundos, com coletor e origens ativos e logs de origem disponíveis, os 20 eventos únicos emitidos durante a falha MUST ficar consultáveis em até 60 segundos após o destino voltar; duplicatas por retentativa são toleradas.
- **FR-012**: As aplicações próprias MUST emitir logs JSON exclusivamente por stdout/stderr, sem arquivos locais de log. O armazenamento persistente do agregador e o estado técnico do coletor MUST ser distinguidos de logs de aplicação e mantidos fora da árvore de código.
- **FR-013**: Consultas de logs MUST ser acessíveis somente pela máquina local (loopback), com autenticação obrigatória; acesso sem credencial ou com credencial inválida MUST ser negado. A ingestão MUST ficar restrita à rede interna e a componentes autorizados. O acesso ao Docker MUST ser limitado ao necessário para coleta. Credenciais MUST permanecer fora do versionamento.
- **FR-014**: A entrega MUST documentar ativação, consulta, diagnóstico, reinício, persistência, retenção e limitações conhecidas da coleta, incluindo o tratamento de contêineres incompatíveis.
- **FR-015**: A validação MUST comprovar coleta dos dois fluxos, descoberta dinâmica, isolamento de projeto, parsing, preservação do contexto, persistência e recuperação de falha, sem modificar contratos de MCP, modelos, agentes ou Worker.

### Key Entities

- **Evento de log**: mensagem emitida por um contêiner, com horário, fluxo de origem, campos estruturados opcionais e contexto distribuído quando existente.
- **Origem de coleta**: associação entre projeto, serviço e instância do contêiner que permite delimitar o escopo e filtrar eventos.
- **Classificação operacional**: conjunto controlado de dimensões usadas para indexar eventos sem incluir identificadores de alta cardinalidade.
- **Estado de coleta**: informações de descoberta, progresso e falhas necessárias para verificar saúde e retomada do pipeline.
- **Conjunto persistente de eventos**: registros já aceitos pelo agregador e disponíveis para consulta durante a janela de retenção.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em ambiente local saudável e sem pressão de recursos, 100% de uma amostra de 200 eventos únicos, emitidos por dois contêineres do projeto (50 por fluxo em cada contêiner), ficam consultáveis em até 60 segundos após a última emissão.
- **SC-002**: Um novo contêiner de teste do projeto tem seu primeiro evento pós-inicialização consultável em até 60 segundos, sem alteração manual dos alvos.
- **SC-003**: Na mesma validação, nenhum dos 20 eventos identificáveis emitidos por um contêiner de outro projeto aparece no conjunto consultável do projeto selecionado.
- **SC-004**: Uma amostra de 12 eventos — quatro estruturados com contexto distribuído, quatro em texto e quatro com JSON inválido — mantém 100% das mensagens e origens recuperáveis, com os identificadores originais dos quatro eventos estruturados preservados.
- **SC-005**: Todos os 20 eventos de teste cuja ingestão foi confirmada antes de um reinício continuam consultáveis após a recuperação, preservados os dados persistentes.
- **SC-006**: Durante indisponibilidade controlada de 30 segundos, a falha de entrega produz diagnóstico explícito. Mantidos coletor e contêineres de origem ativos e seus logs disponíveis, 100% dos 20 eventos únicos emitidos durante a interrupção e um novo evento emitido após a recuperação tornam-se consultáveis em até 60 segundos após o destino recuperar sua saúde; duplicatas são toleradas.
- **SC-007**: Um colaborador consegue seguir a documentação para ativar a coleta, localizar um evento de teste por serviço e reconhecer uma falha simulada sem editar código de aplicação.
- **SC-008**: Uma consulta autenticada pela máquina local retorna os eventos autorizados; consultas sem credencial ou com credencial inválida são negadas, e as interfaces de consulta e ingestão não ficam publicadas na rede externa à máquina.
- **SC-009**: A política padrão mantém eventos confirmados disponíveis durante 14 dias e habilita remoção automática dos expirados; a validação com janela reduzida comprova a aplicação de um prazo alternativo e a remoção dentro do prazo técnico de limpeza definido no plano.

## Assumptions

- O escopo é desenvolvimento local de um único projeto Compose selecionado, não coleta global de todos os usuários que compartilhem o mesmo host. "Qualquer contêiner ativo" na issue significa qualquer contêiner desse projeto cujo mecanismo de logs seja suportado.
- Grafana Alloy substitui Promtail por decisão explícita do usuário; Loki permanece o destino. Versões e configurações concretas serão escolhidas no gate de planejamento, não nesta etapa.
- Os caminhos previstos pela issue são `infra/compose.obs.yaml`, `infra/alloy/config.alloy` e `infra/loki/config.yaml`; são restrições herdadas de organização, não arquivos criados por este comando.
- O ambiente tem Docker com contêineres Linux e acesso autorizado aos seus logs; compatibilidade no Docker Desktop/Windows e requisitos de permissões precisam ser comprovados no planejamento e nos testes.
- Acesso ao socket Docker é sensível; um mount marcado somente leitura não será tratado como garantia de autorização somente leitura da API. Os controles concretos serão analisados antes da implementação.
- Interface Grafana e dashboards pertencem às issues #104/#109; métricas, traces e coleta de host/GPU pertencem às issues #104/#105/#108. A consulta para aceite desta issue independe dessas entregas.
- Adoção do OpenJarvis permanece conforme a [ADR-0006](../../docs/adr/0006-openjarvis-compose.md). Não é necessário subir ou implementar o OpenJarvis, MCP Server ou Worker para comprovar a coleta com contêineres de teste.
- Não se promete entrega exatamente uma vez, recuperação ilimitada, alta disponibilidade ou uso em produção. A retenção padrão é de 14 dias, configurável; limites de armazenamento, prazo técnico de limpeza e comportamento de buffers deverão ficar explícitos no plano antes de implementar.

## Constitutional Analysis

- **Arquitetura:** mantém a entrega em infraestrutura, sem introduzir app ou biblioteca nem antecipar as fases posteriores à v0.1.
- **Operação:** o plano deverá declarar imagens de versão fixa, rede, volumes, ambiente, dependências saudáveis e healthchecks; acesso a Docker e às consultas exige controles explícitos.
- **Observabilidade:** preserva logs JSON de aplicações em stdout/stderr e identificadores distribuídos; tolerância a mensagens de infraestrutura não elimina o gate de conformidade das aplicações.
- **Qualidade:** testes automatizados de contrato devem preceder a implementação do pipeline e ser executados em CI. Escolha de versões e permissões, assim como cumprimento da retenção de 14 dias configurável, exige evidência verificável no plano e na análise de risco.
- **Gate atual:** especificação, esclarecimentos e análise constitucional documental concluídos; implementação bloqueada até os gates seguintes (`plan`, `checklist`, `tasks`, `analyze`). Não há comprovação de infraestrutura executável nesta etapa.
