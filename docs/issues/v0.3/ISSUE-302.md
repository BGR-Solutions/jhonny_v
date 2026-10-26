# 📌 Issue #302: Integração do OpenJarvis com Servidor MCP

* **Milestone:** `v0.3 - OpenJarvis`
* **Tipo:** Integration / Feature
* **ADRs Vinculadas:** [ADR-0006: OpenJarvis via Compose](../../adr/0006-openjarvis-compose.md)

## 🎯 Descrição
Configurar e homologar a conexão do OpenJarvis ao `mcp-server` para descobrir e executar suas ferramentas, usando os mecanismos suportados pela imagem selecionada na [issue #301](./ISSUE-301.md).

## 📥 Tarefas
- [ ] Verificar o transporte MCP compatível com a imagem e o servidor da v0.2, sem presumir suporte nativo a SSE ou Stdio.
- [ ] Declarar a conexão nas configurações de `infra/openjarvis/`, sem duplicar ferramentas nem criar conversor LangChain/LangGraph próprio por padrão.
- [ ] Validar descoberta de schemas, argumentos, resultados e erros das ferramentas.
- [ ] Testar reconexão e falhas de comunicação com erro explícito e contexto de tracing.

## ✅ Critérios de Aceite
- O OpenJarvis descobre as ferramentas do MCP Server e executa uma chamada de teste com argumentos e resultado preservados.
- Incompatibilidade de transporte ou schema é registrada como bloqueio de integração, sem contornar as aprovações de ações sensíveis.
