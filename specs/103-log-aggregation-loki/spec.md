# Especificação de Feature: Agregação Centralizada de Logs de Contêineres

**Feature Branch**: `103-log-aggregation-loki`
**Criado em**: 2026-10-01
**Status**: Draft (etapa `/speckit-specify`)
**Issue de origem**: #103 — "Setup do Promtail e Loki para Agregação de Logs" (GitHub BGR-Solutions/jhonny_v#3)
**Entrada**: "Configurar a coleta unificada de logs de contêineres capturando saídas `stdout`/`stderr` e enviando para o Loki através do Promtail."

> Esta especificação descreve **o quê** e **por quê**. Decisões de **como** (versões de imagem,
> formato exato dos arquivos de configuração, política de retenção técnica, rede Docker, etc.)
> ficam para a etapa `/speckit-plan`. As ferramentas Loki e Promtail aparecem aqui só porque
> a Issue as define como restrição.

## Cenários de Usuário e Testes *(obrigatório)*

### História de Usuário 1 — Consultar logs de qualquer contêiner em um único lugar (Prioridade: P1)

Como desenvolvedor/operador da plataforma, quero ver os logs (`stdout`/`stderr`) de todos os
contêineres ativos do ambiente num único ponto de consulta, sem precisar rodar `docker logs`
contêiner por contêiner.

**Por que esta prioridade**: é o valor central da Issue. Sem isso, nenhuma das outras histórias
tem utilidade. É o MVP da observabilidade de logs.

**Teste independente**: subir a stack de observabilidade junto com pelo menos um contêiner que
escreva em `stdout` e outro que escreva em `stderr`, e confirmar que as duas linhas aparecem
no armazenamento central de logs.

**Cenários de aceite**:

1. **Dado** que a stack de observabilidade está em execução e um contêiner ativo escreve uma
   linha em `stdout`, **quando** o operador consulta o armazenamento central de logs, **então**
   a linha aparece associada ao contêiner de origem.
2. **Dado** o mesmo cenário com a escrita em `stderr`, **quando** o operador consulta,
   **então** a linha aparece e dá para distingui-la de uma linha vinda de `stdout`.
3. **Dado** que um novo contêiner é iniciado depois que a stack de observabilidade já está
   rodando, **quando** ele produz logs, **então** esses logs são coletados sem reiniciar nem
   reconfigurar a stack de observabilidade (descoberta dinâmica).

---

### História de Usuário 2 — Filtrar logs por metadados do contêiner (Prioridade: P2)

Como operador, quero filtrar os logs por atributos do contêiner (por exemplo: nome do
contêiner, serviço/projeto do Compose, stream `stdout`/`stderr`) para isolar rapidamente um
problema.

**Por que esta prioridade**: sem rótulos, a agregação vira um "mar de linhas" pouco útil para
diagnóstico. Depende da P1.

**Teste independente**: com dois contêineres de serviços diferentes produzindo logs, uma
consulta filtrada por um serviço retorna apenas as linhas desse serviço.

**Cenários de aceite**:

1. **Dado** dois contêineres de serviços distintos gerando logs, **quando** o operador filtra
   pelo rótulo de serviço de um deles, **então** só as linhas daquele serviço são retornadas.
2. **Dado** um contêiner gerando logs em `stdout` e `stderr`, **quando** o operador filtra pelo
   rótulo de stream `stderr`, **então** só as linhas de erro são retornadas.

---

### História de Usuário 3 — Garantir a política "logs só em stdout/stderr" (Prioridade: P3)

Como arquiteto da plataforma, quero que nenhuma aplicação grave logs em arquivos locais do
contêiner, para que a coleta centralizada seja a única fonte de verdade e não haja perda de
logs nem consumo descontrolado de disco.

**Por que esta prioridade**: é um critério de aceite da Issue e uma diretriz arquitetural, mas
é uma regra de conformidade, não uma capacidade nova da stack.

**Teste independente**: inspecionar os serviços definidos no repositório e confirmar que
nenhum deles configura saída de log para arquivo (nem monta volume dedicado a arquivos de log).

**Cenários de aceite**:

1. **Dado** os serviços definidos nos arquivos Compose do repositório, **quando** uma revisão de
   conformidade é feita, **então** nenhum serviço de aplicação grava logs em arquivo local.
2. **Dado** os componentes da própria stack de observabilidade (coletor e armazenamento),
   **quando** são inspecionados, **então** os logs operacionais deles também vão para
   `stdout`/`stderr`.

---

### Casos de Borda

- **Contêiner de vida curta** (termina em poucos segundos): os logs emitidos antes do fim
  ainda precisam ser ingeridos.
- **Reinício do coletor**: ao reiniciar, o coletor não pode perder nem duplicar de forma
  significativa os logs já enviados (precisa guardar a posição de leitura).
- **Armazenamento central indisponível temporariamente**: o coletor deve tentar de novo e não
  derrubar os contêineres de aplicação.
- **Linhas muito longas ou multilinha** (ex.: stack traces): devem ser ingeridas sem derrubar
  o pipeline. Agrupar multilinha fica fora do escopo inicial (ver Premissas).
- **Alto volume / alta cardinalidade**: rótulos dinâmicos não podem incluir valores de
  cardinalidade ilimitada (ex.: ID de requisição, timestamp) para não degradar o
  armazenamento.
- **Contêineres da própria stack de observabilidade**: os logs deles também são coletados,
  sem criar laço de realimentação que gere volume crescente.
- **Segurança do socket Docker**: o coletor precisa de acesso ao socket do Docker para
  descobrir contêineres. Esse acesso deve ser o mais restrito possível (somente leitura).

## Requisitos *(obrigatório)*

### Requisitos Funcionais

