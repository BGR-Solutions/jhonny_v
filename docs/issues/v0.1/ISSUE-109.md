# 📌 Issue #109: Compatibilização dos Dashboards Específicos do Grafana

* **Milestone:** `v0.1 - Infra Core & Observabilidade`
* **Tipo:** Observabilidade / Dashboards
* **ADRs Vinculadas:** N/A
* **Dependências:** [`Issue #104`](./ISSUE-104.md) e [`Issue #108`](./ISSUE-108.md)

## 🎯 Descrição
Diagnosticar e corrigir os dashboards importados que são provisionados pelo Grafana, mas não exibem dados por dependerem de métricas, labels, exporters, versões de schema ou variáveis incompatíveis com a stack atual.

O dashboard `Jhonny V - Visão Global`, entregue na `Issue #104`, permanece como referência mínima funcional baseada nas métricas nativas do Prometheus.

## 📥 Tarefas
- [ ] Inventariar cada dashboard provisionado, sua origem, revisão, datasource, queries, variáveis e dependências externas.
- [ ] Classificar dashboards por domínio: LiteLLM, Docker, Loki, Tempo, FastAPI, Ollama e GPU.
- [ ] Mapear cada expressão PromQL e LogQL para as métricas e labels realmente expostos pela stack.
- [ ] Remover ou substituir placeholders de importação e UIDs de datasources incompatíveis com o provisionamento por arquivo.
- [ ] Corrigir variáveis de `job`, `instance`, `service`, `container`, `model` e hardware conforme os targets ativos.
- [ ] Vincular dashboards de hardware apenas aos exporters e profiles implementados na `Issue #108`.
- [ ] Remover do provisionamento padrão dashboards cujas dependências ainda não estejam disponíveis.
- [ ] Fixar versões ou adaptar painéis incompatíveis com o Grafana utilizado pelo projeto.
- [ ] Criar probes PromQL/LogQL para comprovar que cada painel possui ao menos uma série ou stream compatível.
- [ ] Adicionar validação automatizada dos dashboards habilitados por profile.
- [ ] Documentar pré-requisitos e estados esperados sem dados para cada dashboard.

## 📊 Inventário e Compatibilidade

O inventário executável está em `infra/grafana/validation/dashboard-inventory.json`. Ele relaciona cada target pelo par `panel.id`/`refId`, datasource, domínio, profile obrigatório e probe compatível. O validador rejeita dashboards ou queries não inventariados, placeholders `${DS_*}`, UIDs desconhecidos e schemas posteriores ao Grafana `10.2.2`.

| Domínio | Estado no v0.1 | Dependência / decisão |
| :--- | :--- | :--- |
| Prometheus | Provisionado no dashboard global | Métricas nativas disponíveis em todos os profiles de observabilidade |
| Docker e host | Painéis no dashboard global | `metrics-docker`, `metrics-host-linux`, `issue-108`, `issue-109` ou profile derivado compatível |
| Tempo | Painel no dashboard global | `issue-105`, `issue-109`, `v0.1` ou `full`; requer uma aplicação emitindo spans OTLP para exibir traces |
| GPU | Painéis no dashboard global | Um dos profiles `metrics-gpu-nvidia`, `metrics-gpu-amd` ou `metrics-gpu-intel`, com hardware e driver compatíveis |
| Loki | Grafana Explore | Não há dashboard específico estável; as consultas LogQL permanecem disponíveis no Explore |
| LiteLLM | Não provisionado | O schema de métricas varia com a versão e o serviço é opcional |
| FastAPI | Não provisionado | Os serviços ainda não publicam um contrato estável de métricas no v0.1 |
| Ollama | Não provisionado | O serviço atual não expõe métricas Prometheus |

Nenhum dashboard externo/importado permanece no provisionamento padrão. Assim, não existem IDs de revisão remota, placeholders de importação ou plugins externos implícitos. O dashboard `jhonny-v-global`, de origem interna e revisão `4`, usa somente os UIDs fixos `prometheus` e `tempo`. As variáveis `job` e `instance` são preenchidas pelos labels de `up` e a segunda é filtrada pela primeira.

### Estados esperados sem dados

| Painéis | Estado vazio esperado | Como habilitar dados |
| :--- | :--- | :--- |
| Traces recentes | Nenhum span recebido | Iniciar um profile com Tempo e enviar spans para OTLP `4317` ou `4318` |
| Targets, Docker e host | Exporter correspondente ausente | Ativar um profile de Docker/host da Issue 108 |
| CPU por contêiner | cAdvisor ausente | Ativar `metrics-containers` ou um profile `full-cloud-linux*` |
| Utilização e temperatura da GPU | Exporter ou hardware ausente | Ativar exatamente um profile `metrics-gpu-*` compatível |

O profile `issue-109` é neutro quanto a GPU e inicia Prometheus, Grafana, Loki, Promtail, Tempo, Docker exporter e node-exporter. Após dois ciclos de coleta (cerca de 30 segundos), todos os probes marcados como obrigatórios para esse profile devem retornar séries. Os painéis opcionais acima permanecem com estado vazio, sem causar falha.

## 🧪 Validação

Validação estática, sem iniciar contêineres:

```bash
python infra/grafana/validation/validate_dashboards.py
```

Validação runtime após iniciar o profile:

```bash
docker compose \
	-f infra/compose.yaml \
	-f infra/compose.obs.yaml \
	-f infra/compose.metrics.yaml \
	--profile issue-109 up -d --build --wait

python infra/grafana/validation/validate_dashboards.py --runtime-profile issue-109
```

O job `validate-issue-109` executa as duas validações, confirma o provisionamento e os valores das variáveis pela API, e informa `dashboard`, `panel`, `query` e expressão para qualquer probe sem dados. Execução local com GitHub Actions:

```bash
act pull_request -j validate-issue-109
```

## ✅ Critérios de Aceite
- Todo dashboard provisionado por padrão possui datasource resolvido e dependências disponíveis na stack correspondente.
- Variáveis de dashboard carregam opções válidas sem configuração manual.
- Painéis habilitados retornam dados após o período mínimo de coleta documentado.
- Dashboards dependentes de serviços ou hardware opcionais são provisionados somente com seus profiles.
- O job de validação informa o dashboard, painel e query responsáveis quando não houver dados esperados.
- O dashboard global da `Issue #104` continua funcional durante a evolução dos dashboards específicos.
