# Observability Requirements Checklist: Agregação de Logs com Alloy e Loki

**Purpose**: Orientar a revisão da qualidade dos requisitos da #103, com foco em isolamento/autenticação e persistência/recuperação, antes de tasks/analyze.
**Created**: 2026-10-25
**Feature**: [spec.md](../spec.md)
**Context**: [plan.md](../plan.md), [contrato](../contracts/logging-contract.md), [modelo de dados](../data-model.md).
**Depth**: Padrão.
**Audience / Timing**: Revisor de PR, após o desenho e antes da decomposição de tarefas e análise.

**Note**: Checklist customizado gerado por `/speckit-checklist`; avalia a escrita dos requisitos, não o funcionamento da implementação.
**Review Ownership**: A avaliação e os marcadores pertencem ao revisor. Um agente só deve auxiliar na avaliação mediante solicitação explícita do revisor.
**Marker Semantics**: `[x]` significa aprovação da qualidade do requisito pelo revisor; não significa implementação concluída. Todos os itens são entregues desmarcados.

## Requirement Completeness

- [x] CHK001 O escopo de contêineres elegíveis está definido, incluindo projeto selecionado, origens sem associação e serviços incompatíveis, sem confundir coleta do projeto com coleta global do host? [Completeness, Spec §FR-002/FR-003, Spec §Assumptions]
- [x] CHK002 Os requisitos distinguem explicitamente consulta, ingestão, administração e acesso ao daemon, com identidades e limites de acesso definidos para cada superfície? [Completeness, Spec §FR-013, Contract §2–4/§6]
- [x] CHK003 Os requisitos de preservação abrangem mensagem original, horário, fluxo, serviço, identidade da instância e contexto distribuído sem impor campos ausentes no schema da aplicação? [Completeness, Spec §FR-004/FR-006, Data Model §Evento de log]
- [x] CHK004 A documentação especifica quais dados técnicos persistem e quais estados podem ser perdidos, distinguindo eventos confirmados, posições de leitura e lotes pendentes? [Completeness, Spec §FR-009/FR-011/FR-012, Data Model §Estado técnico do Alloy/§Estado persistente do Loki]

## Requirement Clarity

- [x] CHK005 A expressão “somente pela máquina local” está delimitada quanto a interfaces, usuários locais, redes internas e operadores que controlam o daemon? [Clarity, Spec §FR-013, Plan §Composição e fronteiras]
- [x] CHK006 “Ingestão confirmada”, “consultável”, “expirado” e “removido” possuem significados distintos e coerentes, inclusive quanto à eliminação física dos dados? [Clarity, Spec §FR-009, Data Model §Estado persistente do Loki, Contract §6]
- [x] CHK007 A retenção configurável está definida com valor padrão, unidade, mínimo, valores permitidos e comportamento para configuração inválida? [Clarity, Spec §FR-009, Contract §1, Gap]
- [x] CHK008 O requisito de recuperação explicita duração da falha, tamanho e quantidade da amostra, componentes que permanecem ativos, marco inicial do prazo e tolerância a duplicatas? [Clarity, Spec §FR-011/SC-006, Contract §6]

## Requirement Consistency

- [x] CHK009 As permissões de leitura e escrita, a obrigatoriedade de autenticação e a exposição exclusivamente local são consistentes entre especificação, plano, contrato e modelo de identidades? [Consistency, Spec §FR-013/SC-008, Plan §Acesso e segredos, Contract §2–3, Data Model §Credenciais e acesso]
- [x] CHK010 A tolerância a mensagens de infraestrutura não estruturadas está conciliada explicitamente com a obrigação constitucional de logs JSON, sem criar uma exceção implícita para aplicações próprias ou novos componentes? [Consistency, Spec §FR-007/FR-012, Spec §Constitutional Analysis, Plan §Acesso e segredos, Conflict]
- [x] CHK011 A retenção de 14 dias, sua referência temporal e o prazo de limpeza são consistentes entre os artefatos, sem prometer retroatividade ou remoção instantânea não sustentada pelo desenho? [Consistency, Spec §SC-009, Plan §Retenção, recursos e recuperação, Data Model §Estado persistente do Loki]
- [x] CHK012 Os requisitos de filtragem por instância e preservação do contexto são consistentes com a proibição de indexar identificadores de alta cardinalidade? [Consistency, Spec §FR-004/FR-005/FR-008, Contract §5, Data Model §Evento de log]

## Acceptance Criteria Quality

