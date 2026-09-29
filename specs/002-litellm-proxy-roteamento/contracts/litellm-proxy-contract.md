# LiteLLM Proxy Contract

## Purpose

Definir o contrato funcional e operacional do proxy de modelos para descoberta, autenticação e roteamento entre modelos locais e cloud.

## Endpoint Contract

| Endpoint | Authentication | Expected Behavior | Failure Contract |
|----------|----------------|-------------------|------------------|
| `GET /v1/models` | Obrigatória (chave mestre) | Lista rotas/modelos disponíveis para consumo | Sem chave válida: acesso negado |
| `POST /v1/chat/completions` | Obrigatória (chave mestre) | Executa chamada para rota válida configurada | Sem chave válida: acesso negado |

## Routing Contract

1. Rotas locais devem permanecer disponíveis quando credenciais cloud não existirem.
2. Rotas cloud sem credencial devem ser tratadas como indisponíveis ao serem invocadas.
3. Rotas inexistentes devem ser diferenciadas de rotas indisponíveis por credencial.
4. Falhas runtime em rota cloud não devem acionar fallback automático para rota local.

## Error Semantics Contract

| Scenario | Contractual Result |
|----------|--------------------|
| Rota inexistente | Erro de rota não encontrada (distinto de indisponibilidade por credencial) |
| Rota cloud sem credencial | Retorno de indisponibilidade (`503`) |
| Falha runtime em rota cloud | Retorno de erro da rota solicitada, sem fallback automático |

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
