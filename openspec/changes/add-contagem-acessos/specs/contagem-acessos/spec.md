## Purpose

Contar os acessos ao site de forma agregada, para a StatCode saber se ele está sendo
usado, sem cookies, sem scripts no navegador e sem guardar dado que identifique quem
acessou.

## ADDED Requirements

### Requirement: Registro de acessos sem dado identificável
O servidor SHALL registrar cada requisição com data e hora, IP do visitante anonimizado,
método, caminho, código de resposta, tamanho, origem (referer) e navegador (user agent).
O IP MUST ser anonimizado antes de gravado: IPv4 com o último bloco zerado
(`189.40.12.0`) e IPv6 mantendo só os três primeiros grupos. O registro MUST NOT conter
cookies, conteúdo da colinha nem qualquer dado enviado pelo navegador além desses campos.
O site MUST NOT carregar script de contagem no navegador.

#### Scenario: Visitante atrás do proxy
- GIVEN um visitante com IP `189.40.12.77` acessando pelo proxy do servidor
- WHEN ele abre uma página
- THEN o registro traz `189.40.12.0`, e não o IP do proxy nem o IP completo

#### Scenario: IPv6
- GIVEN um visitante com IP `2804:14c:5b73:8a1f::1`
- WHEN ele abre uma página
- THEN o registro traz `2804:14c:5b73::`

#### Scenario: IP ausente ou ilegível
- GIVEN uma requisição sem IP de origem reconhecível
- WHEN ela é registrada
- THEN o campo de IP fica como `-`, e nenhum outro dado é usado no lugar

#### Scenario: Colinha
- GIVEN um eleitor que monta a colinha
- WHEN ele adiciona ou tira candidatos
- THEN nada é registrado no servidor, porque a colinha não faz requisição

### Requirement: Registros persistentes e com prazo
Os registros SHALL ser gravados num volume persistente, um arquivo por dia, e MUST
sobreviver a um redeploy do site. Registros com mais de 30 dias MUST ser apagados.

#### Scenario: Publicação diária
- GIVEN registros dos últimos três dias
- WHEN o site é republicado
- THEN os registros continuam lá e o dia corrente segue no mesmo arquivo

#### Scenario: Registro antigo
- GIVEN um arquivo de registro de 31 dias atrás
- WHEN a rotina de limpeza roda
- THEN o arquivo é apagado

### Requirement: Relatório agregado interno
Um comando do projeto SHALL gerar um relatório com páginas vistas por dia, visitantes
aproximados, páginas mais vistas, origem dos acessos e navegadores, a partir dos
registros. O relatório MUST ficar só com quem o gerou e MUST NOT ser publicado no site.
O relatório SHALL deixar claro que "visitantes" é uma estimativa.

#### Scenario: Relatório da semana
- WHEN alguém da equipe roda o comando
- THEN recebe um arquivo HTML local com os números agregados dos registros existentes

#### Scenario: Sem registros ainda
- GIVEN um servidor sem arquivos de registro
- WHEN o comando roda
- THEN ele avisa que não há registros, em vez de gerar um relatório vazio
