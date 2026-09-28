# Colinha do Voto

Ferramenta gratuita e apartidária para o eleitor conhecer os candidatos antes de votar:
quem são, se já concorreram, se já foram eleitos e, para quem passou pela Câmara dos
Deputados, o que apresentaram por lá. Tudo a partir de dados abertos oficiais (TSE e
Câmara). Feita pela StatCode.

O eleitor ainda monta a sua **colinha**: escolhe os candidatos e imprime ou anota os
números para levar à urna (o celular não pode entrar na cabine de votação).

## Como começar

Pré-requisitos: [Nix](https://nixos.org/download) com flakes habilitados e Claude Code
(instalado à parte). O `flake.nix` fornece Python 3.12, uv, just, ruff e Node.js. Com
[direnv](https://direnv.net), o ambiente entra sozinho ao abrir a pasta (`direnv allow`
na primeira vez).

```bash
# 1. Descompacte o pacote e crie o repositório. O commit vem antes do nix develop:
#    num repositório git, o Nix só enxerga arquivos rastreados.
cd colinha-do-voto
git init
git add -A && git commit -m "Estrutura inicial"

# 2. Entre no ambiente (gera o flake.lock na primeira vez; faça commit dele)
nix develop
git add flake.lock && git commit -m "Trava o nixpkgs"

# 3. Instale o OpenSpec (fica em .npm-global/, dentro do projeto)
just setup

# 4. Inicialize o OpenSpec para o Claude Code
openspec init --tools claude
#    Se o init sobrescrever openspec/config.yaml, restaure com: git checkout openspec/config.yaml
#    Se ele criar ou alterar um CLAUDE.md, mantenha o bloco dele e o nosso abaixo.

# 5. Confira se as changes estão bem formadas
just specs
```

Se o `just specs` apontar algum problema de formato, peça ao Claude Code para corrigir
antes de começar a implementar.

## Fluxo de trabalho

O projeto está dividido em três changes do OpenSpec, feitas nesta ordem:

| Change | O que entrega | Prioridade |
|---|---|---|
| `01-add-pipeline-tse` | Dados de 2026 limpos + trajetória eleitoral 2014–2024 | MVP |
| `02-add-site-colinha` | Site estático, página de cada candidato e a colinha | MVP |
| `03-add-dados-camara` | Projetos, temas e frentes de quem foi deputado federal | Logo depois do MVP |

Antes de cada uma, **leiam `proposal.md` e `design.md`**: é ali que vocês decidem o que
entra. Depois, no Claude Code:

```
/opsx:apply 01-add-pipeline-tse
```

Revisem o resultado, rodem os testes e arquivem:

```
/opsx:archive 01-add-pipeline-tse
```

Ideias novas ou mudanças de rumo viram uma nova change com `/opsx:propose`. Para pensar
antes de decidir, use `/opsx:explore`.

## Comandos do projeto

Rode `just` para ver a lista completa. Os principais:

```bash
just dev                      # pipeline + site só para RR (ciclo rápido)
just baixar --uf SP           # baixa dados do TSE
just processar --uf SP        # normaliza e cruza o histórico
just camara                   # dados da Câmara (change 03)
just site                     # gera o site em site/dist/
just servir                   # abre o site em http://localhost:8000
just tudo                     # pipeline completo, todas as UFs
just atualizar                # rebaixa, reprocessa e regenera (todo dia até a eleição)
just check                    # lint + testes + validação das specs
just privacidade              # nenhum CPF/nome civil protegido nas saídas e no site
just publicar                 # release do site no GitHub + deploy no Dokploy
```

Comandos extras no Claude Code: `/atualizar-dados`, `/revisar-vinculos RR` e
`/checar-neutralidade`.

## Publicação e ciclo diário até a eleição

O site roda no servidor da StatCode, gerenciado pelo Dokploy (design D9 da change 02).
Quem publica gera o site na própria máquina, confere e só então envia: o `just publicar`
cria uma release no GitHub com o site compactado (`site.tar.gz`), grava a tag em
`deploy/release.txt` e pede o redeploy. O Dokploy constrói a imagem nginx baixando essa
release.

Configuração, uma vez só:

1. `gh auth login` (o `gh` vem do `nix develop`), com permissão para criar releases e
   fazer push em `StatCodeBR/colinha-de-voto`.
2. No Dokploy, crie a aplicação (passo a passo em `docs/deploy.md`):
   provider Git com `https://github.com/StatCodeBR/colinha-de-voto.git`, branch `main`,
   build type Dockerfile, domínio `colinha.statcode.com.br` na porta 80 com HTTPS, e
   Auto Deploy ligado.
3. No GitHub, cadastre o webhook do Dokploy (Settings → Webhooks), evento `push`. Assim
   o commit que o `just publicar` faz em `deploy/release.txt` dispara o deploy. Deixe
   `DOKPLOY_WEBHOOK` fora do `.env`: o webhook do Dokploy confere a branch no conteúdo
   enviado pelo GitHub, e uma chamada direta pode ser recusada.

Todo dia, até 4 de outubro:

```bash
just atualizar       # rebaixa os dados do TSE, reprocessa e regenera o site
just privacidade     # confere que nada pessoal vazou
just servir          # abra três páginas no celular (largura estreita) e confira
just publicar        # cria a release, grava a tag, faz push e dispara o redeploy
```

Se o `just atualizar` parar com erro, o TSE mudou algo (situação nova, coluna nova). O
site anterior continua no ar; registre em `docs/fontes.md` e ajuste antes de publicar.
Vínculos novos em revisão aparecem em `data/processed/revisao_vinculos.csv`
(`/revisar-vinculos SP` no Claude Code).

Para voltar à versão anterior: as releases ficam em
`https://github.com/StatCodeBR/colinha-de-voto/releases` (tags `site-AAAAMMDD-HHMM`).
Escreva a tag anterior em `deploy/release.txt`, faça commit e push, e dispare o redeploy.
Em emergência, dá para passar `RELEASE=<tag anterior>` como build arg na aplicação do
Dokploy e fazer o redeploy (lembre de tirar depois).

## Onde mudar o quê

Nome do projeto, subdomínio, e-mail de contato, anos de histórico e UFs ficam em
`config.toml`. Fontes de dados e peculiaridades encontradas ficam em `docs/fontes.md`.
O que vem depois do MVP está em `docs/roadmap.md`.
