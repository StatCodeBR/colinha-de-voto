# Delta for historico-eleitoral

## ADDED Requirements

### Requirement: Normalização de nomes para comparação
O sistema MUST comparar nomes na forma normalizada: maiúsculas, sem acentos, apenas
letras e espaços, com espaços repetidos colapsados.

#### Scenario: Acentos e apóstrofos
- GIVEN os nomes "Maria D'Ávila  Souza" e "MARIA D AVILA SOUZA"
- WHEN ambos são normalizados
- THEN o resultado é idêntico

### Requirement: Vínculo confirmado
O sistema SHALL marcar como confirmado o vínculo entre uma candidatura do ano da eleição
e uma candidatura anterior quando (a) ambas têm CPF válido e igual e o nome (ao menos
uma palavra em comum, fora partículas) ou a data de nascimento coincidem, ou (b) algum
lado não tem CPF válido, e nome normalizado e data de nascimento são iguais, com essa
combinação única nos dois lados. CPFs válidos e diferentes MUST impedir o vínculo.

#### Scenario: Mesmo CPF
- GIVEN candidaturas de 2026 e 2022 com o mesmo CPF válido
- WHEN o vínculo é calculado
- THEN o vínculo é confirmado

#### Scenario: Mesmo CPF com nome e nascimento divergentes
- GIVEN candidaturas com o mesmo CPF, sem nenhuma palavra do nome em comum e com datas
  de nascimento diferentes
- WHEN o vínculo é calculado
- THEN o caso é marcado como ambíguo e vai para revisão

#### Scenario: CPFs diferentes
- GIVEN duas candidaturas com CPFs válidos e diferentes, mesmo nome e mesma data de
  nascimento
- WHEN o vínculo é calculado
- THEN elas não são vinculadas

#### Scenario: Homônimos com nascimentos diferentes
- GIVEN duas pessoas com o mesmo nome normalizado e datas de nascimento diferentes
- WHEN o vínculo é calculado
- THEN elas não são vinculadas entre si

#### Scenario: Mesmo nome e nascimento, mas chave repetida
- GIVEN que a combinação nome + nascimento aparece em duas candidaturas diferentes no
  mesmo ano anterior
- WHEN o vínculo é calculado
- THEN o caso é marcado como ambíguo, não como confirmado

### Requirement: Casos duvidosos vão para revisão
O sistema MUST classificar como provável o par com mesmo nome normalizado na mesma UF
quando não houver data de nascimento para comparar, e como ambíguo o par cuja chave
aponte para mais de uma pessoa ou cujo CPF coincida com nome e nascimento divergentes. Prováveis e ambíguos MUST NOT aparecer
nas saídas públicas e SHALL ser listados em `revisao_vinculos.csv` com as evidências dos
dois lados.

#### Scenario: Ano sem data de nascimento
- GIVEN uma candidatura anterior sem data de nascimento, com mesmo nome e mesma UF
- WHEN o vínculo é calculado
- THEN o par é marcado como provável
- AND aparece no relatório de revisão
- AND não aparece na trajetória pública

### Requirement: Correções manuais prevalecem
O sistema SHALL aplicar as decisões de `data/manual/vinculos.csv` depois das regras
automáticas: "confirmar" torna o par confirmado e "rejeitar" remove o par, inclusive se
a regra automática o tivesse confirmado.

#### Scenario: Rejeição manual de um vínculo automático
- GIVEN um par confirmado automaticamente
- AND uma linha em `vinculos.csv` rejeitando esse par
- WHEN o vínculo é recalculado
- THEN o par não aparece na trajetória pública

#### Scenario: Confirmação manual de um provável
- GIVEN um par provável
- AND uma linha em `vinculos.csv` confirmando esse par
- WHEN o vínculo é recalculado
- THEN o par aparece na trajetória pública

### Requirement: Resultado de cada candidatura
O sistema MUST traduzir a situação de totalização do TSE para um conjunto fechado de
resultados (eleito, suplente, não eleito, segundo turno sem resultado, sem resultado) e
MUST falhar com a lista de valores desconhecidos em vez de adotar um valor padrão.

