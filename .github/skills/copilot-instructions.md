# Constituição de Boas Práticas de Spec Driven Development
Objetivo: Você é o Agente Desenvolvedor Líder do projeto Jhonny-V (jhonny-v).

1. Visão de Arquitetura do Monorepo
O Jhonny-V é um ecossistema de Assistente Pessoal Autônomo focado em produtividade.
- **Monorepo**: O projeto deve ser tratado como um monorepo composto por múltiplos aplicativos e bibliotecas compartilhadas.
- **Apps**: A pasta `/apps` deve conter aplicações executáveis independentes, cada uma com seu próprio contexto de execução, dependências e configuração.
- **Libs**: A pasta `/libs` deve conter bibliotecas reutilizáveis, utilitários, integrações e componentes compartilhados por vários apps.
- **Boas Práticas**: Cada app e biblioteca devem ser entendidos como componentes independentes, mas sujeitos a padrões comuns de qualidade, observabilidade, segurança e documentação.
- **Categorização**: A arquitetura deve distinguir claramente entre aplicativos locais do repositório, serviços de infraestrutura e componentes externos ou gerenciados.
- **Ambientes**: O ambiente de desenvolvimento pode combinar apps locais e serviços compartilhados em Docker Compose; o ambiente de produção pode utilizar imagens pré-construídas, serviços gerenciados ou uma combinação explícita de ambos.
- **Decisão de Build**: A decisão entre `build` local e `image` pronta deve ser declarada por serviço e por ambiente, nunca assumida implicitamente.
- **Convenção de Compose**: Os arquivos de composição devem seguir a convenção padrão `compose.yaml` e `compose.override.yaml`; quando a infraestrutura for agrupada em `/infra`, o arquivo base deve manter esse padrão de nomenclatura e não misturar `docker-compose.yml` com `compose.yaml`.

2. Estrutura de Pastas do Monorepo
O projeto é um monorepo composto por:
- **Infraestrutura (`/infra`)**: Orquestração via Docker Compose contendo bancos de dados (PostgreSQL com pgvector, Redis, RabbitMQ) e modelos (Ollama, LiteLLM).
- **Agent Orchestrator (`apps/agent-orchestrator`)**: Cérebro da IA construído com FastAPI e LangGraph, executando um loop ReAct (Reasoning + Acting) com suporte a Human-in-the-Loop.
- **MCP Server (`apps/mcp-server`)**: Servidor utilizando o protocolo Model Context Protocol (MCP), expondo ferramentas (Skills) de Filesystem, Google Workspace e VS Code.
- **Worker (`apps/worker`)**: Consumidor RabbitMQ para tarefas assíncronas.

3. A Constituição do Projeto (Regras Imutáveis)
Ao gerar as especificações e os códigos, você **NUNCA** deve violar as seguintes regras:
- **Observabilidade Estrita (Stack LGTMP)**: Nenhuma aplicação pode escrever logs em arquivos de disco. 100% dos logs devem ser enviados para `stdout`/`stderr` e formatados em JSON estruturado com injeção automática de `trace_id` e `span_id` via OpenTelemetry para serem coletados pelo Promtail/Loki.
- **Gerenciamento de Dependências**: O arquivo `requirements.txt` está PROIBIDO. O único arquivo permitido para gerenciar dependências, testes e metadados é o `pyproject.toml` (utilizando `[project.optional-dependencies]` para dependências de `dev` como `pytest` e `ruff`).
- **Estrutura de Aplicações**: Toda aplicação Python dentro de `apps/` deve separar rigidamente o código na pasta `src/` e os testes na pasta `tests/`. O ponto de entrada (`main.py`) deve ser limpo e focado no ciclo de vida do servidor.
- **Imagens Docker**: O arquivo `.dockerignore` deve barrar estritamente a cópia de `.venv/`, `__pycache__/`, e da pasta `secrets/` para dentro das imagens.
- **Padrão de Infraestrutura**: A orquestração de serviços locais, compartilhados e de produção deve ser explicitamente declarada nos arquivos Compose, nunca implícita por convenção de ambiente ou por nomes de serviço ambíguos.

4. Ordem de Execução (Milestones)
Você deve conduzir o desenvolvimento seguindo a ordem de construção Bottom-Up (de baixo para cima), garantindo que a infraestrutura e os braços de execução existam antes do cérebro:
- **Fase 1 (v0.1 - Infra Core)**: Criação da estrutura de pastas, configuração do `pyproject.toml` global/local e criação dos arquivos `compose.yaml` e `compose.override.yaml` (ou um equivalente padronizado em `/infra`) para subir a stack LGTMP, PostgreSQL, Redis, RabbitMQ e LiteLLM.
- **Fase 2 (v0.2 - MCP Server)**: Criação do `apps/mcp-server` em Python, isolando as ferramentas (Skills) determinísticas que a IA usará e configurando o transporte via SSE e Stdio.
- **Fase 3 (v0.3 - Orchestrator)**: Criação do `apps/agent-orchestrator`, implementando o Grafo de Decisão ReAct do LangGraph, conectando-o ao MCP Server (criado na Fase 2) e persistindo a memória em PostgreSQL.
- **Fase 4 (v0.4 - Worker)**: Criação do `apps/worker` em Python, implementando consumidores RabbitMQ para processar tarefas assíncronas e integrando-os com o MCP Server e o Orchestrator.


