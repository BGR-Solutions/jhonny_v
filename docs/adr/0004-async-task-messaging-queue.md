# 0004. Processamento Assíncrono e Filas Persistentes via RabbitMQ

* **Status:** Aceito
* **Data:** 2026-08-08
* **Autores:** Equipe jhonny-core ([@cesarsuchoj](https://github.com/cesarsuchoj))
* **Issues Relacionadas:** `#107`, `#401`, `#402`, `#404`

---

## Contexto e Problema
A execução de certas tarefas solicitadas pelo usuário (ex: consolidação diária de e-mails, relatórios extensos de agenda, sincronização de arquivos) demanda alto tempo de processamento[cite: 181, 183]. Manter essas solicitações em um fluxo HTTP síncrono bloqueia a interface de chat e consome conexões ativas da API e do servidor de modelos[cite: 165, 183].

---

## Opções Consideradas

1. **Processamento Totalmente Síncrono no Orchestrator:**
   * *Prós:* Simplicidade de arquitetura sem dependência de brokers de mensagens.
   * *Contras:* Timeouts na interface do usuário e concorrência excessiva no hardware ao rodar o Ollama[cite: 165, 183].

2. **NATS JetStream:**
   * *Prós:* Binário leve e consumo de memória extremamente reduzido (<30MB RAM)[cite: 188].
   * *Contras:* Recursos de priorização estrita de mensagens e roteamento complexo de mensagens falhas exigem construções adicionais[cite: 189].

3. **RabbitMQ com Filas Duráveis e Dead Letter Queues (DLQ):**
   * *Prós:* Suporte nativo a filas persistentes em disco (`durable=True`) [cite: 185, 193]; priorização de mensagens; mecanismo maduro de Dead Letter Queue (DLQ) e retentativas com backoff exponencial [cite: 185]; painel web de gerência[cite: 185].
   * *Contras:* Footprint de memória superior ao NATS (~100MB-200MB RAM)[cite: 186].

---

## Decisão
Adotar o **RabbitMQ** como broker de mensageria para o desacoplamento de tarefas em segundo plano[cite: 9, 185]. Tarefas não críticas ou de longa duração serão despachadas pelo `apps/agent-orchestrator` em filas duráveis e consumidas assincronamente pelo `apps/worker`[cite: 11, 183, 184].

---

## Consequências

### Positivas
* **Desoneramento de Hardware:** Liberação imediata da interface de chat do usuário após o enfileiramento da tarefa[cite: 183].
* **Garantia de Entrega:** Mensagens persistidas em disco que resistem a reinicializações imprevistas do servidor[cite: 194, 195].
* **Tratamento de Falhas:** Tarefas com erro persistente são isoladas na DLQ sem bloquear a fila principal[cite: 185].

### Negativas / Mitigações
* **Consumo de Memória Adicional:** ~150MB adicionais de RAM na stack de infraestrutura. *Mitigação:* Justificado pelos recursos nativos de priorização e gestão da DLQ[cite: 185, 186].
