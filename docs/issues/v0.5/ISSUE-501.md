# 📌 Issue #501: Configuração do Open WebUI para o Agent Orchestrator

* **Milestone:** `v0.5 - Interfaces & Clients`
* **Tipo:** UI / Integração
* **ADRs Vinculadas:** N/A

## 🎯 Descrição
Adicionar e configurar a interface do Open WebUI no `infra/compose.interfaces.yaml`, conectando-a ao endpoint `/v1` do `agent-orchestrator`.

## 📥 Tarefas
- [ ] Adicionar serviço `open-webui` no Compose.
- [ ] Apontar URL da API para `http://agent-orchestrator:8000/v1`.
- [ ] Configurar persistência dos dados de usuário do Open WebUI em volume.

## ✅ Critérios de Aceite
- Interface web acessível via navegador, capaz de iniciar e manter conversas interagindo com o agente.