- [x] CHK013 As metas de coleta e descoberta definem amostras, distribuição por origem/fluxo e prazos suficientes para um resultado de aceite objetivo? [Measurability, Spec §SC-001/SC-002]
- [x] CHK014 O critério de exclusão de logs estrangeiros delimita a amostra e a janela de observação, distinguindo ausência de ingestão indevida de indisponibilidade geral da coleta? [Measurability, Spec §SC-001/SC-003, Gap]
- [x] CHK015 O critério de retenção diferencia indisponibilidade por filtro de consulta de remoção física e define prazo de limpeza, preservação de dados não expirados e premissas da avaliação? [Measurability, Spec §SC-009, Contract §6]
- [x] CHK016 “Ambiente saudável”, “sem pressão de recursos” e as reservas de capacidade estão definidos com condições observáveis suficientes para evitar aceite ou rejeição arbitrários das metas? [Measurability, Spec §SC-001, Plan §Technical Context, Ambiguity]

## Scenario Coverage

- [x] CHK017 Os requisitos cobrem os fluxos primários de descoberta, consulta e diagnóstico sem exigir aplicações futuras, dashboards ou outras camadas de observabilidade? [Coverage, Spec §User Story 1/§User Story 3, Spec §FR-001/FR-014]
- [x] CHK018 Os fluxos alternativos de texto, JSON inválido e JSON válido sem campos convencionais estão descritos sem descarte silencioso ou alteração da mensagem original? [Coverage, Spec §User Story 2, Spec §FR-007, Data Model §Evento de log]
- [x] CHK019 Os requisitos de erro distinguem autenticação recusada, configuração inválida, origem inacessível, payload inválido e indisponibilidade do destino, preservando diagnósticos sem sucesso aparente? [Coverage, Spec §FR-010, Contract §2–3/§6]
- [x] CHK020 Os requisitos de recuperação distinguem reinício do agregador, reinício do coletor e indisponibilidade apenas do destino, declarando os dados preservados e as garantias de cada cenário? [Coverage, Spec §User Story 3/§SC-005/SC-006, Contract §6]

## Edge Case Coverage

- [x] CHK021 A identidade de origens recriadas e a semântica de mensagens iguais estão definidas sem misturar instâncias ou confundir duplicação legítima com retentativa? [Edge Case, Spec §Edge Cases, Data Model §Origem e descoberta/§Evento de log]
- [x] CHK022 As fronteiras para eventos vazios, grandes, antigos ou emitidos antes da coleta estão documentadas com diagnóstico esperado ou exclusão explícita, sem estreitar silenciosamente o escopo funcional? [Edge Case, Spec §Edge Cases/§FR-010, Data Model §Evento de log, Gap]
- [x] CHK023 As consequências de rotação da origem, falha simultânea, indisponibilidade prolongada e esgotamento de recursos estão descritas sem sugerir recuperação ilimitada ou descarte silencioso de dados não expirados? [Edge Case, Spec §Edge Cases/§Assumptions, Plan §Retenção, recursos e recuperação]

## Non-Functional Requirements

- [x] CHK024 O modelo de confiança distingue isolamento de ingestão, limitação de operações no daemon e isolamento contra administradores do host, documentando a exposição residual de metadados sensíveis? [Security, Spec §FR-003/FR-013, Plan §Docker e descoberta]
- [x] CHK025 Os requisitos de proteção de credenciais definem força, armazenamento, permissões, ausência nos logs e tratamento de arquivos ausentes, vazios ou inconsistentes? [Security, Spec §FR-010/FR-013, Contract §1, Plan §Acesso e segredos]
- [x] CHK026 O ciclo de vida das credenciais inclui requisitos de provisionamento, substituição e revogação, ou uma exclusão justificada desses cenários para o ambiente local? [Security, Gap, Contract §1]
- [x] CHK027 As definições de saúde, prontidão e entrega bem-sucedida estão separadas, com requisitos de diagnóstico que não confundem processo ativo ou configuração válida com ingestão funcional? [Observability, Spec §FR-010, Contract §6, Data Model §Estado técnico do Alloy]

## Dependencies & Assumptions

- [x] CHK028 As dependências de imagens, arquitetura, plataforma e permissões possuem restrições documentadas e evidências exigidas antes do aceite, sem alegar compatibilidade ainda não comprovada? [Dependency, Spec §Assumptions, Plan §Technical Context/§Validation and Delivery]
- [x] CHK029 Os requisitos de governança deixam claros os gates de testes prévios, CI e análise constitucional, sem equiparar aprovação documental a evidência operacional? [Traceability, Spec §Constitutional Analysis, Plan §Constitution Check/§Validation and Delivery]

## Ambiguities & Conflicts

