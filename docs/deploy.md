# Deploy no Dokploy: passo a passo

Configuração feita uma vez. Depois, o dia a dia é só `just atualizar` e `just publicar`
(ver README). Decisões no design D9 da change 02.

Nomes de abas e campos conferidos na documentação do Dokploy em 28/09/2026
(docs.dokploy.com: Applications, Providers, Domains, Auto Deploy). Se a interface de
vocês estiver diferente, a versão do Dokploy pode ser outra.

## 1. DNS (no provedor do domínio statcode.com.br)

- [ ] Criar registro `A` para `colinha` apontando para o IP do servidor do Dokploy
      (ou `CNAME` para o nome do servidor, se for o padrão de vocês).
- [ ] Esperar propagar: `dig colinha.statcode.com.br` deve devolver o IP do servidor.

## 2. Aplicação no Dokploy

- [ ] Entrar no painel do Dokploy e abrir (ou criar) o projeto da StatCode.
- [ ] **Create Service → Application**. Nome: `colinha-do-voto`.
- [ ] Aba **General → Provider**: escolher **Git**.
  - Repository URL: `https://github.com/StatCodeBR/colinha-de-voto.git` (HTTPS; o
    repositório é público, não precisa de chave SSH).
  - Branch: `main`.
  - **Save**.
- [ ] Ainda em **General → Build Type**: escolher **Dockerfile**.
  - Dockerfile Path: `Dockerfile`
  - Docker Context Path: `.`
  - Docker Build Stage: deixar vazio.
  - **Save**.
- [ ] Ligar **Auto Deploy** (na aba General).
- [ ] (Opcional) **Watch Paths**: `Dockerfile`, `deploy/**`. Assim só publicações e
      mudanças de deploy disparam build; mudanças de código Python não.

## 3. Domínio e HTTPS

- [ ] Aba **Domains → Add Domain**:
  - Host: `colinha.statcode.com.br`
  - Path: `/`
  - Container Port: `80`
  - HTTPS: ligado
  - Certificate: `letsencrypt`
  - Salvar. Mudança de domínio vale na hora, sem redeploy.

## 4. Webhook no GitHub

- [ ] Na aplicação do Dokploy, aba **Deployments**: copiar a **Webhook URL**.
- [ ] No GitHub, `StatCodeBR/colinha-de-voto` → **Settings → Webhooks → Add webhook**:
  - Payload URL: a Webhook URL copiada.
  - Content type: `application/json`.
  - Evento: **Just the push event**.
  - **Add webhook**.
- [ ] Não colocar `DOKPLOY_WEBHOOK` no `.env`: o push do `just publicar` já dispara o
      deploy pelo webhook do GitHub.

## 5. Primeira publicação

Pré-requisito: o PR da `change-01-pipeline-tse` já está na `main`.

- [ ] Na máquina de quem publica: `git checkout main && git pull`.
- [ ] `gh auth login` (conta com permissão de criar release e fazer push).
- [ ] `just atualizar` (baixa do TSE, processa e gera o site; alguns minutos).
- [ ] `just privacidade` (tem que dizer "Nenhum CPF, e-mail nem nome civil…").
- [ ] `just servir` e abrir três páginas no celular ou em largura de celular.
- [ ] `just publicar`. Ele cria a release `site-AAAAMMDD-HHMM`, faz commit de
      `deploy/release.txt` e push.
- [ ] No Dokploy, aba **Deployments**: acompanhar o build. O log mostra
      "site da release site-…" quando o download dá certo.
- [ ] Abrir `https://colinha.statcode.com.br` no celular e conferir:
  - [ ] página inicial, uma UF, uma lista e uma página de candidato;
  - [ ] cadeado do HTTPS;
  - [ ] link de um candidato colado no WhatsApp mostra a prévia com nome, número, cargo
        e UF (tarefa 6.3 da change 02).

## 6. Contagem de acessos (change add-contagem-acessos)

Fazer **antes** do primeiro deploy com a change; sem o volume, os registros somem a cada
publicação. Nomes de abas conferidos só de memória: se não baterem, procurar "Volumes" e
"Schedules" na aplicação.

- [x] Aba **Advanced → Volumes** (ou **Mounts**) → **Add Volume**:
  - Tipo: **Volume Mount** (volume do Docker, não pasta do servidor).
  - Volume Name: `colinha-logs`
  - Mount Path: `/var/log/colinha`
  - Salvar e fazer **Deploy** (vale no próximo deploy).
- [x] Aba **Schedules** → nova tarefa, para apagar registros com mais de 30 dias:
  - Nome: `limpar-acessos`
  - Agenda (cron): `15 3 * * *` (todo dia às 3h15)
  - Comando: `find /var/log/colinha -name 'acessos-*.log' -mtime +30 -delete`
  - Shell: `sh`. Salvar e rodar uma vez para conferir que não dá erro.
- [ ] No servidor, conferir o nome real do volume: `docker volume ls | grep colinha`.
      Se o Dokploy tiver acrescentado um prefixo, pôr o nome em `VOLUME_ACESSOS` no `.env`
      de quem roda `just acessos`.
- [ ] No `.env` de quem gera o relatório: `SERVIDOR_SSH=usuario@servidor`. O usuário
      precisa entrar por SSH com chave e rodar `docker` sem senha.
- [ ] Log do Traefik: o Dokploy pode guardar um log de acesso próprio, com o IP completo
      (página **Requests** do painel, ou `accessLog` em `/etc/dokploy/traefik/traefik.yml`).
      Se estiver ligado, desligar ou reduzir a retenção, e anotar aqui o que foi feito. A
      promessa da página "Como fizemos" depende disso.
- [ ] Depois do primeiro deploy: abrir o site, esperar um minuto e conferir que o arquivo
      do dia existe (`docker exec <container> ls /var/log/colinha`), depois `just acessos`.

## Se algo der errado

- **Build falha com "deploy/release.txt vazio"**: ainda não houve `just publicar`.
- **Build falha com "release … sem site.tar.gz"**: a release não tem o anexo; rode
  `just publicar` de novo.
- **Deployment mostra "Branch Not Match"**: a branch da aplicação não é `main`.
- **Site fora do ar depois de publicar**: voltar para a release anterior. Escrever a tag
  anterior (lista em `https://github.com/StatCodeBR/colinha-de-voto/releases`) em
  `deploy/release.txt`, commit e push. Em emergência, na aba **Environment → Build-time
  Arguments**, `RELEASE=<tag anterior>` e **Deploy** (tirar depois).
- **HTTPS não sai**: o DNS ainda não aponta para o servidor, ou a porta 80 do servidor
  está fechada (o Let's Encrypt precisa dela). Ver os logs do Traefik no Dokploy.
- **`just acessos` diz que não há registros**: o volume não está montado em
  `/var/log/colinha`, o nome em `VOLUME_ACESSOS` está errado, ou o nginx não tem permissão
  de escrita na pasta (o volume foi criado antes, com outro dono). Neste último caso:
  `docker run --rm -v colinha-logs:/logs alpine chown 101:101 /logs` e redeploy.
