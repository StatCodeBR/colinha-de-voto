---
description: Baixa os dados mais recentes, reprocessa e resume o que mudou desde a última execução
argument-hint: [UF opcional, ex. RR]
---

Atualize os dados do Colinha do Voto e me diga o que mudou. Até o dia da eleição, os
dados do TSE mudam todo dia (indeferimentos, renúncias, substituições).

1. Guarde uma cópia de `data/processed/resumo.json` (se existir) para comparar.
2. Rode `just baixar --forcar` e `just processar`. Se $ARGUMENTS tiver uma UF,
   acrescente `--uf $ARGUMENTS` nos dois.
3. Compare o resumo novo com o anterior e me mostre, por UF:
   - candidaturas novas e removidas;
   - mudanças de situação (ex.: apta → inapta);
   - variação no número de vínculos confirmados, prováveis e ambíguos.
4. Rode `just test`.
5. Liste os candidatos que mudaram de situação com nome de urna, número e UF, porque
   eles podem estar na colinha de algum eleitor.

Não gere nem publique o site sem eu pedir. Não altere `data/manual/`.
