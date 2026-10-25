# PID conjunto de cuatro motores — 25/10/2026

El usuario confirma que los GPIO estaban intercambiados y que se han corregido antes de la repetición M2/M3. No se ha modificado el mapa del servidor. Las pruebas posteriores M2/M3 completaron 10 s y reciben pulsos en su propio canal; no implica cableado completo certificado.

## Prueba conjunta completada

Configuración guardada sin cambios: kp=0.03, ki=0.02, kd=0, base=18 en los cuatro motores. Es PI con base, sin término derivativo. Consigna 120 RPM, duración 40 s, límite 25 %, ejes libres según confirmación del usuario. Salida del cliente 0. CSV: pid_cuatro_20261025T175742_base18.csv.

Estadísticas excluyendo los primeros 10 s (30 muestras por motor):

| Motor | Media RPM | Mínimo | Máximo | Error absoluto medio respecto a 120 | Pico de toda la prueba |
|---|---:|---:|---:|---:|---:|
| M0 | 121.85 | 83.7 | 173.7 | 15.39 | 305.4 |
| M1 | 120.66 | 89.6 | 155.7 | 11.35 | 275.4 |
| M2 | 120.65 | 89.6 | 155.4 | 14.58 | 311.4 |
| M3 | 121.05 | 89.8 | 155.7 | 12.55 | 286.9 |

Las medias son próximas a consigna, pero no demuestran estabilidad: hay oscilación y sobreimpulso inicial. Ajuste provisional, sin calibración física de RPM ni carga en suelo.

## Candidato descartado

Prueba prevista de 40 s, 120 RPM, 25 % máximo; cambios solo mediante argumentos temporales: base=12, kp=0.01, ki=0.01, kd=0. CSV: pid_cuatro_20261025T175742_base12.csv. Corte por RuntimeError: Sin pulsos durante 3 segundos: M0. M2 comenzó a registrar pulsos tarde. No se desactivó la protección ni se guardaron estas ganancias. No repetir automáticamente este candidato.

## Parada y conservación

El cliente solicita stop() en finally. Diagnóstico final: dos muestras consecutivas con M0/M1/M2/M3 a 0 RPM; HTTP/WebSocket activos y batería disponible. La telemetría no sustituye observación física. No se modificaron config/pid_motores.json, config/canales_encoders.json, firmware instalado ni servicios.

Para repetir el ajuste guardado, con preparación física y autorización previas, desde la raíz y con nombre CSV nuevo:

~~~bash
/usr/bin/python3 raspberry/probar_pid.py --mover --motores M0,M1,M2,M3 --rpm 120 --segundos 40 --potencia-max 25 --registro registros/NOMBRE_NUEVO.csv
~~~

Pendiente: caracterizar arranque individual, mejorar sobreimpulso y oscilaciones y validar otras consignas. No se declara un PID definitivo.
