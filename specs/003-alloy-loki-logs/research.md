# Research: Alloy e Loki para a issue #103

**Data:** 2026-10-25. Pesquisa documental, sem pull/build/execução de imagens. Evidência de capacidade não substitui validação runtime.

## 1. Coletor suportado e versões

- **Decision:** Alloy `v1.21.2`, Loki `3.7.9`, NGINX `1.30.6-alpine`; sonda compilada com Go `1.27.2`. Registrar digests e arquiteturas antes de implementar; ausência de imagem é bloqueio, não fallback para `latest`.
- **Rationale:** Promtail chegou ao fim de vida em 2026-03-02; usuário confirmou Alloy. Versões explícitas permitem reprodução. Go tem correções de segurança de outubro de 2026 e fica apenas no builder.
- **Alternatives considered:** Promtail descartado por fim de suporte; tags flutuantes descartadas; versões da documentação `main/latest` não bastam para comprovar comportamento de release.
- **Evidence:** [Promtail EOL](https://grafana.com/docs/loki/latest/send-data/promtail/), [Alloy releases](https://github.com/grafana/alloy/releases), [Loki releases](https://github.com/grafana/loki/releases), [base NGINX stable](https://raw.githubusercontent.com/nginx/docker-nginx/master/stable/alpine/Dockerfile), [Go release history](https://go.dev/doc/devel/release).

## 2. Docker API em vez de arquivos do host

- **Decision:** `discovery.docker` → filtro por projeto → `loki.source.docker` → `loki.process` → `loki.write`. Acesso por proxy GET/HEAD com allowlist de endpoints, não socket direto no Alloy.
- **Rationale:** a API entrega stdout/stderr sem montar logs físicos do Docker; compatível com daemon Linux da VM no Desktop. A origem já remove o envelope Docker de transporte; não usar `stage.docker`, destinado ao formato json-file em disco.
- **Alternatives considered:** mount de `/var/lib/docker/containers` acopla caminhos/driver; socket direto tem poderes excessivos; Tecnativa `0.5.0` é alternativa funcional, mas habilitar `CONTAINERS` é mais amplo que a allowlist de endpoints requerida e introduz outro tipo de proxy. Reusar uma imagem derivada NGINX em dois serviços separados reduz variedade de bases; o launcher da seção 8 resolve a emissão dos diagnósticos.
- **Evidence:** [discovery.docker](https://grafana.com/docs/alloy/latest/reference/components/discovery/discovery.docker/), [loki.source.docker](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.source.docker/), [tailer da release v1.21.2](https://github.com/grafana/alloy/blob/v1.21.2/internal/component/loki/source/docker/tailer.go), [socket-proxy e limites](https://github.com/Tecnativa/docker-socket-proxy).
- **Limit:** filtro de projeto controla ingestão, não autorização multiusuário no daemon. Inspect pode conter ambiente sensível: rede privada, sem logging de payload e confiança explícita no operador Docker.

## 3. Fluxo e cardinalidade

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

- **Decision:** Loki TSDB v13, filesystem, índice 24h, retenção 336h configurável com mínimo adotado de 24h; compactor/markers/WAL no mesmo volume persistente. Revisão U2: max_chunk_age=5m, chunk_idle_period=1m, flush_check_period=30s, chunk_retain_period=0s, compaction_interval=1m, apply_retention_interval=2m e delete delay=5m. Prazo de aceite permanece 30m após expiração individual em ambiente local saudável, sujeito ao orçamento e comprovação do plano.
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