#### Scenario: Eleito por quociente partidário
- GIVEN uma candidatura com situação "ELEITO POR QP"
- WHEN o resultado é mapeado
- THEN o resultado é `eleito`

#### Scenario: Valor desconhecido
- GIVEN uma situação de totalização que não está no mapeamento
- WHEN o resultado é mapeado
- THEN o processamento falha informando o valor e o ano

### Requirement: Classificação do histórico
O sistema SHALL classificar cada candidato do ano da eleição, usando apenas vínculos
confirmados dentro da janela configurada, em: `eleito`, `concorreu`, `sem_registro` ou
`em_verificacao` (sem confirmados, mas com pendentes). Quando houver confirmados e
pendentes ao mesmo tempo, o detalhe MUST indicar que há registros em verificação.

#### Scenario: Já eleito antes
- GIVEN um candidato com uma candidatura confirmada em 2020 com resultado eleito
- WHEN o histórico é classificado
- THEN a classe é `eleito`

#### Scenario: Nenhum registro encontrado
- GIVEN um candidato sem vínculos confirmados nem pendentes
- WHEN o histórico é classificado
- THEN a classe é `sem_registro`
- AND o detalhe informa a janela de cobertura (primeiro e último ano pesquisados)

#### Scenario: Só pendências
- GIVEN um candidato sem vínculos confirmados e com um vínculo ambíguo
- WHEN o histórico é classificado
- THEN a classe é `em_verificacao`

### Requirement: Trajetória publicada
O sistema MUST incluir no detalhe de cada candidato a lista de candidaturas confirmadas,
da mais recente para a mais antiga, com ano, cargo, local (município ou UF), partido e
resultado. A trajetória MUST NOT incluir o nome usado nas candidaturas anteriores.

#### Scenario: Nome civil diferente em eleição anterior
- GIVEN um vínculo confirmado com uma candidatura anterior registrada com outro nome
- WHEN o detalhe é gerado
- THEN a trajetória mostra a candidatura sem o nome anterior

#### Scenario: Candidata que foi vereadora
- GIVEN uma candidata a deputada estadual em 2026, eleita vereadora em 2020
- WHEN o detalhe é gerado
- THEN a trajetória mostra 2020, vereador(a), o município, o partido da época e
  `eleito`

### Requirement: Busca de reeleição
O sistema SHALL marcar `busca_reeleicao` como verdadeiro quando o candidato tem vínculo
confirmado com uma candidatura eleita para o mesmo cargo, na mesma UF, na eleição que
elegeu o mandato atual (8 anos antes para senador, 4 anos antes para os demais cargos).
Quando não houver vínculo confirmado naquela eleição, mas houver vínculo pendente, o
campo MUST ser nulo, e não falso.

#### Scenario: Deputada eleita em 2022
- GIVEN uma candidata a deputada federal em 2026, eleita deputada federal na mesma UF
  em 2022, com vínculo confirmado
- WHEN o histórico é classificado
- THEN `busca_reeleicao` é verdadeiro

#### Scenario: Senador eleito oito anos antes
- GIVEN um candidato a senador em 2026, eleito senador em 2018
- WHEN o histórico é classificado
- THEN `busca_reeleicao` é verdadeiro

#### Scenario: Eleita para outro cargo
- GIVEN uma candidata a deputada federal em 2026, eleita deputada estadual em 2022
- WHEN o histórico é classificado
- THEN `busca_reeleicao` é falso

#### Scenario: Vínculo pendente
- GIVEN um candidato sem vínculo confirmado em 2022 e com um vínculo ambíguo em 2022
- WHEN o histórico é classificado
- THEN `busca_reeleicao` é nulo

### Requirement: Resumo de qualidade do vínculo
O sistema MUST gravar em `resumo.json`, por UF, a quantidade de vínculos confirmados,
prováveis e ambíguos e a quantidade de candidatos em cada classe de histórico.

#### Scenario: Acompanhar a revisão
- GIVEN que pendências foram resolvidas em `vinculos.csv`
- WHEN o pipeline é executado de novo
- THEN o resumo mostra menos prováveis e ambíguos na UF correspondente
