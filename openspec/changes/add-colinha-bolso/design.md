## Context

A colinha (change 02) vive no `localStorage` e é desenhada por `static/js/colinha.js` na
página `/colinha/`: uma lista `.vagas` na ordem da urna, com o número em quadradinhos
(`.digito`). O botão "Imprimir colinha" chama `window.print()`, e o `@media print` do
`site.css` imprime a lista na folha inteira. O site é estático, com CSP restrita
(`default-src 'self'`), JavaScript puro e sem dependências. A maior parte do público
chega pelo WhatsApp e abre o site no navegador interno do app, onde não há impressão.

Em 2026 a colinha de uma UF tem seis vagas: deputado federal, deputado estadual (ou
distrital), senador (duas vagas), governador e presidente. Os números têm 4, 5, 3, 2 e 2
dígitos.

## Goals / Non-Goals

**Goals:**
- Um PDF A4 com a colinha pequena num canto, pronta para recortar, gerado no aparelho.
- O mesmo cartão quando o eleitor usa "Imprimir colinha".
- Número sempre completo e legível; nome e partido como apoio.

**Non-Goals:**
- Várias cópias por folha, escolha de tamanho, imagem PNG, geração no servidor.
- Reproduzir no PDF a fonte do site (Atkinson Hyperlegible).

## Decisions

### D1. PDF escrito à mão em JavaScript, sem biblioteca
Um módulo `static/js/pdf-colinha.js` monta o arquivo PDF 1.4 direto: uma página A4
(595,28 × 841,89 pt), um fluxo de conteúdo com texto e retângulos, tabela `xref`. O cartão
só precisa de texto, linhas e retângulos, o que cabe em cerca de 200 linhas.

Alternativas consideradas: jsPDF ou pdf-lib (centenas de KB, dependência de terceiros, o
que o projeto não aceita); só a impressão do navegador com "Salvar como PDF" (não existe
no navegador interno do WhatsApp e é difícil de achar no celular); gerar no servidor
(exigiria enviar as escolhas do eleitor, contra a regra de privacidade da colinha).

### D2. Fontes padrão do PDF (Helvetica), com acentos do português
O PDF usa Helvetica e Helvetica-Bold, que todo leitor de PDF tem e que não precisam ser
embutidas, com `WinAnsiEncoding`, que cobre todos os acentos do português. Caractere
fora dessa tabela é trocado pela letra sem acento (decomposição Unicode) e, se ainda não
couber, por "?". A largura do texto é medida com a tabela de larguras da Helvetica
(métricas AFM, embutidas no módulo) para encolher o nome até 6 pt e, se ainda não couber,
cortar com "…".

Alternativa considerada: embutir a Atkinson Hyperlegible. Exigiria recortar e embutir
uma fonte TrueType em JavaScript, o que aumenta o código e o arquivo sem ganho para um
cartão de números grandes.

