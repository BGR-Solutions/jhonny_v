# 0003. Amostragem e Rastreamento Distribuído via OpenTelemetry e Grafana Tempo

* **Status:** Aceito
* **Data:** 2026-08-08
* **Autores:** Equipe jhonny-core ([@cesarsuchoj](https://github.com/cesarsuchoj))
* **Issues Relacionadas:** `#105`, `#405`

---

## Contexto e Problema
A orquestração do assistente envolve chamadas distribuídas entre a Interface, o Agent Orchestrator, o LiteLLM Proxy, o Worker Assíncrono e o MCP Server[cite: 4, 12, 13]. Rastrear gargalos de latência ou falhas de execução entre o ciclo de raciocínio da LLM e a execução de ferramentas em máquinas com recursos limitados exige visibilidade de *distributed tracing*[cite: 78, 108].

---

## Opções Consideradas

1. **Apenas Logs Agregados no Loki:**
   * *Prós:* Simples e com baixíssimo consumo de I/O e CPU[cite: 22].
   * *Contras:* Dificuldade em correlacionar o tempo de resposta exato de cada nó da árvore de decisão do LangGraph e sub-chamadas HTTP/AMQP[cite: 78].

2. **OpenTelemetry Tracing Sem Amostragem (100% dos Traces):**
   * *Prós:* Coleta completa de todos os Spans do sistema.
   * *Contras:* Alto consumo de disco e processamento no Grafana Tempo em cenários de uso contínuo[cite: 108].

3. **OpenTelemetry com Grafana Tempo e Amostragem Dinâmica (Adaptive Sampling):**
   * *Prós:* Permite amostragem mais alta (100%) em ambiente de desenvolvimento e amostragem por limiar/erro em uso regular [cite: 109, 110, 111]; integra-se ao Loki e Prometheus no Grafana via `trace_id`[cite: 22, 77].
   * *Contras:* Requer instrumentação explícita do SDK do OpenTelemetry nas aplicações Python.

---

## Decisão
Adotar o **OpenTelemetry** com armazenamento no **Grafana Tempo**, aplicando políticas de amostragem dinâmica (*adaptive/probabilistic sampling*)[cite: 21, 109]. As aplicações injetará automaticamente o `trace_id` nos cabeçalhos de contexto e logs estruturados[cite: 77, 109].

---

## Consequências

### Positivas
* **Visibilidade End-to-End:** Visualização da latência de cada passo do raciocínio ReAct e da execução das Skills[cite: 78].
* **Correlação Direta:** Integração no Grafana permitindo pular de um log de erro no Loki diretamente para o Span correspondente no Tempo[cite: 25, 77].

### Negativas / Mitigações
* **Overhead de CPU/Memória:** *Mitigação:* Configuração da amostragem no SDK para 100% apenas em desenvolvimento local e amostragem baseada em erros/thresholds em execução regular[cite: 110, 111].
