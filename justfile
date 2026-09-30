# Colinha do Voto: comandos do projeto.
# Rode `just` para ver a lista. Entre no ambiente antes com `nix develop` (ou direnv).

set shell := ["bash", "-euo", "pipefail", "-c"]

uf_dev := "RR"
porta := "8000"

# Lista os comandos
default:
    @just --list --unsorted

# Instala as dependências Python (uv) e o OpenSpec (npm, dentro do projeto)
setup:
    if [ -f pyproject.toml ]; then uv sync; else echo "Sem pyproject.toml ainda: a change 01 cria o pacote Python."; fi
    npm install -g @fission-ai/openspec@latest
    @echo "Pronto. Claude Code é instalado à parte; depois rode 'openspec init --tools claude' se ainda não rodou."

# Ciclo rápido de desenvolvimento: pipeline completo + site só para RR
dev:
    uv run colinha tudo --uf {{uf_dev}}

# Baixa dados do TSE (ex.: just baixar --uf SP --forcar)
baixar *args:
    uv run colinha baixar {{args}}

# Normaliza e cruza o histórico (ex.: just processar --uf SP)
processar *args:
    uv run colinha processar {{args}}

# Coleta dados da Câmara dos Deputados (change 03)
camara *args:
    uv run colinha camara {{args}}

# Confere que nenhum CPF ou nome civil protegido aparece em data/processed/ e site/dist/
privacidade:
    uv run colinha checar-privacidade

# Gera o site estático em site/dist/
site:
    uv run colinha site

# Pipeline completo, todas as UFs (ou just tudo --uf SP)
tudo *args:
    uv run colinha tudo {{args}}

# Rebaixa tudo do TSE, reprocessa e regenera o site (rodar todo dia até a eleição)
atualizar:
    uv run colinha baixar --forcar
    uv run colinha processar
    uv run colinha site

# Serve site/dist/ em http://localhost:8000
servir:
    uv run python -m http.server --directory site/dist {{porta}}

# Roda os testes (ex.: just test -k vinculo)
test *args:
    uv run pytest {{args}}

# Confere estilo e erros comuns
lint:
    ruff check .
    ruff format --check .

# Formata o código
fmt:
    ruff format .
    ruff check --fix .

# Valida as specs e changes do OpenSpec
specs:
    openspec list
    openspec validate --all

# Tudo que precisa passar antes de dizer que terminou
check: lint test specs

# Apaga o site e as saídas públicas (mantém o cache de downloads)
limpar:
    rm -rf site/dist data/processed

# Apaga também os downloads e o parquet intermediário
[confirm("Apagar data/raw e data/interim? Vai ser preciso baixar tudo de novo. Digite y para confirmar")]
limpar-tudo: limpar
    rm -rf data/raw data/interim

# Publica o site: release no GitHub + redeploy no Dokploy
publicar: site
    ./deploy/publicar.sh

# Relatório interno de acessos (últimos 30 dias) em relatorios/; precisa de SERVIDOR_SSH no .env
acessos:
    ./deploy/relatorio-acessos.sh
