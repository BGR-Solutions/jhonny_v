# 0002. Padrão Human-in-the-Loop para Ações de Alto Risco

* **Status:** Aceito
* **Data:** 2026-08-08
* **Autores:** Equipe jhonny-core ([@cesarsuchoj](https://github.com/cesarsuchoj))
* **Issues Relacionadas:** `#202`, `#205`, `#304`, `#502`

---

## Contexto e Problema
Como o assistente possui autonomia para interagir com o sistema de arquivos local (escrita/exclusão de arquivos) e serviços externos (envio de e-mails via Gmail, agendamento de eventos no Google Calendar) [cite: 1, 14], alucinações da LLM ou interpretações equivocadas de instrução podem gerar ações destrutivas indesejadas[cite: 104].

---

## Opções Consideradas

1. **Autonomia Total (Modo Sem Confirmação):**
   * *Prós:* Menor atrito e maior velocidade de resposta em automações.
   * *Contras:* Alto risco de perda irreversível de dados locais ou disparos acidentais de e-mails em lote[cite: 104].

2. **Permissão prévia global por Skill:**
   * *Prós:* Simples de configurar.
   * *Contras:* Não atende cenários onde a leitura é segura, mas a exclusão ou alteração de contexto é crítica[cite: 106].

3. **Arquitetura Human-in-the-Loop (HitL) com Interrupção de Grafo no LangGraph:**
   * *Prós:* Permite pausar o estado do agente (*interrupt_before*) antes da execução do nó de execução da ferramenta sensível, solicitando aprovação humana explícita no cliente (UI/VS Code)[cite: 7, 37, 105, 106].
   * *Contras:* Requer persistência durável do estado do grafo para que a execução possa ser retomada assincronamente após a aprovação do usuário[cite: 37, 114].

---

## Decisão
Adotar o padrão **Human-in-the-Loop (HitL)** utilizando nativamente os mecanismos de interrupção do **LangGraph**[cite: 7, 37, 105]. Ferramentas classificadas como críticas (ex: `write_file`, `delete_file`, `send_email`) exigirão obrigatoriamente um nó de aprovação antes da invocação no `apps/mcp-server`[cite: 14, 106].

---

## Consequências

### Positivas
* **Segurança Operacional:** Elimina o risco de execuções destrutivas não autorizadas por alucinação[cite: 104].
* **Transparência:** O usuário visualiza os argumentos que a ferramenta receberá antes de confirmar a execução[cite: 133].

### Negativas / Mitigações
* **Aumento na Complexidade de Estado:** Exige persistência de histórico e checkpoints por `thread_id` para manter o grafo pausado[cite: 114, 209]. *Mitigação:* Uso do `PostgresSaver` para persistência relacional do grafo[cite: 37, 231, 238].
