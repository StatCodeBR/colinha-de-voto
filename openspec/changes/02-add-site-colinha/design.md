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
Custo: dezenas de milhares de arquivos. Se o provedor limitar, o plano B é gerar
páginas só para candidaturas aptas e deixar as demais na lista com link para o TSE.

### D2. URLs curtas
`/` (escolher UF), `/{uf}/` (cargos da UF), `/{uf}/{cargo}/` (lista),
`/{uf}/{numero}/` (candidato), `/br/{numero}/` (presidente), `/colinha/`,
`/metodologia/`. UF e cargo em minúsculas, cargo em slug (`deputado-estadual`).

### D3. JavaScript puro e progressivo
As listas são HTML completo; o JavaScript acrescenta busca instantânea e filtros usando o
`indice.json` da UF. Busca ignora acentos e maiúsculas e aceita número. Sem framework,
sem dependências, um arquivo por funcionalidade.

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
Estado em `localStorage` com a chave `colinha:v1:{uf}`, sempre dentro de `try/catch`;
se o armazenamento falhar, a colinha funciona só enquanto a página estiver aberta e
avisa isso. Vagas por cargo vêm do `config.toml`. Ordem de exibição: a ordem oficial de
votação na urna em 2026 (confirmar no TSE; em 2018, com duas vagas de senador, foi
deputado federal, deputado estadual ou distrital, senador 1ª vaga, senador 2ª vaga,
governador, presidente). Impressão com CSS de impressão: dígitos grandes, cabe em meia
folha A4.

### D7. Privacidade e terceiros
Nenhum script, fonte ou imagem de outro domínio. Se a StatCode quiser contar visitas,
só contagem agregada de páginas, sem eventos ligados a candidatos e sem cookies.

### D8. Orçamento de desempenho
Página de candidato abaixo de 60 KB transferidos (sem fontes em cache). `indice.json` da
maior UF abaixo de 250 KB com gzip. Fontes: só os pesos usados, em woff2, com
`font-display: swap`.

## Risks / Trade-offs

- **Erro de dado publicado.** Toda página tem "Encontrou um erro?" com e-mail
  pré-preenchido com UF, número e URL; correções entram em `data/manual/` e o site é
  republicado.
- **Percepção de viés.** Template único, ordem alfabética, revisão de neutralidade antes
  de publicar (`/checar-neutralidade` e revisão humana de páginas de partidos diferentes).
- **Limite de arquivos no provedor.** Contar arquivos antes do primeiro deploy (plano B
  em D1).
- **Dados mudam até a eleição.** A colinha confere os candidatos salvos contra o índice
  atual e avisa quando algum deixou de estar apto.

## Open Questions

- Qual provedor hospeda o subdomínio da A Caminho das Pedras e quais os limites dele?
- A StatCode quer alguma contagem de visitas? Se sim, qual ferramenta sem cookies?
- Fotos entram no MVP? (Tarefa opcional; aumentam muito o reconhecimento do candidato.)
