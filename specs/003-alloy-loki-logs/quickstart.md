# Quickstart de validação — issue #103

> Roteiro para executar **depois da implementação**. Os arquivos operacionais, segredos e testes abaixo ainda não foram criados pelo gate plan. Não interpretar estes comandos como evidência de execução atual.

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
uv sync --project .\infra --extra dev
```

Se `.env` já existe, revise-o em vez de executar a cópia. Configure `LOKI_RETENTION_PERIOD=336h`, usuários distintos e caminho dos arquivos de segredo. Senhas ASCII aleatórias de 32 a 72 bytes, htpasswd bcrypt com uma entrada por arquivo; preservar a senha de escrita sem newline de conteúdo. Não usar credenciais padrão reutilizáveis. Nunca registrar saída bruta de arquivos de segredo.

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

Os entrypoints repetem automaticamente as validações aplicáveis a cada serviço em `up`, restart ou recriação; comandos de preflight separados são diagnóstico antecipado, não o único controle. Testar `up` direto com retenção inválida, segredo ausente/vazio/inconsistente e permissões negadas: saída JSON, processo recusado e stack não saudável, sem pytest. Não imprimir senhas para diagnosticar. Para rotacionar credenciais, substituir o conjunto coerente de arquivos e recriar gateway/Alloy; não presumir reload automático.

## Consultar sem expor senha

```powershell
$credential = Get-Credential -Message 'Credencial de leitura dos logs locais'
$query = [uri]::EscapeDataString('{project="jhonny_v"}')
$port = 3100
Invoke-RestMethod -Uri "http://127.0.0.1:$port/loki/api/v1/query_range?query=$query" -Credential $credential
```

Usar projeto/porta efetivamente configurados. Algumas versões do PowerShell exigem opção explícita para Basic Auth em HTTP local; nesse caso usar `curl.exe --user <usuario> --get --data-urlencode 'query={project="jhonny_v"}' http://127.0.0.1:3100/loki/api/v1/query_range` e digitar senha no prompt, nunca no argumento. Ausência/credencial incorreta deve resultar em `401`. Resposta vazia não prova ingestão; as fixtures emitem IDs únicos para confirmar.

## Suíte automatizada prevista

```powershell
uv run --project .\infra ruff check .\infra\tests
uv run --project .\infra black --check .\infra\tests
uv run --project .\infra mypy --strict .\infra\tests
uv run --project .\infra pytest .\infra\tests\test_obs_config.py .\infra\tests\test_obs_access.py .\infra\tests\test_obs_ingestion.py .\infra\tests\test_obs_recovery.py
uv run --project .\infra pytest .\infra\tests\test_obs_retention.py
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

Também validar reinício de Alloy, config inválida, socket inacessível, JSON válido sem message, instâncias recriadas e falha de instrumentação em fixtures próprias sem tracing exigido. Integração tem deadlines explícitos e relata IDs faltantes, nunca senhas. Para autenticação/caminhos usar resultados do contrato; não transformar falha em skip ou resposta vazia.

Antes da integração, executar `go test ./...` no módulo `infra/obs-tools` usando o builder fixado no [plano](./plan.md); não pressupor Go instalado no host. Incluir testes do preflight, comparação bcrypt e launcher (sinais, exit status, pipes e JSON). Na integração, provocar falhas reais NGINX antes de readiness e verificar JSON em ambos os fluxos, ausência de segredos sentinela e de arquivos de log. Executar a matriz de precedência do [contrato](./contracts/logging-contract.md), inclusive método proibido sem credencial.

## Diagnóstico e limpeza

```powershell
docker compose --env-file .\.env -f .\infra\compose.yaml -f .\infra\compose.obs.yaml logs --tail 100 loki alloy logs-gateway docker-log-proxy
docker compose --env-file .\.env -f .\infra\compose.yaml -f .\infra\compose.obs.yaml down
```

Não usar `down -v` na stack do operador. Cleanup automático remove apenas recursos e arquivos temporários criados e identificados pela fixture. Volume persistente do operador continua disponível após `down`.

CI deve executar Ruff, Black, mypy strict, testes Go e os mesmos testes em Docker Linux, armazenando resultados sanitizados. Job de retenção tem timeout 50m para preparação/expiração/observação; o deadline de cada evento continua em 30m após expirar. O smoke test Windows/Desktop é evidência separada; ausência de execução não autoriza declarar a plataforma validada.
