# Proposal: Atuação na Câmara dos Deputados

## Why

A pergunta central da ideia original é "o que essa pessoa já fez?". Para quem já foi
deputado federal, a Câmara publica em dados abertos o que foi apresentado, sobre quais
temas e em quais frentes parlamentares a pessoa atuou. Muitos candidatos de 2026 a
deputado federal, senador e governador passaram pela Câmara entre 2015 e 2026.

## What Changes

- Coleta dos deputados das legislaturas 55, 56 e 57 (2015 a 2027), com dados de
  identificação para vínculo.
- Vínculo entre candidatos de 2026 e deputados, com as mesmas regras e a mesma revisão
  humana da change 01, e correções em `data/manual/vinculos_camara.csv`.
- Coleta das proposições de autoria dos tipos configurados (PL, PLP e PEC), com temas,
  separando autoria principal de coautoria quando o dado permitir.
- Coleta das frentes parlamentares de cada deputado.
- Nova seção "Na Câmara dos Deputados" na página do candidato, com mandatos, contagens
  explicadas, temas mais frequentes, proposições mais recentes com link, frentes e link
  para o perfil oficial.
- Filtro opcional "Já foi deputado(a) federal" nas listas.
- Atualização da página de metodologia.
- Comando `colinha camara`.

Fora do escopo (fase 2): votações nominais, presença, cota parlamentar, relatorias,
Senado e assembleias estaduais.

## Capabilities

### New Capabilities
- `atuacao-camara`: coleta, vínculo, agregação e exibição da atuação de ex-deputados e
  deputados federais.

### Modified Capabilities
- Nenhuma. A seção nova da página do candidato é especificada dentro de
  `atuacao-camara`.

## Impact

- Código novo: `src/colinha/camara/` e um template parcial do site.
- Detalhe do candidato ganha o objeto opcional `camara`.
- Dependência externa: API e arquivos da Câmara. O cache em `data/raw/camara/` permite
  gerar o site mesmo se a API ficar fora do ar na semana da eleição.
