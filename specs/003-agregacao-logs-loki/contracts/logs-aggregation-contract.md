# Contract: Camada de Observabilidade de Logs (`infra/compose.obs.yaml`)

Contrato operacional exposto pela camada a operadores, testes de aceite e futuras integrações (Grafana, ISSUE-104).

## 1. Ativação

| Item | Contrato |
|------|----------|
| Comando | `docker compose --env-file .env -f infra/compose.yaml -f infra/compose.obs.yaml up -d` |
| Combinável com | `infra/compose.core.yaml`, `infra/compose.llm.yaml` (qualquer ordem após a base) |
| Pré-requisito | Docker Engine com `/var/run/docker.sock` disponível no host; `.env` com `LOKI_GATEWAY_USER`, `LOKI_GATEWAY_PASSWORD` e `DOCKER_GID` (ausência aborta o `compose up`) |

## 2. Serviços

| Serviço | Origem | Redes | Porta publicada | Volumes | Healthcheck | `depends_on` |
|---------|--------|-------|-----------------|---------|-------------|--------------|
| `socket-proxy` | `image: wollomatic/socket-proxy:1.13.1` | `docker-api` | Nenhuma | `/var/run/docker.sock:ro` | `./healthcheck` | — |
| `loki` | `build: ./loki` (FROM `grafana/loki:3.7.8`) | `jhonny-core` | `${HOST_IP:-127.0.0.1}:${LOKI_PORT:-3100}:3100` (atendida pelo gateway) | `loki-data:/loki`, `./loki/config.yaml:ro` | `GET 127.0.0.1:3101/ready` | — |
| `loki-gateway` | `image: caddy:2.11.4-alpine` | `network_mode: service:loki` | (a do `loki`) | `./loki-gateway/Caddyfile:ro` | `GET 127.0.0.1:3100/ready` | `loki` (`service_healthy`) |
| `alloy` | `image: grafana/alloy:v1.20.1` | `jhonny-core`, `docker-api` | Nenhuma | `alloy-data:/var/lib/alloy/data`, `./alloy/config.alloy:ro` | `GET /-/ready` | `loki-gateway`, `socket-proxy` (`service_healthy`) |

Nenhum serviço usa `env_file`. As variáveis vêm de interpolação: com default, ou obrigatórias via `${VAR:?}` (credenciais e `DOCKER_GID`). Todos usam `logging: *default-logging` e `restart: unless-stopped`.

## 3. Interface de consulta (Loki HTTP API via gateway)

Base: `http://${HOST_IP:-127.0.0.1}:${LOKI_PORT:-3100}` no host, ou `http://loki:3100` na `jhonny-core`. Todas as chamadas, exceto `GET /ready`, exigem HTTP Basic com `LOKI_GATEWAY_USER:LOKI_GATEWAY_PASSWORD`; sem credencial válida, a resposta é `401`. A ingestão (`POST /loki/api/v1/push`) também passa pelo gateway e é usada só pelo coletor.

| Endpoint | Uso no aceite |
|----------|---------------|
| `GET /ready` | Prontidão (`200` com o texto `ready`), sem autenticação |
| `GET /loki/api/v1/labels` | Deve listar exatamente os rótulos de indexação do [data-model](../data-model.md) (+ `service_name`) |
| `GET /loki/api/v1/label/compose_service/values` | Lista os serviços com logs ingeridos |
| `GET /loki/api/v1/query_range?query=<LogQL>` | Consultas de aceite |

### Consultas LogQL de referência

| Objetivo | LogQL | SC |
|----------|-------|----|
| Logs de um serviço | `{compose_service="<svc>"}` | SC-001, SC-005 |
| Só erros padrão (stderr) | `{compose_service="<svc>", stream="stderr"}` | SC-005 |
| Por nível normalizado | `{compose_service="<svc>"} \| detected_level="error"` | SC-005 |
| Segredo vazado (não deve retornar nada) | `{compose_project=~".+"} \|= "<valor-secreto-de-teste>"` | SC-012 |
| Linhas sem `trace_id` (falha de instrumentação) | `{compose_project="jhonny_v"} \| json \| trace_id=""` | — |
| Por trace | `{compose_project="jhonny_v"} \| trace_id="<id>"` | SC-005 |

## 4. Garantias de segurança

