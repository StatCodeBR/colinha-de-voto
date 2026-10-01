## 1. Configuração e dados

- [x] 1.1 `config.toml`: chave `digitos` por cargo; `config.py` lê e valida (todo cargo configurado tem dígitos)
- [x] 1.2 Geração do site: conferir que todo número de candidatura tem os dígitos do cargo; erro com UF, cargo e número se não tiver
- [x] 1.3 Testes: config sem dígitos de um cargo falha; candidatura com número fora do padrão para a geração
- [x] 1.4 Passar `digitos` ao `config_colinha` da página `/colinha/`

## 2. Gerador de PDF

- [x] 2.1 `static/js/pdf-colinha.js`: escrita de PDF 1.4 (objetos, fluxo de conteúdo, `xref`), página A4, Helvetica e Helvetica-Bold com `WinAnsiEncoding`
- [x] 2.2 Conversão de texto para WinAnsi: acentos do português preservados; fora da tabela, letra sem acento ou "?"; escape de `(`, `)` e `\`
- [x] 2.3 Larguras da Helvetica (AFM) para medir texto; nome encolhe até 6 pt e depois corta com "…"; número nunca é cortado
- [x] 2.4 Desenho do cartão 63 × 88 mm a 10 mm do canto: contorno tracejado, "Recorte na linha tracejada", cabeçalho, uma faixa por vaga com quadradinhos, nome e partido (ou aviso), rodapé com endereço e data
- [x] 2.5 Exportar em `window.ColinhaPDF` e em `module.exports` (para o teste no Node)
- [x] 2.6 `uv add --dev pypdf`; teste em pytest que roda o Node com colinhas sintéticas e confere: uma página A4, textos na ordem da urna, cada número completo, acentos, vaga vazia sem número inventado, caractere fora da tabela trocado, aviso de situação mudada

## 3. Página da colinha

- [x] 3.1 `colinha.js`: montar o objeto do cartão a partir de `slots` (inclusive vagas vazias e avisos da conferência)
- [x] 3.2 Botão "Baixar colinha em PDF": espera a conferência terminar (ou falhar) e baixa `colinha-{uf}.pdf` por `Blob`; carregar `pdf-colinha.js` só na página da colinha, com `?v=`
- [x] 3.3 Esconder "Imprimir colinha" quando `window.print` não existe; texto de ajuda sobre copiadora, tamanho real (100%) e abrir no navegador do celular
- [x] 3.4 `@media print` refeito: só o cartão de 63 mm, tracejado, no canto superior esquerdo, mesma ordem e dados do PDF
- [x] 3.5 Testes de geração: a página da colinha tem os dois botões, o script novo é local e nenhuma página ganhou script de terceiros; CSP do nginx continua válida

## 4. Verificação

- [x] 4.1 `just check`, `just limpar && just dev`, `just privacidade` e `/checar-neutralidade`
- [x] 4.2 Abrir o PDF gerado de RR no Chrome e num leitor de PDF; imprimir (ou visualizar) em 100% e medir o cartão
- [x] 4.3 Conferir em largura de celular a página da colinha e a visualização de impressão
- [ ] 4.4 (equipe) Testar no celular: Android com Chrome e com o navegador interno do WhatsApp; iPhone com Safari e com o WhatsApp. Anotar onde o download não funciona e ajustar o texto de ajuda
