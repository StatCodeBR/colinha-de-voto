## Why

A StatCode precisa saber se o site está sendo usado: quantas pessoas acessam, por quais
páginas entram e se a divulgação (WhatsApp, redes) funciona. Hoje só há o log bruto do
nginx no container, que registra o IP do proxy (Traefik), e não o do visitante, e se perde
a cada redeploy, que acontece todo dia até a eleição. O design da change 02 (D7) já deixou
a regra: contagem agregada de páginas, sem cookies e sem eventos ligados a candidatos.

## What Changes

- O nginx passa a registrar os acessos num volume persistente, um arquivo por dia, com o
  IP do visitante **anonimizado** (último bloco zerado) e sem cabeçalhos além de navegador
  e origem do acesso.
- Os registros são apagados depois de 30 dias.
- Novo comando `just acessos`: gera, a partir desses registros, um relatório HTML interno
  (GoAccess) com páginas vistas por dia, visitantes aproximados, páginas mais vistas,
  origem dos acessos e navegadores. O relatório fica na máquina de quem roda o comando e
  não é publicado.
- A página "Como fizemos" ganha um parágrafo sobre a contagem de acessos.
- `docs/deploy.md` ganha o passo de criar o volume no Dokploy.

Fora do escopo: qualquer script de contagem no navegador (Google Analytics, Plausible,
Umami ou similares), porque o site promete não ter scripts de terceiros e não precisa de
um para contar páginas; cookies; saber quais candidatos entram numa colinha, que continua
só no celular do eleitor; e painel em tempo real.

## Capabilities

### New Capabilities

- `contagem-acessos`: registro de acessos com IP anonimizado, retenção limitada e
  relatório agregado interno.

### Modified Capabilities

- `site-publico`: a metodologia passa a informar a contagem de acessos. A capacidade
  ainda está na change `02-add-site-colinha` (não arquivada); esta change deve ser
  arquivada depois dela.

## Impact

- `deploy/nginx.conf` (formato do log, IP real anonimizado, arquivo por dia) e
  `Dockerfile` (pasta de logs com permissão para o nginx).
- Novo `deploy/relatorio-acessos.sh` e recipe `just acessos`; acesso SSH ao servidor
  configurado no `.env`.
- Template da metodologia.
- Configuração no Dokploy: um volume montado em `/var/log/colinha`.
- Nenhuma mudança na pipeline de dados nem no JavaScript do site.
