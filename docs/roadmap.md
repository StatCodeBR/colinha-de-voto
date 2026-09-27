# Roadmap

Cada item abaixo vira uma change própria (`/opsx:propose`) quando chegar a vez.

## Agora (eleição de 2026)

1. `01-add-pipeline-tse`: dados de 2026 e trajetória 2014–2024.
2. `02-add-site-colinha`: site, página do candidato e colinha.
3. `03-add-dados-camara`: atuação de quem foi deputado federal (2015–2026).
4. Até 4/out: rodar `/atualizar-dados` todo dia e republicar.

## Fase 2 (depois da eleição, antes de 2028)

- Votos por candidatura em cada eleição passada (arquivos de votação nominal do TSE).
- Evolução do patrimônio declarado entre eleições.
- Senado: projetos, relatorias e votações de senadores (API de dados abertos do Senado).
- Assembleia do estado da equipe: a ALESP, por exemplo, publica autores e proposituras
  em XML no seu portal de dados abertos. Uma UF por change.
- Votações nominais selecionadas na Câmara, com critério de escolha público e neutro.
- Presença em plenário e uso da cota parlamentar, sempre com contexto.
- Fotos dos candidatos, se não entrarem no MVP.

## Fase 3 (eleições municipais de 2028)

- Mesmo pipeline para prefeito e vereador (o formato do TSE é o mesmo).
- Vereadores: muitas câmaras municipais usam o SAPL (Interlegis), que tem API. Mapear
  cobertura antes de prometer qualquer coisa.
- Prefeitos: começar só com trajetória eleitoral.
- Escolha por município em vez de UF.

## Divulgação da StatCode

- Post ou vídeo "como construímos o Colinha do Voto com dados abertos".
- Aula prática usando a API da Câmara e os arquivos do TSE.
- Página de projetos abertos da StatCode reunindo A Caminho das Pedras e o Colinha.
