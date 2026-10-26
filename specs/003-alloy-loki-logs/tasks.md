# Tasks: Agregação de Logs com Alloy e Loki

**Input**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md), [data-model.md](./data-model.md), [contrato](./contracts/logging-contract.md) e [quickstart.md](./quickstart.md).

**Prerequisites**: Revisão do plano após C1/C2/U1/U2/A1 e complemento do [checklist](./checklists/observability.md) disponíveis. Os 52 marcadores do checklist estão aprovados no estado observado; foram preservados e não constituem evidência operacional. Executar novo `/speckit-analyze` e resolver seus bloqueios antes de implementar.

**Tests**: Obrigatórios por FR-015 e constituição. Escrever e demonstrar falha por contrato ausente antes da implementação correspondente; erro de importação, pacote ausente ou Docker indisponível não é RED válido. Não transformar falhas em skips ou respostas de sucesso.

**Organization**: Setup, fundação, US1 (P1), US2 (P2), US3 (P2) e consolidação. Esta regeneração substitui os 40 IDs anteriores por 46 tarefas pendentes; IDs antigos não designam o mesmo trabalho. Nenhuma funcionalidade, pasta operacional ou teste é criado neste gate.

## Format: `[ID] [P?] [Story] Description`

- `[P]`: elegível para paralelo somente com pré-requisitos concluídos, arquivos distintos e recursos suficientes.
- `[US1]`, `[US2]`, `[US3]`: histórias da especificação. Setup, fundação e consolidação não recebem story label.
- Caminhos futuros são relativos à raiz do repositório. `infra/obs-tools/` substitui o caminho planejado anteriormente como `infra/healthcheck/`; não mover estrutura física neste gate.
- A tabela de dependências é obrigatória; prioridade ou posição no arquivo não substitui seus vínculos.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Fixar entradas reproduzíveis e ferramentas isoladas, sem iniciar a stack.

- [X] T001 Registrar em `specs/003-alloy-loki-logs/research.md` disponibilidade, procedência, arquiteturas e digests de grafana/alloy:v1.21.2, grafana/loki:3.7.9, nginx:1.30.6-alpine e golang:1.27.2; identificar também a base fixada das origens de teste. Imagem indisponível bloqueia o trabalho até revisão do plano, sem fallback para latest.
- [X] T002 [P] Criar `infra/pyproject.toml` com Python >=3.12 e extra dev pytest/Ruff/Black/mypy/PyYAML/types-PyYAML, configurar marcadores de integração/retenção e mypy strict para todo `infra/tests/`, incluindo conftest; gerar `infra/uv.lock` com uv e usar `infra/.venv`, sem requirements.txt ou exclusões globais de tipagem.
- [X] T003 [P] Ajustar `.gitignore` e `.dockerignore` para excluir secrets, ambientes virtuais, caches e artefatos locais de validação sem apagar conteúdo existente nem expor arquivos sensíveis.
- [X] T004 [P] Atualizar `.env.example` com nomes e defaults não secretos do contrato: projeto exato, porta loopback, retenção 336h, diretório de segredos e usuários distintos; preservar outras variáveis e não preencher senhas.
- [X] T005 Criar `infra/obs-tools/go.mod` e `infra/obs-tools/go.sum`, fixando versão compatível de golang.org/x/crypto para bcrypt; resolver/verificar dependências no builder Go fixado, sem implementar criptografia própria ou instalar Go runtime nas imagens.

**Checkpoint**: Bases e dependências identificadas. Nenhum motor ou componente funcional deve ser implementado antes de seus testes prévios.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Disponibilizar harness seguro e ferramenta compartilhada para saúde, preflight operacional e emissão JSON. Bloqueia todas as histórias.

