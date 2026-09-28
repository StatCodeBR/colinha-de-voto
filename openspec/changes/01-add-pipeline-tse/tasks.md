# Tasks

## 1. Base do projeto
- [x] 1.1 Dentro do `nix develop`, criar o pacote com `uv init --package` (src layout, nome `colinha`) e adicionar pandas, pyarrow, httpx; pytest como dependência de desenvolvimento; configurar o ruff no `pyproject.toml`
- [x] 1.2 Ler `config.toml` com `tomllib` para uma dataclass tipada, com erro claro para chave ausente
- [x] 1.3 CLI com argparse e subcomandos `baixar`, `processar` e `tudo`, aceitando `--uf` e `--forcar`; registrar o entry point `colinha` no `pyproject.toml`; conferir que `just dev`, `just baixar`, `just processar` e `just tudo` funcionam
- [x] 1.4 Criar `data/raw`, `data/interim`, `data/processed` sob demanda e conferir o `.gitignore`

## 2. Reconhecimento das fontes (antes de escrever o parser)
- [x] 2.1 Baixar `consulta_cand_2026` e `consulta_cand_2022` só para RR; listar colunas, tipos e 5 linhas de amostra de cada
- [x] 2.2 Registrar em `docs/fontes.md`, por ano: presença de CPF, título e `DT_NASCIMENTO`; marcadores de nulo encontrados; valores distintos de `DS_CARGO` e `DS_SIT_TOT_TURNO`
- [x] 2.3 Confirmar no portal as URLs de bens, redes sociais e fotos de 2026 e registrar
- [x] 2.4 Medir tempo e memória para ler um ano municipal inteiro (2020 ou 2024) com `usecols`; se passar de alguns minutos, registrar e propor ajuste
- [x] 2.5 Atualizar `design.md` e as specs com `/opsx:update` se algo divergir do previsto

## 3. Coleta
- [x] 3.1 Download com httpx: streaming para arquivo `.part`, renomeio só no fim, 3 tentativas com espera crescente
- [x] 3.2 Manifesto em `data/raw/manifest.json` com URL, `baixado_em`, sha256 e tamanho
- [x] 3.3 Extração dos zips mantendo só os CSVs necessários
- [x] 3.4 Testes: cache evita novo download; falha simulada não deixa arquivo com nome final
- [x] 3.5 Arquivo complementar do ano da eleição (situação de julgamento, declaração de bens e reeleição), descoberto no reconhecimento

## 4. Normalização
- [x] 4.1 Leitor único de CSV do TSE (`;`, `latin-1`, `dtype=str`, `usecols`) com conversão de marcadores de nulo e validação de colunas por ano
- [x] 4.2 Tabela única de candidaturas de todos os anos em `data/interim/candidaturas.parquet`, com colunas em snake_case
- [x] 4.3 Deduplicação por turno mantendo o resultado do último turno
- [x] 4.4 Filtro de cargos titulares configurados e campo `apto`
- [x] 4.5 Regra do nome exibido (nome social)
- [x] 4.6 Total de bens e redes sociais de 2026
- [x] 4.7 Testes com fixtures sintéticas: nulos, zeros à esquerda, coluna ausente, 2º turno, vice excluído, nome social, bens zero versus não declarados

## 5. Vínculo histórico
- [x] 5.1 `normalizar_nome` com testes (acentos, apóstrofos, hífens, espaços)
- [x] 5.2 Vínculo confirmado por CPF e por nome + nascimento com unicidade nos dois lados
- [x] 5.3 Classificação de prováveis e ambíguos
- [x] 5.4 Aplicação de `data/manual/vinculos.csv` (confirmar e rejeitar)
- [x] 5.5 Mapeamento de resultado com falha para valores desconhecidos
- [x] 5.6 Classificação do histórico (`eleito`, `concorreu`, `sem_registro`, `em_verificacao`) e janela de cobertura
- [x] 5.7 `revisao_vinculos.csv` com evidências dos dois lados
- [x] 5.8 Testes: homônimos com nascimentos diferentes; chave repetida vira ambíguo; rejeição manual remove vínculo automático; confirmação manual publica provável

## 6. Saídas públicas
- [x] 6.1 Função única de montagem por allowlist de campos para índice e detalhe
- [x] 6.2 `indice.json` por UF, índice nacional `BR` para presidente, detalhe por candidato
- [x] 6.3 `manifesto.json` e `resumo.json`
- [x] 6.4 Teste de privacidade: coletar todos os CPFs de `data/interim/` e garantir que nenhum aparece em `data/processed/`
- [ ] 6.5 Rodar do zero para RR; conferir contagens com o total de candidatos de RR no DivulgaCandContas (revisão humana: o DivulgaCandContas bloqueia acesso automatizado; contagens em `docs/fontes.md`)
- [x] 6.6 Rodar para todas as UFs; registrar tempo total e contagens em `docs/fontes.md`
- [ ] 6.7 Revisão humana (equipe): conferir 10 candidatos conhecidos contra o DivulgaCandContas, incluindo pelo menos um reeleição e um vereador que concorre a deputado
- [ ] 6.8 (opcional) Descobrir padrão de URL estável do DivulgaCandContas por candidato e incluir no detalhe
