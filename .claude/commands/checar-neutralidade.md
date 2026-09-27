---
description: Audita o site gerado contra as regras de neutralidade, dados pessoais e honestidade
---

Audite `site/dist/` contra as regras invioláveis do `CLAUDE.md`. Gere o site antes com
`just site` se ele não existir.

Verifique e reporte, com arquivo e trecho:

1. Dados pessoais: nenhum CPF, título de eleitor ou e-mail de candidato em HTML ou JSON.
   Use os CPFs de `data/interim/` como lista de busca, não só expressões regulares.
2. Neutralidade: adjetivos avaliativos, rankings, destaques, ordenação diferente da
   alfabética, cores ou logos de partido, diferenças de template entre candidatos.
   Compare as seções de 5 páginas de partidos diferentes.
3. Honestidade: blocos de dados sem fonte ou data; textos como "primeira candidatura"
   sem janela de cobertura; zeros onde deveria haver "Não informado".
4. Privacidade: qualquer script, fonte ou recurso carregado de outro domínio; qualquer
   envio de dados da colinha.
5. Linguagem: siglas sem explicação ("QP", "PLP") e flexão de gênero errada.

Termine com uma lista priorizada de correções. Não corrija nada sem eu pedir.