- [x] CHK030 A prioridade entre negação por autenticação, método e rota não permitidos está suficientemente especificada para evitar respostas contraditórias nas mesmas condições? [Ambiguity, Contract §2–3, Gap]
- [x] CHK031 A relação entre prazo de retenção, idade do evento, reserva de disco e limites de carga está descrita sem prometer disponibilidade de 14 dias para qualquer volume de dados? [Consistency, Spec §FR-009/SC-009, Plan §Technical Context/§Retenção, recursos e recuperação]
- [x] CHK032 As exclusões de produção, alta disponibilidade, entrega exatamente uma vez e evolução de aplicações permanecem consistentes nos requisitos e não eliminam os critérios de aceite já acordados para esta entrega? [Consistency, Spec §Assumptions, Plan §Summary, Contract §7]

## Notes

- Perfil selecionado pelo usuário: opção A, revisão padrão de PR antes de tasks/analyze.
- Focos prioritários: isolamento/autenticação e persistência/recuperação; coleta, contexto, conformidade e critérios mensuráveis são cobertos como requisitos relacionados.
- Referências `Spec`, `Plan`, `Contract` e `Data Model` apontam para os documentos vinculados no cabeçalho; referências por título ou ID servem à rastreabilidade documental.
- `[Gap]`, `[Ambiguity]` e `[Conflict]` indicam aspectos que o revisor deve avaliar; não são conclusões automáticas de falha nem pedidos para aumentar o escopo.
- Marcar `[x]` somente após aprovação da qualidade do requisito; registrar justificativa e ajustes necessários em comentários de revisão.
- `/speckit-implement` lê o estado dos checklists como gate e não deve alterar os marcadores.
- O checklist [requirements.md](./requirements.md) tem ciclo próprio mantido por specify/clarify e não é substituído por este documento.
- Este comando não avalia nem aprova os itens gerados, não altera os requisitos de origem e não comprova funcionamento da infraestrutura.

## Complemento de revisão — achados C1, C2, U1, U2 e A1

**Purpose**: Avaliar a qualidade dos requisitos revisados após o analyze, sem repetir a cobertura geral anterior.
**Created**: 2026-10-25.
**Feature**: [spec.md](../spec.md).
**Context**: [plano revisado](../plan.md), [pesquisa §8–10](../research.md), [contrato](../contracts/logging-contract.md), [quickstart](../quickstart.md) e [constituição](../../../.specify/memory/constitution.md).
**Depth / Audience / Timing**: Padrão; revisor de PR; após revisão do plano e antes da regeneração das tarefas e novo analyze.
**Review Ownership / Marker Semantics**: Os novos itens permanecem `[ ]` até avaliação do revisor. Aprovações anteriores não aprovam automaticamente o desenho revisado; `[x]` não significa implementação concluída.

### Requirement Completeness

- [x] CHK033 A obrigação de emissão estruturada abrange explicitamente todos os componentes entregues e os diagnósticos anteriores à prontidão, distinguindo-a da tolerância de ingestão de mensagens externas? [Completeness, C1, Spec §FR-007/FR-012, Plan §Acesso e segredos, Constitution §II]
- [x] CHK034 Os requisitos de qualidade identificam escopo da checagem de tipos, critérios de reprovação e equivalência entre validação local e CI, sem tratar lint ou testes como substitutos? [Completeness, C2, Plan §Technical Context/§Validation and Delivery, Constitution §III]
- [x] CHK035 Os requisitos de inicialização enumeram parâmetros, materiais sensíveis e permissões sujeitos à validação, com responsabilidade definida por serviço e sem dependência exclusiva do harness de testes? [Completeness, U1, Plan §Inicialização validada, sem depender de pytest, Contract §1]

### Requirement Clarity

- [x] CHK036 O marco inicial do prazo de limpeza está definido por evento e distinguido de ingestão, fechamento do bloco de armazenamento, reinício e início da observação? [Clarity, U2, Spec §FR-009/SC-009, Plan §Retenção, recursos e recuperação, Contract §6]
- [x] CHK037 A precedência entre rota desconhecida, autenticação recusada e método proibido está definida para todas as combinações relevantes nos dois canais de acesso, incluindo as exceções administrativas? [Clarity, A1, Contract §2–3]
- [x] CHK038 Os requisitos diferenciam validação de formato da credencial de leitura, correspondência da credencial de escrita e comprovação de acesso autenticado, sem pressupor conhecimento de senha não armazenada? [Clarity, U1, Plan §Inicialização validada, sem depender de pytest, Contract §1]

### Requirement Consistency

- [x] CHK039 A obrigação de diagnósticos estruturados está conciliada com sanitização e preservação de informação operacional, sem justificar silêncio, exposição de conteúdo sensível ou alteração das mensagens coletadas? [Consistency, C1, Spec §FR-005/FR-007/FR-010/FR-012, Contract §5]
- [x] CHK040 A especificação de inicialização normal, reinício e rotação mantém os mesmos critérios de recusa, sem permitir que uma aprovação anterior dispense nova validação? [Consistency, U1, Contract §1, Data Model §Estado de inicialização, Plan §Inicialização validada, sem depender de pytest]

