## 1. Destino e texto do link

- [x] 1.1 Função pura que devolve destino e texto do "Voltar" para cada tipo de página (UF, lista, candidato, candidato a presidente, colinha, metodologia), com o cargo em minúsculas e a UF por extenso
- [x] 1.2 Testes da função: um caso por linha da tabela da spec, incluindo presidente (destino estático: página inicial)
- [x] 1.3 Preposição certa antes do nome da UF em todo o site ("no Rio de Janeiro", "na Bahia", "colinha do Rio de Janeiro"), descoberta na implementação: o site usava sempre "em"/"de"

## 2. Páginas

- [x] 2.1 Componente do link no template base (bloco opcional; a página inicial e a 404 não usam), com seta decorativa `aria-hidden` e texto completo
- [x] 2.2 Passar o destino para as páginas de UF, lista, candidato, colinha e metodologia
- [x] 2.3 Tirar a linha `.migalha` da lista por cargo (design D4)
- [x] 2.4 CSS: link discreto, área de toque de 44 px, quebra de linha em textos longos, foco visível
- [x] 2.5 Teste de geração: toda subpágina gerada tem exatamente um link "Voltar" com o destino esperado; a página inicial não tem

## 3. Presidente

- [x] 3.1 Em `colinha.js`, trocar destino e texto do "Voltar" das páginas `/br/` pela lista de presidente da última UF (`colinha:uf`), só quando ela existir
- [x] 3.2 Conferir no Chromium: sem UF guardada, destino é a página inicial; com UF guardada, a lista de presidente da UF; sem JavaScript, a página inicial

## 4. Revisão

- [x] 4.1 `just check`, `just limpar && just dev` e `just privacidade`
- [x] 4.2 Abrir três páginas em largura de celular (candidato, lista e presidente) e conferir o link
- [x] 4.3 Rodar `/checar-neutralidade`
