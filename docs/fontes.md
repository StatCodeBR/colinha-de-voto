# Fontes de dados

Só estas fontes são usadas. Qualquer fonte nova precisa entrar aqui antes de ser usada no
código. Itens marcados com **(confirmar)** ainda não foram checados no arquivo real. A parte do
TSE foi conferida nos arquivos reais em 27 e 28/09/2026.

## TSE — Portal de Dados Abertos

- Portal: https://dadosabertos.tse.jus.br
- Candidatos 2026: https://dadosabertos.tse.jus.br/dataset/candidatos-2026
  (candidatos, bens, coligações, vagas, motivo da cassação, redes sociais, fotos e
  proposta de governo)
- URLs no CDN, conferidas em 27 e 28/09/2026 (`CDN` = `https://cdn.tse.jus.br/estatistica/sead/odsele`):

| Arquivo | URL | Anos usados |
|---|---|---|
| Candidaturas | `{CDN}/consulta_cand/consulta_cand_{ano}.zip` | eleição e histórico |
| Complementar | `{CDN}/consulta_cand_complementar/consulta_cand_complementar_{ano}.zip` | eleição |
| Bens | `{CDN}/bem_candidato/bem_candidato_{ano}.zip` | eleição |
| Redes sociais | `{CDN}/consulta_cand/rede_social_candidato_{ano}.zip` | eleição |
| Fotos (não usadas ainda) | `https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes{ano}/fotos/foto_cand{ano}_{UF}_div.zip` | eleição |

- Cada zip traz um CSV por UF, um `_BR` (presidente e vice) e um consolidado `_BRASIL`,
  além de `leiame.pdf`. Nos anos municipais não há `_BR`. O pipeline lê os CSVs por UF e
  o `_BR` e ignora o `_BRASIL`, que repete as mesmas linhas.
- O arquivo de 2026 muda todo dia (o `DT_GERACAO` acompanha): baixar de novo com
  `--forcar` para atualizar.
- **Acesso:** o CDN devolve 403 para qualquer `HEAD` e para o `curl` com User-Agent
  padrão. `GET` com o User-Agent do projeto (httpx) funciona. Não usar `HEAD` para checar
  se um arquivo existe; usar `GET` com `Range: bytes=0-10`. Arquivo inexistente devolve 404.

### Formato

- CSV separado por `;`, codificação `latin-1`, valores entre aspas.
- Uma linha por candidatura e por turno: quem foi ao 2º turno aparece duas vezes com o
  mesmo `SQ_CANDIDATO`. `SQ_CANDIDATO` identifica a candidatura naquele ano, não a pessoa.
- Candidatos a presidente aparecem com `SG_UF` = `BR`.
- Os arquivos incluem candidaturas de eleições suplementares (`NM_TIPO_ELEICAO` =
  `ELEIÇÃO SUPLEMENTAR`), por exemplo 275 linhas em 2024.

### Layouts por ano

2016 ainda está no layout antigo (tudo num arquivo só). Os outros anos, inclusive 2014,
foram republicados no layout novo, em que várias colunas saíram do `consulta_cand` e
foram para o `consulta_cand_complementar`:

| Coluna | 2016 | demais anos | Onde está no layout novo |
|---|---|---|---|
| `DS_DETALHE_SITUACAO_CAND` | sim | não | complementar (vem `#NE` em 2026) |
| `ST_REELEICAO` | sim | não | complementar (vem `#NE` em 2026) |
| `ST_DECLARAR_BENS` | sim | não | complementar |
| `NR_IDADE_DATA_POSSE` | sim | não | complementar |
| Situação de julgamento | parcial | não | complementar: `DS_SITUACAO_JULGAMENTO`, `DS_SITUACAO_JULGAMENTO_PLEITO` |
| E-mail | `NM_EMAIL` | `DS_EMAIL` | (nunca lido) |

`DS_SITUACAO_CANDIDATURA` vem `#NE` em todas as linhas de 2026 e 2024. Nos outros anos
traz `APTO`, `INAPTO` e, raramente, `CADASTRADO`.

### Marcadores de nulo encontrados

| Marcador | Onde aparece |
|---|---|
| `#NULO` (sem `#` final) | layout novo (2020, 2022, 2024, 2026), ex.: `DS_SIT_TOT_TURNO` |
| `#NULO#` | 2014, 2016, 2018 |
| `#NE` | `DS_SITUACAO_CANDIDATURA` (2024, 2026), campos do complementar |
| `-1`, `-3` | códigos (`CD_*`) e alguns valores numéricos |
| `-4` | dado ocultado: CPF e título de candidaturas com sigilo; todo o CPF de 2024 |
| vazio | `DT_NASCIMENTO` nas mesmas linhas com `-4` |
| `NÃO DIVULGÁVEL` / `Não divulgável` | gênero, cor/raça, e-mail, `ST_*` das candidaturas com sigilo |