- [X] T006 Criar `infra/tests/conftest.py` com fixtures tipadas de projeto único, diretório privado, credenciais efêmeras e execução Docker com timeout; validar dados YAML/JSON com guards, sem casts para Any; sanitizar diagnósticos e limpar somente recursos/IDs próprios, sem logs brutos de segredos ou alteração da stack do operador.
- [X] T007 Escrever em `infra/tests/test_obs_config.py` os contratos estáticos de topologia, versões/builds, volumes, tmpfs, mounts, healthchecks, depends_on saudável e entrypoints de validação; demonstrar falha pelas configurações ainda ausentes, não por infraestrutura de testes quebrada. Incluir as três redes internas e obs-edge não interna exclusiva do gateway conforme revisão aprovada.
- [X] T008 [P] Escrever em `infra/obs-tools/main_test.go` testes de probe HTTP: 200, status inesperado, timeout 2s, transporte e saída JSON sanitizada com status não zero; estabelecer o RED antes da implementação.
- [X] T009 Implementar o modo probe em `infra/obs-tools/main.go`, usando biblioteca padrão, timeout 2s e sucesso somente por HTTP 200; satisfazer T008 sem arquivos de log, credenciais em diagnóstico ou dependência de curl/wget.
- [X] T010 Ampliar `infra/obs-tools/main_test.go` com testes prévios do preflight por serviço: retenção inteira >=24h/múltipla de 24h, parâmetros de renderização permitidos, arquivos regulares sem symlink, usuário/hash bcrypt únicos e distintos, correspondência da escrita, tamanho ASCII 32–72 bytes, permissões e volumes; incluir reinício/rotação sem cache de aprovação e ausência de correção automática.
- [X] T011 Implementar preflight e despacho por serviço em `infra/obs-tools/main.go` antes de iniciar o motor: validar retenção/config/volume Loki, materiais do gateway, segredo/config Alloy e config/socket do proxy; gateway compara write-password ao bcrypt de write.htpasswd e valida formato do leitor sem conhecer sua senha. Recusar entradas inválidas com saída não zero e JSON sanitizado; renderizar só configuração/PID em tmpfs, nunca logs.
- [X] T012 Ampliar `infra/obs-tools/main_test.go` com testes prévios do launcher: conversão de diagnósticos em JSON sanitizado, access JSON preservado, erro desconhecido explícito sem payload bruto, sentinelas sensíveis, sinais TERM/INT/QUIT, espera do filho, exit status, drenagem, linhas longas e falhas/bloqueio de pipes; não aceitar truncamento ou deadlock silenciosos.
- [X] T013 Implementar o modo run em `infra/obs-tools/main.go`: aplicar preflight a cada inicialização, iniciar NGINX foreground sem entrypoint shell upstream e capturar os dois pipes antes de iniciar; preservar access JSON e emitir categorias/errno/severidade/etapa sanitizados para erros, sem request/upstream/referrer/segredos brutos. Encaminhar sinais, recolher filho, drenar saída e propagar falhas; iniciar Loki/Alloy com formato JSON nativo e sem alterar seus binários.
- [X] T014 Criar `infra/obs-tools/Dockerfile` multi-stage com CGO_ENABLED=0, builder e bases fixados e targets loki/alloy/nginx; copiar obs-tools para `/usr/local/bin/obs-tools`, preservar usuários/binários upstream e substituir entrypoints explicitamente. Usar tags locais jhonny-v/loki-health:3.7.9-1, jhonny-v/alloy-health:1.21.2-1 e jhonny-v/nginx-obs:1.30.6-1, sem pull remoto implícito.
- [X] T015 Completar `infra/tests/test_obs_config.py` com validação dos targets, arquitetura, executável, usuários e entrypoints; executar testes Go no builder fixado e registrar builds/probes em `specs/003-alloy-loki-logs/research.md`. Contratos de serviços ainda ausentes podem permanecer RED; não enfraquecer assertions para fechar artificialmente a fundação.

**Checkpoint**: Ferramenta comum testada e builds disponíveis. Preflight está no runtime, não em conftest. Loki/Alloy que emitam falha textual de startup continuam bloqueadores, não exceções à política JSON.

## Phase 3: User Story 1 — Localizar logs dos serviços em um ponto central (Priority: P1) — MVP

**Goal**: Coletar stdout/stderr do projeto e consultar por gateway autenticado local, sem ingerir projetos estrangeiros.

**Independent Test**: SC-001/SC-002/SC-003/SC-008: 200 IDs de duas origens e dois fluxos em <=60s, descoberta posterior <=60s, 20 IDs estrangeiros ausentes com controle positivo, consulta autenticada e interfaces internas não publicadas. Startup inválido e diagnósticos JSON são condições do MVP.

