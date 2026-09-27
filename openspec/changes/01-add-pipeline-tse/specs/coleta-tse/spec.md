# Delta for coleta-tse

## ADDED Requirements

### Requirement: Download com cache e manifesto
O pipeline MUST baixar do CDN do TSE os arquivos de candidaturas do ano da eleição e dos
anos de histórico configurados, além de bens declarados e redes sociais do ano da
eleição, registrando cada arquivo em `data/raw/manifest.json` com URL, data e hora de
extração, sha256 e tamanho.

#### Scenario: Primeiro download
- GIVEN que `data/raw/` está vazio
- WHEN o usuário executa `colinha baixar`
- THEN todos os arquivos configurados são baixados
- AND cada um aparece no manifesto com `baixado_em` e sha256

#### Scenario: Arquivo já em cache
- GIVEN que um arquivo já existe em `data/raw/` e está no manifesto
- WHEN o usuário executa `colinha baixar` sem `--forcar`
- THEN o arquivo não é baixado de novo

#### Scenario: Falha de rede no meio do download
- GIVEN que a conexão cai durante um download
- WHEN as tentativas de repetição se esgotam
- THEN nenhum arquivo parcial fica com o nome final
- AND o comando termina com erro dizendo qual URL falhou

### Requirement: Leitura robusta dos CSVs do TSE
O pipeline MUST ler os CSVs com separador `;`, codificação `latin-1` e todas as colunas
como texto, convertendo os marcadores de nulo do TSE em nulo e validando a presença das
colunas esperadas para cada ano.

#### Scenario: Marcador de nulo
- GIVEN uma célula com `#NULO#`, `#NE#` ou um código negativo usado como nulo
- WHEN o arquivo é lido
- THEN o valor resultante é nulo, e não o texto do marcador

#### Scenario: Identificadores com zeros à esquerda
- GIVEN um identificador numérico que começa com zero
- WHEN o arquivo é lido
- THEN o valor é preservado como texto, com os zeros

#### Scenario: Coluna esperada ausente
- GIVEN um arquivo de um ano sem uma coluna obrigatória
- WHEN o arquivo é lido
- THEN o pipeline falha com uma mensagem que nomeia o ano, o arquivo e a coluna

### Requirement: Uma linha por candidatura
O pipeline MUST produzir uma única linha por candidatura (`ano`, `sq_candidato`),
mantendo o resultado do último turno disputado.

#### Scenario: Candidato que foi ao 2º turno
- GIVEN duas linhas com o mesmo `sq_candidato`, uma do 1º e outra do 2º turno
- WHEN a tabela é normalizada
- THEN resta uma linha, com o resultado do 2º turno

### Requirement: Candidaturas exibíveis
O pipeline MUST incluir nas saídas públicas do ano da eleição apenas os cargos titulares
configurados em `config.toml`, mantendo a situação da candidatura para que o site possa
distinguir candidaturas aptas das demais.

#### Scenario: Vice e suplentes
- GIVEN candidaturas a vice-governador e a suplente de senador
- WHEN as saídas públicas são geradas
- THEN elas não aparecem no índice da UF

#### Scenario: Candidatura inapta
- GIVEN uma candidatura com situação inapta
- WHEN as saídas públicas são geradas
- THEN ela aparece no índice com `apto: false`

### Requirement: Proteção de dados pessoais nas saídas
O pipeline MUST NOT gravar CPF, título de eleitor ou e-mail de candidatos em
`data/processed/` nem em qualquer arquivo publicado. Saídas públicas SHALL ser montadas a
partir de uma allowlist explícita de campos, e identificadores públicos MUST NOT ser
derivados de CPF.

#### Scenario: CPF usado no vínculo
- GIVEN candidaturas com CPF preenchido em `data/interim/`
- WHEN as saídas públicas são geradas
- THEN nenhum CPF de entrada aparece em nenhum arquivo de `data/processed/`

#### Scenario: Coluna nova no TSE
- GIVEN que o TSE acrescentou uma coluna nova ao arquivo
- WHEN as saídas públicas são geradas
- THEN a coluna nova não aparece nas saídas, porque não está na allowlist

### Requirement: Nome exibido respeita o nome social
O pipeline MUST usar o nome social como nome exibido quando ele estiver preenchido, e
nesse caso MUST NOT incluir o nome civil em nenhuma saída pública.

#### Scenario: Candidata com nome social
- GIVEN uma candidatura com `NM_SOCIAL_CANDIDATO` preenchido
- WHEN o detalhe do candidato é gerado
- THEN o nome exibido é o nome social
- AND o nome civil não aparece no arquivo

#### Scenario: Sem nome social
- GIVEN uma candidatura sem nome social
- WHEN o detalhe do candidato é gerado
- THEN o nome exibido é o nome civil

### Requirement: Bens declarados e redes sociais
O pipeline MUST calcular o total de bens declarados por candidatura do ano da eleição e
listar as redes sociais informadas ao TSE, distinguindo "não declarou bens" de "declarou
bens com valor zero".

#### Scenario: Candidato que não declarou bens
- GIVEN uma candidatura sem nenhum bem no arquivo de bens
- WHEN o detalhe é gerado
- THEN `bens_total` é nulo e `declarou_bens` reflete a informação do TSE

#### Scenario: Candidato com vários bens
- GIVEN uma candidatura com três bens declarados
- WHEN o detalhe é gerado
- THEN `bens_total` é a soma dos três valores

### Requirement: Saídas para o site
O pipeline MUST gerar, por UF, um índice leve para listas e filtros e um arquivo de
detalhe por candidato, além de um manifesto de fontes com datas de extração e um resumo
com contagens por UF.

#### Scenario: Execução para uma UF
- WHEN o usuário executa `colinha processar --uf RR`
- THEN `data/processed/RR/indice.json` e os detalhes dos candidatos de RR são gerados
- AND o manifesto e o resumo são atualizados

#### Scenario: Candidatos a presidente
- WHEN as saídas são geradas
- THEN os candidatos a presidente ficam em um índice nacional (`BR`), disponível para
  todas as UFs
