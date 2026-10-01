## Why

O celular não entra na cabine de votação, então a colinha precisa ir no papel. Hoje o
botão "Imprimir colinha" usa a impressão do navegador e ocupa a folha inteira: não cabe
no bolso sem dobrar várias vezes, e no celular a impressão é difícil de achar (no
navegador interno do WhatsApp, por onde chega a maior parte do público, ela nem existe).
O eleitor precisa de um arquivo que ele possa baixar, mandar para quem tem impressora ou
levar a uma copiadora, com a colinha pequena num canto da folha A4, pronta para recortar
e guardar no bolso ou na carteira.

## What Changes

- Novo botão **"Baixar colinha em PDF"** na página `/colinha/`. Ele gera, no próprio
  navegador, um PDF A4 com a colinha em formato de bolso (cerca de 6,3 × 8,8 cm, tamanho
  de uma carta de baralho) no canto superior esquerdo, com contorno tracejado e a
  indicação "recorte aqui". O resto da folha fica em branco.
- O cartão traz, na ordem da urna, o cargo, o número em quadradinhos grandes, o nome de
  urna e a sigla do partido. Vaga sem escolha sai com os quadradinhos vazios, para
  preencher à mão.
- O botão "Imprimir colinha" passa a imprimir o mesmo cartão de bolso, no mesmo lugar
  da folha, para que imprimir e baixar deem o mesmo resultado.
- O PDF é montado em JavaScript puro, sem biblioteca e sem enviar nada: o servidor não
  recebe nenhuma requisição ao gerar o arquivo.
- Quantidade de dígitos por cargo passa a vir do `config.toml`, para desenhar os
  quadradinhos vazios.

Fora do escopo:
- Várias cópias do cartão na mesma folha, ou cartões de várias pessoas da família:
  útil, mas cada um monta a sua colinha no próprio celular; fica para depois, se pedirem.
- Escolher tamanho ou posição do cartão: um formato só evita confusão e erro de impressão.
- Imagem (PNG) para salvar na galeria: o celular não entra na cabine, então a imagem não
  resolve o problema.
- Gerar o PDF no servidor: exigiria enviar as escolhas do eleitor, o que a colinha
  promete não fazer.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `colinha`: novo requisito de colinha de bolso (PDF e impressão no mesmo formato). A
  capacidade ainda está na change `02-add-site-colinha` (não arquivada), então o delta
  entra como requisito adicionado; esta change deve ser arquivada depois da 02. O
  requisito "Impressão" da 02 continua valendo (o cartão cabe com folga em meia folha).

## Impact

- `src/colinha/static/js/`: novo `pdf-colinha.js` (montagem do PDF, função pura) e
  ajuste em `colinha.js` (botão e dados do cartão).
- `src/colinha/templates/colinha.html`: botão novo e texto de ajuda; o cartão de
  impressão é montado no HTML da página.
- `src/colinha/static/css/site.css`: bloco `@media print` refeito para o cartão.
- `config.toml` e `config.py`: dígitos por cargo.
- Testes: geração do PDF rodada com o Node do flake e conferida em Python (`pypdf` como
  dependência de desenvolvimento).
- Nenhuma mudança na pipeline de dados, no nginx nem na CSP.
