# Constituição de Boas Práticas de Spec Driven Development

0. Visão de Arquitetura do Monorepo
- O projeto deve ser tratado como um monorepo composto por múltiplos aplicativos e bibliotecas compartilhadas.
- A pasta `/apps` deve conter aplicações executáveis independentes, cada uma com seu próprio contexto de execução, dependências e configuração.
- A pasta `/libs` deve conter bibliotecas reutilizáveis, utilitários, integrações e componentes compartilhados por vários apps.
- Cada app e biblioteca deve ser entendido como um componente independente, mas sujeitos a padrões comuns de qualidade, observabilidade, segurança e documentação.
- A arquitetura deve distinguir claramente entre aplicativos locais do repositório, serviços de infraestrutura e componentes externos ou gerenciados.
- O ambiente de desenvolvimento pode combinar apps locais e serviços compartilhados em Docker Compose; o ambiente de produção pode utilizar imagens pré-construídas, serviços gerenciados ou uma combinação explícita de ambos.
- A decisão entre `build` local e `image` pronta deve ser declarada por serviço e por ambiente, nunca assumida implicitamente.

1. Boas Práticas de Desenvolvimento em Python
- Utilizar o `uv` para isolar as dependências do projeto e nunca as instalar no sistema global.
- Sempre utilizar, ou criar quando não houver, ambientes virtuais separados para cada aplicação (dentro da pasta `/apps`) ou biblioteca (dentro da pasta `/libs`) usando `uv venv`.
- Quando um app em monorepo puder ser executado isoladamente, ele deve manter seu próprio `pyproject.toml`, dependências e configuração de execução.
- Siga a PEP 8 utilizando o formatador automático `Black` e o linter `Ruff`.
- Utilize dicas de tipo (Type Hinting) para melhorar a legibilidade e validadores estáticos como o `mypy`.
- Escreva testes automatizados utilizando o framework `pytest` e valide a cobertura com o `pytest-cov`.
- Gerencie suas dependências de forma clara utilizando `pyproject.toml`.
- Configure seu arquivo `.gitignore` para ignorar ambientes virtuais, arquivos gerados automaticamente e credenciais.
- Automatize as verificações de código (testes, linters e tipagem) utilizando ferramentas de CI/CD como GitHub Actions.
- O código nunca deve instanciar loggers isolados do zero; deve-se sempre importar e utilizar o módulo utilitário centralizado criado em `utils_lib.logger`.
- Cada app deve manter contratos claros de entrada, saída e dependências de infraestrutura, evitando acoplamento implícito entre serviços do monorepo.

2. Boas Práticas de Documentação Python
- Documente classes e funções Python com docstrings conforme a convenção da PEP 257 e utilizando o padrão Google Style.
- Faça um resumo claro na primeira linha, descreva o que faz, não como faz.
- Explicar parâmetros, retornos e exceções de forma consistente.
- Manter docstrings atualizadas quando o código muda.
- Evitar duplicação de informações já cobertas por type hints.
- Usar exemplos simples que podem ser testados com `doctest`.
- Quando um módulo for compartilhado por vários apps, sua documentação deve deixar explícitas as responsabilidades, dependências e limitações de uso.

3. Boas Práticas para Projetos Docker Compose
- Utilize a nomenclatura padrão `compose.yaml` e faça a divisão de configurações por ambientes utilizando arquivos como `compose.override.yaml`.
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

4. Boas Práticas para Observabilidade em Múltiplos Servidores e Serviços
- Centralize a agregação de logs usando a ferramenta Grafana Loki, e certifique-se de usar logs estruturados, como JSON.
- Todas as aplicações são estritamente proibidas de escrever logs diretamente em arquivos de disco ou console (`print` ou `println`).
- Implemente o rastreamento distribuído propagando IDs de Correlação (Trace IDs e Span IDs) pelas requisições usando o padrão OpenTelemetry.
- Extraia e monitore métricas de negócio e infraestrutura usando modelos baseados em pull (Prometheus) e crie painéis centralizados no Grafana.
- Configure alertas focando em sintomas perceptíveis (ex: taxa de erros) e evite a fadiga gerada por alertas de anomalias sem impacto real.
- Evite acoplamentos e padronize a coleta de logs, métricas e traces utilizando o OpenTelemetry.
- Mantenha monitoramentos sintéticos externos pingando continuamente seus endpoints para garantir o uptime do sistema.
- Realize revisões periódicas das configurações de observabilidade para garantir que novos serviços e alterações no sistema sejam devidamente monitorados.
- Em ambientes com vários apps e serviços, a observabilidade deve ser consistente em todos os componentes do monorepo, independentemente de estarem rodando localmente em Compose ou em imagens de produção.

5. Boas Práticas de Segurança em Múltiplos Servidores
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

6. Checklist Operacional para Monorepo e Docker Compose
- Cada app em `/apps` deve ter uma definição clara de responsabilidades, dependências e ambiente de execução.
- Cada biblioteca em `/libs` deve ser reutilizável, testada e documentada, sem depender de execução isolada de um app específico.
- Todo serviço em Compose deve indicar se usa `build`, `image`, `env_file`, `volumes`, `network` e `depends_on` de forma explícita.
- Qualquer dado sensível deve estar em `.env` ou em secret manager, nunca hardcoded no repositório.
- Toda dependência de infra (banco, fila, cache, observabilidade) deve estar mapeada e versionada junto ao ambiente em que é utilizada.
- A execução local em Docker Compose deve ser tratada como um ambiente de desenvolvimento e não como substituto da arquitetura de produção.
- O repositório deve permitir desenvolvimento em múltiplos apps sem mistura de dependências, sem acúmulo de ambientes globais e sem ambiguidade entre aplicações locais e serviços externos.
- Antes de fechar uma alteração, verificar: app isolado, lib compartilhada, Compose válido, observabilidade mantida e segurança preservada.

7. Princípio de Consistência do Monorepo
- Todo app, biblioteca e serviço deve seguir as mesmas regras de qualidade, documentação e segurança, mesmo quando forem executados em contextos diferentes.
- O monorepo deve facilitar a colaboração entre times e a execução paralela de componentes sem conflitar ambientes, ports ou dependências globais.
- Quando houver múltiplos serviços em execução, o padrão operacional deve ser consistente e facilmente compreensível por qualquer desenvolvedor que entre no projeto.
- O que vale para um app local deve valer para qualquer outro app do monorepo, com ajustes explícitos apenas por necessidade de infraestrutura, ambiente ou arquitetura.
