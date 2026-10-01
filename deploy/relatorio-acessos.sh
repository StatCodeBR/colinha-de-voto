#!/usr/bin/env bash
# Relatório de acessos (change add-contagem-acessos, design D5): apaga no servidor os
# registros com mais de 30 dias, lê os restantes pelo SSH (container alpine com o volume
# em leitura) e passa direto ao GoAccess local, que gera relatorios/acessos-AAAAMMDD.html.
# Os registros não são gravados nesta máquina; o relatório só tem números agregados.
#
# Configuração em .env (fora do git):
#   SERVIDOR_SSH=usuario@servidor      host do Dokploy ("local" usa o Docker desta máquina)
#   VOLUME_ACESSOS=colinha-logs        (opcional) nome do volume no Docker do servidor
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi
: "${SERVIDOR_SSH:?defina SERVIDOR_SSH no .env (ex.: usuario@servidor)}"
volume="${VOLUME_ACESSOS:-colinha-logs}"
command -v goaccess >/dev/null || { echo "goaccess não encontrado: entre no nix develop" >&2; exit 1; }

remoto="docker run --rm -v $volume:/logs alpine find /logs -name 'acessos-*.log' -mtime +30 -delete \
  && docker run --rm -v $volume:/logs:ro alpine sh -c 'cat /logs/acessos-*.log 2>/dev/null || true'"
executar() {
  if [ "$SERVIDOR_SSH" = local ]; then bash -c "$remoto"; else ssh "$SERVIDOR_SSH" "$remoto"; fi
}

mkdir -p relatorios
saida="relatorios/acessos-$(date +%Y%m%d).html"

# Formato "combined" do deploy/nginx.conf, com o fuso de Brasília nos horários. O GoAccess
# descarta linhas sem IP ("-"); elas entram como 0.0.0.0 para contar as páginas vistas.
gerar() {
  IFS= read -r primeira || { echo "Nenhum registro de acesso no servidor (volume $volume)." >&2; return 3; }
  { printf '%s\n' "$primeira"; cat; } | sed 's/^- /0.0.0.0 /' | goaccess - \
    --no-global-config \
    --log-format='%h %^[%x] "%r" %s %b "%R" "%u"' \
    --datetime-format='%d/%b/%Y:%H:%M:%S %z' \
    --tz=America/Sao_Paulo \
    --ignore-panel=HOSTS \
    --ignore-panel=REMOTE_USER \
    --ignore-panel=KEYPHRASES \
    --ignore-panel=GEO_LOCATION \
    --ignore-panel=ASN \
    --html-report-title="Colinha do Voto: acessos (visitantes são aproximados)" \
    -o "$saida"
}

set +e
executar | gerar
estados=("${PIPESTATUS[@]}")
set -e
[ "${estados[0]}" -eq 0 ] || { echo "falha ao ler os registros no servidor" >&2; exit 1; }
[ "${estados[1]}" -ne 3 ] || exit 3
[ "${estados[1]}" -eq 0 ] || exit "${estados[1]}"

echo "Relatório: $saida"
echo "Páginas vistas são exatas. \"Visitantes\" é aproximado: muitas pessoas dividem o mesmo"
echo "IP na rede do celular, e o IP é gravado sem o último bloco."