### Acceptance Criteria Quality

- [x] CHK041 O orçamento de limpeza documenta etapas, limites e margem de forma mensurável, distinguindo valores configurados, hipóteses a comprovar e garantia de aceite do projeto? [Measurability, U2, Plan §Retenção, recursos e recuperação, Spec §SC-009, Assumption]
- [x] CHK042 Os critérios de retenção exigem evidência de remoção física e preservação de eventos válidos em operação contínua, sem aceitar ausência em consulta ou intervenção forçada como prova equivalente? [Measurability, U2, Contract §6, Spec §SC-009]
- [x] CHK043 O limite total da avaliação está distinguido do prazo individual de limpeza, sem ampliar silenciosamente os 30 minutos ou omitir o tempo necessário para confirmar eventos antes de expirarem? [Measurability, U2, Plan §Validation and Delivery, Contract §6, Quickstart §Suíte automatizada prevista]

### Scenario Coverage

- [x] CHK044 Os requisitos de diagnóstico abrangem falhas de inicialização, encerramento e comunicação interna, incluindo a informação mínima de um erro não reconhecido, sem estabelecer sucesso aparente? [Coverage, C1, Spec §FR-010, Plan §Acesso e segredos, Contract §5]
- [x] CHK045 Os requisitos de recusa abrangem parâmetros inválidos, arquivos ausentes, vazios ou inconsistentes e acesso indevido, declarando diagnóstico e proibição de correção automática de permissões? [Coverage, U1, Contract §1, Spec §FR-010/FR-013]
- [x] CHK046 As regras de acesso cobrem combinações de falhas simultâneas, credenciais de outra interface e caminhos não canônicos, sem ampliar implicitamente o conjunto de rotas autorizadas? [Coverage, A1, Contract §2–3, Spec §FR-013]

### Edge Case Coverage

- [x] CHK047 Os requisitos de retenção tratam eventos de idades diferentes no mesmo bloco de armazenamento e escrita atrasada ou fora de ordem, sem restringir silenciosamente a entrada para cumprir o prazo? [Edge Case, U2, Plan §Retenção, recursos e recuperação, Data Model §Estado persistente do Loki]
- [x] CHK048 Os requisitos de diagnóstico definem ausência de truncamento silencioso e tratamento de saturação ou indisponibilidade da saída, sem confundir proteção de segredos com descarte de falhas? [Edge Case, C1, Spec §FR-010, Plan §Acesso e segredos, Gap]

### Non-Functional Requirements

- [x] CHK049 A proteção de materiais sensíveis define limites de tamanho, identidades autorizadas e critérios de permissões no host e no runtime, distinguindo evidência real de modos de acesso sintetizados pela plataforma? [Security, U1, Contract §1, Plan §Inicialização validada, sem depender de pytest, Assumption]
- [x] CHK050 A exigência constitucional de tipagem possui critérios documentados que impeçam aprovação por exclusões abrangentes ou supressões indiscriminadas de erros? [Consistency, C2, Constitution §III, Plan §Technical Context, Gap]

### Dependencies & Assumptions

- [x] CHK051 As hipóteses de compatibilidade das ferramentas e plataformas possuem evidência exigida e consequência de falha explícitas, sem equiparar decisão documental a comprovação operacional? [Dependency, C1/C2/U1/U2, Plan §Technical Context/§Constitution Check, Research §8–9, Assumption]

### Ambiguities & Conflicts

- [x] CHK052 A relação entre desenho revisado, tarefas anteriores e critérios de aprovação está explícita, identificando a necessidade de sincronização antes de novo analyze, sem reaproveitar aprovações como fechamento automático dos cinco achados? [Traceability, C1/C2/U1/U2/A1, Plan §Summary/§Constitution Check, Conflict]

### Notes do complemento

- Perfil confirmado pelo usuário: opção A, complemento dos cinco achados; profundidade e público mantidos da rodada anterior.
- C1/C2/U1/U2/A1 são identificadores do relatório analyze anterior, usados para rastrear o motivo da revisão, não avaliações automáticas dos novos requisitos.
- Referências `Constitution`, `Research` e `Quickstart` apontam para os documentos vinculados no contexto do complemento; `Spec`, `Plan`, `Contract` e `Data Model` mantêm os significados do cabeçalho original.
- As tarefas existentes ainda descrevem partes do desenho anterior e serão sincronizadas por `/speckit-tasks`; este checklist não as altera nem conclui que os achados foram resolvidos.
- Somente o revisor aprova os itens; `/speckit-implement` lê os marcadores como gate e não deve modificá-los.
