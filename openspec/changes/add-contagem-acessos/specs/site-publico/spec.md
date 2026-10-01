## ADDED Requirements

### Requirement: Transparência sobre a contagem de acessos
A página de metodologia MUST informar que os acessos às páginas são contados de forma
agregada, sem cookies e sem scripts de contagem, com o IP anonimizado e guardado por no
máximo 30 dias, e que o site não sabe quais candidatos o eleitor escolhe na colinha.

#### Scenario: Eleitor quer saber se é rastreado
- WHEN o eleitor abre `/metodologia/`
- THEN encontra um parágrafo sobre a contagem de acessos com esses quatro pontos: sem
  cookies, IP anonimizado, prazo de 30 dias e colinha que não sai do celular
