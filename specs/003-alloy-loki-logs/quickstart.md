# Quickstart de validação — issue #103

> Validação local aprovada: 29 testes de regressão e um cenário contínuo de retenção, em projetos e volumes Linux exclusivos no Docker Desktop. Ruff/Black, mypy strict e Go race/vet também passaram. CI Linux remoto e ACL de bind Windows do operador ainda não foram comprovados e bloqueiam o aceite completo da entrega. Não usar as credenciais efêmeras dos testes como provisionamento do operador.

O desenho autorizado usa max_chunk_age=3m (janela fora de ordem aproximada 90s, antes 150s), compactação 30s, aplicação de retenção 1m, delete delay 3m e ressync de índice 30s. Mais operações de disco são esperadas. query_timeout=1m é explícito; o cache de listagem de 1m mais ressync e consulta em andamento cabem no delay de 3m. CacheTTL de arquivos não é frequência de atualização. O cenário abaixo comprovou o prazo na carga declarada, não sob sobrecarga ou saltos arbitrários de timestamp.

## Evidência local executada — 2026-10-26

Windows, Docker Desktop com Engine Linux 29.6.1/amd64, Compose 5.1.4, Python 3.14.3 e uv 0.12.1. Builds locais fixados por digest conforme [research](./research.md), Go 1.27.2 no builder Linux. As fixtures usam volumes privados no runtime Linux, não binds NTFS de segredos do operador.

| Validação | Resultado |
|-----------|-----------|
| `pytest infra/tests -m "not retention"` | 29 passaram em 881,85s |
| Cenário `test_continuous_physical_retention` | Passou em 1227,19s; quatro timestamps cobertos por dois chunks antigos observados e removidos, dois arquivos de marcadores removidos |
| Amplitude máxima dos chunks amostrados | 214,32s, limite 240s |
| Primeiro flush | 72,46s, limite 120s |
| Publicação de índice após primeiro flush | 265,16s, limite 1020s |
| Marcação após elegibilidade/índice | 23,98s, limite conjunto 120s |
| Sweeper após delay de 180s | 59,999s, limite 60s |
| Maior remoção após expiração individual | 509,66s, limite 1800s |
| Ruff / Black / mypy strict | PASS em todos os seis arquivos de testes |
| `go test -race ./...` / `go vet ./...` | PASS no builder fixado |

Loki manteve StartedAt e RestartCount durante a retenção; não houve restart, flush forçado, deleção manual ou alteração de intervalos no cenário principal. Controles válidos continuaram consultáveis e seus chunks físicos preservados. Escrita contínua a cada 30s e atraso de 60s foram exercitados. Observador sem rede e com mount somente leitura amostra remoções a cada 50ms, sem payloads; teste controlado comprovou observação em até 0,5s. Uma execução não certifica todas as fases de rotação TSDB; o orçamento de 17m para publicação e o deadline individual são revalidados pelo job obrigatório em cada CI.

Relatórios JUnit incluem contagens e tempos medidos. O [workflow](../../.github/workflows/validate-issue-103.yml) executa qualidade, integração e retenção em Docker Linux, sem skips implícitos. Ele foi criado localmente, mas ainda requer execução remota; não houve commit/push nesta implementação. A ACL Windows/WSL2 do bind real também precisa de evidência antes de certificar o procedimento do operador.

## Pré-requisitos

- Docker Engine com contêineres Linux ou Docker Desktop/WSL2, Compose v2 com `--wait`, `uv` e Python >=3.12.
- Daemon local autorizado, 2 GiB de RAM disponíveis e pelo menos 10 GiB livres para os dados de teste.
- Versões/bases do [plano](./plan.md) verificadas, incluindo digests e ferramentas de healthcheck.
- Segredos provisionados pelo operador conforme o [contrato](./contracts/logging-contract.md), sem colar senhas em comandos/histórico. Preparador de testes deve gerar credenciais efêmeras em diretório temporário privado, sem imprimir valores.
- No Windows/Desktop, validar ACL privada no host e usar mounts WSL2 com permissões Linux verificáveis. Se o runtime só fornecer modos sintetizados e não houver comprovação de acesso restrito, interromper o roteiro, sem relaxar a validação.

Execute a partir da raiz do repositório em PowerShell:

```powershell
if (-not (Test-Path -LiteralPath .env)) { Copy-Item .env.example .env }
docker version
docker compose version
uv sync --project .\infra --extra dev --locked
```

Se `.env` já existe, revise-o em vez de executar a cópia. Configure `LOKI_RETENTION_PERIOD=336h`, usuários distintos e caminho dos arquivos de segredo. Senhas ASCII aleatórias de 32 a 72 bytes, htpasswd bcrypt com uma entrada por arquivo; preservar a senha de escrita sem newline de conteúdo. Não usar credenciais padrão reutilizáveis. Nunca registrar saída bruta de arquivos de segredo.