### Tests first

- [X] T016 [P] [US1] Escrever `infra/tests/test_obs_access.py` com matriz real de ambos os listeners: rota desconhecida 404; rota conhecida sem credencial/válida de outra interface/inválida 401 antes do método; credencial correta com método proibido 405 e Allow; encaminhamento conserva status upstream. Cobrir paths codificados/barras extras, Basic challenge, binds loopback, backend/admin privados e allowlist Docker contra upstream simulado, sem enviar mutações ao daemon.
- [X] T017 [P] [US1] Escrever em `infra/tests/test_obs_ingestion.py` SC-001/SC-002/SC-003 com IDs únicos, duas origens x dois fluxos x 50 eventos, origem nova e 20 eventos estrangeiros; usar polling/deadlines de 60s, controles positivos e diagnóstico de origem incompatível/sem serviço Compose, sem confundir ausência de eventos com indisponibilidade geral.
- [X] T018 [P] [US1] Ampliar `infra/tests/test_obs_config.py` com integração de `compose up` direto e sem pytest no caminho do entrypoint: reter saída/status de inicializações inválidas, mounts ausentes/vazios, retenção inválida, escrita inconsistente e permissões negadas; comprovar interoperabilidade bcrypt/NGINX e JSON nos dois fluxos, incluindo falhas reais anteriores à readiness e sentinelas sensíveis. Cobrir recriação/rotação e ausência de logs em arquivo.
- [X] T019 [US1] Criar `infra/compose.obs.test.yaml` com origens Linux não TTY e base de teste fixada, integrar inicialização em `infra/tests/conftest.py` e executar T016/T017/T018 até demonstrar RED por contratos operacionais ausentes. Manter projeto/volumes/segredos exclusivos, sem alterar aplicações ou recursos do operador.

### Implementation

- [X] T020 [P] [US1] Criar `infra/docker-log-proxy/nginx.conf` para socket Unix com GET/HEAD allowlist de ping/version/list/inspect/logs e listagem exata /networks, prefixo de versão opcional e IDs hexadecimais; negar demais endpoints/métodos/caminhos de escape, manter streaming sem buffering, access JSON sanitizado stdout e error_log stderr capturado pelo launcher, sem arquivo de log.
- [X] T021 [P] [US1] Criar `infra/logs-gateway/nginx.conf.template` com leitura 8080/escrita interna 8081, htpasswd separados e readiness só em loopback 8082; implementar a precedência rota/auth/método do contrato sem return de método anterior à autenticação, conservar erros upstream e impedir arquivos estáticos/bypass de caminhos. Emitir access JSON sem query/Authorization e erros somente pelo launcher.
- [X] T022 [P] [US1] Criar `infra/loki/config.yaml` com single-binary TSDB v13/filesystem, índice 24h, fator de replicação 1, structured metadata e caminhos persistentes WAL/índice/chunks/compactor; usar retenção parametrizada validada e logs JSON nativos, sem publicação do backend.
- [X] T023 [P] [US1] Criar coleta básica em `infra/alloy/config.alloy` com descoberta a cada 5s, filtro exato com.docker.compose.project repetido antes do source, identidade serviço/origem e promoção do fluxo nas regras do source; enviar internamente com segredo por arquivo, logs JSON e posições persistentes, sem montar arquivos físicos de logs do host.
- [X] T024 [US1] Criar `infra/compose.obs.yaml` com quatro serviços usando builds/tags locais do plano, três redes internas isoladas e obs-edge não interna exclusiva do gateway, volumes nomeados, configs/segredos read-only, tmpfs, memória/restart e healthchecks 5s/timeout 3s/12 retries/start 30s; declarar env_file/build/image por serviço, dependências service_healthy e preflight automático, publicar somente 127.0.0.1:${LOKI_PORT:-3100}:8080. Gateway monta write-password adicional para comparação; não anexar a jhonny-core nem criar porta administrativa externa.
- [X] T025 [US1] Completar `infra/tests/conftest.py` com probes privados autorizados e cenários de preflight/rotação chamando obs-tools real; não duplicar nele o validador operacional. Coletar apenas diagnósticos sanitizados de recursos próprios e impedir correção automática de permissões; preparar condições de ACL/UID/GID compatíveis com o contrato.
- [X] T026 [US1] Executar `infra/tests/test_obs_config.py`, `infra/tests/test_obs_access.py` e os cenários US1 de `infra/tests/test_obs_ingestion.py`, incluindo sintaxe Alloy/Loki/NGINX, startup direto inválido, lifecycle real NGINX e JSON de todos os componentes; corrigir componentes da história até satisfazer SC-001/SC-002/SC-003/SC-008 e preflight, sem filtros que ocultem logs reais.
- [X] T027 [US1] Atualizar `specs/003-alloy-loki-logs/quickstart.md` com ativação, consulta, diagnóstico, provisionamento privado e rotação efetivamente suportados; explicar preflight automático e manual, bcrypt/senha ASCII 32–72 bytes e limitações de ACL no Windows/Desktop, preservando .env existente e confiança no operador Docker.

