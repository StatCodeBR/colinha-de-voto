## ADDED Requirements

### Requirement: Navegação de volta
Toda subpágina do site MUST ter, no topo do conteúdo, um link "Voltar" para a página de
cima na hierarquia do site, com o destino escrito por extenso. O link SHALL funcionar
sem JavaScript e MUST NOT depender do histórico do navegador. Os destinos são:

| Página | Destino |
|---|---|
| UF (`/{uf}/`) | página inicial (escolha de estado) |
| Lista por cargo (`/{uf}/{cargo}/`) | página da UF |
| Candidato (`/{uf}/{numero}/`) | lista do cargo do candidato na UF |
| Candidato a presidente (`/br/{numero}/`) | lista de presidente da última UF visitada; sem UF conhecida, página inicial |
| Colinha e metodologia | página inicial |

A página inicial não tem link "Voltar".

#### Scenario: Chegada pelo WhatsApp numa página de candidato
- GIVEN um eleitor que abriu `/rr/4455/` direto de um link, sem outra página no histórico
- WHEN ele toca em "Voltar para deputado federal em Roraima"
- THEN vê a lista de candidaturas a deputado federal em Roraima

#### Scenario: Navegador sem JavaScript
- GIVEN um navegador com JavaScript desativado
- WHEN o eleitor abre qualquer subpágina
- THEN o link "Voltar" aparece e leva ao destino da tabela

#### Scenario: Presidente com UF conhecida
- GIVEN um eleitor que visitou páginas de São Paulo antes
- WHEN ele abre a página de um candidato a presidente e toca em "Voltar"
- THEN vê a lista de candidaturas a presidente de São Paulo

#### Scenario: Presidente sem UF conhecida
- GIVEN um eleitor que abriu a página de um candidato a presidente sem ter visitado
  nenhuma UF, ou com o armazenamento do navegador bloqueado
- WHEN ele toca em "Voltar"
- THEN vê a página inicial, com a escolha de estado

#### Scenario: Leitor de tela
- WHEN um leitor de tela passa pelo link "Voltar"
- THEN ele lê o destino completo, e não só "Voltar"
