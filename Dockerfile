# Imagem do site (design D9 da change 02). O Dokploy constrói esta imagem a partir do
# repositório; o site já gerado vem da release do GitHub indicada em deploy/release.txt,
# criada pelo `just publicar`. A imagem não roda a pipeline.
#
# Build args (opcionais):
#   REPO     repositório no GitHub (padrão: StatCodeBR/colinha-de-voto)
#   RELEASE  tag da release; vazio usa a de deploy/release.txt (rollback: passe a anterior)
# Build secret (só para repositório privado): github_token, com permissão de leitura.

FROM alpine:3.22 AS site
RUN apk add --no-cache curl jq
ARG REPO=StatCodeBR/colinha-de-voto
ARG RELEASE=
# Só para testar o build sem o GitHub (API simulada).
ARG GITHUB_API=https://api.github.com
# Copiar o arquivo invalida o cache a cada publicação: a release nova é sempre baixada.
COPY deploy/release.txt /tmp/release.txt
RUN --mount=type=secret,id=github_token,required=false <<'SH'
set -eu
tag="${RELEASE:-$(tr -d '[:space:]' < /tmp/release.txt)}"
[ -n "$tag" ] || { echo "deploy/release.txt vazio: rode 'just publicar'" >&2; exit 1; }
set --
if [ -s /run/secrets/github_token ]; then
  set -- -H "Authorization: Bearer $(cat /run/secrets/github_token)"
fi
asset=$(curl -fsSL "$@" -H "Accept: application/vnd.github+json" \
  "$GITHUB_API/repos/$REPO/releases/tags/$tag" \
  | jq -r '.assets[] | select(.name == "site.tar.gz") | .url')
[ -n "$asset" ] || { echo "release $tag sem site.tar.gz" >&2; exit 1; }
curl -fsSL "$@" -H "Accept: application/octet-stream" "$asset" -o /tmp/site.tar.gz
mkdir -p /site
tar -xzf /tmp/site.tar.gz -C /site
test -f /site/index.html
echo "site da release $tag"
SH

FROM nginx:1.28-alpine
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=site /site/ /usr/share/nginx/html/
# Registros de acesso (change add-contagem-acessos). No Dokploy, o volume colinha-logs é
# montado aqui; vazio, ele herda o dono nginx na primeira montagem.
RUN mkdir -p /var/log/colinha && chown nginx:nginx /var/log/colinha
