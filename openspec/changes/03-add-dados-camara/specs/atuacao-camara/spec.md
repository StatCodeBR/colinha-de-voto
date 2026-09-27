# Delta for atuacao-camara

## ADDED Requirements

### Requirement: Coleta de deputados
O sistema MUST coletar os deputados das legislaturas configuradas, com identificador da
Câmara, nome civil, data de nascimento, UF, partido, legislaturas exercidas e, se a
Câmara fornecer, CPF, guardando as respostas em cache em `data/raw/camara/`.

#### Scenario: Coleta com cache
- GIVEN que os deputados já foram coletados
- WHEN o usuário executa `colinha camara` sem `--forcar`
- THEN nenhuma nova requisição de deputados é feita

#### Scenario: API fora do ar com cache existente
- GIVEN que a API não responde
- AND existe cache completo
- WHEN o usuário executa `colinha site`
- THEN o site é gerado com os dados do cache e a data da extração original

### Requirement: Vínculo entre candidato e deputado
O sistema SHALL confirmar o vínculo entre uma candidatura de 2026 e um deputado apenas
por CPF igual ou por nome civil normalizado e data de nascimento iguais e únicos dos dois
lados. Os demais casos MUST ir para `revisao_vinculos_camara.csv`, e as decisões de
`data/manual/vinculos_camara.csv` MUST prevalecer.

#### Scenario: Deputado com mesmo nome e nascimento
- GIVEN um candidato a senador em 2026 e um deputado da legislatura 57 com mesmo nome
  civil normalizado e mesma data de nascimento, sem outro deputado com a mesma chave
- WHEN o vínculo é calculado
- THEN o vínculo é confirmado

#### Scenario: Nome igual sem data de nascimento
- GIVEN um deputado sem data de nascimento disponível
- WHEN o vínculo é calculado
- THEN o caso vai para revisão e não aparece no site

### Requirement: Proposições de autoria
O sistema MUST reunir, para cada deputado vinculado, as proposições dos tipos
configurados apresentadas nas legislaturas configuradas, com tipo, número, ano, ementa,
data de apresentação, link oficial e temas, e SHALL separar autoria principal de
coautoria quando o dado permitir.

#### Scenario: Tipos fora da lista
- GIVEN um deputado autor de um requerimento e de um PL
- WHEN as proposições são agregadas
- THEN só o PL é contado

#### Scenario: Coautoria
- GIVEN um PL em que o deputado é o quinto signatário
- WHEN as proposições são agregadas
- THEN o PL conta como coautoria, não como autoria principal

### Requirement: Frentes parlamentares
O sistema MUST reunir as frentes parlamentares de que cada deputado vinculado participou
nas legislaturas disponíveis.

#### Scenario: Deputado em várias frentes
- GIVEN um deputado que participou de 30 frentes
- WHEN a seção é exibida
- THEN aparece a quantidade e a lista recolhida, que abre ao tocar

### Requirement: Seção "Na Câmara dos Deputados"
A página de um candidato vinculado a um deputado MUST exibir, depois da trajetória
eleitoral: legislaturas e períodos de mandato, contagens por tipo com a distinção entre
autoria principal e coautoria, os cinco temas mais frequentes, as dez proposições mais
recentes com ementa e link oficial, as frentes, o link para o perfil oficial na Câmara,
um texto explicando que quantidade de projetos não mede a qualidade de um mandato, e a
fonte com data de extração.

#### Scenario: Candidato que nunca foi deputado federal
- GIVEN um candidato sem vínculo com a Câmara
- WHEN a página é gerada
- THEN a seção "Na Câmara dos Deputados" não aparece

#### Scenario: Deputado sem proposições dos tipos configurados
- GIVEN um deputado vinculado sem nenhum PL, PLP ou PEC
- WHEN a página é gerada
- THEN a seção aparece com os mandatos e a frase "Nenhum projeto de lei ou proposta de
  emenda à Constituição encontrado neste período", sem exibir um zero isolado

#### Scenario: Autoria não separável
- GIVEN que a fonte não permite distinguir autoria principal de coautoria
- WHEN a página é gerada
- THEN as contagens aparecem como "autoria ou coautoria"
- AND a página explica por quê

### Requirement: Sem comparação entre deputados
O sistema MUST NOT exibir rankings, médias, percentis ou qualquer comparação da atuação
de um deputado com a de outros.

#### Scenario: Página de deputado com muitos projetos
- GIVEN um deputado com o maior número de projetos da UF
- WHEN a página é gerada
- THEN nenhum texto ou elemento visual indica essa posição

### Requirement: Filtro de passagem pela Câmara
As listas do site SHALL oferecer o filtro "Já foi deputado(a) federal", baseado apenas
em vínculos confirmados.

#### Scenario: Filtrar ex-deputados
- WHEN o eleitor ativa o filtro na lista de senadores de uma UF
- THEN só aparecem candidatos com vínculo confirmado com a Câmara
