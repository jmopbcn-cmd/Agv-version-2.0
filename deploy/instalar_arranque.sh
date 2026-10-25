#!/bin/sh
set -eu
[ "$(id -u)" -eq 0 ] || { echo "Ejecutar con sudo." >&2; exit 1; }
ROOT=/home/olmos/Agv-version-2.0
[ -x "$ROOT/.venv/bin/python" ]
[ -f "$ROOT/web/index.html" ]
systemd-analyze verify "$ROOT/deploy/agb-web.service" "$ROOT/deploy/agb-websocket.service"
BACKUP="/var/backups/agb-arranque-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP"
for unit in agb-web.service agb-websocket.service; do
 if [ -f "/etc/systemd/system/$unit" ]; then cp -p "/etc/systemd/system/$unit" "$BACKUP/"; fi
 systemctl is-enabled "$unit" > "$BACKUP/$unit.estado" 2>&1 || true
done
install -m 644 "$ROOT/deploy/agb-web.service" /etc/systemd/system/agb-web.service
systemctl daemon-reload
systemctl enable agb-websocket.service agb-web.service
systemctl start agb-websocket.service agb-web.service
systemctl is-active agb-websocket.service agb-web.service
printf 'Copia de configuracion anterior: %s\n' "$BACKUP"
echo 'Instalacion completada. No se han accionado motores ni reiniciado la Pi.'
