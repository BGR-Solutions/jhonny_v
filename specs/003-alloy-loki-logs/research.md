# Research: Alloy e Loki para a issue #103

**Pesquisa inicial:** 2026-10-25, somente documental. As execuções posteriores estão registradas abaixo; pesquisa de capacidade não substitui evidência runtime.

## Evidência de implementação — 2026-10-26

### US3: recuperação comprovada e revisão autorizada do orçamento

#### Desenho vigente autorizado após investigar o índice

Regressão com o desenho vigente: `pytest infra/tests -m "not retention"` passou em **29 testes / 881,85s**, incluindo reinícios, interrupção, matriz HTTP, parsing, descoberta e observador. Ruff/Black e mypy strict passaram em seis arquivos; `go test -race ./...` e `go vet ./...` passaram novamente no builder fixado. O teste US2 agora espera multiplicidade exata de todas as linhas, inclusive duas ocorrências da mensagem repetida, dentro do mesmo limite de 60s; esperar apenas IDs de outras mensagens era proxy insuficiente.

Retenção contínua: **PASS em 1227,19s**, com quatro timestamps cobertos por dois chunks antigos físicos e dois arquivos de marcadores observados/removidos. Amplitude máxima 214,32s; primeiro flush 72,46s; publicação de índice 265,16s após flush; marcação 23,98s após elegibilidade/índice; maior etapa de sweeper 59,9988s após delay de 180s; maior remoção física 509,66s após expiração individual, limite 1800s. Controles válidos e identidade/restart count de Loki preservados; nenhum flush/restart ou mudança de intervalos no teste principal. A medição certifica a amostra/carga, não todas as fases de rotação ou sobrecarga.

Entrega local: workflow com ações fixadas em commits consultados na API oficial e uv 0.12.1; `actionlint v1.7.7` passou no builder Linux, após ausência da ferramenta no host. `uv lock --check` e `git diff --check` passaram. Compose core/LLM validaram com `--no-interpolate --no-env-resolution --quiet`, sem resolver/expor segredos ou iniciar serviços. Não houve mudança de core/LLM/apps. **Pendências bloqueantes:** CI Linux remota ainda não executada, ACL do bind Windows real ainda não certificada. Nenhum commit/push/fechamento de issue realizado.

Precisão de medição: o primeiro observador do sweeper usava snapshot a cada 10s seguido de consulta, e falhou ao observar 246,8s desde a criação de um marcador. Essa amostra não distinguia atraso real de atraso da observação. Um helper efêmero, sem rede e com volume somente leitura, agora registra remoções em JSON com amostragem de 50ms; seu teste controlado comprovou observação em até 0,5s após unlink. Não modifica dados, intervalos ou deadline; é removido por ID antes da limpeza do volume. Depois, a CI Linux (run 40339607338) mediu 240,0256s, 26ms acima do teto de 240s: o ticker de 1m do sweeper mais o aging de 3m não tem folga. O operador autorizou sweeper 1m30s (teto 270s) usando 30s da reserva, total 30m inalterado.

