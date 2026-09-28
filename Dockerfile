# Imagem do site: nginx com site/dist/ já gerado (design D9 da change 02).
# Gere o site antes (just site); a imagem não roda a pipeline.
FROM nginx:1.28-alpine
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY site/dist/ /usr/share/nginx/html/