| Garantia | Comportamento observável | SC |
|----------|--------------------------|----|
| Escrita na API do Docker negada | Método não permitido → `405`; caminho fora da allowlist → `403` | SC-008 |
| Coletor sem socket | `docker inspect` do `alloy` não lista `/var/run/docker.sock` | SC-008 |
| Proxy isolado | Contêiner fora da `docker-api` não resolve nem conecta em `socket-proxy:2375` | SC-009 |
| Loki só local | Com os defaults, a porta escuta só em `127.0.0.1` | SC-010 |
| Loki autenticado | Sem credencial ou com credencial inválida → `401` (exceto `/ready`); `loki:3101` inalcançável a partir da `jhonny-core` | SC-010 |
| Segredos mascarados | Padrões do FR-022 armazenados como `<redacted>` | SC-012 |

## 5. Variáveis de ambiente

| Variável | Default | Efeito |
|----------|---------|--------|
| `LOKI_PORT` | `3100` | Porta publicada do gateway no host |
| `LOKI_RETENTION_PERIOD` | `7d` | Retenção; valor inválido impede o start do Loki |
| `LOKI_LOG_LEVEL` | `info` | Nível de log do Loki |
| `DOCKER_LOG_MAX_SIZE` | `10m` | Tamanho máximo por arquivo de log do Docker (todas as camadas) |
| `DOCKER_LOG_MAX_FILE` | `3` | Nº de arquivos rotacionados por contêiner (todas as camadas) |
| `LOKI_GATEWAY_USER` | — (obrigatória) | Usuário do gateway (consulta e ingestão) |
| `LOKI_GATEWAY_PASSWORD` | — (obrigatória, segredo) | Senha do gateway; nunca versionada |
| `DOCKER_GID` | — (obrigatória) | GID do grupo dono do socket do Docker (`stat -c %g /var/run/docker.sock`) |
| `ALLOY_QUEUE_MAX_BYTES` | `268435456` | Limite lógico de conteúdo serializado pendente (256 MiB); exige folga adicional para páginas/índices/transações do banco |

## 6. Garantias de entrega

| Situação | Comportamento | Requisito |
|----------|---------------|-----------|
| Loki ou gateway indisponível | Reenvio com backoff de 500 ms a 5 min, sem descarte por tentativas/idade; timeout, 4xx e 5xx preservam a fila | FR-026 |
| Recebimento durável | Registro já mascarado, rótulos, metadados e checkpoint confirmados na mesma transação síncrona | FR-010 |
| Confirmação de ingestão | Somente HTTP `204` autoriza remoção; queda após aceitação e antes da remoção pode duplicar | FR-010, FR-026 |
| Encerramento abrupto/produtor removido | Replay de todos os registros confirmados usando o mesmo volume, independentemente do Docker | FR-010 |
| Fila cheia/falha de disco | Suspensão de novas leituras/checkpoints e sinalização de degradação; preservação de pendências e retomada após liberação | FR-026 |
| Dados ainda não persistidos | Sem garantia se rotação/remoção apagar o histórico Docker; nunca anunciar perda zero irrestrita | FR-010, FR-026 |
| Sem posição salva | Histórico retido pelo Docker é ingerido; duplicatas são aceitas | FR-025 |
| Linha acima de 256 KB | Truncada em 256 KB | FR-023 |
| Linha acima de cerca de 1 MiB | Descartada pelo leitor do coletor (limitação conhecida) | — |
| Timestamp | O do Docker (momento da escrita) | FR-024 |

A fila é estado de transporte, não saída operacional em arquivo. O volume
`alloy-data` tem um único dono e deve ser preservado. O limite é lógico; não
limita o tamanho total físico do volume nem o histórico Docker. Corrupção/perda
do volume fica fora da garantia. Rejeição permanente (incluindo timestamps
antigos ou credenciais inválidas) exige correção operacional e pode bloquear a
fila FIFO. Configuração do Loki que descarte linhas com resposta `204` invalida
a premissa de aceitação usada pelo contrato; a configuração distribuída não
deve habilitar esse descarte.

O limite é global entre os alvos do host: um contêiner ruidoso pode suspender
outros leitores. Não há quota isolada por produtor. O banco reutiliza páginas
após remoção, mas seu arquivo conserva o tamanho máximo alocado; drenar a fila
não devolve esse espaço ao sistema operacional.
