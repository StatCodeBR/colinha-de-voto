# Design: Atuação na Câmara dos Deputados

## Context

A Câmara oferece a API v2 em `dadosabertos.camara.leg.br/api/v2` e, no mesmo portal,
arquivos em massa por ano. O `/deputados/{id}` traz nome civil e data de nascimento
(confirmar se traz CPF). Proposições têm autores e temas. Números brutos de proposições
enganam: um deputado pode ser coautor de centenas de projetos sem ter redigido nenhum,
e requerimentos e moções inflam contagens.

## Goals / Non-Goals

**Goals**
- Mostrar, para quem passou pela Câmara desde 2015, o que apresentou e sobre quais
  temas, sem transformar isso em nota.
- Rodar a partir de cache quando a API estiver instável.

**Non-Goals**
- Avaliar desempenho, comparar deputados ou medir produtividade.
- Votações, presença, gastos (fase 2).

## Decisions

### D1. Arquivos em massa primeiro, API como complemento
Proposições, autores e temas por ano em arquivo evitam dezenas de milhares de chamadas.
A API fica para deputados (detalhes) e frentes. Se os arquivos em massa não existirem ou
não tiverem as colunas necessárias, usar a API com cache por recurso. Registrar a
escolha final em `docs/fontes.md`.

### D2. Cliente educado
httpx com cache em disco por URL, até `max_requisicoes_por_segundo` do `config.toml`,
3 tentativas com espera crescente e `User-Agent` identificando o projeto e o e-mail de
contato.

### D3. Vínculo candidato ↔ deputado
Mesmas regras da change 01: CPF igual (se a Câmara fornecer) ou nome civil normalizado
+ data de nascimento únicos dos dois lados para confirmar; o resto vai para
`revisao_vinculos_camara.csv`. Correções em `data/manual/vinculos_camara.csv`. O vínculo
é feito com a candidatura de 2026, não com a trajetória toda.

### D4. O que conta e como mostrar
- Só tipos configurados (PL, PLP, PEC). Requerimentos, moções e indicações não entram.
- Autoria principal (primeiro signatário ou proponente, conforme o dado) separada de
  coautoria. Se o dado não permitir separar, mostrar só "autoria ou coautoria" e dizer
  isso na página.
- Temas: os cinco mais frequentes nas proposições de autoria, com a contagem.
- Proposições: as dez mais recentes, com tipo, número, ano, ementa e link para a página
  oficial.
- Frentes: quantidade e lista recolhida (abre ao tocar).
- Mandatos: legislaturas em que exerceu mandato, com período.
- Texto fixo explicando que quantidade de projetos não mede a qualidade de um mandato.

### D5. Quem aparece
A seção só aparece para candidatos vinculados a um deputado. Para os demais, a seção não
existe (nada de "0 projetos"). Um deputado vinculado sem proposições dos tipos
configurados mostra a frase explicativa, não um zero solto.

## Risks / Trade-offs

- **Contagem mal interpretada** como nota. Mitigação: texto explicativo fixo, separação
  de autoria e coautoria, sem comparação com outros deputados.
- **Suplentes que assumiram por pouco tempo** têm poucos dados. Mitigação: mostrar o
  período exato do mandato.
- **API instável perto da eleição.** Mitigação: coletar cedo, gerar a partir de cache e
  mostrar a data de extração.
- **Vínculo errado** entre candidato e deputado. Mesma mitigação da change 01.

## Open Questions

- Os arquivos em massa trazem `ordemAssinatura` ou `proponente` para separar autoria?
- `/deputados/{id}` traz CPF?
- Frentes de legislaturas anteriores estão disponíveis ou só a atual?
