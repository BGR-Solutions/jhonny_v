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
4. Validar composição consolidada:
   - `docker compose -f infra/compose.yaml -f infra/compose.llm.yaml config`

## Validation Scenarios

### Scenario 1: Inicialização do proxy

1. Executar `docker compose -f infra/compose.yaml -f infra/compose.llm.yaml up -d`.
2. Verificar estado do serviço com `docker compose ps`.

**Expected outcome**: Serviço LiteLLM em execução sem depender obrigatoriamente de credenciais cloud.

### Scenario 2: Listagem de modelos com autenticação

1. Chamar `GET /v1/models` com chave mestre válida.
2. Repetir chamada sem chave ou com chave inválida.

**Expected outcome**: Com chave válida, listagem responde com sucesso; sem chave válida, acesso é negado.

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
