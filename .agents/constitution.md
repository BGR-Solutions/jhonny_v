1. Boas Práticas de Desenvolvimento em Python
- Utilizar o `uv` para isolar as dependências do projeto e nunca as instale no sistema global.
- Sempre utilize, ou crie quando não houver, ambientes virtuais separados para cada aplicação (dentro da pasta `/apps`) ou biblioteca (dentro da pasta `/libs`) usando `uv venv`.
- Siga a PEP 8 utilizando o formatador automático `Black` e o linter `Ruff`.
- Utilize dicas de tipo (Type Hinting) para melhorar a legibilidade e validadores estáticos como o `mypy`.
- Escreva testes automatizados utilizando o framework `pytest` e valide a cobertura com o `pytest-cov`.
- Gerencie suas dependências de forma clara utilizando `pyproject.toml`.
- Configure seu arquivo `.gitignore` para ignorar ambientes virtuais, arquivos gerados automaticamente e credenciais.
- Automatize as verificações de código (testes, linters e tipagem) utilizando ferramentas de CI/CD como GitHub Actions.
- O código nunca deve instanciar loggers isolados do zero; deve-se sempre importar e utilizar o módulo utilitário centralizado criado em `utils_lib.logger`.

2. Boas Práticas de Documentação Python
- Documente classes e funções Python com docstrings conforme a convenção da PEP 257 e utilizando o padrão Google Style.
- Faça um resumo claro na primeira linha, descreva o que faz, não como faz.
- Explicar parâmetros, retornos e exceções de forma consistente.
- Manter docstrings atualizadas quando o código muda.
- Evitar duplicação de informações já cobertas por type hints.
- Usar exemplos simples que podem ser testados com `doctest`.

3. Boas Práticas para Projetos Docker Compose
- Utilize a nomenclatura padrão `compose.yaml` e faça a divisão de configurações por ambientes utilizando arquivos como `compose.override.yaml`.
- Armazene segredos em um arquivo `.env` (adicionado ao .gitignore) e evite qualquer hardcode de credenciais no arquivo Compose.
- Fixe explicitamente as versões das imagens utilizadas e nunca utilize a tag `:latest` em produção.
- Configure blocos de `healthcheck` nos serviços e garanta a ordem de inicialização com `depends_on` aguardando a condição `service_healthy`.
- Utilize volumes nomeados para garantir a persistência dos dados de serviços como bancos de dados.
- Segmente a comunicação criando redes customizadas (como frontend e backend) e evite utilizar a rede padrão (bridge).
- Configure políticas de reinicialização como `restart: unless-stopped` ou `always` para garantir resiliência.
- Defina limites de recursos (memória e CPU) no bloco `deploy.resources` para evitar que vazamentos derrubem outros serviços do host.

4. Boas Práticas para Observabilidade em Múltiplos Servidores
- Centralize a agregação de logs usando a ferramenta Grafana Loki, e certifique-se de usar logs estruturados, como JSON.
- Todas as aplicações são estritamente proibidas de escrever logs diretamente em arquivos de disco ou console (`print` ou `println`).
- Implemente o rastreamento distribuído propagando IDs de Correlação (Trace IDs e Span IDs) pelas requisições usando o padrão OpenTelemetry.
- Extraia e monitore métricas de negócio e infraestrutura usando modelos baseados em pull (Prometheus) e crie painéis centralizados no Grafana.
- Configure alertas focando em sintomas perceptíveis (ex: taxa de erros) e evite a fadiga gerada por alertas de anomalias sem impacto real.
- Evite acoplamentos e padronize a coleta de logs, métricas e traces utilizando o OpenTelemetry.
- Mantenha monitoramentos sintéticos externos pingando continuamente seus endpoints para garantir o uptime do sistema.
