# 📌 Issue #108: Exporters de Contêineres, Host e Aceleradores de Hardware

* **Milestone:** `v0.1 - Infra Core & Observabilidade`
* **Tipo:** Observabilidade / Infraestrutura
* **ADRs Vinculadas:** N/A
* **Dependência:** [`Issue #104`](./ISSUE-104.md)

## 🎯 Descrição
Implementar a coleta opcional de métricas de contêineres, sistema operacional e aceleradores de hardware. Os coletores são ativados por profiles derivados de `full`, evitando iniciar exporters incompatíveis com o ambiente ou com o hardware disponível. O dashboard global adapta os painéis às séries disponíveis em cada plataforma.

## 🌐 Ambientes e Profiles

| Escopo | Profile | Coletor | Ambiente suportado |
| :--- | :--- | :--- | :--- |
| Validação da issue | `issue-108` | Prometheus, Grafana, Docker exporter e node-exporter | CI Linux e desenvolvimento local |
| Contêineres | `metrics-containers` | cAdvisor | Docker Engine em Linux ou runtime compatível |
| Docker Engine | `metrics-docker` | Jhonny Docker Exporter via socket read-only | Docker Engine e Docker Desktop |
| Host Linux | `metrics-host-linux` | node-exporter sobre `/proc` e `/sys` | Linux |
| Host Windows | `full-windows` | windows_exporter nativo em `host.docker.internal:9182` | Windows residencial com Docker Desktop |
| Host macOS | `full-macos-m4` | Jhonny Host Exporter nativo em `host.docker.internal:9100` | macOS Apple Silicon |
| GPU NVIDIA | `metrics-gpu-nvidia` | NVIDIA DCGM Exporter | Host com driver NVIDIA e acesso à GPU |
| GPU AMD | `metrics-gpu-amd` | AMD ROCm Exporter | Linux com ROCm e GPU AMD suportada |
| GPU Intel | `metrics-gpu-intel` | Intel GPU Exporter | Host com GPU Intel e interfaces DRM/Level Zero suportadas |

### Profiles derivados de `full`

| Profile | Exporters adicionais |
| :--- | :--- |
| `full-cloud-linux` | Docker exporter, node-exporter e cAdvisor |
| `full-cloud-linux-nvidia` | Linux base + NVIDIA DCGM Exporter |
| `full-cloud-linux-amd` | Linux base + AMD Device Metrics Exporter |
| `full-cloud-linux-intel` | Linux base + Intel GPU Exporter |
| `full-windows` | Docker exporter + windows_exporter nativo via file discovery |
| `full-macos-m4` | Docker exporter + Jhonny Host Exporter nativo via file discovery |

O profile `full` original permanece sem exporters opcionais. Assim, nenhum driver ou dispositivo incompatível é solicitado implicitamente.

## 📥 Tarefas
- [ ] Definir Compose específico para métricas de contêineres, host e GPU, sem acoplar dispositivos opcionais à stack base.
- [ ] Configurar cAdvisor no profile `metrics-containers`, incluindo mounts, privilégios e interfaces de cgroup.
- [ ] Implementar o Jhonny Docker Exporter com métricas reais de contêineres, imagens, volumes, redes e daemon.
- [ ] Configurar node-exporter para Linux e discovery de exporters nativos para Windows e macOS.
- [ ] Implementar Jhonny Host Exporter para CPU, memória, disco, rede e processos via APIs nativas do macOS.
- [ ] Configurar NVIDIA DCGM Exporter no profile `metrics-gpu-nvidia`, com runtime NVIDIA explícito.
- [ ] Configurar AMD ROCm Exporter no profile `metrics-gpu-amd`, com acesso a `/dev/kfd` e `/dev/dri`.
- [ ] Configurar Intel GPU Exporter no profile `metrics-gpu-intel`, com acesso somente leitura a DRM.
- [ ] Separar scrape targets por descoberta DNS e file discovery de host.
- [ ] Ampliar `jhonny-v-global` para Docker, host, contêineres e GPUs usando o datasource UID `prometheus`.
- [ ] Documentar combinações suportadas de sistema operacional, runtime, driver, exporter e profile.
- [ ] Criar validação runtime sem GPU e auditoria estática dos profiles de hardware.
- [ ] Coletar logs, targets Prometheus e informações do runtime em falhas do job.

## 🚀 Execução por ambiente

Todos os comandos combinam os fragments base, core, LLM, observabilidade, interfaces e métricas. Use as credenciais definidas no `.env`.

### Docker em Linux na nuvem

```bash
docker compose --env-file .env \
	-f infra/compose.yml \
	-f infra/compose.core.yml \
	-f infra/compose.llm.yml \
	-f infra/compose.obs.yml \
	-f infra/compose.interfaces.yml \
	-f infra/compose.metrics.yml \
	--profile full-cloud-linux up -d
```

Troque o profile por `full-cloud-linux-nvidia`, `full-cloud-linux-amd` ou `full-cloud-linux-intel` somente depois de instalar o driver/runtime correspondente.

### Windows residencial

Instale `windows_exporter`, habilite os collectors `cpu`, `cs`, `logical_disk`, `memory`, `net`, `os`, `process` e exponha a porta `9182` para a rede privada do Docker Desktop.

```powershell
docker compose --env-file .env `
	-f infra/compose.yml `
	-f infra/compose.core.yml `
	-f infra/compose.llm.yml `
	-f infra/compose.obs.yml `
	-f infra/compose.interfaces.yml `
	-f infra/compose.metrics.yml `
	-f infra/compose.metrics.windows.yml `
	--profile full-windows up -d
```

### Mac Mini M4

O Docker Desktop executa contêineres em uma VM Linux e não expõe Mach/IOKit diretamente. Execute o exporter no host antes da stack usando o ambiente isolado do projeto:

```bash
uv venv .venv-host-exporter
source .venv-host-exporter/bin/activate
uv pip install -e infra/exporters/host-native
python infra/exporters/host-native/exporter.py
```

Se o exporter estiver configurado como um pacote Python com `pyproject.toml`, a instalação pode ser feita diretamente no ambiente virtual. Em outro terminal:

```bash
docker compose --env-file .env \
	-f infra/compose.yml \
	-f infra/compose.core.yml \
	-f infra/compose.llm.yml \
	-f infra/compose.obs.yml \
	-f infra/compose.interfaces.yml \
	-f infra/compose.metrics.yml \
	-f infra/compose.metrics.macos.yml \
	--profile full-macos-m4 up -d
```

## ✅ Critérios de Aceite
- Cada profile inicia somente os exporters compatíveis com o ambiente e hardware selecionados.
- Prometheus exibe como `UP` todos os targets solicitados pelos profiles ativos, sem exigir targets de profiles inativos.
- cAdvisor e o coletor do Docker Engine expõem métricas reais de contêineres e daemon, não apenas métricas do próprio exporter.
- Os coletores de host exibem CPU, memória, disco, rede e processos pelas APIs nativas do sistema operacional correspondente.
- NVIDIA DCGM, AMD ROCm e Intel GPU Exporter exibem utilização, memória, temperatura, energia e erros quando essas métricas forem suportadas pelo hardware.
- Grafana provisiona dashboards separados por domínio, sem seleção manual do datasource Prometheus.
- A ausência de driver, dispositivo ou permissão produz diagnóstico acionável e não impede a execução de profiles não relacionados.
- Job `validate-issue-108` executável localmente com `act pull_request -j validate-issue-108`.