**Checkpoint**: MVP autenticado e isolado, com emissão JSON e validação operacional. Não encerra #103: parsing/contexto, recuperação e retenção ainda precisam de aceite.

## Phase 4: User Story 2 — Filtrar eventos e preservar o contexto de diagnóstico (Priority: P2)

**Goal**: Preservar mensagem, contexto e identidade da instância sem alta cardinalidade.

**Independent Test**: SC-004: quatro JSON com tracing, quatro textos e quatro JSON inválidos, 100% das linhas/origens/IDs preservados; filtros por serviço/instância sem indexar IDs.

### Tests first

- [X] T028 [US2] Ampliar `infra/tests/test_obs_ingestion.py` com SC-004, JSON válido sem message, arrays/primitivos, recriação de instância e mensagens legitimamente repetidas; definir assertions de linha original, timestamp Docker, metadados e labels exatas, demonstrando RED antes do parsing funcional.
- [X] T029 [P] [US2] Ampliar `infra/tests/test_obs_config.py` com validação de instrumentação de fixtures: trace_id/span_id originais obrigatórios quando declarado contexto distribuído, nenhum ID sintetizado, print/log em arquivo vedados em produção; distinguir tolerância de ingestão de texto da obrigação JSON de todos os componentes entregues.

### Implementation

- [X] T030 [US2] Completar `infra/alloy/config.alloy` com parsing sem descarte/reescrita e parse_status controlado; manter container_id/container_name em structured metadata e só project/service/stream/parse_status indexados, sem stage.docker, stage.output, deduplicação por texto ou substituição de timestamp pelo campo da aplicação.
- [X] T031 [US2] Executar os cenários US2 de `infra/tests/test_obs_ingestion.py` e `infra/tests/test_obs_config.py` até satisfazer SC-004, consulta por instância, preservação byte a byte salvo delimitador Docker, duplicatas legítimas e ausência de IDs indexados; revalidar coleta básica após modificar Alloy.
- [X] T032 [US2] Atualizar `specs/003-alloy-loki-logs/contracts/logging-contract.md` com consultas e respostas comprovadas da versão fixada, incluindo structured metadata e limites para linhas vazias/grandes; manter regra de preservação e não inventar garantias fora da escala declarada.

**Checkpoint**: Qualidade de evento comprovada independentemente dos cenários de falha e retenção da US3.

## Phase 5: User Story 3 — Reiniciar e diagnosticar a camada de logs (Priority: P2)

**Goal**: Preservar eventos confirmados, recuperar falha curta e aplicar retenção verificável em operação contínua.

**Independent Test**: SC-005/SC-006/SC-009: preservar 20 IDs após restart Loki, recuperar os 20 da interrupção 30s e um novo em <=60s após saúde restaurada, retomar após restart Alloy e remover dados expirados fisicamente em <=30m da expiração individual, sem restart/flush forçado no cenário principal.

### Tests first

