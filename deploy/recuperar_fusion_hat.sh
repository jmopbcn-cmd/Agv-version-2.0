#!/bin/sh
set -eu
[ "$(id -u)" -eq 0 ] || { echo 'Ejecutar con sudo.' >&2; exit 1; }
DEVICE=/sys/bus/i2c/devices/1-0017
[ "$(cat "$DEVICE/name")" = fusion_hat ] || { echo 'Dispositivo inesperado'; exit 1; }
if [ -e /sys/class/power_supply/fusion-hat/capacity ]; then
 echo 'La bateria ya esta disponible; no se modifica el controlador.'
elif [ -L "$DEVICE/driver" ]; then
 echo 'Hay controlador asociado pero falta bateria. No se fuerza su desconexion.' >&2
 exit 1
else
 echo 'Reintentando la inicializacion del dispositivo Fusion HAT existente...'
 printf '%s' 1-0017 > /sys/bus/i2c/drivers/fusion_hat/bind
fi
for field in capacity voltage_now status; do
 printf '%s: ' "$field"
 cat "/sys/class/power_supply/fusion-hat/$field"
done
