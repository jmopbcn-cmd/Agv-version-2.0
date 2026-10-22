# Registro de comprobaciones

## 22 de octubre de 2026

- Acceso SSH real al equipo agv-mc100 y repositorio /home/olmos/agb-car-inteligent.
- Servicio agb-websocket.service habilitado y activo.
- Recepción de JSON real desde ws://127.0.0.1:8765/ con los campos bateria, dispositivo, estado_bateria, fusion_hat, hora, temperatura_cpu y voltaje.
- Sintaxis Python revisada; dependencia instalada websockets 17.3.
- Firmware original del PC conservado; la copia publicable separa las declaraciones Wi-Fi en secrets.h y utiliza secrets.example.h sin credenciales reales.
- Exclusiones Git comprobadas para secrets.h y .venv.
- Comparación de archivos publicados con la copia de trabajo y sincronización de main con GitHub.

## Pendiente

- Compilar el firmware con la placa, core y bibliotecas del entorno Arduino original.
- Flashear y probar la copia con secretos separados en el panel físico.
- Verificar Wi-Fi, navegación táctil, recepción, caducidad de datos y reconexión.
- Nueva prueba de arranque tras reiniciar; durante esta tarea no se ha reiniciado la Raspberry.
- Integrar encoders y medidas reales de velocidad/RPM; los valores actuales del panel son simulados.
