# Pantalla AGV: botones de potencia conjunta

Actualización del 21/11/2026, grabada en la pantalla ESP32 por COM6 y verificada por hash. En AGV → MOTORES hay botones Encender todos 25 %, 50 % y 75 %, y PARAR TODOS. Se aplica PWM fijo, sin PID. El propietario renueva la orden cada 500 ms; al salir de la vista, perder datos o conexión se pide parada.

Solo se grabó la aplicación en 0x10000; se conservaron la tabla de particiones y las preferencias. El servidor debe aceptar la orden encender_todos. El binario fue compilado con ESP32 core 4.0.0. Ver verificacion.json para tamaño y SHA-256.

Se completaron 21 pruebas simuladas del control y comprobaciones de envío de los tres niveles desde la web. No se activaron motores reales para verificar estos botones; la pulsación física y la apariencia en la pantalla quedan pendientes de observación del usuario.
