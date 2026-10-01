# 0006. Coleta de Logs via Proxy de Socket e Gateway Autenticado do Loki

* **Status:** Aceito
* **Data:** 2026-10-01
* **Autores:** Equipe jhonny-core ([@cesarsuchoj](https://github.com/cesarsuchoj))
* **Issues Relacionadas:** `#103`
* **Especificação:** [`specs/003-agregacao-logs-loki/`](../../specs/003-agregacao-logs-loki/) (research, Decisions 3, 12 e 13)

---

## Contexto e Problema
A camada de observabilidade precisa coletar `stdout`/`stderr` de todos os contêineres do host. Ler a API do Docker exige acesso ao socket, que equivale a root no host. O Loki não autentica requisições, então expô-lo diretamente deixaria qualquer processo local consultar e injetar logs. No Docker Engine 28.0.4 do ambiente de referência, contêineres criados em várias redes recebem do DNS embutido o IP da rede errada.

---

## Opções Consideradas

1. **Socket montado direto no coletor:**
   * *Prós:* Configuração mínima.
   * *Contras:* O coletor, exposto à rede, ganha controle total do daemon.
2. **`tecnativa/docker-socket-proxy`:**
   * *Prós:* Popular e simples.
   * *Contras:* Roda como root e loga em texto (viola a constituição 3.3.2).
3. **`wollomatic/socket-proxy` + gateway Caddy com basic auth no namespace do Loki:**
   * *Prós:* Proxy sem root, rootfs somente leitura, allowlist por regex e logs JSON. O gateway só exige basic auth, sem arquivo de hash versionado.
   * *Contras:* Um serviço a mais por função, e o Loki precisa de `build` local para ter healthcheck.
4. **Gateway em rede interna dedicada entre ele e o Loki:**
   * *Contras:* Falhou no protótipo pelo bug de DNS multi-rede.

---

## Decisão
Adotar a opção 3:
- `socket-proxy` é o único serviço que monta `/var/run/docker.sock` (`:ro`). Roda como `65534:${DOCKER_GID}`, com `read_only`, `cap_drop: ALL` e `no-new-privileges`. Só permite os GET/HEAD necessários ao coletor; escrita → `405`, demais leituras → `403`.
- O proxy fica numa rede `internal` (`docker-api`) compartilhada apenas com o `alloy`.
- O Loki escuta em `127.0.0.1:3101`. O `loki-gateway` (Caddy) usa `network_mode: service:loki` e publica a porta 3100 só no loopback do host, com basic auth em tudo exceto `/ready`.
- Nenhum serviço resolvido por nome ou com porta publicada fica em mais de uma rede.

---

## Consequências
* **Positivas:** o socket deixa de ser exposto ao coletor; consulta e push exigem credencial; todos os componentes logam em JSON no stdout/stderr.
* **Negativas:** `GET /containers/{id}/json` expõe variáveis de ambiente ao coletor. A mitigação é a rede `internal`, alcançável só pelo coletor. Exige `DOCKER_GID` no `.env`.
* **Mitigações:** testes de aceite em `infra/tests/` verificam a allowlist, o isolamento de rede e a autenticação a cada mudança (workflow `infra-obs`).
