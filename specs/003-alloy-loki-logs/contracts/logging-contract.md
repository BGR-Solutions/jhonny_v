# Contract: Coleta, consulta e operação de logs

## 1. Configuração de ambiente

| Nome | Padrão / validação |
|------|--------------------|
| COMPOSE_PROJECT_NAME | Projeto Compose efetivo; seleção exata, sem valor curingado |
| LOKI_PORT | 3100, porta host em 127.0.0.1 apenas |
| LOKI_RETENTION_PERIOD | 336h; múltiplos de 24h, mínimo 24h |
| OBS_SECRETS_DIR | Caminho local `secrets/observability`, ignorado |
| OBS_READ_USER | Nome do leitor, sem senha no manifest |
| OBS_WRITE_USER | Nome distinto do escritor |

Arquivos esperados: `read.htpasswd`, `write.htpasswd`, `write-password`, legíveis apenas para operador/runtime autorizado. Senhas ASCII aleatórias de 32 a 72 bytes, sem newline de conteúdo; exatamente uma entrada bcrypt por htpasswd, usuários distintos. Gateway monta também write-password para verificar sua correspondência com o hash; não precisa conhecer a senha do leitor. Arquivos regulares, sem symlink, ausentes/vazios, hashes inválidos ou permissões incompatíveis causam falha. `env_file` não substitui esses arquivos nem conterá seus valores.

Preflight pertence ao entrypoint de produção local de cada serviço, não ao pytest. Roda em toda inicialização/recriação, valida parâmetros/configuração/volumes e os segredos aplicáveis antes do motor, retorna não zero e diagnóstico JSON sanitizado se falhar. Não corrige permissões nem aceita retenção inválida silenciosamente. No Windows/Desktop, comprovar ACL privada no host e permissões dos mounts pelo runtime Linux; se não verificáveis, bloquear o procedimento. Rotação de segredo exige arquivos coerentes e recriação de gateway/Alloy com nova validação.

## 2. Consulta autenticada

URL base: `http://127.0.0.1:${LOKI_PORT}`. HTTP Basic Auth é obrigatório para:

| Método | Caminho | Resultado |
|--------|---------|-----------|
| GET | `/loki/api/v1/query_range` | Envelope Loki com `status=success`, `data.resultType=streams`, streams/values; vazio válido não equivale a pipeline saudável |
| GET | `/loki/api/v1/labels` | Nomes de labels autorizados |
| GET | `/loki/api/v1/label/<name>/values` | Valores da label solicitada |
| GET | `/loki/api/v1/series` | Labels de streams no intervalo |

Para logs usar query_range com `query`, `start`, `end`, `limit`, `direction`. Cada `values` contém timestamp em string e linha; structured metadata quando disponível na resposta upstream. Consulta de referência: `{project="<projeto>",service="<servico>"} | json`. Metadados de contêiner devem permitir filtragem sem virar labels de índice; teste usa as respostas da versão fixada.

- Precedência em ambos os listeners: selecionar rota normalizada exata; rota desconhecida retorna `404` sem upstream, independentemente de método/credencial. Em rota conhecida, autenticar primeiro; sem credencial, inválida ou de outra interface retorna `401` com desafio Basic. Só depois validar método: autenticado com método não permitido recebe `405` e `Allow`. Só encaminhar após essas etapas.
- Escritor não acessa leitura; query/push/config/delete/admin não listados são negados.
- `query`, senhas e Authorization nunca aparecem no access log.
- Gateway conserva status upstream, inclusive `400`, `429`, `5xx`; não converter erro em lista vazia ou `200`.

## 3. Ingestão interna

Endpoint `http://logs-gateway:8081/loki/api/v1/push`, Basic Auth exclusivamente de escritor. Sem porta host. Apenas POST, payload/semântica upstream Loki; sucesso `204`. Leitor é negado com `401`; requisições malformadas preservam erro `4xx`.

| Rota no listener | Credencial | Método | Resposta antes do upstream |
|------------------|------------|--------|---------------------------|
| Desconhecida | Qualquer/ausente | Qualquer | 404 |
| Conhecida | Ausente/inválida/outra interface | Permitido ou proibido | 401 + desafio Basic |
| Conhecida | Válida para o listener | Proibido | 405 + Allow |
| Conhecida | Válida para o listener | Permitido | Encaminhar; conservar status upstream |

Push no listener de leitura e query no de escrita são rotas desconhecidas. Testar também caminhos codificados, barras extras e normalização; nenhuma variante pode ampliar a allowlist. Implementação NGINX deve respeitar a ordem das fases: um `return 405` na fase rewrite anterior ao auth não satisfaz o contrato. Verificar a matriz com servidor real, não só análise textual da configuração. Readiness administrativo é exceção apenas no loopback interno não publicado.

