## 1. Registro no nginx

- [x] 1.1 `deploy/nginx.conf`: `set_real_ip_from` das redes internas do Docker e `real_ip_header X-Forwarded-For`, com `real_ip_recursive on`
- [x] 1.2 `map` que anonimiza o IP (IPv4 com último bloco zerado; IPv6 com os três primeiros grupos; resto vira `-`) e `log_format` combinado usando o IP anonimizado
- [x] 1.3 `map` do dia a partir de `$time_iso8601`; `access_log /var/log/colinha/acessos-$dia.log` com `open_log_file_cache`; `log_not_found off`
- [x] 1.4 `Dockerfile`: criar `/var/log/colinha` com dono `nginx`
- [x] 1.5 Teste local com `docker run` e volume nomeado: requisições com `X-Forwarded-For` de IPv4, IPv6 e sem cabeçalho geram linhas com `189.40.12.0`, `2804:14c:5b73::` e `-`; o arquivo do dia sobrevive a trocar o container
- [x] 1.6 Conferir que nenhuma linha do registro tem IP completo, cookie ou query string da colinha além de `?uf=`

## 2. Relatório

- [x] 2.1 GoAccess no `flake.nix`
- [x] 2.2 `deploy/relatorio-acessos.sh`: limpeza de 30 dias no servidor, leitura dos registros pelo SSH (container `alpine` com o volume em leitura) direto para o GoAccess local, saída em `relatorios/acessos-AAAAMMDD.html`; aviso claro quando não houver registros
- [x] 2.3 Recipe `just acessos`, `SERVIDOR_SSH` no `.env` e `relatorios/` no `.gitignore`
- [x] 2.4 Teste do script contra o container local da tarefa 1.5 (SSH para `localhost` ou variável que troca o comando remoto)

## 3. Site

- [x] 3.1 Parágrafo "Contagem de acessos" na metodologia: sem cookies, sem scripts de contagem, IP anonimizado, 30 dias, colinha que não sai do celular
- [x] 3.2 Teste de geração: a metodologia tem os quatro pontos; nenhuma página ganhou script novo
- [x] 3.3 `just check`, `just limpar && just dev`, `just privacidade` e `/checar-neutralidade`

## 4. Servidor e documentação

- [x] 4.1 `docs/deploy.md`: criar o volume `colinha-logs` montado em `/var/log/colinha` (aba Advanced → Volumes) e a tarefa diária de limpeza (aba Schedules)
- [x] 4.2 README: `just acessos`, o que o relatório mostra e por que "visitantes" é aproximado
- [ ] 4.3 (equipe) Conferir no Dokploy se o log de acesso do Traefik está ligado; se estiver, desligar ou reduzir a retenção, e registrar em `docs/deploy.md`
- [ ] 4.4 (equipe) Depois da primeira publicação com a change: conferir que o arquivo do dia existe no volume e rodar `just acessos`
