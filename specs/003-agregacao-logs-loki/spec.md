# Feature Specification: Agregação Centralizada de Logs de Contêineres (Grafana Alloy + Loki)

**Feature Branch**: `[003-agregacao-logs-loki]`

**Created**: 2026-10-01

**Status**: Draft

**Input**: User description: "ISSUE-103 (`docs/issues/v0.1/ISSUE-103.md`): Configurar a coleta unificada de logs de contêineres capturando saídas `stdout`/`stderr` e enviando para o Loki através do Promtail. Critérios de aceite: os logs de qualquer contêiner ativo são ingeridos e indexados no Loki; nenhuma aplicação grava logs em arquivos locais (uso estrito de `stdout`/`stderr`)." (Coletor alterado para Grafana Alloy na sessão de clarificação de 2026-10-01; ver Clarifications.)

## Clarifications

### Session 2026-10-01

- Q: O escopo de coleta deve abranger todos os contêineres do host Docker ou apenas os do projeto Compose `jhonny_v`? → A: Todos os contêineres ativos do host Docker, sem filtro por projeto.
- Q: Qual período de retenção dos logs no armazenamento central? → A: Configurável por variável de ambiente, com valor default de 7 dias.
- Q: Qual coletor deve ser usado: Promtail (EOL desde o início de 2026, conforme a issue) ou Grafana Alloy (substituto oficial)? → A: Grafana Alloy. Isso substitui a menção ao Promtail na ISSUE-103 e na milestone v0.1, com os mesmos requisitos funcionais.
- Q: O coletor deve acessar o Docker direto pelo socket montado como somente leitura, ou por um proxy intermediário que só libera as consultas de leitura? → A: Por um proxy de socket com permissão só de leitura (listar contêineres e ler logs); só o proxy monta o socket e o coletor fala com ele pela rede interna.
- Q: O proxy de socket deve ficar numa rede interna só dele com o coletor, ou na rede compartilhada `jhonny-core`? → A: Rede interna dedicada (sem saída para a internet) só para proxy ↔ coletor; o coletor e o armazenamento central também ficam na `jhonny-core`.
- Q: A porta do Loki deve ser publicada no host por padrão (em `127.0.0.1`), ou ele deve ficar acessível só pela rede interna do Compose? → A: Publicada por padrão em `${HOST_IP:-127.0.0.1}`, com porta configurável por variável de ambiente documentada no `.env.example`.
- Q: Devemos limitar o tamanho dos arquivos onde o próprio Docker guarda o `stdout`/`stderr` de cada contêiner, com um padrão aplicado a todas as camadas Compose? → A: Sim. Um limite padrão em todas as camadas Compose (core, llm, obs) de 10 MB × 3 arquivos por contêiner, ajustável por variável de ambiente.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consultar os logs de todos os contêineres em um único ponto (Priority: P1)

Como integrante da equipe, quero que os logs de saída padrão e de erro de todos os contêineres ativos do ambiente local fiquem disponíveis num único ponto central de consulta, sem precisar inspecionar cada contêiner individualmente.

**Why this priority**: É o valor central da issue e o primeiro passo da stack LGTMP exigida pela constituição (seção 3.3.4). Sem a ingestão centralizada, nenhuma visualização ou correlação posterior (Grafana, Tempo) é possível.

**Independent Test**: Pode ser testada de forma independente subindo a camada de observabilidade junto com a camada core, gerando uma linha de log conhecida em um contêiner ativo e confirmando que essa linha é retornada por uma consulta no ponto central de logs.

**Acceptance Scenarios**:

1. **Given** a camada de observabilidade em execução e um contêiner ativo que escreve uma linha na saída padrão, **When** um integrante consulta o ponto central de logs, **Then** a linha aparece associada ao contêiner de origem.
2. **Given** o mesmo cenário, mas com a linha escrita na saída de erro, **When** um integrante consulta o ponto central de logs, **Then** a linha aparece e é distinguível de uma linha da saída padrão.
3. **Given** a camada de observabilidade já em execução, **When** um novo contêiner é iniciado e produz logs, **Then** esses logs passam a ser coletados sem reiniciar nem reconfigurar a camada de observabilidade.

---

### User Story 2 - Filtrar logs por origem e por atributos estruturados (Priority: P2)

Como responsável pela operação do ambiente, quero filtrar os logs por origem (serviço, projeto, contêiner, saída padrão/erro) e por atributos dos logs estruturados (nível, `trace_id`), para isolar rapidamente a causa de um problema.

