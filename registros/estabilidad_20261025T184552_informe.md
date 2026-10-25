# Comparacion de estabilidad de cuatro motores — 25/10/2026

Prueba solicitada por el usuario con ejes libres segun preparacion confirmada, un motor cada vez y potencia fija, sin PID. No se cambian ganancias, GPIO, firmware ni mapa. Cada motor: 0–10 s cambios rapidos de 10/25/50/75 % (2.5 s por nivel); 10–50 s mesetas de 10/25/50/75 % (10 s cada una); 50–60 s al 90 %. Descanso de 3 s despues de cada motor. Los cuatro completan la secuencia, sin interrupcion.

## Criterio de comparacion

Se excluyen los primeros 3 s de cada meseta de 10 s. Quedan siete muestras por potencia y motor a aproximadamente 1 Hz. CV = desviacion estandar poblacional / media RPM x 100. Menor CV indica menor variacion relativa de la lectura. Puntaje global: promedio de los cinco CV con igual peso; se informa tambien promedio 25–90 y resultado al 90, para mostrar dependencia del nivel. No se mezclan transitorios con mesetas ni se confunde mayor RPM con mayor estabilidad.

| Motor | CV medio 10–90 % | CV medio 25–90 % | CV al 90 % | RPM medias al 90 % | Rango RPM al 90 % |
|---|---:|---:|---:|---:|---|
| M3 | 3.149 % | 2.863 % | 1.909 % | 701.46 | 676.6–718.6 |
| M1 | 3.439 % | 3.183 % | 2.541 % | 639.01 | 622.8–670.7 |
| M2 | 3.614 % | 3.347 % | 3.143 % | 697.17 | 670.7–730.5 |
| M0 | 3.637 % | 2.487 % | 1.116 % | 686.89 | 676.6–700.6 |

M3 tiene menor variacion global en esta pasada. M0 gana especificamente al 90 % y en promedio 25–90 %; su variacion al 10 % eleva su puntaje global. Las diferencias globales son pequenas (3.149–3.637 %); una pasada y siete muestras por meseta no establecen superioridad mecanica definitiva. El ensayo mide el conjunto motor/transmision/sensor/montaje/alimentacion: no aisla la causa de las variaciones. Se requiere repeticion, preferiblemente en orden inverso, para evaluar reproducibilidad.

## Detalle por potencia

| Potencia | M0: RPM / CV | M1: RPM / CV | M2: RPM / CV | M3: RPM / CV |
|---|---|---|---|---|
| 10 % | 194.17 / 8.235 % | 223.29 / 4.460 % | 223.26 / 4.681 % | 228.40 / 4.295 % |
| 25 % | 459.39 / 2.389 % | 437.10 / 2.542 % | 485.04 / 4.894 % | 471.34 / 3.700 % |
| 50 % | 609.91 / 4.111 % | 559.46 / 2.614 % | 593.69 / 2.824 % | 629.60 / 3.312 % |
| 75 % | 663.83 / 2.334 % | 618.50 / 5.036 % | 666.39 / 2.528 % | 679.20 / 2.531 % |
| 90 % | 686.89 / 1.116 % | 639.01 / 2.541 % | 697.17 / 3.143 % | 701.46 / 1.909 % |

No hay muestras a cero en las ventanas analizadas. Se registran todos los canales para identificar movimiento no solicitado. Voltajes medios por meseta aproximadamente 8.38–8.40 V. Los cambios rapidos de 2.5 s se conservan en el registro, pero el muestreo de aproximadamente 1 Hz no permite caracterizar con precision sobreimpulso ni tiempos de respuesta de esos cambios. RPM basadas en 20 pulsos/vuelta configurados, sin calibracion fisica independiente. No valida carga, marcha en suelo ni PID a estas velocidades.

Al terminar se solicita parada de todos los motores y se reciben dos muestras consecutivas con M0/M1/M2/M3 a 0 RPM mediante deploy/comprobar_arranque.py. HTTP/WebSocket activos y bateria disponible. No se reprogramaron placas.

Archivos de evidencia con el mismo prefijo: .jsonl (muestras y eventos) y _estadisticas.json. Herramienta reproducible: raspberry/estabilidad_motores.py; ejecuta movimiento y necesita preparacion fisica y autorizacion antes de usarla. Se guarda sin lanzarla automaticamente ni instalar servicio.
