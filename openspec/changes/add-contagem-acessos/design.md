## Context

O site é estático, servido por nginx (imagem `nginx:1.28-alpine`) atrás do Traefik do
Dokploy (change 02, D9). O log de acesso padrão da imagem vai para a saída do container,
registra o IP do Traefik (e não o do visitante) e se perde quando o container é trocado,
o que acontece a cada `just publicar` (todo dia até a eleição). A CSP do site só permite
recursos do próprio domínio, e a metodologia promete: sem cookies, sem scripts de
terceiros, colinha só no navegador.

## Goals / Non-Goals

**Goals:**
- Páginas vistas por dia e por página, origem dos acessos e navegadores, confiáveis.
- Estimativa de visitantes, sabendo que é aproximada.
- Nenhum dado que identifique uma pessoa guardado no servidor, nem por pouco tempo.

**Non-Goals:**
- Tempo na página, cliques, rolagem ou qualquer medida que exija script no navegador.
- Relatório público ou em tempo real.

## Decisions

### D1. Contar pelo log do nginx, não por script no navegador
O servidor já recebe cada página pedida; basta registrar direito.

Alternativas consideradas: Plausible ou Umami hospedados pela StatCode (sem cookies,
mas exigem um script em todas as páginas, abrem a CSP e contrariam a promessa de "sem
scripts de contagem"); Google Analytics (terceiro, cookies, dados fora do controle da
StatCode). Rejeitadas.

### D2. IP real recuperado e anonimizado antes de gravar
`set_real_ip_from` com as redes internas do Docker (`10.0.0.0/8`, `172.16.0.0/12`,
`192.168.0.0/16`) e `real_ip_header X-Forwarded-For` recuperam o IP do visitante que o
Traefik repassa. Um `map` grava só o prefixo: IPv4 com o último bloco zerado, IPv6 com os
três primeiros grupos. Formato do registro: o `combined` do nginx com o IP anonimizado
no lugar do IP (o GoAccess lê como `COMBINED`).

Ajustes feitos na implementação: o caminho é gravado sem query string (só `?uf=XX`
continua, porque é a página da colinha de cada UF), para que `fbclid`, `utm_*` e afins
não entrem no registro; a origem (referer) fica só com o domínio; IP interno (o do proxy,
quando o visitante chega sem `X-Forwarded-For` válido) vira `-`. O GoAccess descarta
linhas com IP `-`, então o `just acessos` as troca por `0.0.0.0` no caminho até ele,
sem gravar nada.

Alternativas consideradas: gravar o IP completo e anonimizar só no relatório (o dado
identificável ficaria 30 dias no disco); gravar um hash do IP (o espaço de IPv4 é pequeno
e o hash se reverte por força bruta, o mesmo motivo de não usar hash de CPF, design D3 da
change 01); não gravar IP nenhum (perde qualquer estimativa de visitantes, que é uma das
perguntas da StatCode).

### D3. Um arquivo por dia num volume persistente
`access_log /var/log/colinha/acessos-$dia.log`, com `$dia` tirado de `$time_iso8601` por
`map`, e `open_log_file_cache` para não abrir o arquivo a cada requisição. No Dokploy, um
volume nomeado `colinha-logs` montado em `/var/log/colinha`. O `Dockerfile` cria a pasta
com dono `nginx`, e o volume vazio herda essa permissão na primeira montagem.

Alternativa considerada: manter o log na saída do container. Rejeitada porque o redeploy
diário apaga o histórico.

### D4. Limpeza de 30 dias no próprio servidor
Uma tarefa agendada do Dokploy (aba Schedules da aplicação), diária, roda no container:
`find /var/log/colinha -name 'acessos-*.log' -mtime +30 -delete`. O `just acessos` roda a
mesma limpeza antes do relatório, como segunda garantia.

Alternativa considerada: rotação por logrotate (não existe na imagem alpine do nginx e
exigiria outro processo no container).

### D5. Relatório gerado na máquina da equipe, só com números agregados
`just acessos` (script `deploy/relatorio-acessos.sh`) lê os arquivos pelo SSH, com um
container `alpine` que só monta o volume em leitura, e passa o conteúdo direto ao
GoAccess local, que gera `relatorios/acessos-AAAAMMDD.html` (pasta fora do git). Os
registros transitam, mas não são gravados na máquina de quem roda. O GoAccess entra no
`flake.nix`. O host SSH fica no `.env` (`SERVIDOR_SSH`).

Alternativa considerada: rodar o GoAccess no servidor e publicar o relatório numa página
protegida. Rejeitada por prazo e por criar uma área nova para proteger.

## Risks / Trade-offs

- [Visitantes subestimados: operadoras móveis põem muitos usuários atrás do mesmo IP
  (CGNAT), e o prefixo anonimizado junta ainda mais] → o relatório e o README chamam o
  número de "visitantes aproximados"; a métrica principal é páginas vistas.
- [O Traefik do Dokploy pode ter log de acesso próprio, com IP completo] → tarefa de
  conferir a configuração do Traefik no Dokploy; se estiver ligado, desligar ou reduzir a
  retenção. Fora desta change, mas a promessa da metodologia depende disso.
- [O log de erros do nginx inclui o IP do cliente em alguns erros] → vai para a saída do
  container (some no redeploy); `log_not_found off` evita registrar cada 404 como erro.
- [Volume sem permissão de escrita para o nginx] → o nginx não derruba o site por isso,
  só não grava; tarefa de conferir que o arquivo do dia aparece depois do primeiro deploy.
- [Robôs de busca e pré-visualização do WhatsApp inflam os números] → o GoAccess separa
  robôs conhecidos; a prévia do WhatsApp aparece como origem própria.

## Migration Plan

1. Merge desta change e criação do volume no Dokploy, antes da próxima publicação.
2. `just publicar` normal. Os registros começam a partir desse deploy; o que veio antes
   não é recuperável.
3. Conferir no dia seguinte com `just acessos`.

Rollback: voltar `deploy/release.txt` não afeta o log; para desligar a contagem, reverter
o `nginx.conf` e publicar. O volume pode ser apagado no Dokploy.
