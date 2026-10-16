# Quickstart: Configuração do LiteLLM Proxy e Roteamento de Modelos

## Purpose

Validar ponta a ponta que o proxy LiteLLM está configurado com autenticação, roteamento híbrido (local/cloud) e semântica de erro esperada.

Consulte também:
- [LiteLLM Proxy Contract](./contracts/litellm-proxy-contract.md)
- [Data Model](./data-model.md)

## Prerequisites

- Repositório clonado localmente
- Docker Compose disponível
- Arquivo `.env` criado a partir de `.env.example`
- Chave mestre do proxy definida em `.env`

## Setup

1. Copiar `.env.example` para `.env`.
2. Definir chave mestre do proxy no `.env`.
3. (Opcional) Definir credenciais cloud para ativar rotas externas. Se as URLs base não forem sobrescritas, credenciais presentes fazem o serviço usar os endpoints oficiais; sem credenciais, o endpoint mock retorna `503`.
4. Para validar chat local sem depender do Ollama real, iniciar com `--profile validation` e sobrescrever `OLLAMA_API_BASE=http://ollama-local-mock:11435`. Por padrão, o proxy usa `http://ollama:11434`; garantir que o modelo esteja disponível.
5. Validar composição consolidada:
   - `docker compose -f infra/compose.yaml -f infra/compose.llm.yaml config`

## Validation Scenarios

### Scenario 1: Inicialização do proxy (SC-001, SC-002)

1. Executar `docker compose -f infra/compose.yaml -f infra/compose.llm.yaml up -d`.
2. Verificar estado do serviço com `docker compose ps`.

**Expected outcome**: Serviço LiteLLM em execução sem depender obrigatoriamente de credenciais cloud.

### Scenario 2: Listagem de modelos com autenticação (SC-002, SC-004, SC-006)

1. Chamar `GET /v1/models` com chave mestre válida.
2. Repetir chamada sem chave, com chave malformada e com chave inválida.

**Expected outcome**: Com chave válida, listagem responde com sucesso; sem chave ou chave malformada retorna `401`; chave inválida retorna `403`.

A listagem inclui todos os aliases configurados, inclusive rotas cloud indisponíveis por falta de credenciais. Ela não fornece metadados de disponibilidade; a tentativa de chat na rota cloud é que responde `503`.

### Scenario 3: Chat em rota válida (SC-003, SC-005)

1. Executar `POST /v1/chat/completions` para rota local com chave mestre válida.

**Expected outcome**: Chamada processada com sucesso pela rota configurada.

### Scenario 4: Rota cloud sem credencial (SC-007)

1. Garantir ausência de credencial cloud no `.env`.
2. Executar `POST /v1/chat/completions` para rota cloud configurada.

**Expected outcome**: Retorno consistente de indisponibilidade (`503`) para rota cloud sem credencial.

### Scenario 5: Falha runtime sem fallback automático (SC-008)

1. Simular falha do provedor cloud (timeout/erro) em uma rota cloud.
2. Repetir chamada de chat para a mesma rota.

**Expected outcome**: Proxy retorna erro da rota solicitada sem redirecionar automaticamente para rota local.

### Scenario 6: Alias malformado e rota inexistente (SC-010)

1. Executar `POST /v1/chat/completions` com alias malformado/não suportado.
2. Executar `POST /v1/chat/completions` com alias bem formado, porém inexistente.

**Expected outcome**: Alias malformado retorna `400`; rota inexistente retorna `404`; ambos distintos de `503`.

### Scenario 7: Precedência de erros em falha combinada (SC-010)

1. Enviar requisição com chave inválida e alias inexistente.
2. Enviar requisição autenticada para rota cloud sem credencial.

**Expected outcome**: No caso combinado, prevalece erro de autenticação (`401`/`403`); com autenticação válida, aplica-se semântica de rota (`404`/`503`).

### Scenario 8: Recuperação após falha transitória cloud (SC-008)

1. Forçar falha transitória de provedor cloud.
2. Restabelecer disponibilidade do provedor.
3. Repetir chamada para a mesma rota cloud.

**Expected outcome**: Após normalização do provedor, rota volta a responder sem alterações manuais de configuração.

### Scenario 9: Modo híbrido com credenciais cloud (SC-009)

1. Configurar as credenciais OpenAI e Anthropic no `.env`, sem sobrescrever as URLs base padrão.
2. Executar o proxy e enviar chamadas autenticadas para uma rota local e para cada rota cloud configurada.
3. Repetir a execução 10 vezes e registrar os resultados de cada provedor.

**Expected outcome**: O proxy inicia em todas as rodadas e as chamadas cloud usam os endpoints oficiais quando as credenciais estão presentes.

## Release Evidence (Mandatory)

Para cada cenário executado, registrar:

1. Comando executado (exato).
2. Timestamp da execução.
3. Resultado observado (status HTTP e resumo da resposta).
4. Índice da rodada (ex.: run 3/10).

## Pass/Fail Rules

- SC-001/SC-002: executar 10 rodadas de startup/listagem.
- SC-003/SC-005/SC-007/SC-008: executar 10 chamadas por cenário.
- SC-004/SC-006/SC-010: executar 20 chamadas por cenário.
- Se qualquer limiar mínimo não for atingido, status do gate é **FAIL**.
- Em resultado misto, reprovar até correção e nova rodada completa.

## Latest Execution Evidence (2026-09-30)

### Startup/Listagem Window (SC-001, SC-002)

- Rodadas executadas: 10
- `GET /v1/models` com `x-api-key` válido: 10/10 com status `200`
- Tempo até primeiro `200`: 9/10 em até 30s (rodada 1 levou 34s; demais entre 14s e 15s)

Resumo por rodada:

- run=1 elapsed=34s code=200
- run=2 elapsed=15s code=200
- run=3 elapsed=15s code=200
- run=4 elapsed=14s code=200
- run=5 elapsed=14s code=200
- run=6 elapsed=15s code=200
- run=7 elapsed=14s code=200
- run=8 elapsed=14s code=200
- run=9 elapsed=15s code=200
- run=10 elapsed=15s code=200

### Known Environment Constraints (pending validations)

- Ollama real pode falhar ao baixar modelos neste runner por restrição de DNS externo para `registry.ollama.ai`.
- Cenário cloud sem credencial passou a retornar `503` de forma determinística no ambiente local via endpoint mock `litellm-cloud-unavailable`.
- Com chave inválida no header `x-api-key`, endpoint retornou `400` (`No connected db`) neste runtime atual do LiteLLM, divergindo da resposta `403` esperada. SC-004/SC-006 e T025 permanecem pendentes.

### Diagnostic Samples (not release-gate evidence)

- Request: `POST /v1/chat/completions` com `model=cloud-openai-gpt-4o-mini`, sem `OPENAI_API_KEY` configurada.
- Response: `503`
- Body excerpt: `cloud_route_unavailable_without_credentials`

### Local Chat Authorized Evidence (SC-003 / T020 / T026)

- Request: `POST /v1/chat/completions` com `model=local-ollama-llama3` e `x-api-key` válido.
- Response: `200`
- Body excerpt: `mock response from local ollama backend`
- `GET /v1/models` com `x-api-key` válido: `200`

Essas amostras únicas não satisfazem os limites de 10/20 chamadas dos critérios de aceite. Os gates SC-003, SC-004, SC-006, SC-007, SC-008 e SC-009 continuam pendentes; não marcar T020, T021, T025, T026 ou T029 como concluídas até registrar todas as rodadas exigidas.