**Why this priority**: Sem rótulos de origem e sem leitura dos logs estruturados, a agregação vira um volume indistinto de linhas, pouco útil para diagnóstico. Também prepara a correlação log ↔ trace prevista para a ISSUE-105.

**Independent Test**: Pode ser testada com dois serviços distintos gerando logs, um deles em JSON estruturado com nível e `trace_id`, validando que as consultas filtradas retornam apenas as linhas esperadas.

**Acceptance Scenarios**:

1. **Given** dois serviços distintos gerando logs, **When** um integrante filtra pela identificação de um dos serviços, **Then** apenas as linhas desse serviço são retornadas.
2. **Given** um serviço que emite logs JSON estruturados com nível e `trace_id`, **When** um integrante filtra por um nível (ex.: `ERROR`) ou por um `trace_id` específico, **Then** apenas as linhas correspondentes são retornadas.
3. **Given** um serviço que emite logs em texto não estruturado, **When** esses logs são ingeridos, **Then** continuam consultáveis pelos rótulos de origem, sem falha nem descarte.

---

### User Story 3 - Garantir conformidade com a política de logs apenas em `stdout`/`stderr` (Priority: P3)

Como responsável pela arquitetura, quero comprovar com evidência objetiva que nenhum serviço do repositório grava logs em arquivos locais, para que a coleta centralizada seja a única fonte de verdade, conforme a constituição (seções 3.3.1 e 6.4).

**Why this priority**: É um critério de aceite da issue e uma regra bloqueante da constituição, mas é verificação de conformidade, não uma capacidade nova.

**Independent Test**: Pode ser testada revisando as definições de serviço de todas as camadas Compose do repositório e confirmando que nenhuma configura saída de log para arquivo nem monta volume dedicado a arquivos de log.

**Acceptance Scenarios**:

1. **Given** as definições de serviço de todas as camadas do repositório (core, llm e observabilidade), **When** uma revisão de conformidade é executada, **Then** nenhum serviço grava logs em arquivo local.
2. **Given** os próprios componentes de coleta e armazenamento de logs, **When** são inspecionados, **Then** seus logs operacionais também vão apenas para `stdout`/`stderr`.

---

### Edge Cases

