# Testes de aceite da infraestrutura

Testes `pytest` da camada de observabilidade (Loki + Grafana Alloy), rodados contra a stack em execução. Especificação: [`specs/003-agregacao-logs-loki/`](../../specs/003-agregacao-logs-loki/).

## Pré-requisitos

- Docker Engine com Compose v2 e [`uv`](https://docs.astral.sh/uv/).
- `.env` na raiz do repositório, criado a partir do `.env.example`, com `LOKI_GATEWAY_USER`, `LOKI_GATEWAY_PASSWORD`, `DOCKER_GID` (`stat -c %g /var/run/docker.sock`) e `LITELLM_MASTER_KEY` preenchidos.
- Stack no ar, a partir da raiz:

  ```bash
  docker compose --env-file .env -f infra/compose.yaml -f infra/compose.core.yaml -f infra/compose.obs.yaml up -d --build --wait
  ```

## Execução

```bash
cd infra
uv sync --extra dev
uv run pytest -v                     # suíte completa (SC-014)
uv run pytest -v -m "not disruptive" # sem reiniciar serviços
uv run pytest -v -m disruptive       # só os que reiniciam ou recriam serviços
```

Os testes leem as credenciais do ambiente e, como fallback, do `.env` da raiz (ou do caminho em `JV_ENV_FILE`). Pré-requisito ausente faz o teste **falhar**, nunca pular.

## Lint

```bash
uv run ruff check . && uv run black --check .
```
