# 📌 Issue #504: Testes de Integração End-to-End (E2E)

* **Milestone:** `v0.5 - Interfaces & Clients`
* **Tipo:** QA / E2E
* **ADRs Vinculadas:** N/A

## 🎯 Descrição
Executar a validação completa do fluxo End-to-End no ecossistema, garantindo a integridade de todas as camadas.

## 📥 Tarefas
- [ ] Criar script de teste E2E automatizado simulando interações completas de usuário.
- [ ] Validar os caminhos UI/VS Code -> OpenJarvis -> LiteLLM (modelos), OpenJarvis -> MCP (ferramentas) e integração de publicação -> RabbitMQ -> Worker, incluindo persistência e telemetria Loki/Tempo.
- [ ] Cobrir regressões da substituição: continuidade por `thread_id`, streaming, erros, aprovação/rejeição de ações e retomada após reinício, conforme a [ADR-0006](../../adr/0006-openjarvis-compose.md).
- [ ] Documentar relatórios de cobertura de testes e homologação no `docs/`.

## ✅ Critérios de Aceite
- Todos os testes da suíte E2E executam com sucesso.
- Dashboard do Grafana exibe traces contínuos e sem erros de telemetria durante a execução dos testes.