`NÃO INFORMADO` em `DS_COR_RACA` é valor do próprio TSE (o candidato não informou) e
não é tratado como marcador.

### Situação de julgamento em 2026 (complementar, 28/09/2026)

`DS_SITUACAO_JULGAMENTO_PLEITO` é a decisão mais recente; quando vem `#NULO`, a
candidatura não foi inserida na urna (`ST_CANDIDATO_INSERIDO_URNA` = `NÃO`) e vale
`DS_SITUACAO_JULGAMENTO`. Valores encontrados: `DEFERIDO`, `DEFERIDO COM RECURSO`,
`DEFERIDO EM PRAZO RECURSAL OU COM RECURSO`, `INDEFERIDO EM PRAZO RECURSAL OU COM
RECURSO`, `PENDENTE DE JULGAMENTO`, `PEDIDO NÃO CONHECIDO EM PRAZO RECURSAL OU COM
RECURSO`, `INDEFERIDO`, `PEDIDO NÃO CONHECIDO`, `RENÚNCIA`, `CANCELADO`, `FALECIMENTO`.

### Cargos (`DS_CARGO`)

- Gerais (2014, 2018, 2022, 2026): `PRESIDENTE`, `VICE-PRESIDENTE`, `GOVERNADOR`,
  `VICE-GOVERNADOR`, `SENADOR`, `1º SUPLENTE`, `2º SUPLENTE`, `DEPUTADO FEDERAL`,
  `DEPUTADO ESTADUAL`, `DEPUTADO DISTRITAL`. A grafia bate com o `config.toml`.
- Municipais (2016, 2020, 2024): `PREFEITO`, `VICE-PREFEITO`, `VEREADOR`.

### Resultado (`DS_SIT_TOT_TURNO`)

Valores em todos os anos: `ELEITO`, `ELEITO POR QP`, `ELEITO POR MÉDIA`, `SUPLENTE`,
`NÃO ELEITO`, `2º TURNO` e nulo (`#NULO` ou `#NULO#`). Vêm com acento (`MÉDIA`, `NÃO`);
o mapeamento do vínculo (change 01, D6) precisa normalizar antes de comparar.

### CPF e data de nascimento

Preenchimento conferido em 28/09/2026, todas as UFs:

| Ano | CPF preenchido | `DT_NASCIMENTO` preenchida |
|---|---|---|
| 2026 | 99,99% (3 com `-4`) | 99,99% |
| 2024 | **0%** (todo `-4`) | 99,99% |
| 2022 | 99,9% | 99,9% |
| 2020 | 99,95% | 99,95% |
| 2018 | 99,6% | 99,6% |
| 2016 | 99,98% | 99,98% |
| 2014 | 99,9% | 100% |

- O CPF só está oculto em 2024. Nos outros anos, inclusive 2026, está preenchido. O
  vínculo pode usar CPF para 2014 a 2022 e depende de nome + nascimento só para 2024.
- `NR_TITULO_ELEITORAL_CANDIDATO` está preenchido em quase todos os anos e o e-mail
  aparece preenchido em 2014. O pipeline nunca lê essas colunas.

### Bens (2026)

- 77.272 bens de 13.912 candidaturas: bate exatamente com `ST_DECLARAR_BENS` = `S` do
  complementar. Quem tem `N` não aparece no arquivo de bens.
- `VR_BEM_CANDIDATO` com vírgula decimal (`150000,00`), sem separador de milhar.
- 266 bens com valor zero e 2 com valor negativo. A soma usa os valores como o TSE
  publica.

### Redes sociais (2026)

- 62.912 links de 18.528 candidaturas. Colunas: `AA_ELEICAO` (não `ANO_ELEICAO`),
  `SQ_CANDIDATO`, `NR_ORDEM_REDE_SOCIAL`, `DS_URL`.
- 43.547 links não começam com `http://` ou `https://` (ex.: `instagram.com/...`). O site
  (change 02) só pode gerar link clicável para `http(s)`; o resto aparece como texto ou é
  normalizado com `https://` se for um domínio.

## Câmara dos Deputados — Dados Abertos

