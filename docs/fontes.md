# Fontes de dados

Só estas fontes são usadas. Qualquer fonte nova precisa entrar aqui antes de ser usada no
código. Itens marcados com **(confirmar)** ainda não foram checados no arquivo real.

## TSE — Portal de Dados Abertos

- Portal: https://dadosabertos.tse.jus.br
- Candidatos 2026: https://dadosabertos.tse.jus.br/dataset/candidatos-2026
  (candidatos, bens, coligações, vagas, motivo da cassação, redes sociais, fotos e
  proposta de governo)
- Download direto de candidaturas:
  `https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_{ano}.zip`
  Cada zip traz um CSV por UF e um consolidado `consulta_cand_{ano}_BRASIL.csv`.
- Bens declarados, redes sociais e fotos: URLs do CDN **(confirmar no portal)**.

### Formato conhecido

- CSV separado por `;`, codificação `latin-1`, valores entre aspas.
- Marcadores de nulo: `#NULO#`, `#NE#`, `#NE`, `-1`, `-3`, `-4` **(confirmar quais
  aparecem em cada coluna)**.
- Uma linha por candidatura e por turno: quem foi ao 2º turno aparece duas vezes com o
  mesmo `SQ_CANDIDATO`.
- `SQ_CANDIDATO` identifica a candidatura naquele ano, não a pessoa.
- Candidatos a presidente aparecem com UF `BR` **(confirmar)**.
- Colunas principais: `ANO_ELEICAO`, `NR_TURNO`, `SG_UF`, `SG_UE`, `NM_UE`, `DS_CARGO`,
  `SQ_CANDIDATO`, `NR_CANDIDATO`, `NM_CANDIDATO`, `NM_URNA_CANDIDATO`,
  `NM_SOCIAL_CANDIDATO`, `NR_CPF_CANDIDATO`, `DT_NASCIMENTO`, `SG_PARTIDO`, `DS_GENERO`,
  `DS_COR_RACA`, `DS_GRAU_INSTRUCAO`, `DS_OCUPACAO`, `DS_SITUACAO_CANDIDATURA`,
  `DS_DETALHE_SITUACAO_CAND`, `DS_SIT_TOT_TURNO`, `ST_REELEICAO`. Os nomes variam entre
  anos: validar a lista de cada ano e registrar diferenças abaixo.

### CPF e identificação entre eleições

- Em 2024 o TSE passou a ocultar o CPF dos candidatos no DivulgaCandContas e nos dados
  abertos, inclusive nos arquivos de eleições anteriores (Resolução nº 23.729/2024).
- Em janeiro de 2026, a minuta de resolução para as eleições de 2026 retirou o CPF da
  lista de documentos sigilosos. **(confirmar se `consulta_cand_2026` traz o CPF
  preenchido)**
- Consequência: o vínculo com anos anteriores depende de nome + data de nascimento.
  **(confirmar se `DT_NASCIMENTO` está presente em todos os anos da janela)**

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
| | | | |