- Quando um contêiner tiver vida curta (encerrar segundos após iniciar), os logs emitidos antes do encerramento ainda devem ser ingeridos.
- Quando o coletor for reiniciado, não deve haver lacuna de logs dos contêineres que continuaram ativos; a entrega é "ao menos uma vez" e uma pequena duplicação das últimas linhas anteriores ao reinício é aceitável.
- Quando o armazenamento central estiver temporariamente indisponível, o coletor deve tentar reenviar sem afetar a execução dos contêineres de aplicação.
- Quando uma linha JSON estiver malformada, ela deve ser ingerida como texto bruto, sem descartar a linha nem interromper a coleta.
- Quando um log estruturado não contiver `trace_id`/`span_id`, a linha deve ser ingerida normalmente; a ausência é problema de instrumentação da aplicação (constituição 3.3.3) e não deve bloquear a coleta. A falha de instrumentação é detectada por consulta (linhas JSON sem o metadado `trace_id`), e não pelo coletor, que não descarta nem altera essas linhas.
- Quando houver atributos de alta cardinalidade (ex.: `trace_id`, ID completo do contêiner, IDs de requisição), eles NÃO devem virar rótulos de indexação, para não degradar o armazenamento; devem continuar pesquisáveis como conteúdo/metadado da linha.
- Quando os próprios contêineres de observabilidade produzirem logs, eles devem ser coletados sem criar laço de realimentação com volume crescente.
- O socket do Docker dá controle total do host mesmo montado como somente leitura; por isso o coletor NÃO o monta e acessa o Docker só por um proxy de socket restrito a leitura.
- Quando o coletor (ou qualquer cliente do proxy) tentar uma operação de escrita na API do Docker (ex.: criar, iniciar ou remover contêiner), o proxy MUST negar a operação.
- Quando qualquer contêiner fora da rede dedicada (ex.: serviços da `jhonny-core`) tentar acessar o proxy de socket, a conexão MUST falhar por falta de rota, impedindo a leitura de metadados sensíveis (como variáveis de ambiente) de outros contêineres.
- Quando o proxy de socket estiver indisponível, ou for reiniciado ou recriado, a descoberta de novos contêineres e a leitura de logs são suspensas sem afetar os contêineres de aplicação. Ambas são retomadas automaticamente quando o proxy voltar, a partir da última posição salva (FR-010).
- Quando o daemon Docker ou o host reiniciar, contêineres que voltarem com o mesmo ID retomam a leitura a partir da posição salva; contêineres recriados (com ID novo) são tratados como novos alvos (FR-003). Nos dois casos vale a entrega "ao menos uma vez".
- Quando um contêiner gerar logs mais rápido do que o coletor consegue ler e atingir o limite de rotação do Docker (FR-019), as linhas mais antigas ainda não lidas podem ser descartadas; o limite default deve dar folga suficiente para que isso não ocorra em condições normais do ambiente local.
- Linhas muito longas ou multilinha (ex.: stack traces) devem ser ingeridas sem derrubar o pipeline; o agrupamento multilinha está fora do escopo inicial.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST coletar automaticamente as saídas `stdout` e `stderr` dos contêineres em escopo, sem configuração individual por contêiner.
- **FR-002**: O escopo de coleta MUST abranger todos os contêineres ativos do host Docker, sem filtro por projeto Compose; o rótulo de projeto (FR-005) permite isolar os contêineres do `jhonny_v` na consulta.
- **FR-003**: O sistema MUST descobrir dinamicamente contêineres iniciados ou encerrados após a subida da camada de observabilidade, sem reinício dela.
- **FR-004**: O sistema MUST enviar os logs coletados para o armazenamento central (Loki), onde ficam indexados e consultáveis.
- **FR-005**: Cada linha ingerida MUST receber rótulos de origem derivados dos metadados do contêiner, no mínimo: projeto Compose, serviço Compose, nome do contêiner e stream (`stdout`/`stderr`). O rótulo `service_name`, que o armazenamento central atribui automaticamente a partir do serviço Compose, também é um rótulo de indexação de baixa cardinalidade e é o único rótulo além dos mínimos.
- **FR-006**: O conjunto de rótulos de indexação MUST ter cardinalidade limitada; atributos de alta cardinalidade (`trace_id`, `span_id`, ID do contêiner) MUST NOT ser usados como rótulo de indexação.
- **FR-007**: O sistema MUST interpretar linhas de log em JSON estruturado, expondo o nível do log como atributo filtrável e `trace_id`/`span_id` como atributos pesquisáveis, sem promovê-los a rótulos de indexação.
- **FR-008**: Linhas não JSON ou JSON malformado MUST ser ingeridas como texto bruto, preservando os rótulos de origem, sem descarte.
- **FR-009**: O coletor MUST descobrir contêineres e ler seus logs exclusivamente por meio de um proxy de socket do Docker. O proxy é o único serviço que monta `/var/run/docker.sock` (em modo somente leitura), opera como lista de permissões (allowlist) que libera apenas `GET` para listar/inspecionar contêineres, ler logs de contêineres, listar/inspecionar redes (exigido pela descoberta de contêineres), `_ping` e `version`, e MUST negar qualquer método ou endpoint não listado e só é acessível por uma rede interna dedicada (sem saída para a internet) compartilhada exclusivamente com o coletor, sem porta publicada no host. O proxy MUST NOT ser conectado à rede `jhonny-core` nem a qualquer outra rede. O coletor MUST NOT montar o socket do Docker.
- **FR-010**: O coletor MUST persistir sua posição de leitura para não perder logs ao reiniciar (entrega "ao menos uma vez").
- **FR-011**: O armazenamento central MUST persistir os dados em volume nomeado declarado explicitamente, sobrevivendo à recriação do contêiner.
- **FR-012**: O armazenamento central MUST reter os logs por um período configurável por variável de ambiente, com valor default de 7 dias quando a variável não for definida, e descartar automaticamente os dados mais antigos que esse período. Um valor inválido MUST impedir a inicialização do armazenamento central (fail-fast), sem recair silenciosamente no default.
- **FR-013**: A camada de observabilidade MUST ser um overlay Compose próprio (`infra/compose.obs.yaml`), combinável com `infra/compose.yaml`, reutilizando a rede `jhonny-core` declarada na base para coletor e armazenamento central e declarando explicitamente a rede interna dedicada proxy ↔ coletor, com versões de imagem fixadas (sem `:latest`), `healthcheck` nos serviços e `depends_on` com `condition: service_healthy` do coletor para o armazenamento e para o proxy de socket.
- **FR-014**: As configurações do coletor e do armazenamento MUST ser versionadas em `infra/alloy/` e `infra/loki/config.yaml`, respectivamente, sem segredos embutidos. O diretório `infra/alloy/` substitui o `infra/promtail/config.yaml` citado na issue; a configuração do coletor fica em `infra/alloy/config.alloy`.
- **FR-015**: O armazenamento central MUST publicar sua porta de consulta no host por padrão, seguindo o padrão das demais camadas: vinculada a `${HOST_IP:-127.0.0.1}` e com número de porta configurável por variável de ambiente. Essa é a interface usada pelos testes de aceite antes da existência do Grafana (ISSUE-104). O coletor e o proxy de socket MUST NOT publicar portas no host.
- **FR-016**: Nenhum serviço do repositório (aplicação ou infraestrutura) MAY gravar logs em arquivo local; todos MUST usar exclusivamente `stdout`/`stderr`.
- **FR-017**: O coletor utilizado MUST ser o Grafana Alloy, substituto oficial e mantido do Promtail (em fim de vida desde o início de 2026), atendendo aos mesmos requisitos funcionais (FR-001 a FR-010). O Promtail MUST NOT ser adotado.
- **FR-018**: A variável de ambiente de retenção (FR-012), a porta publicada do armazenamento central (FR-015), o nível de log do armazenamento central (FR-020) e as variáveis de limite de rotação (FR-019) MUST ser documentadas em `.env.example` com seus valores default.
- **FR-019**: Todos os serviços de todas as camadas Compose do repositório (core, llm e obs) MUST aplicar um limite comum de rotação para as saídas `stdout`/`stderr` mantidas pelo Docker no host: default de 10 MB por arquivo e 3 arquivos por contêiner, ajustável por variável de ambiente. O limite MUST ser definido num bloco único por arquivo Compose (extensão `x-logging`), idêntico em todos os arquivos e reutilizado por todos os serviços do arquivo, sem duplicação por serviço. É o mesmo padrão do `x-common-environment`, já que âncoras YAML não atravessam arquivos. O limite vale para os serviços definidos nas camadas Compose do repositório; contêineres criados fora delas seguem a configuração de log do daemon Docker e continuam no escopo de coleta do FR-002.
- **FR-020**: Os serviços da camada de observabilidade MUST emitir seus próprios logs em JSON estruturado no `stdout`/`stderr` (constituição 3.3.2). O nível de log do armazenamento central MUST ser configurável por variável de ambiente (`LOKI_LOG_LEVEL`, default `info`). [NEEDS CLARIFICATION: formato de log do proxy de socket — ver CHK006/CHK019 em `checklists/observability.md`]
- **FR-021**: Os documentos `docs/issues/v0.1/ISSUE-103.md` e `docs/milestones/v0.1-infra-core.md` MUST ser atualizados na implementação para refletir: Grafana Alloy no lugar do Promtail, `infra/compose.obs.yaml` no lugar de `compose.obs.yml`, `infra/alloy/config.alloy` no lugar de `infra/promtail/config.yaml` e o proxy de socket no lugar da montagem direta do socket. Depois da atualização, nenhum desses documentos pode citar o Promtail como componente adotado.