### Provisionamento do operador

1. Em armazenamento Linux/WSL2 privado, prepare o diretório escolhido por OBS_SECRETS_DIR com modo 0700, sem symlink. O bind usa o diretório real do daemon Linux; não presumir que permissões NTFS sintetizadas provam isolamento.
2. Exporte do secret manager três arquivos: `read.htpasswd` com uma entrada bcrypt do usuário leitor, `write.htpasswd` com uma entrada bcrypt de outro usuário e `write-password` com a senha aleatória de escrita, sem newline. Gere senhas independentes. O leitor conserva sua senha no secret manager, não em outro arquivo montado. Use exportação privada sem valores em argv, env, histórico ou logs.
3. Os arquivos devem ser regulares, modo 0600, pertencentes a root ou à identidade runtime autorizada. O preflight verifica owner/modo; não aplica chmod/chown nem gera credenciais automaticamente. O processo mestre e workers NGINX executam como root para acessar socket/arquivos privados, sem privileged; não se promete execução non-root de todas as bases. Loki preserva UID 10001.
4. No Windows, valide também a ACL do diretório host pelo procedimento da organização. Um teste com volume Linux privado não certifica a ACL de um bind NTFS do operador. Sem ambas as evidências, interrompa o provisionamento.
5. Execute preflight e startup abaixo. Rotação exporta um conjunto coerente novo e recria gateway/Alloy; não editar arquivos parcialmente enquanto a stack usa o conjunto.

## Validar e iniciar somente a camada de logs

```powershell
docker compose --env-file .\.env -f .\infra\compose.yaml -f .\infra\compose.obs.yaml config --quiet
if ($LASTEXITCODE -ne 0) { throw 'Composição inválida' }
docker compose --env-file .\.env -f .\infra\compose.yaml -f .\infra\compose.obs.yaml build loki alloy docker-log-proxy logs-gateway
if ($LASTEXITCODE -ne 0) { throw 'Build recusado' }
docker compose --env-file .\.env -f .\infra\compose.yaml -f .\infra\compose.obs.yaml run --rm --no-deps --entrypoint /usr/local/bin/obs-tools loki preflight --service loki
if ($LASTEXITCODE -ne 0) { throw 'Preflight Loki recusado' }
docker compose --env-file .\.env -f .\infra\compose.yaml -f .\infra\compose.obs.yaml run --rm --no-deps --entrypoint /usr/local/bin/obs-tools logs-gateway preflight --service logs-gateway
if ($LASTEXITCODE -ne 0) { throw 'Preflight gateway recusado' }
docker compose --env-file .\.env -f .\infra\compose.yaml -f .\infra\compose.obs.yaml up -d --wait --wait-timeout 120
if ($LASTEXITCODE -ne 0) { throw 'Stack não saudável; consultar diagnósticos sanitizados' }
docker compose --env-file .\.env -f .\infra\compose.yaml -f .\infra\compose.obs.yaml ps
```

Esperado: quatro serviços saudáveis; apenas gateway publica `127.0.0.1:<LOKI_PORT>`. Não inicia PostgreSQL, Ollama, LiteLLM, MCP, Worker ou OpenJarvis. Erros de configuração/segredo/socket devem interromper o procedimento, nunca ignorados.

Revisão aprovada durante implementação: o gateway deve participar de obs-edge não interna, exclusivamente dele, além das redes internas de ingestão/storage. As três redes internas permanecem isoladas. Confirmar acesso HTTP real pelo host: no Engine validado, um gateway ligado somente a redes internas atingiu healthy sem publicar a porta solicitada. `invalid IP:0` em `compose port` não é sucesso nem motivo para expor backend ou usar host networking.

O preflight do Alloy consulta somente o inventário do projeto pelo proxy e recusa uma origem ativa sem serviço Compose com `source_missing_compose_service`; não imprime inspect/env. Alvos sem serviço também são excluídos pelo relabel. Se surgirem depois da inicialização, rode novamente o preflight do Alloy para diagnosticar antes de recriá-lo. Drivers que negam leitura dos logs são diagnosticados pelo source e não são anunciados como suportados.

Os entrypoints repetem automaticamente as validações aplicáveis a cada serviço em `up`, restart ou recriação; comandos de preflight separados são diagnóstico antecipado, não o único controle. Testar `up` direto com retenção inválida, segredo ausente/vazio/inconsistente e permissões negadas: saída JSON, processo recusado e stack não saudável, sem pytest. Não imprimir senhas para diagnosticar. Para rotacionar credenciais, substituir o conjunto coerente de arquivos e recriar gateway/Alloy; não presumir reload automático.

## Consultar sem expor senha

