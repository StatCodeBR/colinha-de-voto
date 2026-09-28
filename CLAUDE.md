# Colinha do Voto

Ferramenta web gratuita e apartidária que ajuda o eleitor brasileiro a conhecer os
candidatos antes de votar, usando apenas dados abertos oficiais (TSE e Câmara dos
Deputados). Mantida pela StatCode e publicada em subdomínio da StatCode (ver
`config.toml`). Público: eleitores comuns, a maioria no celular, chegando por links
compartilhados no WhatsApp.

## Contexto e prazo

- 1º turno: domingo, 4 de outubro de 2026. Meta: changes 01 e 02 no ar até quinta,
  1º de outubro, para dar tempo de divulgar.
- A estrutura precisa servir para 2028 (municipal) e 2030. Ano, cargos, UFs e anos de
  histórico vêm do `config.toml`; nada de 2026 fixo no código.

## Como trabalhamos (OpenSpec)

- Toda mudança de comportamento passa por uma change em `openspec/changes/`. Ordem:
  `01-add-pipeline-tse` → `02-add-site-colinha` → `03-add-dados-camara`.
- Implemente com `/opsx:apply <change>` e marque as tarefas em `tasks.md` à medida que
  concluir.
- Se os dados reais contradisserem a spec (coluna inexistente, formato diferente, URL
  mudou), pare, registre em `docs/fontes.md` e atualize os artefatos com `/opsx:update`
  antes de seguir. Não crie contornos silenciosos.
- Ao terminar uma change: testes passando, `/opsx:verify` se disponível, depois
  `/opsx:archive`.

## Ambiente e comandos

O ambiente vem do `flake.nix` (`nix develop` ou direnv): Python 3.12, uv, just, ruff e
Node. O uv usa o Python do Nix (`UV_PYTHON_DOWNLOADS=never`); não instale outro Python.
Dependências Python entram com `uv add`, nunca com pip. Ferramentas de sistema novas
entram no `flake.nix`.

Use sempre as recipes do `justfile`. Todo comando recorrente novo vira uma recipe, com
comentário de uma linha acima (é o que aparece em `just --list`).

```bash
just dev                  # pipeline + site só para RR: use para iterar
just baixar --uf RR       # (--forcar para ignorar o cache)
just processar --uf RR
just camara
just site
just servir               # http://localhost:8000
just tudo                 # todas as UFs
just test -k vinculo
just lint / just fmt
just specs                # openspec list + validate
just check                # lint + test + specs
just privacidade          # nenhum CPF/nome civil protegido em data/processed/
```

Para iterar rápido, use `just dev` (RR, a menor UF). Só rode todas as UFs quando o
fluxo estiver correto.

## Estrutura

```
flake.nix              ambiente de desenvolvimento (Nix)
justfile               comandos do projeto
config.toml            configuração do projeto (nome, subdomínio, anos, UFs, cargos)
src/colinha/           pacote Python (CLI, coleta, normalização, vínculos, site)
src/colinha/templates/ templates Jinja2 do site
src/colinha/static/    CSS, JS e fontes auto-hospedadas
tests/                 pytest com fixtures sintéticas em tests/fixtures/
data/raw/              arquivos originais + manifest.json (fora do git)
data/interim/          parquet normalizado; PODE conter CPF (fora do git)
data/processed/        JSON públicos consumidos pelo site (fora do git)
data/manual/           correções humanas de vínculo (NO git)
site/dist/             site gerado (fora do git)
docs/fontes.md         fontes, URLs e peculiaridades descobertas
openspec/              specs e changes
```

## Regras invioláveis

### Neutralidade
- Mesmo template, mesmas seções e mesma ordem para todo candidato.
- Ordem padrão das listas: alfabética pelo nome de urna. Nada de destaques, "mais
  votados", notas, rankings ou medidores de produtividade.
- Sem cores, logos ou símbolos de partido. Partido aparece como texto (sigla).
- Textos descritivos, sem adjetivos avaliativos: "Apresentou 12 projetos de lei" sim,
  "muito atuante" não.
- Sem anúncios e sem scripts de terceiros.

### Dados pessoais
- Nunca exibir nem gravar em `data/processed/` ou `site/dist/`: CPF, título de eleitor,
  e-mail ou endereço. CPF só existe em memória e em `data/interim/`, para vínculo.
- Saídas públicas são montadas a partir de uma lista explícita de campos permitidos
  (allowlist), nunca removendo colunas de uma tabela completa.
- IDs públicos nunca derivam de CPF (hash de CPF é reversível por força bruta).
- Se houver nome social, ele é o nome exibido e o nome civil não aparece na saída.
- Não buscar informação sobre candidatos fora das fontes oficiais de `docs/fontes.md`.

### Honestidade dos dados
- Todo bloco de dados mostra fonte e data de extração.
- Vínculos entre eleições só aparecem se forem "confirmados". Prováveis e ambíguos vão
  para revisão humana.
- Ausência de registro se escreve com a janela de cobertura ("Nenhuma candidatura
  encontrada de 2014 a 2024"), nunca "primeira candidatura".
- Dado ausente aparece como "Não informado". Nunca preencher com zero ou suposição.

### Privacidade da colinha
- A colinha vive só no `localStorage` do navegador. Nenhum envio, nenhum evento de
  analytics com candidato escolhido.
- Fontes auto-hospedadas.

## Convenções de código

- Python 3.12+, src layout, type hints. Regras de negócio em funções puras e testáveis.
- Identificadores do domínio em português sem acento (`candidatura`, `cargo`,
  `vinculo`); colunas normalizadas em snake_case.
- CSV do TSE sempre lido com `sep=";"`, `encoding="latin-1"`, `dtype=str`.
- Testes com fixtures sintéticas pequenas; nada de dados reais de pessoas em `tests/`.
- Interface em português do Brasil, linguagem simples, frases curtas, flexão de gênero
  conforme o gênero declarado ("eleita"/"eleito").
- JavaScript puro, sem framework e sem dependências. CSS com variáveis (tokens definidos
  no `design.md` da change 02).

## Antes de dizer que terminou

- `just check` passa (lint, testes e specs).
- `just limpar && just dev` roda sem erro.
- O teste de dados pessoais passa (nenhum CPF de entrada aparece na saída).
- Em mudanças no site: rodar `/checar-neutralidade` e abrir três páginas em largura de
  celular.