### Key Entities *(include if feature involves data)*

- **Linha de log**: ocorrência emitida por um contêiner, com carimbo de tempo, conteúdo (JSON estruturado ou texto) e stream de origem.
- **Rótulos de origem**: pares chave/valor de baixa cardinalidade (projeto, serviço, contêiner, stream) usados para indexar e filtrar linhas.
- **Atributos estruturados**: campos extraídos de logs JSON (nível, `trace_id`, `span_id`), filtráveis/pesquisáveis sem serem rótulos de indexação.
- **Coletor**: agente que descobre contêineres, lê seus logs, aplica rótulos e atributos e entrega ao armazenamento central; mantém a posição de leitura.
- **Proxy de socket do Docker**: intermediário entre o coletor e a API do Docker, que libera só as operações de leitura necessárias para descobrir contêineres e ler logs.
- **Armazenamento central**: serviço que recebe, indexa por rótulos, retém pelo período definido e responde consultas sobre as linhas de log.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% dos contêineres ativos em escopo (FR-002) têm logs consultáveis no ponto central, sem nenhuma configuração manual por contêiner.
- **SC-002**: Uma linha escrita em `stdout`/`stderr` fica consultável no ponto central em até 10 segundos, em condições normais do ambiente local.
- **SC-003**: Um contêiner iniciado após a camada de observabilidade tem seus logs coletados em até 30 segundos após iniciar, sem reiniciar a camada.
- **SC-004**: Após reiniciar o coletor, 0 linhas são perdidas para contêineres que continuaram ativos durante o reinício. A medição usa um emissor de sequência numerada contínua: depois do reinício, nenhum número da sequência pode faltar no armazenamento central (duplicatas são permitidas).
- **SC-005**: Em teste com ao menos 2 serviços, filtros por serviço, por nível e por `trace_id` retornam 0 falsos positivos.
- **SC-006**: A revisão de conformidade das camadas Compose encontra 0 serviços configurados para gravar logs em arquivo local.
- **SC-007**: A camada de observabilidade inicia com todos os serviços saudáveis na primeira tentativa, em 100% das execuções de validação, tanto só com a camada base quanto combinada com as camadas core e llm, em qualquer ordem de inicialização das camadas. Contêineres de camadas iniciadas depois são descobertos pelo FR-003.
- **SC-008**: Em teste de validação, 100% das tentativas de operação de escrita na API do Docker feitas através do proxy de socket são negadas, e o coletor não tem o socket do Docker montado.
- **SC-009**: Em teste de validação, 0 contêineres além do coletor conseguem alcançar o proxy de socket. A verificação é exaustiva pela topologia (o proxy está conectado só à rede dedicada, cujo único outro membro é o coletor) e é complementada por uma tentativa de conexão a partir da rede `jhonny-core`, que MUST falhar.
- **SC-010**: Com os valores default, o armazenamento central responde a consultas a partir do host em `127.0.0.1` e não é alcançável por outras interfaces de rede da máquina. A verificação usa o bind da porta publicada (somente `127.0.0.1`) e uma tentativa de acesso por um endereço IP não-loopback do host, que MUST falhar.
- **SC-011**: 100% dos serviços definidos nas camadas Compose do repositório aplicam o limite comum de rotação; com os valores default, o espaço em disco ocupado pelos logs de cada contêiner no host não passa de 30 MB, medidos como o tamanho em disco de todos os arquivos `json-file` do contêiner (o arquivo ativo e os rotacionados, incluindo o envelope JSON do Docker).