- **Decision:** preservar prazo individual de 30m. Operador autorizou alterar max_chunk_age=3m, compaction_interval=30s, apply_retention_interval=1m, retention_delete_delay=3m, tsdb_shipper.resync_interval=30s e query_timeout=1m explícito, antes de qualquer edição funcional. Orçamento: amplitude 4m + flush 2m + índice 17m + compactação/retenção conjuntas 2m + delete delay 3m + sweeper 1m + reserva 1m = 30m.
- **Rationale:** o teste refutou índice <=3m. [HeadManager](https://github.com/grafana/loki/blob/v3.7.9/pkg/storage/stores/shipper/indexshipper/tsdb/head_manager.go) fixa rotação de 15m e checagem de 1m; [shipper](https://github.com/grafana/loki/blob/v3.7.9/pkg/storage/stores/shipper/indexshipper/shipper.go) fixa upload em 1m e permite ressync configurável. [tables_manager](https://github.com/grafana/loki/blob/v3.7.9/pkg/compactor/tables_manager.go) compacta durante a própria aplicação de retenção; budget conjunto evita dupla contagem, não omite dependência.
- **Cache safety:** [listagem em cache](https://github.com/grafana/loki/blob/v3.7.9/pkg/storage/stores/shipper/indexshipper/storage/cached_client.go) dura 1m; ressync=30s mais query_timeout=1m ficam abaixo de delete delay=3m. CacheTTL de arquivos (24h default) controla descarte de arquivos sem uso, não frequência de atualização; não confundir esses mecanismos. Preservação de controles e ausência de erros de consulta continuam obrigatórias.
- **Behavior/risk:** mais I/O e janela de escrita fora de ordem aproximadamente 90s em vez de 150s, aceitos explicitamente pelo operador. O atraso de 60s passou no teste. Sem mudança de aplicações, rede, dependências ou deadline. Saltos arbitrários de timestamp/sobrecarga não são certificados pela amostra. Retenção tem aceite local na amostra medida, não certificação de CI remota ou dos mounts do operador.
- **Alternatives considered:** aumentar formalmente o deadline para 45m foi rejeitado em favor de investigar 30m; preservar todos os intervalos deixou orçamento incompatível com rotação TSDB; forçar flush/restart ou mudar somente a assertion violaria o contrato.

#### Histórico das revisões anteriores (substituídas pelo desenho vigente)

**Segunda revisão autorizada:** o cenário contínuo mediu amplitude de 322,7s. A [condição shouldFlushChunk de Loki v3.7.9](https://github.com/grafana/loki/blob/v3.7.9/pkg/ingester/flush.go) usa `to.Sub(from) > MaxChunkAge` na rotina periódica; não é teto rígido de append. Operador escolheu preservar configuração, reservar 6m para amplitude e reduzir a reserva para 8m, mantendo flush 2m e total 30m. Alternativa rejeitada: max_chunk_age=4m para antecipar corte, com mais chunks. O teto revisado precisa de prova sob a carga declarada a cada 30s e não certifica saltos arbitrários de timestamp. Análise constitucional: sem mudança de produção, rede, dependência ou deadline individual; a etapa física permanece bloqueante.

- **Decision:** manter os intervalos de produção e o deadline individual de 30m; realocar o orçamento de flush de 1m para 2m e a reserva de 10m para 9m. Operador escolheu essa revisão após o teste medir 90,7s até o primeiro chunk físico. O cenário de limpeza continua pendente, sem aceite por esta observação parcial.
- **Rationale:** idle=1m seguido de uma checagem de 30s não garante flush em 1m. O orçamento completo continua somando 30m; não aumentar deadline nem introduzir flush/restart forçado.
- **Alternatives considered:** reduzir idle para 15s e checagem para 10s aumentaria chunks/operações de disco; operador preferiu preservar configuração e comportamento. Pausar foi oferecido.
- **Fixture:** consulta de amostras antigas usa somente no teste `query_ingesters_within: 0s` e `query_store_max_look_back_period: -1ns`. A [implementação de intervalos do Loki v3.7.9](https://github.com/grafana/loki/blob/v3.7.9/pkg/querier/intervals.go) compara a sentinela infinita com `time.Duration(-1)`, não qualquer duração negativa. `-1s` não equivale a infinito. As quatro amostras antigas e o controle foram confirmados antes de expirar com a sentinela exata; nenhuma alteração de lookback em produção.
- **Recovery evidence:** restart Loki preservou 20 IDs confirmados e restart Alloy retomou novos eventos. O teste de interrupção passou separadamente em 103,75s: 20 eventos durante 30s sem Loki e um evento posterior ficaram visíveis no prazo de 60s após recuperação. Gateway emitiu JSON de POST com status 502 durante a falha. [Alloy v1.21.2 registra retentativas em debug](https://github.com/grafana/alloy/blob/v1.21.2/internal/component/common/loki/client/shards.go), não warn; manter logging info e comprovar diagnóstico explícito no gateway, conforme SC-006, sem forçar nível debug ou aceitar sucesso falso.
- **Constitution/risk check incremental:** sem nova dependência, segredo, rede, app ou mudança de contrato público. Mantidos testes prévios, comprovação física, prazo individual e bloqueio até medição completa. Checklists do revisor permanecem intactos; T040 sincronizada com o orçamento autorizado. A análise de consistência deve preceder a alteração da assertion de flush.

T001: manifests consultados com `docker buildx imagetools inspect`, sem trocar tags. Docker Desktop Linux 29.6.1, amd64, Compose 5.1.4. O Engine estava parado e foi iniciado pelo operador; nenhum serviço existente foi reiniciado pelo agente.

| Base | Digest do índice consultado | Arquiteturas relevantes |
|------|----------------------------|-------------------------|
| grafana/alloy:v1.21.2 | sha256:89a5a320168387336b9ac3c850609c3ba7757eadd4ae5f1d819deb35e9854b18 | linux/amd64, linux/arm64 |
| grafana/loki:3.7.9 | sha256:0db216b630ae1f348a1584c67f3cead8b4c1fc839169a39501db664744158e28 | linux/amd64, linux/arm64 |
| nginx:1.30.6-alpine | sha256:47928bf67eb62a1863cb08d9ecb52d3e704304ba614eaee17884204677702951 | linux/amd64; demais plataformas no índice |
| golang:1.27.2 | sha256:820153096fda4de6ac1b7194d12e416b7dd8f4e9a33d17e0345b111b945162d8 | linux/amd64; demais plataformas no índice |
| python:3.12.12-alpine3.22 (origens de teste) | sha256:848ba4413eb897e225159b8fc1b02094576cbae4aa73fc13142608ae2c8c0e32 | linux/amd64; demais plataformas no índice |

O builder foi baixado por digest e `docker run --rm <builder> go version` retornou `go1.27.2 linux/amd64`. Isso comprova somente disponibilidade e execução do builder, não funcionamento da stack nem certificação de outras arquiteturas.

Validação incremental executada:

- Três targets locais reconstruídos com sucesso após ampliar os testes Go; bases permanecem fixadas nos digests acima.
- `go test -race ./...` e `go vet ./...` no builder fixado: PASS. Casos incluem HTTP, retenção, credenciais, ownership, TERM/INT/QUIT, recolhimento/drenagem, exit não zero, leitura/escrita com falha, linha longa e bloqueio de saída limitado. RED adicional comprovado para owner indevido e severidade/errno antes da correção.
- Ruff/Black/mypy strict nos quatro arquivos Python de infraestrutura: PASS no checkpoint anterior à última ampliação do harness; executar novamente ao consolidar.
- Matriz real dos listeners de leitura/escrita: PASS; 401 antes de método, 405/Allow após autenticação, 404 para rotas desconhecidas e erro upstream preservado.
- Allowlist Docker: PASS contra daemon Unix simulado exclusivo do teste, inclusive GET/HEAD de redes e recusa de POST/endpoints administrativos sem atingir o daemon real.
- SC-001/SC-002: PASS, 200 IDs de duas origens/dois fluxos e descoberta posterior dentro de 60s. Esses cenários não certificam parsing, recuperação ou retenção.
- Diagnósticos de aplicação são capturados por `docker logs` de contêineres próprios após espera do processo; progresso do Compose não é saída do aplicativo e não deve ser filtrado como se fosse log de produção.

### Revisão incremental: publicação em redes internas

- **Decision:** manter obs-docker/obs-ingest/obs-storage internas e adicionar obs-edge não interna exclusivamente ao gateway, preservando publicação de 8080 somente em 127.0.0.1. Decisão aprovada pelo operador durante implementação, antes da alteração operacional.
- **Rationale/evidence:** Engine 29.6.1 / Compose 5.1.4: quatro serviços atingiram saúde, mas `compose port logs-gateway 8080` retornou `invalid IP:0`. Reprodução independente com rede criada por `docker network create --internal` e NGINX fixado, `-p 127.0.0.1::80`: `NetworkSettings.Ports={"80/tcp":[]}` apesar de `HostConfig.PortBindings` conter o pedido. Contêiner e rede de reprodução foram removidos pelos seus IDs/nomes exclusivos. Portanto saúde e pedido de bind não comprovam acesso pelo host.
- **Alternatives considered:** remover internal das redes de dados amplia conectividade de Loki/Alloy/proxy; host networking elimina fronteiras/portabilidade. Rede de borda exclusiva preserva as fronteiras de dados. Parar sem correção foi oferecido; operador escolheu revisar plano/análise e adicionar a borda.
- **Validation required:** topologia exata e HTTP real via loopback; nenhuma porta 8081/8082/3100/12345/2375 publicada diretamente. Essa decisão de desenho não certifica os testes restantes.

## 1. Coletor suportado e versões

- **Decision:** Alloy `v1.21.2`, Loki `3.7.9`, NGINX `1.30.6-alpine`; sonda compilada com Go `1.27.2`. Registrar digests e arquiteturas antes de implementar; ausência de imagem é bloqueio, não fallback para `latest`.
- **Rationale:** Promtail chegou ao fim de vida em 2026-03-02; usuário confirmou Alloy. Versões explícitas permitem reprodução. Go tem correções de segurança de outubro de 2026 e fica apenas no builder.
- **Alternatives considered:** Promtail descartado por fim de suporte; tags flutuantes descartadas; versões da documentação `main/latest` não bastam para comprovar comportamento de release.
- **Evidence:** [Promtail EOL](https://grafana.com/docs/loki/latest/send-data/promtail/), [Alloy releases](https://github.com/grafana/alloy/releases), [Loki releases](https://github.com/grafana/loki/releases), [base NGINX stable](https://raw.githubusercontent.com/nginx/docker-nginx/master/stable/alpine/Dockerfile), [Go release history](https://go.dev/doc/devel/release).

## 2. Docker API em vez de arquivos do host

Revisão operacional aprovada: permitir adicionalmente GET/HEAD do endpoint exato `/networks`, com prefixo de versão opcional. A versão fixada do Alloy em execução retornou `Unable to refresh target groups` / `error while computing network labels` ao receber 404 do proxy; a descoberta depende da listagem de redes. Confirmado também na implementação [Docker discovery do Prometheus](https://github.com/prometheus/prometheus/blob/main/discovery/moby/docker.go), chamada `getNetworksLabels` anterior ao processamento dos alvos. Não liberar `/networks/<id>`, mutações ou endpoints administrativos. Listagem expõe metadados de redes do daemon ao coletor confiável; não constitui autorização por projeto. Alternativa de manter a allowlist impede descoberta; trocar o mecanismo amplia desnecessariamente o escopo.

- **Decision:** `discovery.docker` → filtro por projeto → `loki.source.docker` → `loki.process` → `loki.write`. Acesso por proxy GET/HEAD com allowlist de endpoints, não socket direto no Alloy.
- **Rationale:** a API entrega stdout/stderr sem montar logs físicos do Docker; compatível com daemon Linux da VM no Desktop. A origem já remove o envelope Docker de transporte; não usar `stage.docker`, destinado ao formato json-file em disco.
- **Alternatives considered:** mount de `/var/lib/docker/containers` acopla caminhos/driver; socket direto tem poderes excessivos; Tecnativa `0.5.0` é alternativa funcional, mas habilitar `CONTAINERS` é mais amplo que a allowlist de endpoints requerida e introduz outro tipo de proxy. Reusar uma imagem derivada NGINX em dois serviços separados reduz variedade de bases; o launcher da seção 8 resolve a emissão dos diagnósticos.
- **Evidence:** [discovery.docker](https://grafana.com/docs/alloy/latest/reference/components/discovery/discovery.docker/), [loki.source.docker](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.source.docker/), [tailer da release v1.21.2](https://github.com/grafana/alloy/blob/v1.21.2/internal/component/loki/source/docker/tailer.go), [socket-proxy e limites](https://github.com/Tecnativa/docker-socket-proxy).
- **Limit:** filtro de projeto controla ingestão, não autorização multiusuário no daemon. Inspect pode conter ambiente sensível: rede privada, sem logging de payload e confiança explícita no operador Docker.

## 3. Fluxo e cardinalidade

Evidência US2: o RED inicial falhou por ausência de parse_status; depois o teste identificou service_name criado automaticamente por Loki. A configuração discover_service_name=[] corrigiu a raiz dessa label extra. Os testes passaram com linhas preservadas, contextos originais, índice exato e filtros por metadados antes/depois de recriação. A implementação [structured_metadata da release v1.21.2](https://github.com/grafana/alloy/blob/v1.21.2/internal/component/loki/process/stages/structured_metadata.go) lê labels de entrada e as remove do índice. O [JSON stage da release](https://github.com/grafana/alloy/blob/v1.21.2/internal/component/loki/process/stages/json.go) decodifica objetos, portanto a classificação de arrays/primitivos/null usa mustFromJson em template, sem modificar a linha; casos válidos/inválidos comprovados no runtime.

- **Decision:** promover `__meta_docker_container_log_stream` em regras do source. Indexar apenas projeto/serviço/fluxo/status de parsing; identidade de instância em structured metadata. Manter linha original; extrair JSON sem output stage.
- **Rationale:** source remove labels internas; assumir preservação automática do fluxo quebraria FR-004. IDs de contêiner/tracing não devem multiplicar streams indexados. Structured metadata requer schema v13/TSDB.
- **Alternatives considered:** indexar IDs rejeitado por cardinalidade; embrulhar mensagem original em novo JSON rejeitado por perda de equivalência de linha; rejeitar texto inválido contraria FR-007.
- **Evidence:** [source da release](https://github.com/grafana/alloy/blob/v1.21.2/internal/component/loki/source/docker/tailer.go), [loki.process](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.process/), [structured metadata](https://grafana.com/docs/loki/latest/get-started/labels/structured-metadata/).

## 4. Autenticação e escopo de rede

- **Decision:** gateway NGINX Basic Auth com leitores e escritor separados; consulta publicada em loopback; push interno; backend Loki isolado, single tenant.
- **Rationale:** `auth_enabled` do Loki identifica tenants, não autentica senhas. Não atende FR-013 sozinho. Gateway aplica método/path e credencial, não só presença de um header.
- **Alternatives considered:** Loki direto ou `X-Scope-OrgID` como senha rejeitados; TLS/LAN descartados por decisão do usuário e escopo exclusivamente local; produto de identidade externo excede o escopo.
- **Evidence:** [Loki HTTP API](https://grafana.com/docs/loki/latest/reference/loki-http-api/), [NGINX Basic Auth](https://nginx.org/en/docs/http/ngx_http_auth_basic_module.html).
- **Limit:** loopback não separa usuários locais; Basic Auth sem TLS não se aplica a acesso remoto. Operador Docker/root pode contornar controles. Endpoints internos não devem ser conectados às redes gerais das aplicações.

## 5. Retenção e armazenamento

- **Decision (histórico U2):** Loki TSDB v13, filesystem, índice 24h, retenção 336h configurável com mínimo adotado de 24h; compactor/markers/WAL no mesmo volume persistente. O desenho inicial usava max_chunk_age=5m, chunk_idle_period=1m, flush_check_period=30s, chunk_retain_period=0s, compaction_interval=1m, apply_retention_interval=2m e delete delay=5m. Os intervalos foram substituídos pelo desenho vigente autorizado no início deste documento; prazo individual permanece 30m.
- **Rationale:** o índice 24h é requisito de retenção; varredura/deleção é assíncrona, portanto expiração não promete remoção instantânea. Prazo de 30m é meta do projeto a validar, não SLA documentado do fornecedor.
- **Alternatives considered:** bucket externo/cluster fora do escopo; retenção infinita conflita com decisão de 14 dias; teste com menos de 24h depende de comportamentos e limites não necessários.
- **Evidence:** [retention](https://grafana.com/docs/loki/latest/operations/storage/retention/), [storage](https://grafana.com/docs/loki/latest/configure/storage/).
- **Limit:** política alterada não deve ser presumida retroativa; teste cria storage novo antes de inserir dados. Sem quota de disco automática ou replicação; armazenamento cheio precisa erro explícito.
- **Evidence adicional:** [expiration.go da release v3.7.9](https://github.com/grafana/loki/blob/v3.7.9/pkg/compactor/retention/expiration.go) usa `chk.Through` para expiração, portanto eventos de idades diferentes no mesmo chunk podem adiar a remoção dos mais antigos. A documentação de retenção descreve schedules independentes e deslocamento quando os intervalos são iguais. O orçamento deve incluir amplitude temporal, flush, publicação/atualização de índice, compactor e sweeper; não só somar delete delay ao intervalo do compactor.
- **Validation:** teste sem flush/restart forçado, com timestamps próximos do limite, controles não expirados e chunks de idade mista; medir etapas e remoção física. Max_chunk_age não é prova isolada de amplitude máxima sob escrita atrasada/fora de ordem. Não há SLA upstream de 30m: violação do orçamento bloqueia entrega e reabre planejamento, não autoriza sucesso por teste sintético facilitado.

## 6. Falha de 30 segundos

- **Decision:** batching/retries estáveis, backoff limitado a 5s e 30 retentativas; não habilitar fila experimental. Validar integralmente 20 eventos de até 1KiB durante 30s, em até 60s após a volta.
- **Rationale:** defaults permitem backoff de até minutos; limitá-lo torna o aceite verificável. O teste não exige persistência da fila se Alloy cair.
- **Alternatives considered:** `queue_config` experimental e promessa de exactly-once descartadas; aceitar perda da amostra contraria esclarecimento.
- **Evidence:** [loki.write](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.write/).
- **Limit:** retry não é garantia ilimitada; posições persistentes não substituem WAL de envio; 4xx de payload/autenticação devem ser diagnosticados, não tratados como indisponibilidade recuperável indefinidamente.

## 7. Saúde em imagens mínimas

- **Decision:** builds locais explícitos Loki/Alloy/NGINX adicionam obs-tools, com probe HTTP de biblioteca padrão. Preservar binários e usuários upstream; entrypoints passam explicitamente pelo preflight. NGINX usa a mesma sonda, sem depender de curl/wget.
- **Rationale:** Loki distroless não fornece shell; Alloy não garante curl/wget. Healthchecks com comandos ausentes pareceriam corretos apenas no YAML. Sonda verifica status 200 e timeout, sem logs de arquivo.
- **Alternatives considered:** omitir healthcheck ou medir só existência de PID viola o contrato de saúde; instalar Python/curl no runtime aumenta a superfície; external probe não representa saúde nativa por serviço.
- **Evidence:** [Dockerfile Loki](https://github.com/grafana/loki/blob/v3.7.9/cmd/loki/Dockerfile), [Dockerfile Alloy](https://github.com/grafana/alloy/blob/v1.21.2/Dockerfile), [endpoints Alloy](https://grafana.com/docs/alloy/latest/reference/http/).

## 8. Emissão JSON e ciclo de vida dos proxies — C1

- **Decision:** derivar a base NGINX fixa e usar obs-tools como launcher, sem entrypoint shell upstream. NGINX em foreground, access_log JSON stdout e error_log stderr capturados por pipes. Converter diagnósticos em JSON sanitizado antes da emissão do contêiner; arquivos de configuração/PID somente em tmpfs, nenhum arquivo de log.
- **Rationale:** error_log OSS não oferece formato JSON, diferentemente de log_format com escape=json. Coletar texto depois não corrige a violação na emissão. Launcher encaminha sinais, recolhe o master, drena pipes e preserva falhas; isso é decisão de engenharia do projeto, não recurso prometido pelo NGINX.
- **Alternatives considered:** permitir stderr textual contraria a constituição; desligar error_log oculta falhas; patch no motor NGINX aumenta manutenção; instalar outro coletor apenas para corrigir o stdout do próprio proxy adiciona dependência desnecessária.
- **Evidence:** [error_log](https://nginx.org/en/docs/ngx_core_module.html#error_log), [log_format](https://nginx.org/en/docs/http/ngx_http_log_module.html#log_format), [controle/sinais](https://nginx.org/en/docs/control.html), [os/exec](https://pkg.go.dev/os/exec).
- **Validation:** testar startup inválido, runtime, shutdown, status não zero, pipes/linhas longas e sentinelas de credenciais. Nunca repassar conteúdo livre de request/upstream/referrer. Evento não reconhecido continua explícito com categoria/tamanho/digest sem payload; categorias dos erros operacionais exigidos devem ser reconhecíveis.

## 9. Preflight operacional e tipagem — U1/C2

- **Decision:** o mesmo executável Go faz validações por serviço antes de toda inicialização, independentemente de pytest. Gateway verifica bcrypt com golang.org/x/crypto/bcrypt; fixar versão compatível no go.mod/go.sum no início da implementação. Apenas o gateway recebe o segredo de escrita adicional para comparar com o hash. Leitor é validado por formato e teste autenticado, sem armazenar sua senha no gateway.
- **Rationale:** conftest não protege `compose up` do operador. Validação de hash requer comparação real, não igualdade textual entre arquivos. Senhas aleatórias ASCII de 32 a 72 bytes evitam o limite/truncamento bcrypt; testes devem comprovar interoperabilidade com NGINX da base escolhida, incluindo prefixo htpasswd suportado.
- **Alternatives considered:** wrapper host como único gate pode ser contornado; verificar só arquivo não vazio não detecta inconsistência; implementar bcrypt próprio é inadequado.
- **Evidence:** [CompareHashAndPassword](https://pkg.go.dev/golang.org/x/crypto/bcrypt), [htpasswd](https://httpd.apache.org/docs/2.4/programs/htpasswd.html).
- **Decision de qualidade:** mypy strict em infra/tests, dependências mypy/types-PyYAML no extra dev e comando idêntico local/CI. Testes de processo e integração continuam necessários; tipagem não os substitui.
- **Evidence:** [mypy strict](https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-strict), [stubs PyYAML](https://github.com/python/typeshed/tree/main/stubs/PyYAML).
- **Limit:** modos Linux sintetizados por Docker Desktop não provam ACL do Windows. Comprovar restrição no host e no runtime; falha em comprovar impede certificação. Não aplicar chmod/ACL automaticamente.

## 10. Ordem dos erros HTTP — A1

- **Decision:** rota desconhecida retorna 404; rota conhecida autentica primeiro, depois verifica método (401 antes de 405), depois encaminha e preserva status upstream. Aplicar a ambos os listeners.
- **Rationale:** comportamento determinístico evita testes incompatíveis e exposição de payload antes de autenticar. No NGINX, rewrite precede access; portanto não usar return de método na localização pública antes do auth.
- **Implementation direction:** rotas exatas protegidas autenticam na fase access e passam por try_files para localização nomeada interna, onde método é verificado antes de proxy_pass. A localização nomeada não é endpoint público; caminhos desconhecidos não entram nela. Não usar arquivo de log ou conteúdo de usuário para resolver try_files; testar que nenhuma rota servirá arquivo estático. Comprovar a ordem no NGINX real, inclusive métodos proibidos, caminhos codificados e credencial de outra interface.
- **Alternatives considered:** método antes da autenticação é possível, mas não corresponde ao contrato escolhido; deixar a decisão aos defaults produz ambiguidade.
- **Evidence:** [fases NGINX](https://nginx.org/en/docs/dev/development_guide.html#http_phases), [try_files](https://nginx.org/en/docs/http/ngx_http_core_module.html#try_files).

## Resultado da pesquisa

Decisões documentais dos cinco achados registradas, sem escolha funcional pendente. Não se alega comprovação runtime. Build e testes confirmarão executáveis, versões, schemas, JSON, lifecycle, preflight, streaming, rede, parsing e prazo de limpeza antes do aceite; falha nesses pontos bloqueia entrega e exige ajustar/reanalisar o plano, sem reduzir critérios silenciosamente. Tarefas anteriores precisam de regeneração para refletir este desenho.
