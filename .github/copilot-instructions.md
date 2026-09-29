# Constituição Ratificada do Jhonny-V

Status: Ratificada v1.0
Efeito: Esta constituição substitui qualquer orientação genérica do repositório e passa a funcionar como regra normativa de conformidade para arquitetura, implementação, auditoria e entrega.

## 1. Escopo e autoridade

1.1. A presente constituição governa todo trabalho no monorepo Jhonny-V, incluindo código, infraestrutura, documentação, especificações, processos de revisão e critérios de aprovação.
1.2. Qualquer artefato produzido no repositório deve ser interpretado como não conformante se contradizer qualquer regra obrigatória desta constituição.
1.3. A falha em cumprir uma obrigação normativa desta constituição constitui bloqueio explícito de merge, release, aprovação de milestone ou execução de pipeline, salvo exceção formal registrada e aprovada por revisão de arquitetura.

## 2. Princípios normativos do monorepo

2.1. O repositório MUST ser tratado como monorepo com separação explícita entre `apps/`, `libs/`, `infra/` e `docs/`.
2.2. Cada aplicação em `apps/` MUST possuir isolamento operacional próprio, incluindo configuração, dependências, ambiente virtual e ciclo de execução independentes.
2.3. Cada biblioteca em `libs/` MUST ser reutilizável, documentada e sem acoplamento implícito a um único app.
2.4. A arquitetura MUST distinguir claramente entre serviços locais do repositório, infraestrutura compartilhada e componentes externos ou gerenciados.
2.5. A decisão entre `build` local e `image` remota MUST ser declarada por serviço e por ambiente, nunca assumida implicitamente.
2.6. O padrão de composição MUST seguir `compose.yaml` e `compose.override.yaml`; nomes antigos ou híbridos como `docker-compose.yml` MUST NOT ser usados em novas definições.

## 3. Regras obrigatórias de implementação

3.1. Dependências
3.1.1. O arquivo `requirements.txt` MUST NOT existir no repositório.
3.1.2. O gerenciamento de dependências, testes e metadados MUST ser centralizado em `pyproject.toml`.
3.1.3. Dependências de desenvolvimento MUST ser declaradas em `[project.optional-dependencies]` ou equivalente suportado pelo projeto.
3.1.4. Ambientes virtuais MUST ser gerenciados com `uv`, preferencialmente por app ou biblioteca.

3.2. Estrutura de aplicativos Python
3.2.1. Todo app em `apps/` MUST separar código em `src/` e testes em `tests/`.
3.2.2. O ponto de entrada `main.py` MUST ser mínimo e focado no ciclo de vida do processo, sem lógica de negócio dispersa.
3.2.3. Módulos compartilhados MUST preferencialmente residir em `libs/` e MUST ser reutilizados por referência explícita, sem duplicação estrutural.

3.3. Logs e observabilidade
3.3.1. Nenhuma aplicação MUST escrever logs em arquivo local.
3.3.2. Todo log MUST ser emitido para `stdout` ou `stderr` em formato JSON estruturado.
3.3.3. Cada evento de log MUST incluir `trace_id` e `span_id` quando houver contexto distribuído; ausência de contexto MUST ser tratada como falha de instrumentação.
3.3.4. O projeto MUST adotar e manter modelagem de observabilidade compatível com stack LGTMP (Loki, Grafana, Tempo/OTel, Prometheus, Mimir). 
3.3.5. Qualquer uso de `print` ou `println` em código de produção MUST ser tratado como violação de política.

3.4. Infraestrutura e segurança
3.4.1. `infra/` MUST conter a orquestração local de serviços compartilhados e o Compose base deve ser explícito sobre rede, volumes, healthchecks, depends_on e versões fixas.
3.4.2. Serviços MUST declarar explicitamente se usam `build`, `image`, `env_file`, `volumes`, `networks` e `depends_on`.
3.4.3. Segredos MUST ficar em `.env` ou em secret manager e MUST NOT ser committed no repositório.
3.4.4. Imagens no Compose MUST fixar versões e MUST NOT usar `:latest` em produção.
3.4.5. `healthcheck` MUST existir em serviços críticos e a inicialização MUST respeitar `depends_on` com `condition: service_healthy` quando houver dependência operacional.
3.4.6. Volumes nomeados MUST ser usados para persistência de dados de banco e fila.
3.4.7. O arquivo `.dockerignore` MUST excluir `.venv/`, `__pycache__/` e `secrets/`.
3.4.8. O projeto MUST evitar hardcode de credenciais e MUST manter ambiente local e produção claramente separados.