```powershell
$credential = Get-Credential -Message 'Credencial de leitura dos logs locais'
$query = [uri]::EscapeDataString('{project="jhonny_v"}')
$port = 3100
Invoke-RestMethod -Uri "http://127.0.0.1:$port/loki/api/v1/query_range?query=$query" -Credential $credential
```

Usar projeto/porta efetivamente configurados. Algumas versões do PowerShell exigem opção explícita para Basic Auth em HTTP local; nesse caso usar `curl.exe --user <usuario> --get --data-urlencode 'query={project="jhonny_v"}' http://127.0.0.1:3100/loki/api/v1/query_range` e digitar senha no prompt, nunca no argumento. Ausência/credencial incorreta deve resultar em `401`. Resposta vazia não prova ingestão; as fixtures emitem IDs únicos para confirmar.

## Reexecutar a suíte automatizada

```powershell
uv run --project .\infra ruff check .\infra\tests
uv run --project .\infra black --check .\infra\tests
uv run --project .\infra mypy --strict .\infra\tests
uv run --project .\infra pytest .\infra\tests -m "not retention" -o junit_family=xunit1
uv run --project .\infra pytest .\infra\tests -m retention -o junit_family=xunit1
```

Fixtures geram projeto único `jhonny-v-obs-test-<id>` e arquivos temporários restritos. Nenhum teste pode parar o Loki do projeto do operador, alterar contêiner alheio ou usar comandos globais de cleanup. A fixture da origem estrangeira também é criada pelo próprio teste em outro projeto único e removida pelo seu ID.

| Cenário | Ação / resultado obrigatório |
|---------|-----------------------------|
| SC-001 | 2 origens, 50 eventos por fluxo por origem, 200 IDs consultáveis <=60s |
| SC-002 | Iniciar origem após Alloy; primeiro evento <=60s, sem editar alvos |
| SC-003 | Origem de outro projeto emite 20 IDs; nenhum ingerido |
| SC-004 | 4 JSON com tracing, 4 texto, 4 JSON inválido; linhas/origens preservadas; IDs não indexados |
| SC-005 | Confirmar 20 eventos; reiniciar Loki preservando volume; todos permanecem |
| SC-006 | Parar somente Loki de teste por 30s, emitir 20 IDs <=1KiB, manter Alloy/origens; após voltar saudável, achar todos e novo evento <=60s; checar diagnóstico explícito |
| SC-007 | Operador ativa, consulta e diagnostica sem código de app |
| SC-008 | Read/write distintos, credencial ausente/inválida negada, backend não publicado, proxy Docker nega operações fora da allowlist |
| SC-009 | Volume novo, retenção 24h anterior à ingestão; confirmar eventos próximos de expirar; sem restart/flush forçado, provar remoção física <=30m desde expiração individual e preservar não expirados; cobrir chunks de idade mista e medir orçamento do plano |

O proxy permite a listagem exata `/networks` para a descoberta do Alloy, sem permitir inspeção individual ou mutações de redes. Falha `error while computing network labels` indica descoberta interrompida, mesmo com Alloy healthy; não aceitar consulta vazia como êxito.

Também validar reinício de Alloy, config inválida, socket inacessível, JSON válido sem message, instâncias recriadas e falha de instrumentação em fixtures próprias sem tracing exigido. Integração tem deadlines explícitos e relata IDs faltantes, nunca senhas. Para autenticação/caminhos usar resultados do contrato; não transformar falha em skip ou resposta vazia.

Antes da integração, executar `go test ./...` no módulo `infra/obs-tools` usando o builder fixado no [plano](./plan.md); não pressupor Go instalado no host. Incluir testes do preflight, comparação bcrypt e launcher (sinais, exit status, pipes e JSON). Na integração, provocar falhas reais NGINX antes de readiness e verificar JSON em ambos os fluxos, ausência de segredos sentinela e de arquivos de log. Executar a matriz de precedência do [contrato](./contracts/logging-contract.md), inclusive método proibido sem credencial.

## Diagnóstico e limpeza

```powershell
docker compose --env-file .\.env -f .\infra\compose.yaml -f .\infra\compose.obs.yaml logs --tail 100 loki alloy logs-gateway docker-log-proxy
docker compose --env-file .\.env -f .\infra\compose.yaml -f .\infra\compose.obs.yaml down
```

Não usar `down -v` na stack do operador. Cleanup automático remove apenas recursos e arquivos temporários criados e identificados pela fixture. Volume persistente do operador continua disponível após `down`.

CI deve executar Ruff, Black, mypy strict, testes Go e os mesmos testes em Docker Linux, armazenando resultados sanitizados. Job de retenção tem timeout 50m para preparação/expiração/observação; o deadline de cada evento continua em 30m após expirar. O smoke test Windows/Desktop é evidência separada; ausência de execução não autoriza declarar a plataforma validada.