- **FR-001**: O sistema DEVE coletar automaticamente as saídas `stdout` e `stderr` de **todos**
  os contêineres ativos no host Docker, sem configuração por contêiner.
- **FR-002**: O sistema DEVE descobrir dinamicamente contêineres iniciados ou parados depois
  que a stack de observabilidade já está rodando, sem reiniciá-la.
- **FR-003**: O sistema DEVE enviar os logs coletados para um armazenamento central (Loki),
  onde ficam indexados e consultáveis.
- **FR-004**: Cada linha ingerida DEVE trazer rótulos derivados dos metadados do contêiner,
  no mínimo: nome do contêiner, serviço do Compose, projeto do Compose e stream
  (`stdout`/`stderr`).
- **FR-005**: O conjunto de rótulos DEVE ser de cardinalidade limitada. Metadados de alta
  cardinalidade (ex.: ID completo do contêiner) não podem virar rótulo de indexação.
- **FR-006**: O coletor (Promtail) DEVE descobrir contêineres pelo socket do Docker
  (`/var/run/docker.sock`), montado **somente leitura**.
- **FR-007**: O coletor DEVE guardar a posição de leitura de forma persistente para não
  perder nem duplicar logs ao reiniciar.
- **FR-008**: O coletor e o armazenamento central DEVEM ser serviços da stack de
  observabilidade definida em `infra/compose.obs.yml`, com a configuração versionada em
  `infra/promtail/config.yaml` e `infra/loki/config.yaml`.
- **FR-009**: O armazenamento central DEVE persistir os dados de log em volume nomeado, para
  sobreviver a recriações do contêiner.
- **FR-010**: Nenhum serviço (de aplicação ou de observabilidade) PODE gravar logs em arquivos
  locais. Todos DEVEM usar só `stdout`/`stderr`.
- **FR-011**: O sistema DEVE manter os logs por um período de retenção definido
  [NEEDS CLARIFICATION: qual é o período de retenção desejado — ex.: 7, 14 ou 30 dias?].
- **FR-012**: O armazenamento central DEVE ser acessível para consulta
  [NEEDS CLARIFICATION: só pela rede interna do Compose (consumido por um Grafana numa issue
  futura) ou também exposto em porta do host para acesso direto?].
- **FR-013**: O escopo de coleta DEVE abranger
  [NEEDS CLARIFICATION: todos os contêineres do host Docker, ou só os contêineres dos projetos
  Compose deste repositório (filtrados por rótulo)?].

### Entidades-chave

- **Linha de log**: uma ocorrência emitida por um contêiner, com timestamp, conteúdo textual e
  stream de origem (`stdout`/`stderr`).
- **Rótulos (labels) de stream**: pares chave/valor de baixa cardinalidade, derivados dos
  metadados do contêiner, usados para indexar e filtrar as linhas de log.
- **Coletor (Promtail)**: agente que descobre contêineres, lê os logs deles, aplica os rótulos
  e envia ao armazenamento central. Mantém o estado da posição de leitura.
- **Armazenamento central (Loki)**: serviço que recebe, indexa por rótulos, retém e responde
  consultas sobre as linhas de log.

## Critérios de Sucesso *(obrigatório)*

### Resultados Mensuráveis

- **SC-001**: 100% dos contêineres ativos no escopo definido (FR-013) têm logs consultáveis no
  armazenamento central, sem configuração manual por contêiner.
- **SC-002**: Uma linha escrita em `stdout`/`stderr` por qualquer contêiner no escopo fica
  consultável em até 10 segundos em condições normais.
- **SC-003**: Um contêiner novo começa a ter logs coletados em até 30 segundos após iniciar,
  sem reinício da stack de observabilidade.
- **SC-004**: Depois de reiniciar o coletor, não há lacuna de logs para contêineres que
  continuaram rodando durante o reinício.
- **SC-005**: Uma consulta filtrada por serviço do Compose retorna apenas linhas desse
  serviço (0 falsos positivos em teste com ≥ 2 serviços).
- **SC-006**: 0 serviços definidos no repositório configurados para gravar logs em arquivo
  local (verificável por revisão dos arquivos Compose/configuração).

## Premissas

- O ambiente-alvo é Docker Engine com Docker Compose v2, num único host (sem orquestração
  multi-nó nesta Issue).
- Os contêineres usam o driver de log padrão do Docker (`json-file`), que o coletor lê.
- A visualização (ex.: Grafana) e os alertas sobre logs ficam **fora do escopo** desta Issue e
  serão tratados em issues próprias da stack de observabilidade.
- O agrupamento de linhas multilinha (ex.: stack traces) e o parsing de logs estruturados
  (JSON) em rótulos extras ficam fora do escopo inicial. As linhas são ingeridas como estão.
- O arquivo `infra/compose.obs.yml` ainda não existe e será criado por esta Issue (ou por uma
  issue irmã da stack de observabilidade, se houver).
- Autenticação/multi-tenant no Loki não é necessária para o ambiente atual (uso
  single-tenant).

## Fora do Escopo

- Dashboards, data sources e alertas no Grafana.
- Métricas (Prometheus) e traces (Tempo/OpenTelemetry).
- Coleta de logs do sistema operacional do host (journald, `/var/log`).
- Ambientes Kubernetes.

## Próximas Etapas do Fluxo SDD

1. `/speckit-clarify` — resolver os 3 pontos `[NEEDS CLARIFICATION]` (FR-011, FR-012, FR-013).
2. `/speckit-plan` — decidir versões de imagem, estrutura dos arquivos de configuração, rede,
   volumes e estratégia de validação.
3. `/speckit-tasks` — quebrar o plano em tarefas executáveis.
4. `/speckit-implement` — gerar `infra/compose.obs.yml`, `infra/promtail/config.yaml` e
   `infra/loki/config.yaml`.
