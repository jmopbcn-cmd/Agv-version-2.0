# AGV Car Inteligent — AGV MC100

Telemetría de cuatro encoders con Pico 2 W, Raspberry Pi 5 y panel web. Incluye además firmware de pantalla táctil ESP32E V1.2.

## Contenido

- [Manual de preparación y pruebas: Ubuntu, motores, encoders, USB, servicios y pantallas](raspberry/tests/README.md).

- [PID reutilizable, ajustes y pruebas pendientes](docs/pid_velocidad.md).

- [Arranque automático y comprobación tras reinicio](docs/arranque_y_reinicio.md).

- [Encoders y panel web: configuración, uso, protocolo y pruebas](docs/encoders_panel_web.md).

- [Servidor WebSocket: instalación y arranque](docs/servidor_websocket.md).
- [Pantalla V1.2: preparación y bibliotecas](docs/pantalla_v1.2.md).
- [Hardware](docs/hardware.md) y [conexiones](docs/conexiones.md).
- [Registro de comprobaciones y pruebas pendientes](docs/registro_pruebas.md).

El servidor está en src/servidor_ws.py. El programa Arduino está en firmware/PANTALLA_AGV_ESP32E28/PANTALLA_AGV_ESP32E28.ino.

## Credenciales

Antes de compilar la pantalla, copiar secrets.example.h como secrets.h en la misma carpeta y completar las credenciales Wi-Fi localmente. secrets.h está excluido de Git. No publicar contraseñas, archivos .env ni el entorno .venv.

## Estado actual

Revisión documental del 25 de octubre de 2026: servicios HTTP/WebSocket activos, Pico con cuatro canales en reposo y batería disponibles. El repositorio incluye cliente PI/PID y registros de pruebas conjuntas de 30 y 40 segundos con giro libre; el ajuste sigue siendo provisional y no arranca como servicio. El servidor corrige el cruce de etiquetas Pico M2/M3 mediante config/canales_encoders.json. El firmware ESP32 guardado recibe RPM reales; la versión instalada y su funcionamiento visual requieren comprobación independiente. Ver el manual de pruebas para comandos y límites de validación.

## Incidencia vigente en las pruebas del 25/10/2026

Las nuevas pruebas individuales detectan sobreimpulso en M0/M1 y corte por falta de pulsos en M2 con lectura posterior en M3. El mapa M2/M3 requiere revalidación física; no se considera validado el control de movimiento. Ver [resultados y registros](registros/revision_20261025T175053_resultados.md).

## Ajuste posterior a la alineacion

Tras la correccion de GPIO comunicada y la alineacion de sensores, se guarda PI suave (kp=ki=0.005, kd=0, base=18). Dos pruebas de 60 s completadas a 120 RPM, limite 25 %, sin cortes. Las incidencias anteriores se conservan como historial. Sigue pendiente mejorar el sobreimpulso inicial y la oscilacion. Ver [informe de ajuste](registros/ajuste_20261025T182255_informe.md).

## Ubicacion del repositorio

Carpetas operativas: Windows D:\Documentos\Agv-version-2.0; Raspberry /home/olmos/Agv-version-2.0. Repositorio GitHub jmopbcn-cmd/Agv-version-2.0. Los registros historicos pueden citar la ruta anterior agv-car-inteligent. Los nombres de servicio siguen siendo agv-web.service y agv-websocket.service.

## Control manual de pruebas

El panel incluye potencia independiente de 0 a 75 % y casilla Activar por motor, sin PID, con parada general y watchdog de conexion. Ver [uso y limites](docs/control_manual_web.md).
