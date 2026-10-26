# 📌 Issue #301: Integração da Imagem Docker do OpenJarvis no Compose Core

* **Milestone:** `v0.3 - OpenJarvis`
* **Tipo:** Infraestrutura / Integração
* **ADRs Vinculadas:** [ADR-0006: OpenJarvis via Compose](../../adr/0006-openjarvis-compose.md)

## 🎯 Descrição
Integrar uma imagem Docker do OpenJarvis como serviço `openjarvis` em `infra/compose.core.yaml`, com configurações próprias em `infra/openjarvis/`. Esta issue substitui a criação de uma aplicação FastAPI/LangGraph em `apps/agent-orchestrator`.

O escopo aqui descrito é futuro: esta revisão documental não cria a pasta, não altera o Compose e não remove o placeholder legado.

## 📥 Tarefas
- [ ] Identificar o projeto/distribuição OpenJarvis, validar procedência e licença e registrar a referência de imagem com versão/digest fixado, sem `latest`.
- [ ] Confirmar na versão selecionada os contratos MCP, LiteLLM, HitL, persistência, API/SSE, mensageria e telemetria; registrar lacunas antes de implementar.
- [ ] Concluir os gates SDD e escrever testes de contrato antes das adaptações funcionais.
- [ ] Criar `infra/openjarvis/` com configurações sem segredos, documentando caminhos internos, comandos, portas e opções efetivamente suportados pela imagem.
- [ ] Declarar `image` em `infra/compose.core.yaml`, sem build local, e explicitar `env_file`, volumes, rede, dependências e healthcheck.
- [ ] Manter segredos em `.env` ou secret manager e dados persistentes em volumes nomeados; montar configurações como somente leitura quando suportado.
- [ ] Validar logs JSON em `stdout`/`stderr`, ausência de logs em disco e propagação de `trace_id`/`span_id` para a stack LGTMP.
- [ ] Planejar a retirada do placeholder legado em entrega estrutural separada.

## ✅ Critérios de Aceite
- A composição combinada é validada por `docker compose config` e o serviço inicia de forma saudável usando o healthcheck comprovado da imagem, sem presumir `/health` ou porta `8000`.
- A origem e a versão da imagem, os mounts, as variáveis e as dependências operacionais estão documentados e reproduzíveis.
- Lacunas constitucionais ou funcionais bloqueiam a homologação; nenhuma funcionalidade é removida silenciosamente.