- [X] T033 [P] [US3] Escrever `infra/tests/test_obs_recovery.py` com restart Loki/Alloy, confirmação prévia de 20 IDs, falha de Loki por 30s e 20 IDs <=1KiB durante falha mais um posterior; deadline <=60s após readiness, duplicatas toleradas e diagnóstico explícito. Simular config/socket/armazenamento indisponíveis somente em recursos próprios, sem afetar o daemon compartilhado.
- [X] T034 [P] [US3] Escrever `infra/tests/test_obs_retention.py` com projeto/volume novos e política 24h anterior à ingestão; confirmar eventos sintéticos pouco antes de expirar e medir deadlines individuais timestamp+24h+30m. Incluir streams separados, mesmo chunk com idades mistas/amplitude até 4m conforme revisão autorizada, continuidade e escrita atrasada/fora de ordem de 60s aceita; exigir remoção física e preservação de controles válidos, sem restart/flush, deleção manual ou intervalos facilitados no cenário principal.
- [X] T035 [US3] Estender `infra/tests/conftest.py` e `infra/compose.obs.test.yaml` para fault injection por IDs próprios, política alternativa e inspeção autorizada somente do volume de teste; identificar chunks/objetos e coletar evidências de amplitude temporal, flush, índice, marcadores e sweeper. Ajustar aceitação de timestamps antigos só na fixture, sem supor retroatividade; executar T033/T034 e registrar RED antes das mudanças funcionais.

### Implementation

- [X] T036 [US3] Configurar `infra/alloy/config.alloy` com batch_wait=1s, batch_size=1MiB, timeout=5s, backoff 1s–5s e 30 retentativas; manter posições no volume sem tratá-las como WAL de envio, não habilitar queue_config experimental nem alterar preservação/parsing da US2.
- [X] T037 [P] [US3] Completar `infra/loki/config.yaml` com retenção padrão 336h, mínimo/múltiplos 24h no preflight e desenho autorizado: max_chunk_age=3m, chunk_idle_period=1m, flush_check_period=30s, chunk_retain_period=0s, compaction_interval=30s, apply_retention_interval=1m, retention_delete_delay=3m, tsdb_shipper.resync_interval=30s, query_timeout=1m e delete requests filesystem; validar schema da release, persistir WAL/markers e não antecipar deleção de eventos válidos.
- [X] T038 [US3] Revisar `infra/compose.obs.yaml` para persistência real, usuários/permissões e mounts corretos em reinício/recriação, mantendo preflight e healthchecks reais; nenhum dado em árvore de código, depends_on service_started ou dependência de aplicações futuras.
- [X] T039 [US3] Executar `infra/tests/test_obs_recovery.py` até comprovar SC-005/SC-006 e retomada após restart Alloy; registrar diagnósticos sanitizados e IDs, sem ocultar perdas, ampliar prazos ou considerar prontidão isolada como prova de entrega.
- [X] T040 [US3] Executar `infra/tests/test_obs_retention.py` com job até 50m e deadline individual de limpeza <=30m; medir orçamento revisado e autorizado do plano: amplitude 4m, flush 2m, índice 17m, compactação/retenção conjuntas 2m, delete delay 3m, sweeper 1m30s e reserva 30s (revisado após a CI medir 240,0256s). Comprovar objetos removidos e válidos preservados, sem usar ausência na consulta como prova suficiente; falha de amplitude/backlog/caches ou prazo bloqueia aceite e reabre plan/analyze, sem desabilitar escrita fora de ordem silenciosamente.
- [X] T041 [US3] Atualizar `specs/003-alloy-loki-logs/quickstart.md` com resultados de restart/recuperação/retenção, evidências das etapas medidas e limitações reais; proibir down -v no operador e separar teste principal contínuo de eventual cenário complementar com flush/restart, sem prometer exactly-once, fila durável ou armazenamento ilimitado.

**Checkpoint**: Durabilidade e recuperação comprovadas, prazo de limpeza avaliado sem atalhos. Falha upstream não autoriza reduzir critérios ou concluir tarefa sem evidência.

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Consolidar validação, documentação e rastreabilidade da entrega.

