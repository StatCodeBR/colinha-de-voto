# Proposal: Pipeline de candidaturas do TSE com trajetória eleitoral

## Why

O eleitor não sabe quem são os candidatos nem o que já fizeram. O TSE publica tudo em
dados abertos, mas em arquivos grandes, em CSV `latin-1`, separados por ano e sem um
identificador que ligue a mesma pessoa entre eleições: o CPF foi ocultado dos arquivos
abertos em 2024, inclusive nos anos anteriores. Sem essa ligação, não dá para dizer "já
concorreu" ou "já foi eleita".

Esta change cria a base de dados do projeto: a lista de candidaturas de 2026 por UF e,
para cada candidato, a trajetória eleitoral de 2014 a 2024, com nível de confiança em
cada vínculo e revisão humana dos casos duvidosos.

## What Changes

- Pacote Python `colinha` com CLI (`baixar`, `processar`, `tudo`) e configuração lida
  do `config.toml`.
- Download com cache e manifesto (URL, data de extração, hash) dos arquivos do TSE:
  candidaturas de 2026 e dos anos de histórico, bens declarados e redes sociais de 2026.
- Normalização de todos os anos numa tabela única de candidaturas (parquet em
  `data/interim/`), com uma linha por candidatura (sem duplicar turnos).
- Vínculo entre candidaturas de 2026 e de anos anteriores em três níveis: confirmado,
  provável e ambíguo. Só "confirmado" é publicado.
- Correções manuais de vínculo em `data/manual/vinculos.csv`, que sempre prevalecem.
- Saídas públicas em `data/processed/`: índice por UF, detalhe por candidato, manifesto
  de fontes, resumo com contagens e relatório de revisão de vínculos.
- Barreira de privacidade: saídas públicas montadas por allowlist de campos; CPF,
  título e e-mail nunca saem de `data/interim/`.

Fora do escopo (ficam para a fase 2, ver `docs/roadmap.md`): votos por candidatura,
evolução do patrimônio, Senado e assembleias. O site é a change 02 e a Câmara, a 03.

## Capabilities

### New Capabilities
- `coleta-tse`: baixar, ler e normalizar os dados de candidaturas do TSE e gerar as
  saídas públicas para o site.
- `historico-eleitoral`: ligar cada candidato de 2026 às suas candidaturas anteriores,
  com nível de confiança, revisão humana e classificação do histórico.

### Modified Capabilities
- Nenhuma (projeto novo).

## Impact

- Código novo: `src/colinha/` (config, cli, tse, vinculo, saida) e `tests/`.
- Dependências: pandas, pyarrow, httpx, pytest (dev).
- Dados: `data/raw/`, `data/interim/`, `data/processed/` (fora do git) e
  `data/manual/vinculos.csv` (no git).
- Dependência externa: disponibilidade do CDN do TSE. O cache em `data/raw/` permite
  reprocessar sem baixar de novo.
