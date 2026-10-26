# 📌 Issue #501: Configuração do Open WebUI para o OpenJarvis

* **Milestone:** `v0.5 - Interfaces & Clients`
* **Tipo:** UI / Integração
* **ADRs Vinculadas:** [ADR-0006: OpenJarvis via Compose](../../adr/0006-openjarvis-compose.md)

## 🎯 Descrição
Adicionar e configurar a interface do Open WebUI no `infra/compose.interfaces.yaml`, conectando-a à API do OpenJarvis operado por `infra/compose.core.yaml`. A integração depende da homologação do contrato `/v1` na [issue #305](../v0.3/ISSUE-305.md).

## 📥 Tarefas
- [ ] Adicionar serviço `open-webui` no Compose.
- [ ] Configurar a URL base com o hostname de serviço `openjarvis` e a porta interna homologada na issue #305, sem presumir `8000` ou copiar a URL do antigo serviço.
- [ ] Fornecer autenticação via `.env` ou secret manager e validar a composição com os overlays core, LLM e interfaces.
- [ ] Configurar persistência dos dados de usuário do Open WebUI em volume.

## ✅ Critérios de Aceite
- Interface web acessível via navegador, capaz de iniciar e manter conversas interagindo com o agente.
