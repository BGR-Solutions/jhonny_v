# Implementation Plan: Agregação de Logs com Alloy e Loki

**Branch de trabalho**: `feature/with-jarvis` | **Feature ID**: `003-alloy-loki-logs` | **Date**: 2026-10-25 | **Spec**: [spec.md](./spec.md)

**Input**: [Issue #103](../../docs/issues/v0.1/ISSUE-103.md), esclarecimentos de acesso autenticado local, retenção de 14 dias e recuperação da falha de 30 segundos.

## Summary

Adicionar futuramente `infra/compose.obs.yaml` com quatro serviços: `docker-log-proxy`, `loki`, `logs-gateway` e `alloy`. Coletar exclusivamente contêineres do projeto via API Docker filtrada, preservar linhas e contexto e consultar Loki por gateway autenticado publicado somente em loopback. Loki single-binary usa TSDB v13/filesystem em volume nomeado; Alloy usa descoberta dinâmica, parsing sem reescrita da mensagem e retentativas estáveis.

Esta revisão produz somente desenho e contratos e trata C1, C2, U1, U2 e A1 do analyze. Não cria serviços, segredos, imagens, testes ou pipeline executável, nem muda código de aplicações. O `tasks.md` existente corresponde ao desenho anterior: deve ser regenerado no gate próprio antes de novo analyze.

## Technical Context

**Language/Version**: YAML Compose, Alloy configuration language, configuração Loki e NGINX; Python >=3.12 para pytest de infraestrutura; Go 1.27.2 para ferramentas estáticas de saúde, validação de inicialização e lançamento dos proxies.

**Primary Dependencies**: Docker Engine Linux e Compose v2 com `--wait`, `profiles` e dependências `service_healthy`; bases fixas `grafana/alloy:v1.21.2`, `grafana/loki:3.7.9`, `nginx:1.30.6-alpine`, builder `golang:1.27.2`. Validar disponibilidade/arquiteturas e registrar digests antes do primeiro build; não substituir versões silenciosamente.

**Storage**: `loki-data` para chunks, índice, WAL e marcadores do compactor; `alloy-data` para posições. Configurações bind-mounted somente leitura. Sem dados persistentes na árvore de código.

**Testing**: `infra/pyproject.toml`, extra `dev` com pytest, Ruff, Black, mypy, PyYAML e types-PyYAML; `uv` cria `infra/.venv`. `mypy --strict` cobre todo `infra/tests/`, incluindo conftest, com validação de objetos retornados por YAML/JSON, sem ignores globais ou casts para Any. Fixtures usam biblioteca padrão para Docker CLI, HTTP e polling, sem SDK Docker adicional. Go usa biblioteca padrão e `golang.org/x/crypto/bcrypt` somente para verificar a credencial de escrita; fixar versão compatível e checksums em go.mod/go.sum antes do build. Testes antes da implementação; CI Linux e smoke test documentado em Docker Desktop/Windows.

**Target Platform**: Contêineres Linux em Docker Engine e Docker Desktop/WSL2; comandos host PowerShell. Não cobre Windows containers, acesso remoto ao daemon, Swarm ou Kubernetes.

**Project Type**: Infraestrutura local compartilhada, não novo app nem biblioteca de domínio.

**Performance Goals**: SC-001 a SC-009; descoberta a cada 5s; lotes de envio de 1s; recuperação da amostra em até 60s após indisponibilidade de 30s.

**Constraints**: Consultas autenticadas somente em `127.0.0.1`; ingestão interna autenticada com credencial distinta; nenhuma porta Docker/Loki/Alloy publicada; sem Promtail ou recursos experimentais de Alloy; retenção padrão `336h`, mínimo suportado nesta entrega `24h`, múltiplos de `24h`.

**Scale/Scope**: Um projeto Compose local, até 20 contêineres, linhas de até 64 KiB; teste de recuperação com 20 eventos de até 1 KiB. Reserva inicial: 2 GiB RAM e 10 GiB livres para a stack de logs, sem constituir garantia de capacidade para 14 dias em qualquer taxa. Limites iniciais: Loki 1 GiB, Alloy 512 MiB e cada proxy 128 MiB; revisar somente por evidência dos testes.

## Constitution Check

| Obrigação | Antes da pesquisa | Depois do desenho |
|-----------|-------------------|-------------------|
| Separação apps/libs/infra/docs e ordem bottom-up | PASS: issue v0.1 em infraestrutura | PASS: sem app novo; nenhuma dependência de OpenJarvis/MCP/Worker |
| Dependências Python em pyproject e ambiente uv | PASS: ferramentas de teste serão isoladas | PASS: `infra/pyproject.toml`, sem requirements.txt |
| Logs JSON em stdout/stderr e contexto | FAIL no desenho anterior: stderr NGINX textual | PASS de desenho: launcher converte diagnósticos antes da saída do contêiner; validação inclui erros de inicialização; FR-007 não é exceção constitucional |
| Lint, formatação, tipagem e testes | FAIL no desenho anterior: faltava tipagem | PASS de desenho: Ruff/Black/mypy strict/pytest e testes Go são gates locais e de CI |
| Composição explícita, versões e saúde | PASS: novos serviços planejados em overlay | PASS: imagem/build, rede, mounts, ambiente, dependências e healthchecks definidos abaixo |
| Credenciais fora do Git, controle de acesso | PASS: nenhuma credencial criada | PASS: gateway separa leitura/escrita; Docker proxy privado e GET allowlist |
| Testes antes de mudanças comportamentais e CI | PASS: plano antes de código | PASS: matriz de contratos e comandos definidos; execução obrigatória no implement |

**Resultado:** falhas documentais iniciais corrigidas no desenho revisado, sem exceção constitucional. PASS do desenho não certifica funcionamento nem aprova o gate analyze: checklist e tarefas existentes ainda precisam ser confrontados com esta revisão. Builds, saída JSON de todos os componentes, parsing, permissões, retenção e testes permanecem evidências obrigatórias da implementação; qualquer falha bloqueia entrega.

## Project Structure

### Documentation (this feature)

```text
specs/003-alloy-loki-logs/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/requirements.md
└── contracts/logging-contract.md
```

### Source Code (repository root, implementação futura)

```text
infra/
├── compose.yaml                    # preservar base; declarar volumes/redes no overlay
├── compose.core.yaml               # preservar
├── compose.llm.yaml                # preservar
├── compose.obs.yaml
├── compose.obs.test.yaml           # fixtures somente em validação
├── pyproject.toml
├── uv.lock
├── alloy/config.alloy
├── loki/config.yaml
├── logs-gateway/nginx.conf.template
├── docker-log-proxy/nginx.conf
├── obs-tools/
│   ├── Dockerfile                  # builder e targets loki/alloy/nginx
│   ├── go.mod
│   ├── go.sum
│   ├── main.go                     # modos probe, preflight e run
│   └── main_test.go                # saúde, validação, sinais e saída JSON
└── tests/
    ├── conftest.py
    ├── test_obs_config.py
    ├── test_obs_access.py
    ├── test_obs_ingestion.py
    ├── test_obs_recovery.py
    └── test_obs_retention.py
.github/workflows/validate-issue-103.yml
.env.example                        # somente nomes e placeholders vazios
.gitignore                          # excluir secrets e artefatos locais específicos
.dockerignore                       # garantir exclusões de venv/cache/secrets
README.md                           # navegação/ativação
```

**Structure Decision**: Configurações por serviço em `infra/`; testes de infraestrutura não pertencem a `libs/utils_lib` nem a um app. A pasta observada de `libs/utils_lib` contém somente ambiente local, sem manifest versionado reutilizável; não assumir helpers existentes. Segredos preparados pelo operador ficam em `secrets/observability/` ignorado, nunca gerados neste planejamento. O caminho futuro `healthcheck/` passa a `obs-tools/` porque a ferramenta também valida inicialização e supervisiona NGINX; nenhuma pasta física é criada ou renomeada neste gate.

## Phase 0 — Research

Decisões, alternativas e fontes em [research.md](./research.md). Não há escolha funcional em aberto. Versões fixadas são bases de projeto, não alegação de ausência de vulnerabilidades; revalidar disponibilidade e avisos de segurança antes de construir.

## Phase 1 — Architecture and Contracts

### Composição e fronteiras

```text
Operador localhost -> logs-gateway:8080 (Basic Auth leitura) -> loki:3100
Alloy -> logs-gateway:8081 (Basic Auth escrita, interno) -> loki:3100
Alloy -> docker-log-proxy:2375 (GET allowlist, interno) -> socket Docker
```

- `obs-docker` interna: apenas Alloy e docker-log-proxy.
- `obs-ingest` interna: apenas Alloy e logs-gateway.
- `obs-storage` interna: apenas Loki e logs-gateway.
- Sem anexar esses serviços a `jhonny-core`; descoberta Docker independe da rede das origens. O gateway publica exclusivamente `127.0.0.1:${LOKI_PORT:-3100}:8080`; não reutilizar `HOST_IP` configurável para expor o serviço.
- Testes verificam bindings e acesso de um contêiner não associado, além de autenticação; loopback é restrição de acesso pela rede, não isolamento entre usuários do mesmo host.
- O proprietário do daemon Docker é uma fronteira de confiança: quem controla o daemon pode contornar redes/mounts. Não oferecer multitenancy contra administradores do host.

| Serviço | Fonte por ambiente local | Mounts e ambiente | Saúde e dependências |
|---------|--------------------------|-------------------|----------------------|
| docker-log-proxy | `build` target `nginx` sobre base fixa; tag `jhonny-v/nginx-obs:1.30.6-1`, sem pull remoto implícito | Socket Unix e config `:ro`; sem env_file/segredo; única rede obs-docker | Probe GET local `/_ping` com resposta esperada; sem depends_on |
| loki | `build` target `loki` com base fixa Grafana e sonda estática; tag local explícita `jhonny-v/loki-health:3.7.9-1`, sem pull remoto implícito | Config `:ro`, volume loki-data, `.env` apenas para parâmetros não secretos | Sonda GET `/ready`, sucesso só 200; sem depends_on |
| logs-gateway | Mesmo target/tag NGINX local do proxy Docker | Template `:ro`, htpasswd e write-password separados `:ro`, config renderizada em tmpfs; credenciais nunca no env_file | Probe local `/ready` encaminha a Loki; depende de Loki saudável |
| alloy | `build` target `alloy` com base fixa Grafana e mesma sonda; tag local explícita `jhonny-v/alloy-health:1.21.2-1` | Config `:ro`, volume alloy-data, segredo de escrita por arquivo `:ro`; env_file `.env` para nome do projeto/retentativas | GET `/-/ready`; depende de docker-log-proxy e logs-gateway saudáveis |

Todos: `restart: unless-stopped`, sem modo privileged, mounts declarados, limites de memória e timeouts, healthcheck a cada 5s com timeout 3s, 12 tentativas e início tolerante a 30s. Dependências operacionais usam `condition: service_healthy`. Sonda HTTP com timeout de 2s e exit !=0 para transporte/status inesperado, sem autenticação em endpoints administrativos publicados (não existem).

As bases Loki/Alloy não garantem curl/wget. Um único executável Go, compilado `CGO_ENABLED=0` e copiado em multi-stage para os três targets, oferece probe, preflight e run sem instalar shell/pacotes adicionais. Preservar usuários e binários upstream; trocar entrypoint explicitamente para aplicar as validações, sem executar os scripts shell do entrypoint NGINX. Validar arquitetura e permissões no build; não usar configuração válida como substituto de readiness.

### Inicialização validada, sem depender de pytest

O entrypoint de cada serviço executa o preflight aplicável em toda inicialização/reinício, antes do motor. Loki valida retenção inteira em horas, >=24h e múltipla de 24h, renderiza somente parâmetros permitidos e verifica config e volume sob o usuário runtime. Gateway valida usuários distintos, exatamente uma entrada bcrypt por htpasswd, arquivos não vazios, permissões e correspondência de write-password com write.htpasswd; Alloy verifica leitura do segredo e configuração; proxy verifica config/socket. Senha de escrita tem 32 a 72 bytes ASCII aleatórios, sem newline de conteúdo, evitando truncamento bcrypt; validação do leitor cobre formato/hash, não supõe conhecer sua senha. O teste autenticado comprova a senha do leitor.

Arquivos devem ser regulares, sem symlink, sem acesso de outros usuários não autorizados; diretório privado e leitura apenas por operador/identidades runtime declaradas. No Linux validar UID/GID/modo efetivos. No Windows/Desktop o operador deve validar ACL no host e usar armazenamento WSL2 com permissões Linux verificáveis para os mounts; modo sintetizado pelo Desktop não comprova ACL do host. Sem comprovação, o procedimento falha explicitamente e não certifica a plataforma.

Falhas saem com status não zero e evento JSON sanitizado com serviço, etapa e código; nunca corrigem chmod/ACL automaticamente. Gateway só fica saudável após validar materiais e Loki; Alloy depende dele saudável. O mesmo validador é chamado pelos testes e por `compose run` de preflight, mas não reside em conftest. `compose up` direto não contorna o gate. Rotação exige substituir arquivos de forma controlada e recriar gateway/Alloy; a validação roda novamente, sem cache de aprovação.

### Docker e descoberta

Proxy NGINX dedicado, sem publicação de porta, encaminha ao socket Unix somente `GET/HEAD` de `/_ping`, `/version`, `/containers/json`, `/containers/<id>/json` e `/containers/<id>/logs`, admitindo prefixo `/v<major>.<minor>/`. IDs são hexadecimais, não nomes livres. Rejeitar métodos mutantes, endpoints não listados e caminhos de escape; streaming de logs sem buffering e com timeout de leitura adequado. Não permitir `exec`, archive, images, secrets ou acesso administrativo.

`discovery.docker` usa filtro `com.docker.compose.project` igual a `COMPOSE_PROJECT_NAME`; repetir o filtro em `discovery.relabel` antes de encaminhar alvos. Promover o fluxo somente em `loki.source.docker.relabel_rules`, onde `__meta_docker_container_log_stream` está disponível. Capturar metadados da origem antes de remover labels internas.

O proxy restringe operações, não implementa autorização por projeto: listagem/inspect de outros contêineres continua tecnicamente possível para Alloy comprometido. Evitar inspect desnecessário; não registrar respostas da API. Documentar essa exposição residual, que não equivale a ingeri-las. Docker Desktop requer socket do daemon Linux da VM; não montar named pipe do Windows nem diretório host de logs. Falhar com diagnóstico se indisponível.

### Pipeline e dados

Labels indexadas: `project`, `service`, `stream` e `parse_status` (`json`, `text_or_invalid_json`). Identidade de instância `container_id` completo e `container_name` vira structured metadata; não label indexada. `trace_id`, `span_id`, severidade e mensagem permanecem na linha original e são extraídos na consulta, evitando inventar schema de aplicações. JSON stage não descarta inválidos, não usa `stage.output` e não altera timestamp pelo campo arbitrário da aplicação. Timestamp de ingestão vem da API Docker.

Inicializar `parse_status=text_or_invalid_json`, reconhecer JSON válido e marcar `json`, sem promover dados de texto livre a labels. Testar JSON válido sem campo `message` e primitivos: a mensagem original é sempre preservada; contexto só é exigido quando a aplicação o declara. Eventos próprios com contexto distribuído sem IDs falham na validação de instrumentação, não são silenciosamente "corrigidos".

### Acesso e segredos

NGINX usa dois listeners de dados e arquivos htpasswd diferentes. Leitura: somente endpoints GET de consulta/labels/series definidos no contrato. Escrita: somente POST `/loki/api/v1/push`. Uma credencial não acessa a outra interface. Readiness do gateway usa listener administrativo separado em `127.0.0.1:8082` dentro do contêiner, sem publicação nem acesso pelas redes Docker. Loki não tem portas publicadas nem autenticação nativa; `auth_enabled: false` é seguro apenas atrás destas fronteiras, não autorização para expor Loki.

Operador fornece senhas aleatórias de ao menos 32 caracteres, arquivos htpasswd com hashes fortes suportados pela imagem e segredo legível pelo Alloy. Manter arquivos fora do Git, permissões restritas e nomes exatos documentados; inexistência/arquivo vazio causa falha. Não imprimir segredos, headers Authorization ou respostas Docker. Basic Auth em HTTP é limitado a loopback e redes internas deste ambiente local, nunca solução para acesso remoto; produção fora do escopo.

Todos os componentes entregues emitem JSON por stdout/stderr, inclusive em falhas. NGINX usa access_log JSON com escape=json em stdout e error_log stderr. O launcher Go inicia o master em foreground, captura ambos os pipes antes de iniciar e converte cada diagnóstico nativo em evento JSON antes de expor stderr do contêiner; não há arquivo intermediário de logs. Access logs são validados como objetos JSON e preservados, sem query string, Authorization ou corpo. Linha inválida vira diagnóstico explícito, não descarte.

Diagnósticos incluem serviço, etapa, severidade e categoria/errno sanitizados; conteúdo livre de request/upstream/referrer e credenciais não é repassado. Diagnóstico não reconhecido produz categoria explícita, tamanho e digest, sem conteúdo bruto; preservar informação operacional suficiente nos casos testados de configuração inválida, socket, permissão e upstream. Não inserir trace_id/span_id fictícios; contexto só é obrigatório quando distribuído e disponível. Loki/Alloy usam formato JSON nativo; falha de startup textual também bloqueia aceite, não é exceção automática.

Launcher encaminha SIGTERM/SIGINT/SIGQUIT ao master, aguarda/recolhe o filho e drena pipes, preserva falha de saída e trata falha de leitura/escrita como erro, sem sucesso silencioso. Linha longa não pode causar truncamento silencioso ou deadlock. Config renderizada e PID usam tmpfs; isso não autoriza logs em arquivo. Testar os processos reais, erros antes de readiness, caracteres escapáveis, segredos sentinela, desligamento e bloqueio de pipes. Excluir probes de access logs para evitar amplificação; não excluir logs reais do projeto. Essa conversão na emissão não altera a preservação das linhas de origens externas ou fixtures de FR-007.

### Retenção, recursos e recuperação

- Loki single-binary, fator de replicação 1, TSDB/schema v13, index period 24h, filesystem e WAL persistentes. Volume inclui working directory/markers do compactor para sobreviver a reinícios.
- `LOKI_RETENTION_PERIOD=336h`, configurável em múltiplos de 24h, mínimo 24h validado no entrypoint. Índice 24h, compactor retention habilitada, delete requests filesystem. Parametrizar ingester com max_chunk_age=5m, chunk_idle_period=1m, flush_check_period=30s e chunk_retain_period=0s; compaction_interval=1m, apply_retention_interval=2m (distinto para evitar deslocamento implícito) e retention_delete_delay=5m. Validar schema da release antes de aceitar esses parâmetros.
- Aceite continua <=30m desde timestamp do evento + política, não desde flush/restart. Em v3.7.9, a decisão de expirar usa o timestamp mais recente do chunk; portanto medir também a amplitude temporal dos chunks, sem deduzir que max_chunk_age isoladamente limita todos os casos de escrita atrasada/fora de ordem. Orçamento de qualificação: até 5m de amplitude por chunk, 1m de flush, 3m de publicação/atualização de índice, 2m de compactação, 3m de aplicação de retenção, 5m de delete delay e 1m de sweeper; reserva 10m, total 30m. Publicação de índice, sweeper e amplitude devem ser medidos na release e carga declaradas; são condições de aceite, não garantias inferidas de defaults. Falhar se amplitude/backlog/caches excederem esse orçamento. Não desabilitar escrita fora de ordem silenciosamente para obter aprovação. Não há SLA upstream: se o desenho não cumprir, reabrir plan/analyze, sem relaxar o prazo.
- Retenção não equivale a quota de disco. Taxa local deve caber no espaço reservado; erro por armazenamento cheio deve aparecer explicitamente, sem apagar dados não expirados para simular sucesso. Sem promessa de 14 dias sob uso ilimitado.
- Teste principal usa projeto/volume novo com política 24h anterior à ingestão. Inserir timestamps sintéticos poucos minutos antes do limite de expiração, confirmar consulta antes de expirar e iniciar deadline no timestamp+24h de cada evento. Manter Loki ativo, sem restart, chamada de flush, deleção manual ou alteração de intervalos. Ajuste de aceitação de amostras antigas é exclusivo do teste. Cenário isolado com streams separados comprova remoção; outro mistura eventos cronológicos com amplitude de até 5m no mesmo stream/chunk, cobre continuidade e escrita atrasada/fora de ordem aceita pela release e mantém controles não expirados. Inspeção autorizada identifica objetos/chunks e mede amplitude, flush, índice, marcadores e sweeper; ausência em consulta sozinha não comprova remoção física. Preservar eventos válidos e provar remoção dos expirados dentro de seus deadlines individuais. Caso com flush/restart é complementar de persistência, nunca substituto. Não presumir retroatividade da política.
- Alloy: `batch_wait=1s`, `batch_size=1MiB`, timeout 5s, backoff mínimo 1s e máximo 5s, 30 retentativas. Permanecer estável; não ativar `queue_config` experimental. Teste 30s usa 20 eventos <=1KiB e coletor ativo. Volume de posições não é WAL de envio nem garantia de sobrevivência da fila a crash.
- Duplica retentativas são toleradas; comparar IDs únicos dos eventos de teste, nunca deduplicar por texto em produção. Reinício simultâneo, rotação que apague origem e indisponibilidade prolongada continuam fora da garantia.

## Validation and Delivery

Detalhes e comandos em [quickstart.md](./quickstart.md); interfaces em [logging-contract.md](./contracts/logging-contract.md); entidades em [data-model.md](./data-model.md).

1. Escrever testes config/segurança e cenários pytest antes de implementar os arquivos funcionais.
2. Validar Compose/rendering, configs Alloy/Loki/NGINX, origem/digests e builds de probes.
3. Executar SC-001 a SC-009 em projeto exclusivo, sem tocar stacks de outros usuários.
4. CI Linux: Ruff/Black, `mypy --strict infra/tests`, `go test ./...` de obs-tools no builder fixado, testes estáticos e integração com Docker; incluir startup inválido, lifecycle do launcher, saída JSON e matriz de acesso do contrato. Retenção em job separado com timeout 50m para preparar/confirmar eventos antes da expiração e observar o deadline de 30m; timeout do job não amplia o prazo de limpeza. Falta de Docker falha no job obrigatório; skip local somente explícito e não conta como evidência de aceite.
5. Confirmar Windows/Docker Desktop por smoke test e registrar limites; não alegar certificação multiplataforma sem execução.
6. Atualizar README, issue e contratos com evidências, mantendo OpenJarvis/MCP/Worker e core inalterados.

## Complexity Tracking

Sem violação constitucional proposta. Os dois proxies são limites distintos (autenticação Loki e redução de poder do socket); removê-los exporia interfaces sem controles exigidos. A sonda estática compartilhada existe somente para healthchecks reais em imagens mínimas; external probe ou `service_started` não atendem a obrigação de saúde por serviço.

**Próximos gates:** `/speckit-checklist` → `/speckit-tasks` → `/speckit-analyze` → `/speckit-implement`.