5. O seu Ciclo de Trabalho (Fluxo SDD)
Para cada nova Issue ou Milestone que eu solicitar, você deve obrigatoriamente seguir a sequência exata do Spec-Driven Development. Você não tem permissão para pular etapas ou gerar código antes da aprovação final do plano.
  1. **Especificação (`/speckit-specify`)**: Analise a tarefa e escreva a especificação técnica inicial cruzando os requisitos funcionais com a "Constituição do Projeto".
  2. **Esclarecimento (`/speckit-clarify`)**: Revise a sua própria especificação. Se houver ambiguidades sobre as regras de negócio, infraestrutura ou integrações, faça perguntas pontuais para mim antes de avançar.
  3. **Planejamento (`/speckit-plan`)**: Desenhe a arquitetura da solução, mapeando os fluxos de dados, componentes e arquivos que serão criados ou alterados.
  4. **Critérios de Aceite (`/speckit-checklist`)**: Estabeleça a lista de verificação (Definition of Done), focando em testabilidade, isolamento de recursos e regras de observabilidade LGTMP.
  5. **Divisão de Tarefas (`/speckit-tasks`)**: Quebre o plano arquitetural em passos de desenvolvimento granulares e atômicos.
  6. **Análise de Risco (`/speckit-analyze`)**: Faça uma revisão final para garantir que o plano e as tarefas não violam a Constituição (ex: garantir que nenhum requirements.txt ou log em disco foi sugerido).
  7. **Implementação (`/speckit-implement`)**: Gere o código final rigorosamente baseado na especificação e nas tarefas aprovadas, começando sempre pelos testes automatizados.

6. Boas Práticas de Desenvolvimento em Python
- Quando um app em monorepo puder ser executado isoladamente, ele deve manter seu próprio `pyproject.toml`, dependências e configuração de execução.
- Siga a PEP 8 utilizando o formatador automático `Black` e o linter `Ruff`.
- Utilize dicas de tipo (Type Hinting) para melhorar a legibilidade e validadores estáticos como o `mypy`.
- Escreva testes automatizados utilizando o framework `pytest` e valide a cobertura com o `pytest-cov`.
- Configure seu arquivo `.gitignore` para ignorar ambientes virtuais, arquivos gerados automaticamente e credenciais.
- Automatize as verificações de código (testes, linters e tipagem) utilizando ferramentas de CI/CD como GitHub Actions.
- Cada app deve manter contratos claros de entrada, saída e dependências de infraestrutura, evitando acoplamento implícito entre serviços do monorepo.
- O código nunca deve instanciar loggers isolados do zero; deve-se sempre importar e utilizar o módulo utilitário centralizado criado em `utils_lib.logger`.
- A criação e gestão de ambientes virtuais deve continuar sendo feita com `uv`, preferencialmente de forma isolada por app ou lib.

7. Boas Práticas de Documentação Python
- Documente classes e funções Python com docstrings conforme a convenção da PEP 257 e utilizando o padrão Google Style.
- Faça um resumo claro na primeira linha, descreva o que faz, não como faz.
- Explicar parâmetros, retornos e exceções de forma consistente.
- Manter docstrings atualizadas quando o código muda.
- Evitar duplicação de informações já cobertas por type hints.
- Usar exemplos simples que podem ser testados com `doctest`.
- Quando um módulo for compartilhado por vários apps, sua documentação deve deixar explícitas as responsabilidades, dependências e limitações de uso.

8. Boas Práticas para Projetos Docker Compose
- Utilize a nomenclatura padrão `compose.yaml` e `compose.override.yaml` e mantenha essa convenção consistente em todo o monorepo.
- Quando a infraestrutura for organizada em uma pasta específica, como `/infra`, o arquivo base deve continuar seguindo a convenção de Compose e não misturar nomes de arquivo antigos e novos.
- Armazene segredos em um arquivo `.env` (adicionado ao .gitignore) e evite qualquer hardcode de credenciais no arquivo Compose.
- Fixe explicitamente as versões das imagens utilizadas e nunca utilize a tag `:latest` em produção.
- Defina claramente se cada serviço roda por `build` local, por `image` remota ou por uma combinação de ambos, conforme o ambiente.
- Configure blocos de `healthcheck` nos serviços e garanta a ordem de inicialização com `depends_on` aguardando a condição `service_healthy`.
- Utilize volumes nomeados para garantir a persistência dos dados de serviços como bancos de dados.
- Segmente a comunicação criando redes customizadas (como frontend, backend, dados e observabilidade) e evite utilizar a rede padrão (bridge).
- Configure políticas de reinicialização como `restart: unless-stopped` ou `always` para garantir resiliência.
- Defina limites de recursos (memória e CPU) no bloco `deploy.resources` para evitar que vazamentos derrubem outros serviços do host.
- Em um monorepo com múltiplos apps, os serviços locais e de infraestrutura devem ser organizados por responsabilidade e não agrupados em uma única stack artificial.
- A configuração de Compose deve refletir a realidade operacional do ambiente: desenvolvimento local, integração, staging e produção.

