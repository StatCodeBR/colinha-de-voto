---
description: Revisa com você os vínculos prováveis ou ambíguos entre 2026 e eleições anteriores
argument-hint: [UF, ex. SP]
---

Vamos revisar os vínculos pendentes da UF $ARGUMENTS.

1. Leia `data/processed/revisao_vinculos.csv` (e `revisao_vinculos_camara.csv`, se
   existir) filtrando pela UF $ARGUMENTS.
2. Para cada caso, um de cada vez, mostre lado a lado as evidências: nome normalizado,
   data de nascimento (ou idade), UF e município, cargo, partido e ano de cada
   candidatura. Diga qual regra gerou o caso (provável ou ambíguo) e por quê.
3. Sugira "confirmar" ou "rejeitar" com uma justificativa curta, ou diga que não dá para
   decidir com os dados disponíveis.
4. Só grave em `data/manual/vinculos.csv` (ou `vinculos_camara.csv`) depois que eu
   responder explicitamente sobre aquele caso. Preencha `revisado_por` com o nome que eu
   informar e `revisado_em` com a data de hoje.

Regras: use apenas os dados já baixados das fontes oficiais. Não pesquise na web
informações pessoais de candidatos. Na dúvida, a resposta certa é não vincular.
