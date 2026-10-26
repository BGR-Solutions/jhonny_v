# Data Model: Eventos e estado de coleta

## Evento de log

| Campo | Origem / regra | Armazenamento |
|-------|----------------|---------------|
| timestamp | RFC3339Nano fornecido pelo Docker, convertido a nanossegundos | Timestamp nativo Loki |
| line | Linha original, sem envelope Docker, sem reescrita pelo parser | Conteúdo Loki |
| project | Label Compose com igualdade exata ao projeto selecionado | Label indexada |
| service | Label Compose do serviço; alvo sem serviço reconhecível é diagnosticado como incompatível | Label indexada |
| stream | `stdout` ou `stderr`, promovido no source | Label indexada |
| parse_status | `json` ou `text_or_invalid_json`, valores controlados | Label indexada |
| container_id | ID completo Docker; distingue recriações | Structured metadata, não indexado |
| container_name | Nome do contêiner sem prefixo `/`; não substitui ID | Structured metadata, não indexado |
| trace_id / span_id | Preservados na linha JSON; não sintetizados | Campos extraídos por consulta, não labels indexadas |
| severity / message | Mantidos conforme schema original da aplicação | Campos extraídos quando presentes |

JSON válido não exige o campo `message`; arrays/primitivos não devem ser descartados. Um timestamp de aplicação pode ser consultado na linha, mas não sobrescreve o timestamp de transporte. Linha vazia ou maior que 64KiB fica fora do contrato da amostra e exige diagnóstico/documentação do comportamento upstream, nunca promessa falsa de ingestão.

Não há chave de unicidade de produção: mensagens iguais podem ser eventos distintos. IDs únicos de teste são apenas dados da fixture. Retentativas podem produzir duplicatas; a validação compara o conjunto de IDs recebidos sem removê-las do storage.

## Origem e descoberta

`Projeto 1:N Serviço 1:N Instância 1:N Eventos`. Elegibilidade exige projeto exato e serviço Compose reconhecível. A instância passa por `descoberta → elegível → coletando → parada/removida`; metadados dos eventos já ingeridos continuam identificando a instância antiga.

Docker daemon é externo à stack de logs, compartilhado e administrado por operador autorizado. Labels de projeto não são identidade criptográfica nem limite contra usuário com controle do daemon.

## Estado técnico do Alloy

- Posições persistentes em `alloy-data`, vinculadas à identidade do source e do contêiner.
- Ciclo operacional: `iniciando → pronto → falha de leitura/envio → retentativa → pronto`.
- Estado de configuração saudável não prova entrega: monitorar também diagnósticos/contadores de falha do componente e eventos consultáveis.
- Lote pendente em memória não é log de aplicação nem fila durável. A garantia de 30s exige coletor vivo e origem disponível.

## Estado persistente do Loki

- `loki-data`: chunks filesystem, índice TSDB v13, WAL, compactor e marcadores persistentes.
- Evento: `emitido → lido → envio pendente → aceito → consultável → expirado → removido`.
- Aceitação HTTP e visibilidade de consulta são etapas distintas; testes aguardam consultas, não apenas status de push.
- Política padrão 336h, configurável em múltiplos de 24h, mínimo 24h. Expiração é avaliada pelo horário do evento; limpeza assíncrona deve cumprir a meta local de 30m após expiração.
- Deadline individual: timestamp do evento + política + 30m. Em v3.7.9 o compactor avalia expiração pelo timestamp mais recente do chunk; amplitude entre primeiro/último evento, flush e atualização de índice fazem parte do orçamento do [plano](./plan.md). Um chunk com evento ainda válido não pode ser apagado antecipadamente. Medir esses estados em operação contínua, inclusive escrita atrasada/fora de ordem aceita; flush/restart de teste não substitui a comprovação.
- Persistência pressupõe preservação do volume. `down -v` ou remoção de volume não está coberta.

## Credenciais e acesso

| Identidade | Permissão | Material local não versionado |
|------------|-----------|-------------------------------|
| Operador leitor | GET de consultas permitidas em loopback | Senha local e `read.htpasswd` |
| Alloy escritor | POST push na rede interna | `write.htpasswd` e `write-password` |
| Alloy cliente Docker | GET/HEAD allowlist via proxy privado | Sem senha; identidade delimitada pela rede privada e confiança no daemon |

Nunca persistir Authorization, hashes ou senhas em eventos de teste, metadados ou configurações versionadas. Credencial de escrita não deve servir para consulta, nem a de leitura para push.

## Estado de inicialização

`criado → validando → executando → saudável`; erro em validação leva a `falha` com saída não zero e evento JSON sanitizado. A validação ocorre no entrypoint, inclusive em reinícios, e não depende do harness de testes. Não persistir um marcador que dispense nova verificação. Config renderizada/PID ficam em tmpfs, não são logs nem estado durável.

Gateway recebe read.htpasswd, write.htpasswd e write-password somente leitura, valida bcrypt e correspondência da escrita antes de iniciar. A senha do leitor não é armazenada nele; o teste autenticado comprova seu uso. Rotação muda o conjunto coerente de arquivos e recria gateway/Alloy, repetindo validação.
