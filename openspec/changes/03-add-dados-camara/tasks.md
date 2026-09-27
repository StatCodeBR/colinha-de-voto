# Tasks

## 1. Reconhecimento das fontes
- [ ] 1.1 Conferir no portal da Câmara os endpoints de deputados, detalhes e frentes; registrar em `docs/fontes.md` se `/deputados/{id}` traz CPF e data de nascimento
- [ ] 1.2 Verificar se existem arquivos em massa por ano de proposições, autores e temas; registrar URLs e colunas, incluindo se há ordem de assinatura ou proponente
- [ ] 1.3 Decidir entre arquivos em massa e API para proposições; atualizar o `design.md` com `/opsx:update` se mudar algo

## 2. Coleta
- [ ] 2.1 Cliente httpx com cache em disco, limite de requisições por segundo, 3 tentativas e `User-Agent` com e-mail de contato
- [ ] 2.2 Deputados das legislaturas configuradas e seus detalhes
- [ ] 2.3 Proposições dos tipos configurados, com autores e temas, de 2015 até hoje
- [ ] 2.4 Frentes por deputado
- [ ] 2.5 Subcomando `colinha camara` com `--forcar`
- [ ] 2.6 Testes: cache evita nova requisição; build funciona só com cache

## 3. Vínculo
- [ ] 3.1 Vínculo candidato 2026 ↔ deputado reutilizando `normalizar_nome` e as regras da change 01
- [ ] 3.2 `revisao_vinculos_camara.csv` e aplicação de `data/manual/vinculos_camara.csv`
- [ ] 3.3 Testes: chave única confirma; sem nascimento vai para revisão; rejeição manual remove

## 4. Agregação
- [ ] 4.1 Por deputado: mandatos com período, contagens por tipo (autoria principal e coautoria), cinco temas, dez proposições mais recentes, frentes
- [ ] 4.2 Objeto `camara` no detalhe do candidato, montado por allowlist
- [ ] 4.3 Testes: tipos fora da lista não contam; coautoria separada; deputado sem PL gera a frase explicativa

## 5. Site
- [ ] 5.1 Template parcial "Na Câmara dos Deputados" depois da trajetória, com texto explicativo fixo, links oficiais e fonte com data
- [ ] 5.2 Filtro "Já foi deputado(a) federal" nas listas (campo no `indice.json`)
- [ ] 5.3 Atualizar a página de metodologia com a fonte da Câmara e as regras de contagem
- [ ] 5.4 Rodar `/checar-neutralidade`
- [ ] 5.5 Revisão humana (equipe): conferir 5 deputados contra o site da Câmara, incluindo um suplente que assumiu por pouco tempo
