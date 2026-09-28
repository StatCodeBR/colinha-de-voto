#!/usr/bin/env bash
# Publica site/dist/ como imagem nginx e pede o redeploy ao Dokploy (design D9, change 02).
# Configuração em .env (fora do git):
#   COLINHA_IMAGEM=registry.exemplo/statcode/colinha-do-voto
#   DOKPLOY_WEBHOOK=https://dokploy.exemplo/api/deploy/...
# Faça login no registry antes (docker login). Para voltar à versão anterior, aponte a
# aplicação no Dokploy para a tag anterior (listada em deploy/publicacoes.log).
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi
: "${COLINHA_IMAGEM:?defina COLINHA_IMAGEM no .env}"
: "${DOKPLOY_WEBHOOK:?defina DOKPLOY_WEBHOOK no .env}"

[ -f site/dist/index.html ] || { echo "site/dist/ vazio: rode 'just site'" >&2; exit 1; }
uv run colinha checar-privacidade

tag="$(date +%Y%m%d-%H%M)"
docker build -t "$COLINHA_IMAGEM:$tag" -t "$COLINHA_IMAGEM:latest" .
docker push "$COLINHA_IMAGEM:$tag"
docker push "$COLINHA_IMAGEM:latest"
curl -fsS -X POST "$DOKPLOY_WEBHOOK" >/dev/null
echo "$(date -Iseconds) $COLINHA_IMAGEM:$tag" >> deploy/publicacoes.log
echo "Publicado: $COLINHA_IMAGEM:$tag"
