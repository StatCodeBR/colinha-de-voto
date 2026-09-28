# Tasks

## 1. Fundação do site
- [ ] 1.1 Adicionar jinja2; comando `colinha site` que limpa e regenera `site/dist/` a partir de `data/processed/`
- [ ] 1.2 Template base com cabeçalho mínimo, rodapé StatCode, meta tags e `lang="pt-BR"`
- [ ] 1.3 Tokens de cor e tipografia do `design.md` em CSS; baixar e auto-hospedar as fontes (woff2, só os pesos usados), conferindo a licença
- [ ] 1.4 Componente número em caixinhas com `aria-label` do número completo
- [ ] 1.5 CSS de impressão
- [ ] 1.6 Conferir contraste AA de todos os pares de cor e ajustar tokens se preciso

## 2. Páginas
- [ ] 2.1 Página inicial com explicação curta e escolha de UF (27 UFs); atalho para a última UF escolhida
- [ ] 2.2 Página da UF com os cargos na ordem da urna, incluindo presidente
- [ ] 2.3 Listas estáticas por UF e cargo, em ordem alfabética, com etiqueta de histórico
- [ ] 2.4 JavaScript de busca e filtros sobre o `indice.json` (normalização de acentos, contador, estado vazio com orientação, filtro de candidaturas não aptas)
- [ ] 2.5 Página do candidato com todas as seções da spec, "Não informado", flexão de gênero e textos sem sigla solta
- [ ] 2.6 Seção de trajetória com janela de cobertura e os três casos (sem registro, em verificação, confirmados + pendentes)
- [ ] 2.7 Fonte e data em cada seção, a partir do manifesto; link "Encontrou um erro?" com e-mail pré-preenchido
- [ ] 2.8 Página de metodologia
- [ ] 2.9 Página 404 que leva de volta à escolha de UF
- [ ] 2.10 Testes de geração: toda página de candidato tem as mesmas seções na mesma ordem; nenhuma página contém CPF de entrada

## 3. Colinha
- [ ] 3.1 Módulo de estado da colinha em `localStorage` (`colinha:v1:{uf}`) com `try/catch` e aviso quando não houver armazenamento
- [ ] 3.2 Botões "Adicionar à colinha" e "Tirar da colinha" na lista e na página do candidato; troca confirmada quando a vaga estiver ocupada; duas vagas de senador
- [ ] 3.3 Confirmar no TSE a ordem oficial de votação da urna em 2026 e registrar em `docs/fontes.md`
- [ ] 3.4 Página `/colinha/` na ordem da urna, com vagas vazias identificadas, botão de apagar e impressão
- [ ] 3.5 Conferência dos candidatos guardados contra o índice atual, com aviso de candidatura não apta
- [ ] 3.6 Teste manual guiado no celular: montar, trocar, apagar, imprimir, trocar de UF
- [ ] 3.7 (opcional) Teste automatizado com pytest-playwright cobrindo montar e imprimir

## 4. Compartilhamento, acessibilidade e desempenho
- [ ] 4.1 Meta tags de prévia por página e botão de compartilhar (nativo, com link do WhatsApp como alternativa)
- [ ] 4.2 `robots.txt` e `sitemap.xml`
- [ ] 4.3 Revisão de acessibilidade: teclado, foco visível, leitor de tela no número em caixinhas, `prefers-reduced-motion`
- [ ] 4.4 Medir o tamanho da maior página de candidato e do maior `indice.json`; ajustar se passar do orçamento

## 5. Neutralidade e revisão
- [ ] 5.1 Rodar `/checar-neutralidade` e corrigir o que aparecer
- [ ] 5.2 Revisão humana (equipe): duas pessoas conferem lado a lado 10 páginas de partidos diferentes, incluindo candidatos a governador e presidente

## 6. Publicação
- [ ] 6.1 `Dockerfile` e `nginx.conf` próprios servindo `site/dist/`: gzip para HTML, CSS, JS e JSON; cache longo para fontes e CSS, curto para HTML e `indice.json`; página 404 do site. Adicionar Docker ou Podman ao `flake.nix` e testar localmente com `docker run`
- [ ] 6.2 Escolher e configurar o registry; criar a aplicação no Dokploy (provider Docker) com o domínio `colinha.statcode.com.br` e HTTPS; implementar `just publicar` (hoje ela só avisa que falta configurar): gerar o site, montar a imagem com tag de data e hora, enviar ao registry e chamar o webhook do Dokploy, com URL do webhook e credenciais em `.env`
- [ ] 6.3 Testar no celular: link colado no WhatsApp mostra a prévia correta
- [ ] 6.4 Documentar no README o ciclo diário até a eleição (`just atualizar` e `just publicar`) e como voltar para a imagem anterior
- [ ] 6.5 (opcional) Fotos: baixar as fotos de 2026, converter para WebP de 240px, exibir com texto alternativo e sem quebrar o orçamento de desempenho