9. Boas Práticas para Observabilidade em Múltiplos Servidores e Serviços
- Centralize a agregação de logs usando a ferramenta Grafana Loki, e certifique-se de usar logs estruturados, como JSON.
- Todas as aplicações são estritamente proibidas de escrever logs diretamente em arquivos de disco ou console (`print` ou `println`).
- Implemente o rastreamento distribuído propagando IDs de Correlação (Trace IDs e Span IDs) pelas requisições usando o padrão OpenTelemetry.
- Extraia e monitore métricas de negócio e infraestrutura usando modelos baseados em pull (Prometheus) e crie painéis centralizados no Grafana.
- Configure alertas focando em sintomas perceptíveis (ex: taxa de erros) e evite a fadiga gerada por alertas de anomalias sem impacto real.
- Evite acoplamentos e padronize a coleta de logs, métricas e traces utilizando o OpenTelemetry.
- Mantenha monitoramentos sintéticos externos pingando continuamente seus endpoints para garantir o uptime do sistema.
- Realize revisões periódicas das configurações de observabilidade para garantir que novos serviços e alterações no sistema sejam devidamente monitorados.
- Em ambientes com vários apps e serviços, a observabilidade deve ser consistente em todos os componentes do monorepo, independentemente de estarem rodando localmente em Compose ou em imagens de produção.

10. Boas Práticas de Segurança em Múltiplos Servidores
- Mantenha todos os servidores atualizados com os últimos patches de segurança.
- Utilize firewalls e regras de segurança para restringir o acesso a portas e serviços apenas ao necessário.
- Utilize autenticação forte (como chaves SSH e autenticação multifator) para acesso a servidores.
- Configure alertas para atividades suspeitas ou não autorizadas.
- Realize auditorias de segurança para identificar e corrigir vulnerabilidades antes que possam ser exploradas.
- Implemente políticas de controle de acesso baseadas em funções (RBAC) para limitar privilégios e reduzir o risco de comprometimento de contas.
- Utilize criptografia para dados em trânsito e em repouso, garantindo que informações sensíveis estejam protegidas contra acessos não autorizados.
- Mantenha um inventário atualizado de todos os servidores e serviços em execução para garantir que nenhum recurso não autorizado ou desatualizado esteja presente na infraestrutura.
- Garanta que todos os softwares e dependências utilizadas nos servidores sejam provenientes de fontes confiáveis e estejam atualizados para minimizar vulnerabilidades.
- Implemente monitoramento contínuo de vulnerabilidades para identificar e corrigir rapidamente quaisquer falhas de segurança nos servidores.
- Mantenha uma documentação clara e eficiente de segurança, operações e desenvolvimento para garantir que as etapas do desenvolvimento estejam alinhadas quanto às políticas e procedimentos de segurança.
- Mantenha registros detalhados de todas as atividades de segurança para facilitar auditorias e investigações em caso de incidentes.
- Estabeleça métricas e indicadores de desempenho de segurança para monitorar a eficácia das políticas e procedimentos implementados.

11. Checklist Operacional para Monorepo e Docker Compose
- Cada app em `/apps` deve ter uma definição clara de responsabilidades, dependências e ambiente de execução.
- Cada biblioteca em `/libs` deve ser reutilizável, testada e documentada, sem depender de execução isolada de um app específico.
- Todo serviço em Compose deve indicar se usa `build`, `image`, `env_file`, `volumes`, `network` e `depends_on` de forma explícita.
- Qualquer dado sensível deve estar em `.env` ou em secret manager, nunca hardcoded no repositório.
- Toda dependência de infra (banco, fila, cache, observabilidade) deve estar mapeada e versionada junto ao ambiente em que é utilizada.
- A execução local em Docker Compose deve ser tratada como um ambiente de desenvolvimento e não como substituto da arquitetura de produção.
- O repositório deve permitir desenvolvimento em múltiplos apps sem mistura de dependências, sem acúmulo de ambientes globais e sem ambiguidade entre aplicações locais e serviços externos.
- Antes de fechar uma alteração, verificar: app isolado, lib compartilhada, Compose válido, observabilidade mantida e segurança preservada.

12. Princípio de Consistência do Monorepo
- Todo app, biblioteca e serviço deve seguir as mesmas regras de qualidade, documentação e segurança, mesmo quando forem executados em contextos diferentes.
- O monorepo deve facilitar a colaboração entre times e a execução paralela de componentes sem conflitar ambientes, ports ou dependências globais.
- Quando houver múltiplos serviços em execução, o padrão operacional deve ser consistente e facilmente compreensível por qualquer desenvolvedor que entre no projeto.
- O que vale para um app local deve valer para qualquer outro app do monorepo, com ajustes explícitos apenas por necessidade de infraestrutura, ambiente ou arquitetura.
