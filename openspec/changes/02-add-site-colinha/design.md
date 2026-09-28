# Design: Site público e colinha

## Context

Público amplo, de todas as idades, a maioria no celular e muitas vezes com internet
fraca. O link chega pelo WhatsApp, então a prévia do link importa. O site não tem
servidor: tudo é gerado antes, a partir de `data/processed/`. A equipe ensina Python;
manter o site em Python + Jinja2 evita uma segunda cadeia de build.

## Goals / Non-Goals

**Goals**
- Página de candidato útil em até 3 segundos numa conexão 3G.
- Página de candidato e listas funcionando sem JavaScript.
- Colinha imprimível, privada e à prova de erro de digitação.
- Neutralidade visível: mesma cara para todos.

**Non-Goals**
- Contas de usuário, comentários, comparação entre candidatos, recomendações.

## Decisions

### D1. Uma página HTML estática por candidato
Alternativa considerada: uma única página que carrega o candidato por JavaScript.
Rejeitada porque a prévia do WhatsApp lê as meta tags do HTML e não executa JavaScript.
Custo: cerca de 20 mil arquivos em 2026. Em servidor próprio (D9) não há limite de
arquivos por deploy.

### D2. URLs curtas
`/` (escolher UF), `/{uf}/` (cargos da UF), `/{uf}/{cargo}/` (lista),
`/{uf}/{numero}/` (candidato), `/br/{numero}/` (presidente), `/colinha/`,
`/metodologia/`. UF e cargo em minúsculas, cargo em slug (`deputado-estadual`).

### D3. JavaScript puro e progressivo
As listas são HTML completo; o JavaScript acrescenta busca instantânea e filtros sobre
as próprias linhas da lista, que trazem os campos de filtro em atributos `data-*`. Busca
ignora acentos e maiúsculas e aceita número e partido. Sem framework, sem dependências,
um arquivo por funcionalidade (`busca.js`, `colinha.js`, `compartilhar.js`).

Alternativa considerada: filtrar sobre o `indice.json` da UF, como previsto no início.
Trocada na implementação porque a lista estática já tem todas as linhas do cargo: filtrar
o HTML evita um segundo download e mantém um único lugar com os dados exibidos. O
`indice.json` continua publicado em `/dados/{UF}.json`, usado pela colinha para conferir
candidaturas guardadas.

O único script inline (marca `html.js`) tem o hash na Content-Security-Policy do nginx
(D9); CSS e JS levam `?v=<hash do conteúdo>` para permitir cache longo.

### D4. Direção visual
O assunto é a urna eletrônica e o papelzinho anotado que o eleitor leva para votar. O
elemento marcante é o **número em caixinhas**: cada dígito numa caixa, como na tela da
urna. Ele aparece na lista, no topo da página do candidato e na colinha. O resto da
interface fica quieto.

Cores (tokens em `:root`):

| Token | Valor | Uso |
|---|---|---|
| `--papel` | `#FFFFFF` | fundo |
| `--cinza-urna` | `#E9ECEF` | blocos e caixinhas dos dígitos |
| `--texto` | `#1A1C1F` | texto principal |
| `--texto-suave` | `#555B64` | fontes, datas, notas |
| `--tinta` | `#2340A8` | links e anotações da colinha (azul de caneta esferográfica) |
| `--confirma` | `#1B7F3B` | botão "Adicionar à colinha", como a tecla CONFIRMA |
| `--corrige` | `#B4530F` | botão "Tirar da colinha", como a tecla CORRIGE |
| `--pauta` | `#C9D6EA` | linhas de caderno, só na colinha |

Regras de cor: nenhuma cor dominante associada a partido ou campanha; nunca combinar
verde e amarelo; conferir contraste AA de todo par texto/fundo antes de publicar.

Tipografia: Atkinson Hyperlegible Next para o texto e Atkinson Hyperlegible Mono para
números, fontes feitas para máxima legibilidade (verificar a licença ao baixar e
auto-hospedar). Fallback: `system-ui` e `ui-monospace`. Corpo de 18px no celular, escala
1,25, linhas com no máximo 70 caracteres, texto alinhado à esquerda.

