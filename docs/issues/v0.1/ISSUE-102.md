# 📌 Issue #102: Configuração do LiteLLM Proxy e Roteamento de Modelos

* **Milestone:** `v0.1 - Infra Core & Observabilidade`
* **Tipo:** Infraestrutura / Feature
* **ADRs Vinculadas:** [`ADR-0001: Abstração de Provedores de LLM com LiteLLM Proxy`](../../adr/0001-litellm-proxy-abstraction.md)

## 🎯 Descrição
Configurar o contêiner do LiteLLM Proxy no Compose, permitindo desacoplar a escolha dos modelos (Ollama local e Provedores Cloud) do código das aplicações.

## 📥 Tarefas
- [ ] Adicionar serviço `litellm` no `infra/compose.llm.yaml`.
- [ ] Criar arquivo de configuração `infra/litellm/config.yaml`.
- [ ] Configurar rotas para o Ollama local e modelos alternativos (OpenAI, Anthropic).
- [ ] Configurar chave master de autenticação do proxy via `.env`.

## ✅ Critérios de Aceite
- Endpoint `http://localhost:4000/v1/models` responde com sucesso retornando os modelos listados.
- Teste de chamada no endpoint `/v1/chat/completions` executado via cURL ou Postman.
