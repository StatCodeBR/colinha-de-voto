# Delta for site-publico

## ADDED Requirements

### Requirement: Escolha da UF
O site MUST permitir escolher a UF na página inicial e SHALL lembrar a última UF
escolhida no navegador, sem enviá-la a nenhum servidor.

#### Scenario: Primeira visita
- GIVEN um eleitor que nunca acessou o site
- WHEN ele abre a página inicial
- THEN vê uma frase curta explicando o site e a lista das 27 UFs

#### Scenario: Visita de retorno
- GIVEN um eleitor que escolheu SP antes
- WHEN ele abre a página inicial
- THEN vê um atalho para os candidatos de SP, além da lista completa

### Requirement: Listas por UF e cargo
O site MUST apresentar os candidatos da UF agrupados por cargo, na ordem da urna, com
nome de urna, número em caixinhas, partido e etiqueta de histórico. A ordem padrão SHALL
ser alfabética pelo nome de urna, e as listas MUST funcionar sem JavaScript.

#### Scenario: Lista sem JavaScript
- GIVEN um navegador com JavaScript desativado
- WHEN o eleitor abre `/sp/deputado-estadual/`
- THEN vê a lista completa em ordem alfabética, com links para cada candidato

#### Scenario: Candidatura inapta
- GIVEN uma candidatura com `apto: false`
- WHEN a lista é exibida com os filtros padrão
- THEN ela não aparece
- AND um filtro "Mostrar candidaturas que não estão aptas" permite vê-la, com a
  situação escrita por extenso

### Requirement: Busca e filtros
O site SHALL oferecer busca por nome, número ou partido, ignorando acentos e
maiúsculas, e filtros por gênero, partido, histórico (já foi eleito, já concorreu,
nenhuma candidatura encontrada) e busca de reeleição, mostrando a quantidade de
resultados.

#### Scenario: Busca sem acento
- GIVEN uma candidata chamada "Conceição"
- WHEN o eleitor digita "conceicao"
- THEN ela aparece nos resultados

#### Scenario: Filtro de gênero
- WHEN o eleitor filtra por candidatas mulheres
- THEN só aparecem candidaturas com gênero feminino declarado
- AND o contador mostra quantas são

#### Scenario: Nenhum resultado
- GIVEN filtros que não retornam ninguém
- WHEN a lista é atualizada
- THEN o site diz que não há candidatos com esses filtros e sugere qual filtro remover

### Requirement: Página do candidato
O site MUST gerar uma página estática por candidato com, nesta ordem: identificação
(cargo, UF, nome de urna, nome exibido, número em caixinhas, partido ou federação),
botão da colinha, trajetória eleitoral, dados declarados ao TSE e fontes. Todos os
candidatos SHALL usar o mesmo template, com as mesmas seções na mesma ordem.

#### Scenario: Dado não informado
- GIVEN um candidato sem grau de instrução informado
- WHEN a página é gerada
- THEN o campo mostra "Não informado"

#### Scenario: Bens não declarados
- GIVEN um candidato que não declarou bens
- WHEN a página é gerada
- THEN o campo mostra "Não declarou bens ao TSE", e não "R$ 0,00"

#### Scenario: Flexão de gênero
- GIVEN uma candidata eleita vereadora em 2020
- WHEN a trajetória é exibida
- THEN o texto diz "Vereadora" e "Eleita"

### Requirement: Trajetória com cobertura explícita
A seção de trajetória MUST sempre informar a janela de anos pesquisada e MUST NOT
afirmar que é a primeira candidatura da pessoa.

#### Scenario: Nenhum registro
- GIVEN um candidato com histórico `sem_registro`
- WHEN a página é gerada
- THEN a seção diz "Nenhuma candidatura encontrada de 2014 a 2024"

#### Scenario: Histórico em verificação
- GIVEN um candidato com histórico `em_verificacao`
- WHEN a página é gerada
- THEN a seção diz que o histórico está em verificação, sem listar os registros pendentes

#### Scenario: Confirmados e pendentes
- GIVEN um candidato com candidaturas confirmadas e registros em verificação
- WHEN a página é gerada
- THEN a trajetória lista só as confirmadas
- AND informa que outros registros possíveis estão em verificação

### Requirement: Fonte, data e reporte de erro
Cada seção de dados MUST mostrar a fonte e a data de extração, e cada página de
candidato SHALL ter um link "Encontrou um erro?" que abre um e-mail pré-preenchido com
UF, número e endereço da página.

#### Scenario: Seção de dados declarados
- WHEN a página do candidato é exibida
- THEN abaixo dos dados declarados aparece "Fonte: TSE, dados extraídos em" seguido da
  data do manifesto

### Requirement: Neutralidade na interface
O site MUST NOT exibir notas, rankings, destaques, adjetivos avaliativos, cores ou
logos de partido, nem ordenar candidatos por votos, tempo de carreira ou qualquer
critério além do alfabético por padrão.

#### Scenario: Candidatos de partidos diferentes
- GIVEN duas páginas de candidatos de partidos diferentes
- WHEN elas são comparadas
- THEN a estrutura, as cores e os textos fixos são idênticos

### Requirement: Metodologia pública
O site MUST ter uma página de metodologia com as fontes e datas de extração, o método
de vínculo entre eleições, a janela de cobertura, as limitações conhecidas, como
reportar erros e quem mantém o projeto.

#### Scenario: Eleitor quer saber de onde vem o dado
- WHEN o eleitor abre `/metodologia/`
- THEN encontra os links das fontes oficiais e a data da última atualização

### Requirement: Compartilhamento
Cada página de candidato MUST ter meta tags de prévia (título com nome de urna, número,
cargo e UF; descrição neutra) e um botão de compartilhar que usa o compartilhamento
nativo do celular, com link para o WhatsApp como alternativa.

#### Scenario: Link colado no WhatsApp
- GIVEN o link `/sp/12345/`
- WHEN ele é colado numa conversa
- THEN a prévia mostra o nome de urna, o número, o cargo e a UF

### Requirement: Acessibilidade e desempenho
O site MUST atender contraste WCAG AA, navegação completa por teclado, foco visível,
leitura correta por leitor de tela (o número em caixinhas é lido como número completo)
e `prefers-reduced-motion`. A página de candidato SHALL ficar abaixo de 60 KB
transferidos, sem contar fontes em cache.

#### Scenario: Leitor de tela no número
- GIVEN o número 12345 exibido em caixinhas
- WHEN um leitor de tela passa pelo elemento
- THEN ele lê "número 12345", uma única vez

### Requirement: Autoria e rodapé
Todas as páginas MUST ter rodapé com a autoria da StatCode (com link), as fontes de
dados e links para metodologia e reporte de erro, sem anúncios nem scripts de terceiros.

#### Scenario: Qualquer página
- WHEN qualquer página é exibida
- THEN o rodapé mostra "Feito pela StatCode com dados abertos do TSE" e os links
