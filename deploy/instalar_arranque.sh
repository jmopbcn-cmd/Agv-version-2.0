#!/bin/sh
set -eu
[ "$(id -u)" -eq 0 ] || { echo "Ejecutar con sudo." >&2; exit 1; }
ROOT=/home/olmos/Agv-version-2.0
[ -x "$ROOT/.venv/bin/python" ]
[ -f "$ROOT/web/index.html" ]
systemd-analyze verify "$ROOT/deploy/agv-web.service" "$ROOT/deploy/agv-websocket.service"
BACKUP="/var/backups/agv-arranque-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP"
for unit in agv-web.service agv-websocket.service; do
 if [ -f "/etc/systemd/system/$unit" ]; then cp -p "/etc/systemd/system/$unit" "$BACKUP/"; fi
 systemctl is-enabled "$unit" > "$BACKUP/$unit.estado" 2>&1 || true
done
install -m 644 "$ROOT/deploy/agv-web.service" /etc/systemd/system/agv-web.service
systemctl daemon-reload
systemctl enable agv-websocket.service agv-web.service
systemctl start agv-websocket.service agv-web.service
systemctl is-active agv-websocket.service agv-web.service
printf 'Copia de configuracion anterior: %s\n' "$BACKUP"
echo 'Instalacion completada. No se han accionado motores ni reiniciado la Pi.'
