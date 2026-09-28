#!/usr/bin/env bash
# Publica o site (design D9, change 02): compacta site/dist/, cria uma release no GitHub
# com o site.tar.gz, grava a tag em deploy/release.txt (commit + push) e pede o redeploy
# ao Dokploy, que constrói a imagem nginx baixando essa release.
#
# Configuração em .env (fora do git):
#   GITHUB_REPO=StatCodeBR/colinha-de-voto   (opcional; padrão: o remote origin)
#   DOKPLOY_WEBHOOK=https://...               (opcional se o Dokploy já faz deploy no push)
# Antes: gh auth login.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi
repo="${GITHUB_REPO:-$(git remote get-url origin | sed -E 's#^(git@github.com:|https://github.com/)##; s#\.git$##')}"

[ "$(git branch --show-current)" = "main" ] || {
  echo "publique a partir da branch main (é a que o Dokploy acompanha)" >&2
  exit 1
}
[ -f site/dist/index.html ] || { echo "site/dist/ vazio: rode 'just site'" >&2; exit 1; }
[ -z "$(git status --porcelain -- deploy/release.txt)" ] || {
  echo "deploy/release.txt tem mudanças não commitadas" >&2
  exit 1
}
uv run colinha checar-privacidade

tag="site-$(date +%Y%m%d-%H%M)"
tmp="$(mktemp -d)"
trap 'rm -f "$tmp/site.tar.gz"; rmdir "$tmp"' EXIT
tar -czf "$tmp/site.tar.gz" -C site/dist .
echo "site.tar.gz: $(du -h "$tmp/site.tar.gz" | cut -f1)"

gh release create "$tag" "$tmp/site.tar.gz" \
  --repo "$repo" \
  --title "Site $tag" \
  --notes "Site gerado em $(date -Iseconds). Dados: data/processed/manifesto.json na hora da geração."

echo "$tag" > deploy/release.txt
git add deploy/release.txt
git commit -m "Publica $tag" -- deploy/release.txt
git push

if [ -n "${DOKPLOY_WEBHOOK:-}" ]; then
  curl -fsS -X POST "$DOKPLOY_WEBHOOK" >/dev/null
fi
echo "Publicado: $tag (https://github.com/$repo/releases/tag/$tag)"
