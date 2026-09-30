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
3. (Opcional) Definir credenciais cloud para ativar rotas externas.
4. Para usar provedores cloud reais, sobrescrever `OPENAI_API_BASE`/`ANTHROPIC_API_BASE` com endpoints dos provedores; por padrão o ambiente local usa um endpoint mock de indisponibilidade (`503`) para rotas cloud sem credencial.
5. Para validar chat local sem dependência externa, o ambiente usa por padrão `OLLAMA_API_BASE=http://ollama-local-mock:11435`. Para usar Ollama real, sobrescrever para `http://ollama:11434` e garantir modelo disponível.
6. Validar composição consolidada:
   - `docker compose -f infra/compose.yaml -f infra/compose.llm.yaml config`

## Validation Scenarios

### Scenario 1: Inicialização do proxy

1. Executar `docker compose -f infra/compose.yaml -f infra/compose.llm.yaml up -d`.
2. Verificar estado do serviço com `docker compose ps`.

**Expected outcome**: Serviço LiteLLM em execução sem depender obrigatoriamente de credenciais cloud.

### Scenario 2: Listagem de modelos com autenticação

1. Chamar `GET /v1/models` com chave mestre válida.
2. Repetir chamada sem chave, com chave malformada e com chave inválida.

**Expected outcome**: Com chave válida, listagem responde com sucesso; sem chave ou chave malformada retorna `401`; chave inválida retorna `403`.

### Scenario 3: Chat em rota válida

1. Executar `POST /v1/chat/completions` para rota local com chave mestre válida.

**Expected outcome**: Chamada processada com sucesso pela rota configurada.

### Scenario 4: Rota cloud sem credencial

1. Garantir ausência de credencial cloud no `.env`.
2. Executar `POST /v1/chat/completions` para rota cloud configurada.

**Expected outcome**: Retorno consistente de indisponibilidade (`503`) para rota cloud sem credencial.

### Scenario 5: Falha runtime sem fallback automático

1. Simular falha do provedor cloud (timeout/erro) em uma rota cloud.
2. Repetir chamada de chat para a mesma rota.

**Expected outcome**: Proxy retorna erro da rota solicitada sem redirecionar automaticamente para rota local.

### Scenario 6: Alias malformado e rota inexistente

1. Executar `POST /v1/chat/completions` com alias malformado/não suportado.
2. Executar `POST /v1/chat/completions` com alias bem formado, porém inexistente.

**Expected outcome**: Alias malformado retorna `400`; rota inexistente retorna `404`; ambos distintos de `503`.

### Scenario 7: Precedência de erros em falha combinada

1. Enviar requisição com chave inválida e alias inexistente.
2. Enviar requisição autenticada para rota cloud sem credencial.

**Expected outcome**: No caso combinado, prevalece erro de autenticação (`401`/`403`); com autenticação válida, aplica-se semântica de rota (`404`/`503`).

### Scenario 8: Recuperação após falha transitória cloud

1. Forçar falha transitória de provedor cloud.
2. Restabelecer disponibilidade do provedor.
3. Repetir chamada para a mesma rota cloud.

**Expected outcome**: Após normalização do provedor, rota volta a responder sem alterações manuais de configuração.

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
- Com chave inválida no header `x-api-key`, endpoint retornou `400` (`No connected db`) neste runtime atual do LiteLLM, divergindo da semântica alvo documentada.

### Cloud Without Credential Evidence (SC-007)

- Request: `POST /v1/chat/completions` com `model=cloud-openai-gpt-4o-mini`, sem `OPENAI_API_KEY` configurada.
- Response: `503`
- Body excerpt: `cloud_route_unavailable_without_credentials`

### Local Chat Authorized Evidence (SC-003 / T020 / T026)

- Request: `POST /v1/chat/completions` com `model=local-ollama-llama3` e `x-api-key` válido.
- Response: `200`
- Body excerpt: `mock response from local ollama backend`
- `GET /v1/models` com `x-api-key` válido: `200`