Loki nativo (`loki:3100`) fica apenas em obs-storage. Nem origens nem Alloy recebem acesso direto a essa rede. `auth_enabled: false` não é exposto ao host.

O gateway participa também de obs-edge, rede não interna exclusiva necessária à publicação no host. obs-docker, obs-ingest e obs-storage continuam internas. Nenhum outro serviço participa de obs-edge; não anexar rede default/core. Somente 8080 é publicada em loopback, nunca 8081/8082. Validar HTTP real pelo host, não apenas a declaração ports ou estado healthy.

## 4. Acesso Docker

`docker-log-proxy:2375`, somente rede obs-docker, sem porta host. Permitir GET/HEAD de ping/version/list/inspect/logs e listagem exata `/networks`, com prefixo de versão opcional e IDs hexadecimais. Negar todos os demais métodos/caminhos. Healthcheck testa conectividade real com o daemon por ping; arquivo de socket `:ro` não garante API somente leitura.

Testes negativos: POST create/start/stop/exec, GET archive/images/secrets, caminho codificado/bypass. Não executar ações destrutivas de verdade: comprovar recusa pelo proxy antes de chegar ao daemon. Logs de teste não revelam inspect nem env de outros contêineres.

## 5. Saída do pipeline

Labels indexadas exatas: `project`, `service`, `stream`, `parse_status`. `container_id` e `container_name` em structured metadata. Não indexar texto livre ou `trace_id`/`span_id`. Preservar linhas JSON e inválidas byte a byte, exceto delimitador de nova linha retirado pelo transporte Docker. Sem `stage.output`, `stage.docker` ou reescrita de IDs.

Os próprios componentes entregues devem emitir JSON, inclusive diagnósticos de inicialização. Launcher Go dos proxies captura pipes e converte diagnósticos NGINX em eventos JSON sanitizados antes da emissão do contêiner; nenhum log intermediário em arquivo. Não repassar request, upstream, referrer, Authorization ou senhas em texto livre. Diagnóstico desconhecido produz evento explícito sem payload sensível, não descarte. Testar sinais, drenagem, saída não zero, linhas longas e segredos sentinela. Essa regra de emissão não autoriza reescrever mensagens das origens coletadas.

### Evidência incremental da US2

O teste `test_parsing_preserves_lines_context_and_instance` passou na versão fixada: quatro JSON com tracing, quatro textos, quatro JSON inválidos, JSON sem message, arrays/primitivos/null, espaços e UTF-8 preservados; mensagens iguais emitidas legitimamente duas vezes não foram descartadas. Timestamp permaneceu o do Docker apesar de campo de aplicação em 2001.

Consulta comprovada: `{project="<projeto>",service="source-a"} | container_id="<id-completo>" | container_name="<nome-sem-barra>"`. Após recriação, o filtro pelo ID antigo continuou retornando as linhas antigas, e o novo ID retornou o novo evento. Structured metadata é consultável pelo filtro de pipeline, não pelo seletor de labels de índice. `/loki/api/v1/series` comprovou exatamente project/service/stream/parse_status; `discover_service_name: []` evita a label adicional automática do Loki.

Em Alloy v1.21.2, structured_metadata pode consumir e remover labels de entrada diretamente. A classificação usa templates sem alterar Entry; validação JSON por mustFromJson reconhece também arrays/primitivos/null, ao contrário de presumir que stage.json classifica todos os tipos. Nenhum stage.output, troca de timestamp ou reconstrução da linha é empregado. Linha vazia e acima de 64KiB continuam fora da amostra suportada; não foram certificadas por estes testes.

## 6. Disponibilidade, recuperação e retenção

Restart Loki/Alloy e recuperação de 20 eventos durante a interrupção de 30s mais um posterior passaram na regressão. O diagnóstico da falha é o access log JSON do gateway com método POST e status 502; Alloy mantém logging info, pois a release registra cada retentativa em debug. Retenção contínua passou localmente em 1227,19s, com remoção física máxima observada 509,66s após expiração individual e controles válidos preservados. O desenho autorizado reserva amplitude 4m, flush 2m, publicação TSDB 17m, compactação/retenção conjuntas 2m, delete delay 3m, sweeper 1m30s e reserva 30s, mantendo 30m totais (a CI mediu o sweeper em 60,0256s após o delay, acima do teto antigo de 60s). max_chunk_age=3m reduz a janela de escrita fora de ordem para aproximadamente 90s; o teste atrasado em 60s passou. Ressync de índices=30s e query_timeout=1m preservam margem antes da deleção física de 3m. Efeitos de I/O e janela foram autorizados pelo operador. Isso não substitui evidência de CI Linux ou ACL do bind real do operador, ainda pendentes.

