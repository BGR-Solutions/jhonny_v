# LiteLLM Proxy Contract

## Purpose

Definir o contrato funcional e operacional do proxy de modelos para descoberta, autenticação e roteamento entre modelos locais e cloud.

## Endpoint Contract

| Endpoint | Authentication | Expected Behavior | Failure Contract |
|----------|----------------|-------------------|------------------|
| `GET /v1/models` | Obrigatória (chave mestre) | Lista todos os aliases configurados, sem sinalizar disponibilidade de credenciais | Sem chave: `401`; chave malformada: `401`; chave inválida: `403` |
| `POST /v1/chat/completions` | Obrigatória (chave mestre) | Executa chamada para rota válida configurada | Sem chave: `401`; chave malformada: `401`; chave inválida: `403` |
| `GET /health/liveliness` | Não requerida | Informa somente se o processo está vivo; não inclui dados de modelos ou credenciais | Exceção limitada à autenticação de API |

`GET /v1/models` lista todos os aliases configurados, independentemente de credenciais disponíveis. A listagem não contém metadados de disponibilidade; uma chamada cloud sem credenciais retorna `503`.

## Authorization & Error Matrix

| Condition | Expected Status | Notes |
|----------|------------------|-------|
| Header ausente | `401` | Rejeição antes de qualquer validação de rota |
| Header malformado | `401` | Rejeição antes de qualquer validação de rota |
| Chave inválida | `403` | Rejeição antes de qualquer validação de rota |
| Alias malformado/não suportado no payload | `400` | Erro de requisição inválida |
| Rota inexistente | `404` | Distinto de `503` |
| Rota cloud sem credencial | `503` | Indisponibilidade por credencial |
| Falha runtime de provedor cloud | `5xx` da rota solicitada | Sem fallback automático |

## Error Precedence Contract

1. Autenticação falha (`401`/`403`) sempre tem prioridade sobre erros de rota.
2. Erros de payload/alias (`400`) são avaliados antes de existência de rota (`404`) ou indisponibilidade por credencial (`503`).
3. `404` (rota inexistente) prevalece sobre `503` quando a rota não existe.
4. `503` aplica-se somente a rota cloud existente sem credencial.
5. Falha runtime preserva erro da rota alvo (sem fallback para local).

## Routing Contract

1. Rotas locais devem permanecer disponíveis quando credenciais cloud não existirem.
2. Rotas cloud sem credencial devem ser tratadas como indisponíveis ao serem invocadas.
3. Rotas inexistentes devem ser diferenciadas de rotas indisponíveis por credencial.
4. Falhas runtime em rota cloud não devem acionar fallback automático para rota local.

## Error Semantics Contract

| Scenario | Contractual Result |
|----------|--------------------|
| Rota inexistente | Erro de rota não encontrada (distinto de indisponibilidade por credencial) |
| Alias/payload inválido | Erro de requisição inválida (`400`) |
| Rota cloud sem credencial | Retorno de indisponibilidade (`503`) |
| Falha runtime em rota cloud | Retorno de erro da rota solicitada, sem fallback automático |
| Falha combinada (auth + rota) | Erro de autenticação conforme precedência |

## Configuration Contract

| Path | Contract |
|------|----------|
| `infra/compose.llm.yaml` | Define ciclo de vida do serviço LiteLLM no ambiente local e integração com rede/configuração compartilhada |
| `infra/litellm/config.yaml` | Define aliases de modelos, provedores alvo e regras de disponibilidade por credencial |
| `.env` / `.env.example` | Define chave mestre do proxy e credenciais opcionais de provedores cloud |

## Scope Boundaries

- Este contrato cobre apenas configuração e validação operacional do proxy no ambiente local.
- Não cobre alterações em código das aplicações consumidoras.
- Não cobre política de fallback avançada ou orquestração multi-região de provedores.
- Não cobre rate limiting, abuse protection ou rotação de chave mestre com garantia para requisições em voo nesta release.