### D3. Cartão de 63 × 88 mm a 10 mm do canto superior esquerdo
Tamanho de carta de baralho: cabe na carteira e no bolso da camisa. Contorno tracejado e
"Recorte na linha tracejada" pequeno do lado de fora, acima do contorno. (A tesoura da
ZapfDingbats, outra fonte padrão do PDF, foi testada e não aparece em todos os leitores:
o poppler não a desenhou. Ficou só o texto.) Dentro do cartão:
1. Cabeçalho: "Minha colinha · Roraima".
2. Uma faixa por vaga, de altura igual, na ordem da urna: cargo (com "1º voto" e "2º
   voto" no senador), número em quadradinhos de cerca de 6 mm, e uma linha com nome de
   urna e sigla do partido.
3. Rodapé: endereço do site e "Gerado em DD/MM/AAAA. Confira antes de votar."

A altura das faixas é dividida pelo número de vagas (2 vagas em eleição municipal, 6
em geral), com teto para não ficar exagerada. O mesmo cartão serve para 2028 e 2030 sem
mudança de código.

Alternativas consideradas: cartão do tamanho de um cartão de crédito (85,6 × 54 mm, baixo
demais para seis vagas com números legíveis); faixa estreita no topo da folha (difícil de
dobrar e guardar).

### D4. Os dois caminhos usam a mesma lista de vagas
`colinha.js` já monta a lista `slots` com as vagas na ordem da urna. O PDF recebe um
objeto simples feito a partir dela (`{titulo, vagas: [{cargo, digitos, numero, nome,
partido, aviso}], rodape}`), e a impressão usa o HTML que já está na página, com um
`@media print` novo que desenha a lista como cartão de 63 mm de largura, tracejado, no
canto da folha. Assim os dados e a ordem são os mesmos; só a fonte muda (Atkinson na
impressão, Helvetica no PDF).

Alternativa considerada: imprimir o próprio PDF (abrir o blob e chamar a impressão). Não
funciona de forma confiável entre navegadores.

### D5. Vagas vazias com quadradinhos, a partir do `config.toml`
Nova chave `digitos` por cargo no `config.toml` (`PRESIDENTE = 2`, `GOVERNADOR = 2`,
`SENADOR = 3`, `DEPUTADO FEDERAL = 4`, `DEPUTADO ESTADUAL = 5`, `DEPUTADO DISTRITAL = 5`; em
2028, `PREFEITO = 2` e `VEREADOR = 5`). Vaga vazia sai com o cargo e os quadradinhos em
branco, para o eleitor escrever à mão. A geração do site confere que todo número de
candidatura tem a quantidade de dígitos do seu cargo e para com erro se não tiver, porque
um quadradinho a menos no cartão induziria o eleitor a errar.

Alternativa considerada: vaga vazia sem quadradinhos. Perde a utilidade de completar à
mão depois.

### D6. Escolha que mudou de situação vai para o cartão com aviso
Se a conferência que já existe (requisito "Colinha desatualizada") marcou uma vaga como
"não aparece mais nos dados" ou "não está mais apta", o cartão mostra o número com a
linha "Confira no site: a situação mudou" no lugar do partido. O botão de PDF só gera o
arquivo depois que essa conferência termina (ou falha por rede, caso em que gera sem
aviso, como a página).

### D7. Download pelo próprio navegador, com ajuda para quem não consegue
O arquivo é um `Blob` baixado por um link com `download="colinha-rr.pdf"`. Abaixo dos
botões, um texto curto: "Não conseguiu imprimir? Baixe o PDF e mande para quem tem
impressora, ou leve a uma copiadora. Se o download não começar, abra o site no navegador
do celular (Chrome ou Safari)." Se `window.print` não existir, o botão de imprimir some.

### D8. Testes do PDF com o Node do ambiente e conferência em Python
`pdf-colinha.js` expõe a função em `window.ColinhaPDF` e também em `module.exports`
quando carregado pelo Node. Um teste em pytest roda `node` com um script que gera PDFs a
partir de colinhas sintéticas e os confere com `pypdf` (dependência de desenvolvimento,
`uv add --dev pypdf`): uma página A4, textos na ordem da urna, acentos preservados,
quadradinhos vazios, caractere fora da tabela trocado.

## Risks / Trade-offs

- [Número errado no cartão leva a voto errado] → o número vem do mesmo objeto guardado
  que a página mostra; teste de que cada número aparece completo no PDF; checagem de
  dígitos por cargo na geração do site (D5); rodapé "Confira antes de votar".
- [Download não funciona no navegador interno do WhatsApp] → texto de ajuda (D7); tarefa
  de teste em Android (Chrome e WhatsApp) e iPhone (Safari e WhatsApp).
- [Impressora em "ajustar à página" muda o tamanho do cartão] → o cartão continua
  proporcional e legível; o texto de ajuda pede "tamanho real (100%)".
- [Nome muito longo] → encolhe até 6 pt e corta com "…"; o número nunca é cortado.
- [Cartão impresso fica velho se o eleitor mudar de ideia] → data de geração no rodapé.

## Migration Plan

Sem migração: a colinha guardada no navegador continua no mesmo formato
(`colinha:v1:*`). Publicar com `just publicar` normalmente.