Movimento: só como resposta a uma ação (o dígito entrando na colinha ao adicionar).
Respeitar `prefers-reduced-motion`.

Página do candidato no celular:

```
┌──────────────────────────────┐
│ Deputado estadual em SP      │
│ MARIA DA SILVA               │
│ ┌─┐┌─┐┌─┐┌─┐┌─┐              │
│ │1││2││3││4││5│  SIGLA       │
│ └─┘└─┘└─┘└─┘└─┘              │
│ [ Adicionar à colinha ]      │
├──────────────────────────────┤
│ Trajetória eleitoral         │
│ 2022  Deputada estadual      │
│       SP, Suplente           │
│ 2020  Vereadora              │
│       Campinas, Eleita       │
│ Pesquisamos de 2014 a 2024.  │
├──────────────────────────────┤
│ (Câmara, change 03)          │
├──────────────────────────────┤
│ Dados declarados ao TSE      │
│ Idade, gênero, cor ou raça,  │
│ instrução, ocupação, bens,   │
│ redes sociais                │
├──────────────────────────────┤
│ Fontes: TSE, extraído em ... │
│ Encontrou um erro?           │
└──────────────────────────────┘
```

A trajetória vem antes dos dados declarados porque é o que o site tem de diferente.

### D5. Linguagem
Português simples, frases curtas, sem sigla solta: "Eleita pela votação do partido
(quociente partidário)" em vez de "ELEITO POR QP". Flexão de gênero pelo gênero
declarado. Botões dizem o que fazem: "Adicionar à colinha", "Tirar da colinha",
"Imprimir colinha". Estado vazio orienta: "Nenhum candidato com esses filtros. Tente
tirar o filtro de partido."

### D6. Colinha
Estado em `localStorage` com a chave `colinha:v1:{uf}` e, para presidente, `colinha:v1:BR`
(a escolha de presidente vale para a colinha de todas as UFs), sempre dentro de `try/catch`;
se o armazenamento falhar, a colinha funciona só enquanto a página estiver aberta e
avisa isso. Vagas por cargo e ordem de votação vêm do `config.toml` (`vagas_colinha` e
`ordem_urna`). Ordem usada: a de 2018, que também teve duas vagas de senador (deputado
federal, deputado estadual ou distrital, senador 1ª vaga, senador 2ª vaga, governador,
presidente). O site do TSE bloqueia acesso automatizado; a ordem de 2026 precisa ser
confirmada por uma pessoa (tarefa 3.3). Impressão com CSS de impressão: dígitos grandes, cabe em meia
folha A4.

### D7. Privacidade e terceiros
Nenhum script, fonte ou imagem de outro domínio. Se a StatCode quiser contar visitas,
só contagem agregada de páginas, sem eventos ligados a candidatos e sem cookies.

### D8. Orçamento de desempenho
Página de candidato abaixo de 60 KB transferidos (sem fontes em cache). `indice.json` da
maior UF abaixo de 250 KB com gzip. Fontes: só os pesos usados, em woff2, com
`font-display: swap`.

Medido em 28/09/2026, todas as UFs: maior página de candidato 9,8 KB (2,6 KB com gzip;
redes sociais limitadas a 20 links exibidos, mesmo limite para todos); maior
`indice.json` (SP) 49 KB com gzip; CSS e JS 5,7 KB com gzip; fontes 52 KB (variáveis,
subconjunto latino). A página mais pesada é a lista de deputado estadual de SP: 1,5 MB de
HTML, 101 KB com gzip. 20.228 páginas geradas em 13 s.

### D9. Publicação
O site roda no servidor da StatCode, gerenciado pelo Dokploy, em
`colinha.statcode.com.br`, com HTTPS pelo domínio configurado no Dokploy.

