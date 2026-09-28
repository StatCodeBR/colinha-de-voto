## Why

Quem chega por um link do WhatsApp cai direto numa página de candidato e não tem como
subir para a lista do cargo ou para o estado, a não ser pelo nome do site no topo, que
leva à página inicial. No celular, o botão "voltar" do navegador também não ajuda: na
primeira página aberta ele fecha o site ou volta para o WhatsApp.

## What Changes

- Toda subpágina (UF, lista por cargo, candidato, colinha e metodologia) ganha, no topo
  do conteúdo, um link "Voltar" que leva à página de cima na hierarquia do site, com o
  destino escrito por extenso (ex.: "Voltar para deputado federal em Roraima").
- O link funciona sem JavaScript e não depende do histórico do navegador.
- Nas páginas de presidente, que servem a todas as UFs, o destino é a lista de
  presidente da última UF visitada; sem UF conhecida, a escolha de estado.
- Na lista por cargo, o link "Voltar" substitui a linha de navegação atual (link para a
  UF acima do título).

Fora do escopo: trilha completa de navegação ("Início > Roraima > Deputado federal"),
porque o site tem só três níveis e uma trilha ocupa espaço no celular; e botões que
usam o histórico do navegador, pelo motivo acima.

## Capabilities

### New Capabilities

- Nenhuma.

### Modified Capabilities

- `site-publico`: novo requisito de navegação de volta nas subpáginas. A capacidade
  ainda está na change `02-add-site-colinha` (não arquivada); esta change deve ser
  arquivada depois dela.

## Impact

- Templates em `src/colinha/templates/` (base e páginas) e o cálculo do destino em
  `src/colinha/site/__init__.py`.
- `src/colinha/static/js/colinha.js` (destino das páginas de presidente pela última UF).
- CSS: estilo do link, com área de toque de pelo menos 44 px.
- Nenhuma mudança na pipeline de dados.
