# 📌 Issue #305: Homologação da API OpenAI-Compatible e SSE do OpenJarvis

* **Milestone:** `v0.3 - OpenJarvis`
* **Tipo:** API / Client Layer
* **ADRs Vinculadas:** [ADR-0006: OpenJarvis via Compose](../../adr/0006-openjarvis-compose.md)

## 🎯 Descrição
Homologar a interface HTTP do OpenJarvis para preservar o contrato `/v1/chat/completions` compatível com OpenAI e respostas em streaming SSE. Os endpoints e recursos da imagem precisam ser verificados antes de configurar os clientes.

## 📥 Tarefas
- [ ] Verificar e configurar os contratos de requisição, resposta, autenticação e erros suportados pela imagem.
- [ ] Validar streaming SSE, encerramento do fluxo e eventos de ferramentas/aprovação necessários às interfaces, sem depender de eventos internos do LangGraph.
- [ ] Homologar o mapeamento de `thread_id` entre requisições e sessões do OpenJarvis.
- [ ] Documentar hostname de serviço `openjarvis`, porta interna e URL base efetivamente homologados, sem reutilizar automaticamente a antiga porta `8000`.

## ✅ Critérios de Aceite
- Clientes HTTP compatíveis recebem respostas em streaming SSE tratadas passo a passo.
- Os contratos são testados para respostas normais, streaming, erros e continuidade de sessão.
- Lacunas de compatibilidade são registradas e bloqueiam a homologação; não se presume que a API da imagem seja OpenAI-Compatible.
