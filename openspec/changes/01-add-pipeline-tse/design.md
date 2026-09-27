# Design: Pipeline TSE e trajetória eleitoral

## Context

Os arquivos de candidaturas do TSE ficam no CDN
(`consulta_cand/consulta_cand_{ano}.zip`), com um CSV por UF e um consolidado nacional.
São CSVs com `;`, `latin-1`, marcadores de nulo próprios (`#NULO#`, `#NE#`, `-1`...) e
uma linha por turno. `SQ_CANDIDATO` identifica a candidatura naquele ano, não a pessoa.

O CPF foi ocultado dos dados abertos em 2024, inclusive retroativamente. Para 2026, a
minuta do TSE voltou a tratar o CPF como público, mas é preciso confirmar no arquivo.
Na prática, o vínculo com anos anteriores vai depender de nome completo e data de
nascimento.

## Goals / Non-Goals

**Goals**
- Dados de 2026 limpos por UF, prontos para o site.
- Trajetória de 2014 a 2024 (eleições gerais e municipais) para cada candidato.
- Nenhum vínculo errado publicado: na dúvida, não vincular.
- Pipeline idempotente, que roda do zero em poucos minutos numa máquina comum.

**Non-Goals**
- Votos por candidatura, evolução patrimonial, Senado, assembleias (fase 2).
- Qualquer interface (change 02).

## Decisions

### D1. pandas + pyarrow
Leitura nativa de `latin-1`, familiaridade da equipe (a StatCode ensina pandas) e volume
que cabe em memória lendo só as colunas necessárias (`usecols`). DuckDB e polars foram
considerados; ficam como alternativa se o processamento dos anos municipais ficar lento.

### D2. Três camadas de dados com fronteira de privacidade
- `data/raw/`: zips originais e `manifest.json` (URL, `baixado_em`, sha256, tamanho).
- `data/interim/`: parquet normalizado. Pode conter CPF, porque é onde o vínculo
  acontece. Nunca é publicado.
- `data/processed/`: JSON públicos. Gerados por uma única função que monta cada registro
  a partir de uma allowlist de campos. Nunca se parte da tabela completa removendo
  colunas, porque uma coluna nova do TSE vazaria sem ninguém perceber.

### D3. Identificadores
- Candidatura: (`ano`, `sq_candidato`).
- Página pública: `{uf}/{numero}` (ex.: `sp/12345`); presidente em `br/{numero}`. Curto e
  fácil de compartilhar. O número é único por UF entre os cargos de 2026 (a quantidade de
  dígitos difere por cargo).
- Nenhum identificador público deriva de CPF: um hash de CPF é reversível por força
  bruta.

### D4. Vínculo em níveis

| Nível | Regra | Publicado? |
|---|---|---|
| confirmado | CPF válido e igual dos dois lados | sim |
| confirmado | nome normalizado + data de nascimento iguais, e a chave é única nos dois lados | sim |
| provável | nome normalizado igual na mesma UF, sem data de nascimento para comparar, com idade compatível (±1 ano) | não, vai para revisão |
| ambíguo | a chave aponta para mais de uma pessoa em algum dos lados | não, vai para revisão |

Correções em `data/manual/vinculos.csv` (confirmar ou rejeitar um par específico)
prevalecem sobre qualquer regra.

Normalização de nome: maiúsculas, sem acento (NFKD), só letras e espaços, espaços
colapsados. Apóstrofos e hífens viram espaço.

### D5. Classificação do histórico
Usa só vínculos confirmados, dentro da janela configurada (`anos_historico`):
- `eleito`: pelo menos uma candidatura com resultado eleito.
- `concorreu`: candidaturas confirmadas, nenhuma eleita.
- `sem_registro`: nenhuma candidatura confirmada e nenhuma pendente.
- `em_verificacao`: nenhuma confirmada, mas há prováveis ou ambíguas pendentes.

Se houver confirmadas e também pendentes, o detalhe do candidato leva
`ha_registros_em_verificacao: true`.

### D6. Mapeamento de resultado

| `DS_SIT_TOT_TURNO` (normalizado) | resultado |
|---|---|
| ELEITO, ELEITO POR QP, ELEITO POR MEDIA | `eleito` |
| SUPLENTE | `suplente` |
| NAO ELEITO | `nao_eleito` |
| 2O TURNO (sem linha de 2º turno) | `segundo_turno_sem_resultado` |
| nulo | `sem_resultado` |

Para quem foi ao 2º turno, vale o resultado da linha de `NR_TURNO` 2. Valores não
mapeados geram erro com a lista dos valores encontrados, em vez de cair num padrão.

### D7. Formato das saídas

`data/processed/{uf}/indice.json`, leve, para listas e filtros:

```json
{
  "uf": "SP",
  "gerado_em": "2026-09-28T10:00:00-03:00",
  "candidatos": [
    {
      "id": "sp/12345", "nome_urna": "...", "numero": "12345",
      "cargo": "DEPUTADO ESTADUAL", "partido": "SIGLA", "genero": "FEMININO",
      "historico": "concorreu", "busca_reeleicao": false, "apto": true
    }
  ]
}
```

`data/processed/{uf}/candidatos/{numero}.json`, detalhe:
identificação (nome de urna, nome exibido, número, cargo, UF, partido/federação),
perfil declarado (idade, gênero, cor/raça autodeclarada, grau de instrução, ocupação),
situação da candidatura, total de bens declarados (ou `null` quando não declarou),
redes sociais, `trajetoria` (ano, cargo, local, partido, resultado) e `fontes`
(nome, URL, `extraido_em`).

`data/processed/manifesto.json`: fontes e datas usadas no build.
`data/processed/resumo.json`: contagens por UF, por nível de vínculo e por classe de
histórico.
`data/processed/revisao_vinculos.csv`: pendências com as evidências dos dois lados
(esse arquivo contém dados para revisão interna e não é publicado no site).

### D8. Nome exibido
Se `NM_SOCIAL_CANDIDATO` estiver preenchido, ele é o nome exibido e o nome civil não
entra em nenhuma saída pública. Caso contrário, o nome exibido é o nome civil
(`NM_CANDIDATO`). O nome de urna é sempre exibido.

## Risks / Trade-offs

- **Homônimo vinculado errado** atribui a trajetória de outra pessoa a alguém, com dano
  para a pessoa e para a StatCode. Mitigação: exigir data de nascimento, unicidade nos
  dois lados, revisão humana, link "Encontrou um erro?" em toda página (change 02).
- **Mudança de nome** (casamento, nome social) faz perder vínculos e gera falso
  "sem registro". Mitigação: texto sempre com a janela de cobertura e correção manual.
- **TSE muda colunas ou layout.** Mitigação: validar colunas esperadas por ano e falhar
  com mensagem clara.
- **Dados de 2026 mudam até a eleição** (indeferimentos, renúncias). Mitigação:
  `/atualizar-dados` diário até 4/out.
- **Anos municipais são grandes.** Mitigação: `usecols`, processamento por ano, cache
  em parquet.

## Open Questions

- O arquivo de 2026 traz o CPF preenchido?
- `DT_NASCIMENTO` está presente em todos os anos da janela, depois do mascaramento de
  2024?
- Existe um padrão de URL estável no DivulgaCandContas para linkar cada candidato?
- Candidaturas inaptas: o site mostra por padrão ou só sob filtro? (Proposta: os dados
  incluem todas; o site mostra aptas por padrão.)