3.5. Qualidade e testes
3.5.1. Código Python MUST seguir PEP 8 e utilizar Black e Ruff como padrões de formatação e lint.
3.5.2. Funções, classes e módulos publicamente compartilhados MUST usar type hints e documentação em estilo Google quando aplicável.
3.5.3. Testes MUST ser implementados com `pytest` e validados por pipeline/CI antes da aprovação de mudança.
3.5.4. Testes automatizados MUST ser escritos antes da implementação funcional quando a mudança aumentar risco ou alterar comportamento de contrato.
3.5.5. Módulos reutilizados MUST documentar responsabilidades, dependências e limitações explícitas.

## 4. Sequência de execução obrigatória

4.1. O desenvolvimento MUST seguir a ordem bottom-up:
4.1.1. Fase 1 — v0.1 Infra Core: infraestrutura e composição base.
4.1.2. Fase 2 — v0.2 MCP Server: ferramentas e transporte.
4.1.3. Fase 3 — v0.3 Agent Orchestrator: grafos, memória e integração.
4.1.4. Fase 4 — v0.4 Worker: consumidores assíncronos e fila.
4.2. Nenhuma fase posterior MAY ser considerada válida antes da maturidade funcional da infraestrutura e dos braços de execução precedentes.

## 5. Fluxo SDD obrigatório

5.1. Para cada issue, milestone ou mudança arquitetural, o agente MUST executar, na ordem, os gates abaixo:
5.1.1. `specify` — especificação técnica inicial vinculada à constituição.
5.1.2. `clarify` — eliminação de ambiguidades críticas antes da implementação.
5.1.3. `plan` — arquitetura, dados, integrações e arquivos afetados.
5.1.4. `checklist` — critérios de aceitação e definição de pronto.
5.1.5. `tasks` — decomposição em passos atômicos.
5.1.6. `analyze` — revisão de risco contra a constituição.
5.1.7. `implement` — codificação com testes automatizados e validação final.
5.2. Qualquer etapa do fluxo SDD MUST ser considerada incompleta se a análise constitucional não forem concluída.
5.3. A geração de código sem o fechamento do plano e da análise de risco MUST ser tratada como não conformante.

## 6. Critérios de auditoria objetiva

6.1. Conformidade MUST ser avaliada por evidência verificável, não por intenção declarada.
6.2. Cada mudança deve ser auditável por pelo menos uma das seguintes evidências:
6.2.1. arquivo de configuração atual no repositório;
6.2.2. testes automatizados executados;
6.2.3. estrutura de diretórios e arquivos efetiva;
6.2.4. resultado de validação de Compose, lint, testes ou checagem de importação.
6.3. A ausência de evidência objetiva MUST ser tratada como falha de conformidade.
6.4. Mudanças que introduzirem `requirements.txt`, logs em disco, hardcoded secrets, rede implícita ou estrutura de app fora do padrão MUST ser bloqueadas imediatamente.

## 7. Estado de aprovação e bloqueio

7.1. O projeto MUST ser considerado em estado de conformidade somente quando todos os critérios obrigatórios desta constituição forem atendidos.
7.2. Qualquer violação de regra normativa MUST resultar em bloqueio de entrega até correção e revalidação.
7.3. Esta constituição deve ser revisada formalmente sempre que houver mudança de arquitetura, regulatório, infraestrutura ou política de segurança.

## 8. Resumo executivo

A conformidade do Jhonny-V depende de: isolamento real de apps e libs, governança estrita de dependências, observabilidade distribuída, infraestrutura declarada e SDD obrigatório. Regras vagas ou interpretações subjetivas não são válidas; a execução do projeto deve ser demonstrável por artefatos, configuração e evidência operacional.
