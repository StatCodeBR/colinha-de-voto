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
just publicar                 # imagem nginx + deploy no Dokploy
```

Comandos extras no Claude Code: `/atualizar-dados`, `/revisar-vinculos RR` e
`/checar-neutralidade`.

## Publicação e ciclo diário até a eleição

O site roda no servidor da StatCode, gerenciado pelo Dokploy, como uma imagem nginx com
o site já gerado (design D9 da change 02). Quem publica gera o site na própria máquina,
confere e só então envia.

Configuração, uma vez só:

1. Crie o `.env` na raiz (fica fora do git):
   ```bash
   COLINHA_IMAGEM=<registry>/statcode/colinha-do-voto
   DOKPLOY_WEBHOOK=<URL do webhook de deploy da aplicação no Dokploy>
   ```
2. `docker login <registry>`.
3. No Dokploy, a aplicação usa o provider Docker com a imagem
   `$COLINHA_IMAGEM:latest`, porta 80, e o domínio `colinha.statcode.com.br` com HTTPS.

Todo dia, até 4 de outubro:

```bash
just atualizar       # rebaixa os dados do TSE, reprocessa e regenera o site
just privacidade     # confere que nada pessoal vazou
just servir          # abra três páginas no celular (largura estreita) e confira
just publicar        # monta a imagem, envia ao registry e dispara o redeploy
```

Se o `just atualizar` parar com erro, o TSE mudou algo (situação nova, coluna nova). O
site anterior continua no ar; registre em `docs/fontes.md` e ajuste antes de publicar.
Vínculos novos em revisão aparecem em `data/processed/revisao_vinculos.csv`
(`/revisar-vinculos SP` no Claude Code).

Para voltar à versão anterior: cada publicação gera uma tag de data e hora, anotada em
`deploy/publicacoes.log`. No Dokploy, troque a imagem da aplicação para a tag anterior
(`$COLINHA_IMAGEM:AAAAMMDD-HHMM`) e faça o redeploy.

## Onde mudar o quê

Nome do projeto, subdomínio, e-mail de contato, anos de histórico e UFs ficam em
`config.toml`. Fontes de dados e peculiaridades encontradas ficam em `docs/fontes.md`.
O que vem depois do MVP está em `docs/roadmap.md`.