## Assumptions

- O ambiente-alvo é Docker Engine com Docker Compose v2 num único host local; orquestração multi-nó e Kubernetes estão fora do escopo.
- Os contêineres usam um driver de log legível pela API do Docker: `json-file`, `local` ou outro driver com o cache de leitura dual do Docker Engine (≥ 20.10) ativo. Contêineres com driver `none`, ou com o cache dual desativado, não têm logs coletáveis e ficam fora do SC-001. O limite de rotação (FR-019) é aplicado definindo o driver `json-file` nos serviços do repositório.
- Esta feature altera também as camadas `infra/compose.core.yaml` e `infra/compose.llm.yaml`, mas só para aplicar o limite comum de rotação (FR-019), sem nenhuma outra mudança de comportamento nesses serviços.
- Os documentos `docs/issues/v0.1/ISSUE-103.md` e `docs/milestones/v0.1-infra-core.md` citam o Promtail; a atualização deles é exigida pelo FR-021 (princípio V da constituição).
- Como a coleta abrange todo o host (FR-002), contêineres de outros projetos no mesmo host também são ingeridos; isso é aceitável no ambiente local, e a separação é feita pelo rótulo de projeto.
- O nome do overlay segue a convenção da constituição e da milestone v0.1 (`infra/compose.obs.yaml`), e não `compose.obs.yml`, que aparece em versões anteriores da issue.
- A rede `jhonny-core` permanece a rede compartilhada dos serviços; a rede dedicada proxy ↔ coletor é nova, declarada pela camada de observabilidade e interna (sem saída para a internet).
- A rede `jhonny-core` e o padrão de volumes nomeados de `infra/compose.yaml` (ISSUE-101) já existem e serão reutilizados/estendidos.
- O armazenamento central opera em modo single-tenant, sem autenticação própria, aceitável apenas para o ambiente local; o acesso fica restrito por padrão à interface `127.0.0.1` do host.
- Visualização (Grafana, ISSUE-104), tracing (Tempo/OTel, ISSUE-105) e alertas estão fora do escopo; esta feature só garante que os logs estejam disponíveis para essas integrações. Essas integrações vão consumir os rótulos de indexação (FR-005), os metadados estruturados `trace_id`/`span_id` (FR-007), usados na correlação log → trace com o Tempo (ADR 0003), e a API HTTP de consulta do Loki na rede `jhonny-core` (`http://loki:3100`).
- Coleta de logs do sistema operacional do host (journald, `/var/log`) está fora do escopo.
- Agrupamento multilinha e extração de campos JSON além de nível, `trace_id` e `span_id` estão fora do escopo inicial.
- A adequação das aplicações em `apps/` ao formato JSON estruturado é responsabilidade de cada app; esta feature só garante a ingestão de ambos os formatos.
