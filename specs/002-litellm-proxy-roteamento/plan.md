# Implementation Plan: Configuração do LiteLLM Proxy e Roteamento de Modelos

**Branch**: `[002-litellm-proxy-roteamento]` | **Date**: 2026-09-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-litellm-proxy-roteamento/spec.md`

## Summary

Configurar uma camada dedicada de proxy de modelos na infraestrutura local para desacoplar as aplicações da escolha de provedores/modelos. O plano define um overlay de Compose para o LiteLLM, uma configuração versionada de rotas para modelos locais e cloud, política explícita de autenticação por chave mestre em todos os endpoints e comportamento de erro previsível para indisponibilidade de credenciais e falhas de runtime.

## Technical Context

**Language/Version**: YAML (Docker Compose e configuração de proxy), Markdown para documentação operacional

**Primary Dependencies**: Docker Compose; imagem do LiteLLM Proxy; variáveis de ambiente locais em `.env`

**Storage**: Arquivos versionados em `infra/` e variáveis de ambiente locais (sem persistência de dados de negócio)

**Testing**: Validação manual por `docker compose config`, `docker compose up`, requisições HTTP para `/v1/models` e `/v1/chat/completions`

**Target Platform**: Ambiente local de desenvolvimento em Linux/macOS/Windows com Docker Compose

**Project Type**: Monorepo com stack de infraestrutura em camadas (`compose.yaml` + overlays `compose.*.yaml`)

**Performance Goals**: Endpoint de listagem disponível em até 30 segundos após start; chamadas autenticadas de chat roteadas com sucesso para rotas válidas

**Constraints**: Não hardcode de segredos; autenticação obrigatória em todos os endpoints; sem fallback automático de rota cloud para local; distinção explícita entre rota inexistente e rota indisponível por credencial

**Scale/Scope**: 1 serviço LiteLLM no overlay LLM, com conjunto inicial de rotas locais + cloud para validação da issue

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Constituição operacional adotada da branch `feature/copilot-development` (arquivo `.github/copilot-instructions.md`) para reger arquitetura, segurança e fluxo SDD desta feature.
- Gates aplicados para esta feature a partir da constituição e diretrizes do repositório:
  - Manter a convenção de Compose em arquivos `.yaml` sob `infra/` com base em `infra/compose.yaml` e overlays explícitos.
  - Preservar desacoplamento entre configuração de modelos e código das aplicações.
  - Garantir autenticação por chave mestre e credenciais via variáveis de ambiente, sem segredos versionados.
  - Validar que comportamento de falha mantém previsibilidade operacional (sem fallback implícito de rota cloud para local).
- **Status pré-pesquisa**: PASS
- **Status pós-design**: PASS — os artefatos de design mantêm o escopo em infraestrutura/configuração e critérios de validação operacionais.

## Project Structure

### Documentation (this feature)

```text
specs/002-litellm-proxy-roteamento/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── litellm-proxy-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
infra/
├── compose.yaml
├── compose.core.yaml
├── compose.llm.yaml            # novo overlay da stack LLM
└── litellm/
    └── config.yaml             # configuração de rotas e políticas do proxy

.env.example                    # inclui variáveis de chave mestre/credenciais cloud
```

**Structure Decision**: Evoluir o padrão já adotado de infraestrutura em camadas, adicionando `infra/compose.llm.yaml` para o serviço LiteLLM e `infra/litellm/config.yaml` para roteamento. Esse recorte evita acoplamento com apps e mantém os contratos operacionais concentrados na camada de infraestrutura.

## Ownership & Configuration Boundaries

### File Ownership

| File | Owner | Responsibility Boundary |
|------|-------|--------------------------|
| `infra/compose.llm.yaml` | Plataforma/Infra | Ciclo de vida do serviço, rede, montagem de config e injeção de variáveis |
| `infra/litellm/config.yaml` | Plataforma/AI Enablement | Rotas, aliases, provedores, políticas de disponibilidade e semântica de erro |
| `.env.example` | Plataforma/Security | Contrato de variáveis required/optional e instruções de preenchimento seguro |

### Environment Variable Dependency Matrix

| Variable | Required | Owner | Provisioning | Rotation/Revocation |
|----------|----------|-------|--------------|---------------------|
| `LITELLM_MASTER_KEY` | Sim | Security/Plataforma | Manual via `.env` local | Rotação planejada fora do escopo desta release |
| `OPENAI_API_KEY` | Opcional (rotas cloud OpenAI) | Plataforma/Integrações | `.env` quando modo híbrido for usado | Governança de rotação pelo provedor/segurança |
| `ANTHROPIC_API_KEY` | Opcional (rotas cloud Anthropic) | Plataforma/Integrações | `.env` quando modo híbrido for usado | Governança de rotação pelo provedor/segurança |

### Release Modes

- **Local-only mode**: sem credenciais cloud; somente rotas locais devem operar.
- **Hybrid mode**: com credenciais cloud; rotas locais e cloud devem operar conforme contrato.
- Ambos os modos devem produzir evidência repetível para aprovação de release.

## Complexity Tracking

Nenhuma violação de constituição identificada; complexidade mantida em um único overlay adicional e um arquivo de configuração dedicado ao proxy.