Fluxo (decidido em 28/09/2026: releases do GitHub, o mesmo padrão de outro projeto da
StatCode): a equipe roda a pipeline e o gerador na própria máquina, revisa o resultado e
só então executa `just publicar`, que compacta `site/dist/` em `site.tar.gz` (~9 MB),
cria a release `site-AAAAMMDD-HHMM` no GitHub com esse anexo, grava a tag em
`deploy/release.txt` (commit e push) e chama o webhook do Dokploy. O Dokploy usa o
provider Git deste repositório: constrói a imagem pelo `Dockerfile`, que baixa o
`site.tar.gz` da release indicada em `deploy/release.txt` e o coloca num nginx com
`nginx.conf` próprio (gzip, cache, página 404).

Por que a tag fica num arquivo versionado: se o Dockerfile buscasse "a última release",
o cache do Docker poderia reaproveitar o download antigo. Com o arquivo, cada publicação
muda o contexto do build e força o download; o histórico do git registra cada
publicação. Rollback: voltar `deploy/release.txt` para a tag anterior (commit e push) ou
passar `RELEASE=<tag anterior>` como build arg no Dokploy e fazer o redeploy.

Repositório privado: o download precisa de um token do GitHub com leitura, passado ao
build como secret `github_token`. Público: nada a configurar. A URL do webhook fica em
`.env`, fora do git.

Alternativas consideradas:
- Build dentro do Dokploy (Dockerfile que roda a pipeline): rejeitada porque publicaria
  dados sem revisão humana de vínculos e neutralidade, baixaria ~310 MB do TSE a cada
  deploy e dependeria de o TSE aceitar o IP do servidor.
- rsync de `site/dist/` para um volume servido por nginx: rejeitada porque a troca não é
  atômica e não deixa histórico de versões para voltar atrás.
- Build type "Static" do Dokploy: rejeitado porque não permite ajustar gzip, cache e 404.
- Imagem pronta num registry (GHCR ou próprio), puxada pelo provider Docker: funciona e
  evita o build no servidor, mas exige configurar um registry. Preterida por releases,
  que a equipe já usa em outro projeto.
- Imagem Docker salva (`docker save`) como anexo de release: rejeitada porque o Dokploy
  não carrega imagem de release; exigiria deploy manual por SSH.

Implementação: `Dockerfile` em dois estágios (alpine baixa a release; nginx:1.28-alpine
serve) e `deploy/nginx.conf` com gzip, cache de 30 dias em `/static/` (CSS e JS com
`?v=`), 5 minutos no resto, 404 própria e cabeçalhos de segurança, incluindo
Content-Security-Policy que só permite recursos do próprio domínio. `just publicar` roda
`deploy/publicar.sh` (confere privacidade antes de tudo); usa o `gh`, que entrou no
`flake.nix`. O build foi testado com uma API do GitHub simulada. Docker (para testar a
imagem localmente) vem do sistema: o daemon não roda dentro do shell do Nix.

## Risks / Trade-offs

- **Erro de dado publicado.** Toda página tem "Encontrou um erro?" com e-mail
  pré-preenchido com UF, número e URL; correções entram em `data/manual/` e o site é
  republicado.
- **Percepção de viés.** Template único, ordem alfabética, revisão de neutralidade antes
  de publicar (`/checar-neutralidade` e revisão humana de páginas de partidos diferentes).
- **GitHub ou servidor fora do ar na semana da eleição.** Um deploy que falha não
  derruba o site: a imagem anterior continua no ar, e o rollback é feito pela tag da
  release (D9).
- **Dados mudam até a eleição.** A colinha confere os candidatos salvos contra o índice
  atual e avisa quando algum deixou de estar apto.

## Open Questions

- O repositório `StatCodeBR/colinha-de-voto` vai ser público ou privado? Privado exige o
  token de leitura como build secret no Dokploy (D9).
- A StatCode quer alguma contagem de visitas? Se sim, qual ferramenta sem cookies?
- Fotos entram no MVP? (Tarefa opcional; aumentam muito o reconhecimento do candidato.)