- Docker proxy ping, Loki `/ready`, gateway `127.0.0.1:8082/ready` dentro do contêiner e Alloy `/-/ready`: healthchecks reais, sem portas administrativas publicadas. Gateway ready depende de Loki; Alloy ready sozinho não comprova entrega.
- HTTP probe: status 200, timeout 2s, saída não zero se falhar. Erros JSON sem credenciais.
- 20 eventos <=1KiB durante interrupção de Loki por 30s, mantidos Alloy/origens ativos, devem ser encontrados até 60s após Loki voltar saudável. Duplicatas toleradas; IDs de teste únicos.
- 20 eventos confirmados antes de restart Loki permanecem consultáveis depois. Restart Alloy deve retomar coleta de eventos novos.
- Retenção padrão 14 dias e limpeza automática até 30m após timestamp do evento + política em ambiente saudável e escala declarada. Orçamento e parâmetros estão no [plano](../plan.md). Teste principal usa volume novo, política 24h anterior à ingestão e eventos próximos de expirar, confirmados antes do limite. Loki continua ativo sem restart/flush forçado. Cobrir streams separados e chunks de idade mista com amplitude medida até 4m na carga declarada, inclusive escrita atrasada/fora de ordem aceita. Medir etapas e remover fisicamente os chunks dentro dos deadlines individuais, preservando eventos válidos; ausência em consulta ou filtro de lookback não prova deleção. Teste com flush/restart é somente complementar. Job até 50m não amplia os 30m de limpeza.
- Falta de disco, origem ilegível, permissão negada, config inválida e autenticação recusada devem gerar diagnóstico e falha verificáveis. Não declarar sucesso por mero contêiner em execução.

## 7. Matriz de rastreabilidade

| Requisitos / critérios | Evidência local / lacuna de entrega |
|-----------------------|---------------------|
| FR-001, FR-014; SC-007 | [Compose](../../../infra/compose.obs.yaml) independente exercitado sem apps; [roteiro](../quickstart.md) atualizado. ACL do operador continua bloqueante |
| FR-002 a FR-005; SC-001 a SC-003 | [Ingestão](../../../infra/tests/test_obs_ingestion.py): 200 IDs, descoberta posterior, exclusão de 20 IDs estrangeiros e filtros por serviço/instância passaram |
| FR-006 a FR-008; SC-004 | Mesmo teste: linhas/contexto/timestamp/duplicatas exatos e índice de quatro labels passaram |
| FR-009; SC-005/SC-009 | [Restart](../../../infra/tests/test_obs_recovery.py) e [retenção física contínua](../../../infra/tests/test_obs_retention.py) passaram; medições no quickstart |
| FR-010/FR-011; SC-006 | Falha 30s e recuperação de 20 IDs mais novo <=60s passaram; startup/config/socket/permissões inválidos diagnosticados |
| FR-012 | [Config/runtime](../../../infra/tests/test_obs_config.py): JSON em ambos os fluxos e ausência de logs locais passaram; volumes técnicos fora do código |
| FR-013; SC-008 | [Matriz HTTP](../../../infra/tests/test_obs_access.py), loopback e proxy fake passaram; nenhuma mutação executada no daemon real |
| FR-015 | 29 testes de regressão + 1 retenção, mypy strict/Ruff/Black e Go race/vet passaram. [CI](../../../.github/workflows/validate-issue-103.yml) criada e lintada, ainda sem execução remota |

| Achado do planejamento | Evidência de tratamento |
|-----------------------|-------------------------|
| C1 — stderr textual NGINX | Launcher converte ambos os pipes antes da emissão; Go lifecycle/sinais/pipes e startup JSON reais passaram |
| C2 — tipagem ausente | mypy strict em todos os seis arquivos, sem exclusão global; extra dev e lock em infra |
| U1 — preflight apenas no teste | Entrypoints aplicam preflight em toda inicialização/rotação; falhas reais de materiais, socket e volume read-only passaram |
| U2 — retenção sem prova contínua | Cenário principal com quatro timestamps, dois chunks e dois marcadores removidos, sem restart/flush; etapas e limites medidos |
| A1 — precedência HTTP | 404 desconhecido; 401 antes de método; 405/Allow após autenticação; status upstream preservados, em ambos os listeners |

Cleanup das execuções concluídas removeu somente projetos/volumes/IDs próprios. Não restaram contêineres/volumes com label `obs.test` na verificação final. Checklists do revisor não foram alterados. A rastreabilidade local não fecha T045/T046 enquanto faltarem execução remota e permissões do operador.
