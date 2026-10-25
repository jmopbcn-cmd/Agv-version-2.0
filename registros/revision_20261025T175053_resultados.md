# Revisión con pruebas del 25 de octubre de 2026

Base: edf6a06258e33236349d89687b81efd6506d2e69. Usuario confirma chasis preparado, sin ruedas o ejes libres, estable y corte de alimentación disponible. No se modificaron ganancias, GPIO, mapa de canales ni firmware instalado.

## Software y reposo

Cinco pruebas unitarias de raspberry/tests/test_pid.py correctas. Sintaxis Python revisada mediante AST, sin ejecutar los diagnósticos MicroPython. Servicios HTTP/WebSocket activos y habilitados; HTML coincide con web/index.html; batería y cuatro canales recibidos. Revisión de patrones de credenciales en los archivos a publicar sin hallazgos; secrets.h sigue ignorado.

## Movimiento individual

Comando utilizado por motor: /usr/bin/python3 -B raspberry/probar_pid.py --mover --motores Mx --rpm 60 --segundos 5 --potencia-max 25 --registro ARCHIVO.csv. Configuración PI existente, base 18, kp 0.03, ki 0.02, kd 0.

| Motor ordenado | RPM recibidas durante la prueba | Resultado |
|---|---|---|
| M0 | 0; 335.3; 35.9; 0; 0 | Finalizó; fuerte sobreimpulso y giro discontinuo. No valida regulación a 60 RPM. |
| M1 | 0; 353.3; 24.0; 275.4; 6.0 | Finalizó; fuerte oscilación. No valida regulación a 60 RPM. |
| M2 | 0; 0; 0; 0 | Corte RuntimeError: Sin pulsos durante 3 segundos: M2. |
| M3 | No ejecutado | Secuencia suspendida tras el fallo de M2. |

Tras M2, el comprobador recibió una muestra M3=317.4 RPM con M2=0; la siguiente muestra mostró los cuatro a cero. Esto sugiere una posible discrepancia entre canal ordenado y publicado, pero no demuestra la causa ni permite corregir el mapa sin identificar físicamente motor y encoder. El mapa guardado intercambia M2/M3 y debe revalidarse con el montaje actual. La prueba conjunta no se ejecutó.

El cliente solicita motor.stop() en finally, también al fallar. Tras M0 y M1 se recibieron dos muestras con los cuatro canales a cero; tras el fallo de M2 se repitió el diagnóstico y se recibieron otras dos muestras de cuatro ceros. No había otro cliente probar_pid/test_4_motores detectado antes de empezar. La telemetría no sustituye la confirmación visual de parada ni permite descartar un fallo de sensor.

## Registros y límites

CSV originales: revision_20261025T175053_M0.csv, revision_20261025T175053_M1.csv y revision_20261025T175053_M2.csv. El CSV M2 termina antes de registrar la muestra que provoca la excepción; el mensaje de error y la lectura posterior M3 quedan descritos arriba. Son ensayos breves con arranque incluido; no se calculan medias de régimen estable. No se valida carga, velocidad real calibrada, pantallas físicas ni ajuste del PID.

Pendiente: identificar a mano el encoder que corresponde a cada motor, resolver la discrepancia M2/M3 y después repetir pruebas individuales; revisar PI/base a baja consigna antes de una prueba conjunta. No declarar el sistema de movimiento correcto por superar pruebas de software.
