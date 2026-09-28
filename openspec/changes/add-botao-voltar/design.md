## Context

O site é estático, gerado em Python com Jinja2 (change 02, D1 a D3). Hoje só a lista por
cargo tem um link para cima (o nome da UF acima do título); as demais páginas só têm o
nome do site no cabeçalho, que leva à página inicial. As páginas de presidente
(`/br/{numero}/`) são únicas para todo o país, e a última UF visitada fica no
`localStorage` (`colinha:uf`), gravada pela colinha.

## Goals / Non-Goals

**Goals:**
- Destino do "Voltar" calculado na geração, em Python, junto com os outros textos da
  página, para ser testável e funcionar sem JavaScript.
- Um único componente, no template base, usado por todas as subpáginas.

**Non-Goals:**
- Trilha de navegação completa.
- Mudar o cabeçalho ou o rodapé.

## Decisions

### D1. Destino fixo pela hierarquia, não `history.back()`
Cada página recebe na geração o destino e o texto do link ("Voltar para deputado
federal em Roraima").

Alternativa considerada: botão com `history.back()`. Rejeitada porque quem chega pelo
WhatsApp não tem página anterior no site (o botão fecharia o site ou voltaria ao app),
não funciona sem JavaScript e, depois de vários filtros e páginas, leva a lugares
imprevisíveis.

### D2. Link (`<a>`), não `<button>`
É navegação para outra página: link é o elemento certo para teclado, leitor de tela e
"abrir em nova aba". Estilo discreto, com seta "←" decorativa (`aria-hidden`), texto
completo e área de toque de 44 px.

Alternativa considerada: botão com a cor de ação (verde da colinha). Rejeitada para
não competir com "Adicionar à colinha", que é a ação principal da página.

### D3. Presidente: destino estático para a página inicial, trocado por JavaScript
O HTML sai com destino "Voltar para a escolha de estado" (`/`). Se houver UF guardada
em `colinha:uf`, o `colinha.js`, que já lê essa chave, troca o destino para
`/{uf}/presidente/` e o texto para "Voltar para presidente em {UF}".

Alternativa considerada: gerar uma página de presidente por UF (`/{uf}/{numero}/`).
Rejeitada porque multiplica 14 páginas por 27 UFs e duplica o endereço compartilhado no
WhatsApp.

### D4. A lista por cargo troca a linha de navegação atual pelo "Voltar"
A linha `.migalha` com o nome da UF sai, para não haver dois links para o mesmo lugar.

## Risks / Trade-offs

- [Texto longo no celular, ex.: "Voltar para deputado distrital no Distrito Federal"]
  → quebra em duas linhas sem cortar; a área de toque acompanha.
- [Presidente com UF guardada de outra visita, antiga] → leva à lista de presidente
  daquela UF, que é igual em todas as UFs; o eleitor troca de estado pela página
  inicial.
