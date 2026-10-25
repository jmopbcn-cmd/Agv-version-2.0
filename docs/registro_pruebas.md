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

## 25 de octubre de 2026 — revisión documental y diagnóstico en reposo

- Repositorio inspeccionado en /home/olmos/agb-car-inteligent, base c2fb463ac9eb8f61852616d4f1a01e1b47b222a2. Se añade [manual de preparación y pruebas](../raspberry/tests/README.md).
- Ubuntu 24.04.5 LTS, Python 3.12.3. Entorno .venv: websockets 17.3, pyserial 3.5, mpremote 1.29.0; fusion_hat 1.14.0 disponible en Python del sistema y ausente de .venv.
- Unidades WebSocket y HTTP active/enabled; escuchan 8765/8080. deploy/comprobar_arranque.py confirma HTTP idéntico a web/index.html, batería y voltaje válidos y dos mensajes de cuatro canales a 0 RPM.
- Mapa actual: HAT M0/M1/M2/M3 recibe etiquetas Pico M0/M1/M3/M2. Los archivos locales no versionados test_encoder_m2.py y test_encoder_m3.py leen GP4/GP5 pero conservan rótulos M1. Se documenta sin modificarlos ni incorporarlos.
- Se revisa la copia guardada de ESP32: consume RPM del JSON. No se confirma el contenido grabado ni la visualización física.
- Solo documentación modificada. No se accionaron motores, abrieron sesiones USB de programación, alteraron firmware/configuración, reiniciaron servicios ni reinició la Pi. Los ensayos de movimiento citados son históricos; no se repitieron.
- Pendientes y requisitos de instalación desde cero indicados expresamente en el manual.

## 25 de octubre de 2026 — revisión para publicación

Se incorporan los diagnósticos Pico M2/M3, corrigiendo únicamente sus rótulos para distinguir etiqueta Pico, GP4/GP5 y canal HAT M3/M2. No se alteran GPIO ni cálculos. Se incorpora pico_main_backup.py, idéntico a firmware/PICO_2W/main.py en esta revisión, sin afirmar que coincida con lo grabado. Se actualiza la URL de clonación del manual. Las menciones anteriores a archivos no versionados y rótulos M1 describen el estado previo. No se ejecutan pruebas de movimiento ni se carga firmware.

## Pruebas nuevas: incidencia detectada

Ver [resultados y CSV](../registros/revision_20261025T175053_resultados.md): M0/M1 con sobreimpulso a 60 RPM; M2 cortado por falta de pulsos y lectura posterior en M3. Mapa M2/M3 pendiente de revalidación física. M3 y prueba conjunta suspendidos. Parada solicitada y cuatro canales a cero en diagnóstico final.

## GPIO corregidos y PID conjunto posterior

El usuario confirma corrección de GPIO intercambiados. Repetición M2/M3 de 10 segundos completada sin corte. El PI conjunto guardado completa 40 segundos a 120 RPM; candidato de base menor descartado por corte de falta de pulsos en M0. Se conservan las ganancias anteriores. Ver [estadísticas y límites](../registros/pid_cuatro_20261025T175742_resultados.md).

## Ajuste PI tras alineacion de sensores

Ganancias guardadas kp=ki=0.005, kd=0, base=18 para los cuatro motores. Dos minutos de prueba independientes completados a 120 RPM y limite 25 %, con ganancias nuevas; referencia anterior cortada por M3. Sigue pendiente mejorar el arranque. Ver [informe](../registros/ajuste_20261025T182255_informe.md).
