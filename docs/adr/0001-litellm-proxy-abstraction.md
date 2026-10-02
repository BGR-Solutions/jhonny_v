# 0001. Abstração de Provedores de LLM via LiteLLM Proxy

* **Status:** Aceito
* **Data:** 2026-08-08
* **Autores:** Equipe jhonny-core ([@cesarsuchoj](https://github.com/cesarsuchoj))
* **Issues Relacionadas:** `#102`, `#303`

---

## Contexto e Problema
[cite_start]O assistente **`jhonny-core`** utiliza Modelos de Linguagem (LLMs) para raciocínio ReAct e chamada de ferramentas (*Function Calling*)[cite: 1, 115, 125]. [cite_start]Durante o desenvolvimento ou em execução em hardware local limitado (CPU/GPU), um modelo executado pelo Ollama pode apresentar latência elevada ou limitação de janela de contexto[cite: 115, 165]. [cite_start]Nesses cenários, é necessário trocar temporariamente o provedor por APIs em nuvem (ex: OpenAI, Anthropic, Gemini) sem alterar o código das aplicações ou interromper o serviço[cite: 116, 117].

---

## Opções Consideradas

1. **Conectar a aplicação diretamente ao SDK do Ollama ou OpenAI:**
   * *Prós:* Integração direta sem serviços adicionais na infraestrutura.
   * *Contras:* Exige alteração de código ou múltiplos clientes HTTP na camada de orquestração para tratar retentativas, fallbacks e chaves de API.

2. **Utilizar o LiteLLM Proxy como Gateway Único de LLMs:**
   * [cite_start]*Prós:* Expe uma interface padrão OpenAI-Compatible (`/v1/chat/completions`) [cite: 8, 38][cite_start]; unifica log de custos/tokens; permite alternar modelos ou definir estratégias de *fallback* automático editando apenas o arquivo `infra/litellm/config.yaml` [cite: 117][cite_start]; suporte a Semantic Caching via Redis[cite: 171].
   * *Contras:* Adiciona um contêiner Proxy na camada de rede.

---

## Decisão
[cite_start]Adotar o **LiteLLM Proxy** como gateway centralizador e exclusivo para todas as chamadas de modelos de linguagem no ecossistema **`jhonny-core`**[cite: 9, 116]. [cite_start]O `apps/agent-orchestrator` comunicará estritamente com o LiteLLM, delegando a ele as regras de roteamento e resiliência entre o Ollama local e modelos Cloud[cite: 9, 10, 11, 117].

---

## Consequências

### Positivas
* [cite_start]**Desacoplamento Total:** Troca transparente de modelos sem refatoração de código[cite: 117].
* [cite_start]**Observabilidade Centralizada:** Métricas nativas do LiteLLM enviadas ao Prometheus sobre uso de tokens e latência[cite: 20].
* [cite_start]**Cache Semântico:** Redução de chamadas repetidas ao Ollama via integração nativa do LiteLLM com o Redis[cite: 171].

### Negativas / Mitigações
* **Overhead de Rede:** Adição de um salto de rede interno no Docker. *Mitigação:* Comunicação via rede interna acelerada do Docker Compose (`bridge`).