- API v2: https://dadosabertos.camara.leg.br/api/v2 (documentação Swagger no portal)
- Endpoints previstos: `/deputados?idLegislatura=`, `/deputados/{id}`,
  `/deputados/{id}/frentes`, `/proposicoes?idDeputadoAutor=`, `/proposicoes/{id}/temas`.
- Atenção: `/proposicoes` sem filtro de data tende a devolver só um período recente;
  sempre passar datas ou ano explicitamente **(confirmar)**.
- Arquivos em massa por ano (proposições, autores, temas) no portal, se existirem, são
  preferíveis a milhares de chamadas à API **(confirmar URLs e colunas)**.
- Verificar se `/deputados/{id}` traz CPF e data de nascimento **(confirmar)**.

## Descobertas durante a implementação

Registre aqui, com data, tudo que divergir do esperado: colunas ausentes, formatos,
URLs, contagens por UF, tempo de processamento.

| Data | Fonte | Descoberta | Impacto |
|---|---|---|---|
| 27/09/2026 | TSE CDN | `HEAD` e `curl` padrão recebem 403 da Akamai; `GET` com httpx funciona | usar só `GET` |
| 28/09/2026 | consulta_cand | Layout novo sem `ST_REELEICAO`, `ST_DECLARAR_BENS` e `DS_DETALHE_SITUACAO_CAND`; `DS_SITUACAO_CANDIDATURA` vem `#NE` em 2026 | baixar o complementar; `apto` vem da situação de julgamento (design D9) |
| 28/09/2026 | complementar | `ST_REELEICAO` vem `#NE` em 2026 | `busca_reeleicao` fica nulo; decidir na seção 6 se deriva da trajetória |
| 28/09/2026 | consulta_cand | CPF preenchido em todos os anos menos 2024 | vínculo por CPF cobre 2014 a 2022 |
| 28/09/2026 | todos | Pipeline de normalização, todas as UFs e 7 anos: 54 s, pico de 1,2 GB | dentro do previsto; sem necessidade de DuckDB/polars |
| 28/09/2026 | vínculo | Regra nome + nascimento aplicada a 2022 e 2020 sem CPF: 100% de precisão contra o CPF, 94% de cobertura | sustenta os vínculos de 2024 |
| 28/09/2026 | vínculo | CPF igual com nomes sem nenhuma palavra em comum: 10 pares; 9 com mesmo nascimento (mudança de nome civil) e 1 com nascimento 6 anos diferente (CPF digitado errado) | salvaguarda `cpf_divergente` (design D4); trajetória nunca mostra nome anterior |
| 28/09/2026 | vínculo | Todas as UFs: 31.748 confirmados, 139 ambíguos, 53 prováveis; 169 pessoas com duas candidaturas confirmadas no mesmo ano (substituição, suplementar) | 192 linhas em `revisao_vinculos.csv` |
| 28/09/2026 | redes sociais | URLs publicadas em MAIÚSCULAS; o caminho de URL diferencia maiúsculas, então alguns links (ex.: compartilhamento do Facebook) podem não abrir | change 02: exibir sem prometer que o link funciona; domínio pode ir para minúsculas |
| 28/09/2026 | redes sociais | Cerca de 10 candidaturas cadastraram e-mail como caminho de rede (ex.: `facebook.com/NOME@GMAIL.COM`) | links com e-mail não são publicados; `just privacidade` procura e-mails |
| 28/09/2026 | redes sociais | Uma candidatura com 912 links (máx.); a seguinte tem 184 | change 02: limite de exibição igual para todos |
| 28/09/2026 | DivulgaCandContas | API devolve 403 para acesso automatizado | tarefa 6.5 feita por pessoa no navegador |
| 28/09/2026 | saídas | Todas as UFs: 46 s; 20.093 JSON (84 MB); maior `indice.json` SP 490 KB (49 KB gzip); detalhe típico ~3 KB, maior 49 KB (912 links) | dentro do orçamento do design 02 (D8) |
| 28/09/2026 | saídas RR | Dep. estadual 250 (233 aptas), dep. federal 108 (102), governador 5 (5), senador 13 (13) | comparar com o DivulgaCandContas (6.5) |
| 28/09/2026 | DivulgaCandContas (conferência humana, RR) | Governador 5, senador 13, dep. federal 108, dep. estadual 250, vice-governador 6, 1º suplente 15, 2º suplente 16; total 413. Bate com a pipeline (376 titulares + 37 vices e suplentes) | tarefa 6.5 da change 01 concluída |
| 28/09/2026 | consulta_cand 2026 | 20.987 candidaturas, 20.063 nos cargos titulares; 18.984 aptas e 1.079 inaptas | página por candidatura: ~20 mil arquivos |
