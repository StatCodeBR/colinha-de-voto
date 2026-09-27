# Proposal: Site público e colinha do eleitor

## Why

Os dados da change 01 só ajudam alguém se chegarem ao eleitor de um jeito simples,
no celular, a partir de um link no WhatsApp. O eleitor quer responder três perguntas:
quem são as opções, o que cada um já fez e em quem vou votar. A última pergunta termina
na urna, onde o celular não pode entrar: por isso a colinha impressa ou anotada.

## What Changes

- Gerador de site estático em Python (Jinja2) que lê `data/processed/` e escreve
  `site/dist/`. Comando `colinha site`.
- Página inicial com escolha da UF.
- Listas por UF e cargo, estáticas (funcionam sem JavaScript) e enriquecidas com busca
  e filtros em JavaScript puro: nome, número, partido, gênero, histórico e reeleição.
- Página de cada candidato em `/{uf}/{numero}/`, com identificação, trajetória
  eleitoral, dados declarados ao TSE, fontes com data e link para reportar erro.
- Colinha: o eleitor adiciona candidatos, vê tudo na ordem da urna e imprime. Os dados
  ficam só no navegador.
- Página de metodologia: fontes, datas, método de vínculo, cobertura, limitações e
  código.
- Metadados de compartilhamento (título e descrição na prévia do WhatsApp) e botão de
  compartilhar.
- Identidade visual própria e neutra, com o número em caixinhas como elemento marcante.
- Publicação em subdomínio da StatCode, no mesmo provedor da A Caminho das Pedras.

Fora do escopo: dados da Câmara (change 03), fotos (tarefa opcional), voto de legenda
na colinha, comparação lado a lado entre candidatos.

## Capabilities

### New Capabilities
- `site-publico`: navegação, listas, busca e filtros, página do candidato, metodologia,
  compartilhamento, acessibilidade e regras de neutralidade na interface.
- `colinha`: montar, revisar e imprimir a colinha, com privacidade local.

### Modified Capabilities
- Nenhuma.

## Impact

- Código novo: `src/colinha/site/`, `src/colinha/templates/`, `src/colinha/static/`.
- Dependência: jinja2.
- Consome os JSON da change 01; não altera o pipeline.
- Hospedagem: milhares de arquivos HTML (um por candidato). Verificar limites de
  arquivos por deploy no provedor da StatCode.
