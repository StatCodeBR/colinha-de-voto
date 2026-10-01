## ADDED Requirements

### Requirement: Colinha de bolso em PDF
A página da colinha SHALL oferecer um botão "Baixar colinha em PDF" que gera, no próprio
navegador, um arquivo PDF em folha A4 com a colinha em formato de bolso: um cartão de
cerca de 63 × 88 mm no canto superior esquerdo da folha, com contorno tracejado para
recorte, e o resto da folha em branco. O cartão MUST trazer o estado da colinha e, na
ordem da urna, para cada vaga: o cargo, o número em quadradinhos com um dígito em cada, o
nome de urna e a sigla do partido. Todos os candidatos MUST aparecer com o mesmo formato,
sem cores, logos ou destaques. A geração MUST NOT fazer nenhuma requisição ao servidor e
MUST NOT usar biblioteca de terceiros.

#### Scenario: Baixar a colinha completa
- GIVEN uma colinha de RR com as seis vagas preenchidas
- WHEN o eleitor toca em "Baixar colinha em PDF"
- THEN o navegador baixa `colinha-rr.pdf`, com uma página A4
- AND o cartão no canto superior esquerdo mostra as seis vagas na ordem da urna, cada uma
  com cargo, número, nome de urna e partido

#### Scenario: Vaga sem escolha
- GIVEN uma colinha de SP sem escolha para senador, 2º voto
- WHEN o PDF é gerado
- THEN essa vaga aparece com o cargo e três quadradinhos vazios, para preencher à mão
- AND nenhum número é inventado nem completado com zeros

#### Scenario: Colinha vazia
- GIVEN uma colinha sem nenhuma escolha
- WHEN o eleitor abre a página da colinha
- THEN o botão de PDF continua disponível e gera o cartão com todas as vagas em branco

#### Scenario: Nome com caractere que a fonte do PDF não tem
- GIVEN um nome de urna com um caractere fora do alfabeto latino comum
- WHEN o PDF é gerado
- THEN o caractere é trocado pela letra sem acento equivalente ou por "?", e o número,
  que é o que vale na urna, sai sempre completo

#### Scenario: Escolha que mudou de situação
- GIVEN uma escolha guardada que não está mais apta ou não aparece mais nos dados do TSE
- WHEN o PDF é gerado
- THEN o cartão mostra o número dessa vaga com o aviso "Confira no site: a situação
  mudou" no lugar do partido

#### Scenario: Número fora do padrão do cargo
- GIVEN uma candidatura cujo número não tem a quantidade de dígitos do cargo no
  `config.toml`
- WHEN o site é gerado
- THEN a geração para com erro indicando a candidatura, em vez de publicar um cartão com
  quadradinhos errados

#### Scenario: Privacidade
- GIVEN uma colinha preenchida
- WHEN o PDF é gerado
- THEN nenhuma requisição é feita ao servidor, e o arquivo não traz nada além do que está
  no cartão (sem identificação do eleitor nem do aparelho)

### Requirement: Impressão no formato de bolso
O botão "Imprimir colinha" SHALL imprimir o mesmo cartão de bolso, no mesmo lugar da
folha A4, com os mesmos dados e a mesma ordem do PDF.

#### Scenario: Imprimir
- WHEN o eleitor toca em "Imprimir colinha"
- THEN a impressão mostra só o cartão tracejado no canto superior esquerdo, sem menus,
  rodapé ou botões

#### Scenario: Navegador sem impressão
- GIVEN um navegador que não oferece impressão, como o navegador interno do WhatsApp
- WHEN o eleitor está na página da colinha
- THEN a página explica que ele pode baixar o PDF e mandar para quem tem impressora, ou
  abrir o site no navegador do celular