- [X] T042 Criar `.github/workflows/validate-issue-103.yml` com Ruff/Black, mypy strict em todo infra/tests, testes Go de obs-tools no builder fixado e pytest estático/integração em Docker Linux; incluir JSON/startup/preflight/matriz HTTP/lifecycle e job obrigatório de retenção com timeout 50m sem ampliar deadline 30m. Usar credenciais efêmeras e relatórios sanitizados; Docker ausente ou skip implícito falha no gate.
- [X] T043 [P] Atualizar `README.md`, `docs/issues/v0.1/ISSUE-103.md` e `docs/milestones/v0.1-infra-core.md` com composição de logs, acesso, pré-requisitos e estado real, preservando roadmap de OpenJarvis e independência de MCP/Worker/Grafana.
- [X] T044 Executar validação consolidada de `specs/003-alloy-loki-logs/quickstart.md`: Ruff/Black/mypy strict, go test ./... no módulo obs-tools/builder fixado, sintaxe de Compose/Alloy/Loki/NGINX e toda suíte infra/tests; comprovar SC-001 a SC-009 e preservar contratos core/LLM sem exceções silenciosas ou supressões abrangentes de tipagem.
- [ ] T045 Registrar em `specs/003-alloy-loki-logs/quickstart.md` ambiente/comandos/resultados de CI Linux e smoke Windows/Docker Desktop, incluindo ACL do host e permissões Linux verificáveis dos mounts; se não comprovados, declarar bloqueio/lacuna sem certificar plataforma, relaxar permissões ou marcar tarefa concluída.
- [ ] T046 Completar `specs/003-alloy-loki-logs/contracts/logging-contract.md` com rastreabilidade FR-001 a FR-015/SC-001 a SC-009 e C1/C2/U1/U2/A1 para evidências reais; confirmar cleanup somente de recursos próprios e ausência de segredos/logs em disco versionados. Preservar todos os marcadores de checklist pertencentes ao revisor.

**Fechamento local:** T001–T044 concluídas; 29 testes de regressão + 1 cenário contínuo de retenção passaram, além de Ruff/Black/mypy strict, Go race/vet, actionlint e validação de Compose core/LLM sem resolução de segredos. **T045 bloqueada:** CI remota e ACL do bind Windows do operador não comprovadas. A matriz local e o cleanup de T046 estão documentados, mas a tarefa permanece pendente por depender de T045; não fechar a issue ou certificar plataforma enquanto faltarem essas evidências.

## Dependencies & Execution Order

### Grafo de fases e histórias

```text
Setup -> Foundational -> US1 (P1, MVP) -> US2 (P2)
                                    \-> US3 (P2)
US2 + US3 -> Polish -> validação final
```

US2 e US3 dependem da coleta básica da US1. US3 não depende conceitualmente de parsing, mas T036 sucede T030 para serializar edições de Alloy. Não alterar conftest ou executar testes que o importem enquanto ele estiver em mudança; reservar uma janela exclusiva para T035 antes ou depois das execuções US2, sem exigir seu resultado para aceitar US2.

### Pré-requisitos por tarefa

As dependências são transitivas. As execuções iniciais RED constam nas tarefas de teste ou no fechamento de fixtures imediatamente anterior ao trabalho funcional. Além do grafo, observar a exclusão mútua de edição/execução do harness indicada acima.

| Tarefa | Depende de |
|--------|------------|
| T001, T002, T003, T004 | Gates documentais anteriores; sem dependências entre si |
| T005 | T001 |
| T006 | T001, T002, T003, T004 |
| T007 | T006 |
| T008 | T005 |
| T009 | T008 |
| T010 | T009 |
| T011 | T010 |
| T012 | T011 |
| T013 | T012 |
| T014 | T001, T013 |
| T015 | T007, T014 |
| T016, T017, T018 | T015 |
| T019 | T016, T017, T018 |
| T020, T021, T022, T023 | T019 |
| T024 | T020, T021, T022, T023 |
| T025 | T024 |
| T026 | T025 |
| T027 | T026 |
| T028, T029 | T027 |
| T030 | T028, T029 |
| T031 | T030 |
| T032 | T031 |
| T033, T034 | T027 |
| T035 | T033, T034 |
| T036 | T035, T030 |
| T037 | T035 |
| T038 | T036, T037 |
| T039, T040 | T038 |
| T041 | T039, T040, T027 |
| T042, T043 | T032, T041 |
| T044 | T042, T043 |
| T045 | T044 |
| T046 | T045 |

T035 e as execuções que importam conftest não são concorrentes, mas podem ser ordenados em qualquer sentido. T032 e T041 editam documentos diferentes e podem prosseguir independentemente; a consolidação T046 fecha o contrato com as evidências de ambas as histórias.

