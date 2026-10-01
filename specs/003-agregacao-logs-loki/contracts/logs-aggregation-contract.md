# Contract: Camada de Observabilidade de Logs (`infra/compose.obs.yaml`)

Contrato operacional exposto pela camada a operadores, testes de aceite e futuras integrações (Grafana, ISSUE-104).

## 1. Ativação

| Item | Contrato |
|------|----------|
| Comando | `docker compose --env-file .env -f infra/compose.yaml -f infra/compose.obs.yaml up -d` |
| Combinável com | `infra/compose.core.yaml`, `infra/compose.llm.yaml` (qualquer ordem após a base) |
| Pré-requisito | Docker Engine com `/var/run/docker.sock` disponível no host |

## 2. Serviços

| Serviço | Origem | Redes | Porta publicada | Volumes | Healthcheck | `depends_on` |
|---------|--------|-------|-----------------|---------|-------------|--------------|
| `socket-proxy` | `image: tecnativa/docker-socket-proxy:v0.5.0` | `docker-api` | Nenhuma | `/var/run/docker.sock:ro` | `GET /_ping` | — |
| `loki` | `build: ./loki` (FROM `grafana/loki:3.7.8`) | `jhonny-core` | `${HOST_IP:-127.0.0.1}:${LOKI_PORT:-3100}:3100` | `loki-data:/loki`, `./loki/config.yaml:ro` | `GET /ready` | — |
| `alloy` | `image: grafana/alloy:v1.20.1` | `jhonny-core`, `docker-api` | Nenhuma | `alloy-data:/var/lib/alloy/data`, `./alloy/config.alloy:ro` | `GET /-/ready` | `loki`, `socket-proxy` (`service_healthy`) |

Nenhum serviço usa `env_file`; as variáveis vêm de interpolação com default. Todos usam `logging: *default-logging` e `restart: unless-stopped`.

## 3. Interface de consulta (Loki HTTP API)

| Endpoint | Uso no aceite |
|----------|---------------|
| `GET /ready` | Prontidão (`200` com o texto `ready`) |
| `GET /loki/api/v1/labels` | Deve listar exatamente os rótulos de indexação do [data-model](../data-model.md) (+ `service_name`) |
| `GET /loki/api/v1/label/compose_service/values` | Lista os serviços com logs ingeridos |
| `GET /loki/api/v1/query_range?query=<LogQL>` | Consultas de aceite |

### Consultas LogQL de referência

| Objetivo | LogQL | SC |
|----------|-------|----|
| Logs de um serviço | `{compose_service="<svc>"}` | SC-001, SC-005 |
| Só erros padrão (stderr) | `{compose_service="<svc>", stream="stderr"}` | SC-005 |
| Por nível (JSON) | `{compose_service="<svc>"} \| level="ERROR"` | SC-005 |
| Por trace | `{compose_project="jhonny_v"} \| trace_id="<id>"` | SC-005 |

## 4. Garantias de segurança

| Garantia | Comportamento observável | SC |
|----------|--------------------------|----|
| Escrita na API do Docker negada | Qualquer método não-GET via proxy → `403 Forbidden` | SC-008 |
| Coletor sem socket | `docker inspect` do `alloy` não lista `/var/run/docker.sock` | SC-008 |
| Proxy isolado | Contêiner fora da `docker-api` não resolve nem conecta em `socket-proxy:2375` | SC-009 |
| Loki só local | Com os defaults, a porta escuta só em `127.0.0.1` | SC-010 |

## 5. Variáveis de ambiente

| Variável | Default | Efeito |
|----------|---------|--------|
| `LOKI_PORT` | `3100` | Porta publicada do Loki no host |
| `LOKI_RETENTION_PERIOD` | `7d` | Retenção; valor inválido impede o start do Loki |
| `LOKI_LOG_LEVEL` | `info` | Nível de log do Loki |
| `DOCKER_LOG_MAX_SIZE` | `10m` | Tamanho máximo por arquivo de log do Docker (todas as camadas) |
| `DOCKER_LOG_MAX_FILE` | `3` | Nº de arquivos rotacionados por contêiner (todas as camadas) |
