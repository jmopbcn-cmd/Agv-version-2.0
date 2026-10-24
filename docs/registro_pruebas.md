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
- La integración de encoders del panel web se actualiza en el registro del 24 de octubre. La validación de la pantalla ESP32 sigue siendo independiente.

## 24 de octubre de 2026 — encoders y panel web

Ver [guía de encoders](encoders_panel_web.md) para detalles, configuración y límites.

- Usuario: giro y parada observados en cuatro encoders; M0/M1 individualmente y M2/M3 juntos.
- Revisión remota: servicio activo, JSON real con Pico conectada, M0–M3 a 0 RPM y PARADO; panel HTTP responde 200.
- Sintaxis Python comprobada sin ejecutar pruebas físicas. No se accionaron motores ni se reinició el equipo.
- Pendientes: calibración, prueba simultánea documentada de cuatro motores, desconexión USB y arranque tras reinicio. PID sin implementar.

## Fallo detectado tras reinicio del 24 de octubre

El nuevo arranque 04:31:54 recupera HTTP, WebSocket y cuatro encoders. La bateria no se recupera: /sys/class/power_supply esta vacio. El registro del kernel muestra timeouts I2C -110 y fallo de probe de fusion_hat en 1-0017. La primera comprobacion no cubria bateria y su OK era parcial. Se corrige para exigir bateria y voltaje.

Se prepara deploy/recuperar_fusion_hat.sh para reintentar bind del dispositivo existente solo si no tiene driver asociado. Requiere sudo, no descarga el modulo ni escribe ordenes de motor. La inicializacion del driver puede configurar perifericos del HAT. Recuperacion manual y posterior reinicio pendientes; no se instala reintento automatico hasta validar el procedimiento.

## Recuperación tras apagado completo — 24 de octubre de 2026

El usuario comunica nuevo encendido después de solicitar apagado y corte de alimentación. Comprobación remota: ambos servicios habilitados y activos, HTTP coincide con web/index.html, dos mensajes WebSocket con fusion_hat=true, batería 34/36 %, voltaje 7.098/7.128 V y cuatro encoders a 0 RPM. El kernel registra Fusion Hat driver probed successfully. Se recupera la lectura tras este encendido; no demuestra resuelto el fallo del reinicio normal anterior. Las variaciones de porcentaje son lecturas del controlador, no una calibración de carga. Pantalla ESP32 y representación visual web pendientes de confirmación del usuario.

Los intentos anteriores de reasociar el controlador y reinicializar el bus no recuperaron la batería. No se instala reintento automático. No se ejecutaron órdenes de motores.