### Parallel opportunities

- Setup: T001/T002/T003/T004 em arquivos distintos. T005 pode prosseguir após T001 enquanto T006/T007 preparam harness/contratos.
- Fundação: T008–T014 podem avançar com T006/T007, sem edições concorrentes no mesmo arquivo; tarefas sucessivas em main.go/main_test.go são serializadas explicitamente.
- US1: T016/T017/T018 em arquivos distintos; após RED T019, T020/T021/T022/T023 geram quatro configurações distintas.
- US2: T028 com T029, ambos após T027.
- US3: T033 com T034 após T027; T037 pode avançar em Loki enquanto US2 altera Alloy. T036 aguarda T030.
- Execuções T039/T040 usam projetos/volumes exclusivos; serializar se não houver capacidade reservada para ambos. Não iniciar integração enquanto arquivos importados estiverem sendo alterados.
- Polish: T043 em paralelo a T042; validação consolidada só após ambos.

## Parallel Example: User Story 1

```text
Depois de T015:
  T016 -> infra/tests/test_obs_access.py
  T017 -> infra/tests/test_obs_ingestion.py
  T018 -> infra/tests/test_obs_config.py
Depois de T019 (RED):
  T020 -> infra/docker-log-proxy/nginx.conf
  T021 -> infra/logs-gateway/nginx.conf.template
  T022 -> infra/loki/config.yaml
  T023 -> infra/alloy/config.alloy
```

## Parallel Example: User Story 2

```text
Depois de T027:
  T028 -> infra/tests/test_obs_ingestion.py
  T029 -> infra/tests/test_obs_config.py
Depois de ambos: T030 -> T031 -> T032
```

## Parallel Example: User Story 3

```text
Depois de T027:
  T033 -> infra/tests/test_obs_recovery.py
  T034 -> infra/tests/test_obs_retention.py
Depois de T035:
  T037 -> infra/loki/config.yaml
  T036 -> infra/alloy/config.alloy (também aguarda T030)
```

## Implementation Strategy

1. **MVP first**: Setup/fundação e US1, com coleta, isolamento, acesso autenticado, preflight e JSON. Não antecipar OpenJarvis/MCP/Worker nem declarar a issue concluída pelo MVP.
2. **Incrementos**: US2 adiciona qualidade/contexto e US3 acrescenta persistência, recuperação e retenção. Respeitar a coordenação de arquivos compartilhados e revalidar os contratos afetados.
3. **Tests first**: Falha esperada de contrato antes de funcionalidade; preservar testes e deadlines. Não atribuir aprovação a falha de ferramenta/ambiente.
4. **Gates de risco**: Novo analyze antes de implement. Versão inexistente, diagnóstico textual, preflight contornável, tipagem suprimida ou retenção fora do orçamento bloqueiam avanço/entrega conforme o gate afetado, exigindo correção e reanálise.
5. **Entrega**: CI, smoke documentado, rastreabilidade e evidência persistente antes de marcar tarefas. Checklist é de propriedade do revisor e não deve ser alterado pelo implement.

## Rastreabilidade dos cinco achados

| Achado | Trabalho de implementação e comprovação |
|--------|----------------------------------------|
| C1 — emissão JSON | T012–T015, T018, T020–T026, T042, T044 |
| C2 — tipagem | T002, T006, T042, T044 |
| U1 — preflight operacional | T010–T014, T018, T024–T027, T038, T045 |
| U2 — retenção contínua | T034–T035, T037, T040–T042, T044 |
| A1 — precedência HTTP | T016, T021, T026, T042, T044 |

## Constitutional Analysis

A decomposição mantém infraestrutura v0.1 em infra, dependências em pyproject/uv, versões/builds explícitos, segredos externos, saúde real e testes prévios/CI. Inclui tipagem e emissão JSON de todos os componentes novos, sem usar FR-007 como exceção à constituição. Preflight é obrigatório na inicialização normal, e o aceite de retenção não depende de flush/restart facilitadores.

O desenho não equivale a comprovação operacional e este arquivo não encerra o analyze anterior. Todos os 46 itens permanecem pendentes; nenhuma imagem, configuração executável, serviço ou teste funcional foi criado/executado nesta geração.
