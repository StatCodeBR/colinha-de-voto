# Delta for colinha

## ADDED Requirements

### Requirement: Montar a colinha
O eleitor MUST poder adicionar e tirar candidatos da colinha a partir da lista e da
página do candidato, respeitando as vagas por cargo definidas em `config.toml`.

#### Scenario: Adicionar deputado federal
- GIVEN uma colinha vazia em SP
- WHEN o eleitor clica em "Adicionar à colinha" na página de um candidato a deputado
  federal
- THEN o candidato entra na vaga de deputado federal
- AND o botão passa a dizer "Tirar da colinha"

#### Scenario: Vaga ocupada
- GIVEN uma colinha que já tem um candidato a governador
- WHEN o eleitor adiciona outro candidato a governador
- THEN o site pergunta se ele quer trocar o candidato anterior pelo novo
- AND só troca se o eleitor confirmar

#### Scenario: Duas vagas de senador
- GIVEN uma colinha com um candidato a senador
- WHEN o eleitor adiciona outro candidato a senador
- THEN o segundo ocupa a segunda vaga de senador, sem pergunta

### Requirement: Ordem da urna
A página `/colinha/` MUST mostrar os candidatos escolhidos na ordem oficial de votação
da urna para a eleição configurada, com o número em caixinhas grandes, o nome de urna e
o cargo, e com as vagas vazias identificadas.

#### Scenario: Colinha parcial
- GIVEN uma colinha com deputado federal e presidente escolhidos
- WHEN o eleitor abre `/colinha/`
- THEN vê as seis vagas na ordem da urna
- AND as vagas sem escolha aparecem como "Ainda não escolhido"

### Requirement: Privacidade da colinha
A colinha MUST ficar guardada só no navegador do eleitor e MUST NOT ser enviada a
nenhum servidor, nem gerar evento de analytics com candidato escolhido. O eleitor SHALL
poder apagar a colinha com um botão.

#### Scenario: Apagar a colinha
- WHEN o eleitor clica em "Apagar colinha" e confirma
- THEN todas as escolhas daquela UF são removidas do navegador

#### Scenario: Armazenamento indisponível
- GIVEN um navegador que bloqueia o armazenamento local
- WHEN o eleitor adiciona um candidato
- THEN a colinha funciona enquanto a página estiver aberta
- AND o site avisa que as escolhas não serão guardadas

### Requirement: Colinha separada por UF
O site SHALL manter uma colinha por UF, e o candidato a presidente SHALL aparecer em
todas elas.

#### Scenario: Troca de UF
- GIVEN uma colinha montada em SP
- WHEN o eleitor escolhe RJ
- THEN vê a colinha de RJ, sem os candidatos de SP
- AND a colinha de SP continua guardada

### Requirement: Impressão
A colinha MUST ter versão de impressão legível com números grandes, cabendo em meia
folha A4, e SHALL lembrar que o celular não pode ser usado na cabine de votação.

#### Scenario: Imprimir
- WHEN o eleitor clica em "Imprimir colinha"
- THEN a impressão mostra só os cargos, números e nomes de urna, sem menus nem rodapé
  extenso

### Requirement: Colinha desatualizada
Ao abrir a colinha, o site MUST conferir os candidatos guardados contra o índice atual
da UF e avisar quando algum não estiver mais apto ou não existir mais.

#### Scenario: Candidatura indeferida depois de escolhida
- GIVEN um candidato na colinha cuja candidatura passou a não estar apta
- WHEN o eleitor abre `/colinha/`
- THEN a vaga mostra um aviso com a situação atual e sugere escolher outro candidato
