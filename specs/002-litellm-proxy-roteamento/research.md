# Research: Configuração do LiteLLM Proxy e Roteamento de Modelos

## Decision 1: Modelo de composição da infraestrutura LLM

- **Decision**: Criar `infra/compose.llm.yaml` como overlay dedicado ao LiteLLM Proxy, mantendo `infra/compose.yaml` como base compartilhada.
- **Rationale**: Preserva a organização modular por responsabilidade, facilita ativação seletiva da stack de LLM e evita inflar o arquivo de serviços core.
- **Alternatives considered**:
  - Incluir LiteLLM em `compose.core.yaml` — rejeitado por misturar responsabilidades de core infra com integração de modelos.
  - Criar um compose isolado sem base compartilhada — rejeitado por perder reaproveitamento de rede/variáveis comuns.

## Decision 2: Fonte única de roteamento de modelos

- **Decision**: Versionar o roteamento em `infra/litellm/config.yaml` como arquivo único de definição de modelos e aliases.
- **Rationale**: Garante desacoplamento entre aplicações e escolha de modelos/provedores, permitindo evolução de rotas sem tocar código de app.
- **Alternatives considered**:
  - Definir rotas via variáveis inline no Compose — rejeitado por reduzir legibilidade e governança de mudanças.
  - Manter roteamento no código consumidor — rejeitado por conflitar com o objetivo da issue.

## Decision 3: Política de credenciais cloud ausentes

- **Decision**: O proxy sobe normalmente com rotas locais ativas quando credenciais cloud não estão definidas; rotas cloud ficam indisponíveis.
- **Rationale**: Mantém ambiente local funcional para validação mínima obrigatória e reduz bloqueios de onboarding.
- **Alternatives considered**:
  - Falhar startup sem credenciais cloud — rejeitado por quebrar fluxo local mesmo quando apenas rota local é necessária.
  - Expor rota cloud como válida até falhar tardiamente sem distinção — rejeitado por ambiguidade operacional.

## Decision 4: Segurança de acesso aos endpoints

- **Decision**: Exigir chave mestre em todos os endpoints do proxy, incluindo `/v1/models` e `/v1/chat/completions`.
- **Rationale**: Evita enumeração não autorizada de modelos e mantém política de segurança consistente para descoberta e execução.
- **Alternatives considered**:
  - Tornar `/v1/models` público em dev — rejeitado por introduzir comportamento divergente e risco de exposição.
  - Segurança parcialmente configurável nesta issue — rejeitado para manter escopo enxuto e previsível.

## Decision 5: Semântica de erro para rotas cloud

- **Decision**: Retornar `503` quando a rota cloud existe mas está indisponível por ausência de credencial; não aplicar fallback automático para rota local em falhas runtime.
- **Rationale**: Diferencia indisponibilidade de inexistência (`404`), melhora diagnóstico e mantém previsibilidade de rota alvo.
- **Alternatives considered**:
  - Retornar `404` para indisponibilidade de credencial — rejeitado por mascarar configuração existente.
  - Fallback automático para local — rejeitado por alterar comportamento esperado e dificultar troubleshooting.
