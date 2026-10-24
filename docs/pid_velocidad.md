# PID de velocidad — desarrollo

## Archivos reutilizables

- config/pid_motores.json: ganancias kp, ki y kd independientes por motor. Estado provisional, sin ajuste validado.
- raspberry/pid_velocidad.py: clase PID pura importable desde otro programa.
- raspberry/probar_pid.py: cliente de prueba manual del servidor local; no se instala al arranque.
- registros/: medidas CSV reales. Columna potencia indica la orden calculada; mover indica si se aplicó.

Ejemplo sin movimiento, desde /home/olmos/agb-car-inteligent:

    python3 raspberry/probar_pid.py --registro registros/nueva_prueba.csv

Ejemplo con movimiento, solo tras comprobar sensores y preparar el vehículo:

    python3 raspberry/probar_pid.py --mover --motores M0 --rpm 120 --segundos 10 --registro registros/nueva_prueba_motor.csv

Cada registro requiere nombre nuevo. El Python del sistema dispone de fusion_hat y websockets; el entorno .venv del servidor no incluye fusion_hat. Se puede elegir otro archivo con --config. Las opciones --kp, --ki y --kd sustituyen temporalmente los valores del archivo.

## Límites y comportamiento

Solo potencia positiva; inversión de M0 y M2 conservada de las pruebas existentes. Un regulador por motor con integral condicional contra saturación y derivada sobre medida. kd=0 durante estas pruebas: se está probando control PI, aunque el módulo permite PID.

Potencia limitada al 25 % por defecto (máximo admitido por herramienta: 35 %); pruebas de 1–60 segundos; consigna 0–120 RPM. Corte ante datos ausentes, caducados, repetidos o inválidos, pérdida de Fusion HAT o Pico, o 3 segundos sin pulsos con orden de al menos 10 %. Se solicita parada de todos los motores inicializados al terminar o ante excepción y SIGTERM/Ctrl+C. No protege contra bloqueo del sistema, corte de comunicación con hardware o SIGKILL. El bloqueo de archivo evita dos copias de este cliente; no evita otros programas de motores. No hay parada de emergencia por hardware implementada aquí.

El servidor añade muestra_encoders (tiempo monotónico de recepción) y edad_encoders_s. El firmware Pico permanece sin modificar. Las muestras se publican cada segundo, calculadas en Pico aproximadamente cada 500 ms; no es un lazo rápido. La consigna está en RPM calculadas con 20 pulsos/vuelta aún sin calibración independiente.

## Pruebas reales del 24 de octubre de 2026

Cuatro pruebas unitarias pasan: saturación y antiacumulación, reinicio por consigna cero, rechazo de medida no finita/negativa y derivada sin salto por cambio de consigna. Pruebas sin movimiento con telemetría real realizadas. No equivalen a ajuste físico.

M0, consigna 120 RPM, kp=0.03, ki=0.02, kd=0: arranque lento, sobreimpulso a 227.5 RPM y últimas lecturas 101.8, 149.7, 113.8 RPM. Mejora respecto a ganancias anteriores, pero NO se considera estabilizado ni validado. Ver registros/pid_M0_04.csv.

Prueba conjunta: M0 y M2 registraron algunos pulsos; M1 y M3 quedaron en 0. Se activó la parada por ausencia de pulsos M1. Ruedas levantadas y libres, confirmado por usuario. Ver registros/pid_cuatro_01.csv.

M1 individual: orden del 24 %, encoder M1 siempre 0; usuario confirma giro físico. Segunda prueba de 2 segundos observando todos los canales: M1, M2 y M3 no incrementan total; M0 incrementa solo 2 pulsos al final, insuficiente para afirmar un cruce de canales. No modificar el mapeo por ese indicio. Ver registros/pid_M1_01.csv y pid_M1_mapa_01.csv.

## Pendiente antes de ajustar los cuatro

Resolver discrepancia entre giro físico y pulsos de M1. Revisar alineación disco/sensor, alimentación, masa y señal del encoder hasta GP3 Pico según configuración. No se ha inspeccionado el cableado ni identificado la causa. Comprobar también M3. No aumentar potencia ni eliminar el corte de ausencia de pulsos para compensarlo. Después caracterizar cada motor y validar giro, parada y regulación sostenida, primero libre y luego bajo carga. Las ganancias guardadas son solo una base de trabajo.

## Repetición M0/M1 con resultado correcto

Pruebas individuales de 2 segundos, potencia inicial 24 % y límite 25 %. M0: pico observado 257.5 RPM, incremento 99 pulsos en M0 y cero en otros canales. M1: pico observado 275.4 RPM, incremento 111 pulsos en M1 y cero en otros canales. Ambos regresan a PARADO/0 RPM en varias muestras consecutivas. Registros recheck_M0_1792811963041932581 y recheck_M1_1792811969055340501, CSV y JSON de cuatro canales. Mapeo M0/M1 coherente en esta repetición. No se determina la causa de la ausencia de pulsos anterior ni se valida estabilidad PID con esta prueba breve.


## Prueba conjunta prolongada solicitada

Se amplía duración admitida a 60 segundos. Se intenta prueba de 30 segundos a 120 RPM y límite 25 %. Primer intento sin base interrumpido por ausencia de pulsos de M1 antes de completar el arranque.

Se añade base configurable por motor: potencia = base + P + I + D, con saturación y antiacumulación incluyendo base. Consigna cero siempre devuelve potencia cero. Configuración experimental guardada: base=18, kp=0.03, ki=0.02, kd=0 para cada motor. --base permite sustitución temporal.

Segunda prueba: los cuatro registran RPM. Se interrumpe alrededor de 14 segundos por 3 segundos sin pulsos M2. El usuario no pudo observar si M2 seguía girando. M3 oscila y llega a 340.6 RPM. No es ajuste estable ni una prueba de 30 segundos completada. Resumen JSON calcula solo media de la prueba incompleta incluyendo arranque: no confundirla con media en régimen. Registros pid_cuatro_30s_01.csv y pid_cuatro_30s_02.csv.

Pendiente: observar giro físico y encoder M2 de forma simultánea; ajustar M3 independientemente; repetir 30–60 segundos sin cortes y medir media, dispersión y tiempo cerca de consigna. El encendido no activa PID.

### Repetición conjunta pid_cuatro_30s_03

Misma consigna 120 RPM, base 18 y límite 25 %. Corte alrededor de 7 segundos por ausencia de pulsos M2. M2 registró inicialmente 257.5/155.7/113.8 RPM y después cero pese a orden aproximada 23 %. M3 indicó hasta 365.3 RPM y mantuvo 359.3 RPM en una muestra con orden cero. Posible discrepancia de correspondencia motor/encoder o señal; no confirmada. No se cambia mapeo ni se presenta media estable. Pendiente observación física M2 y prueba individual M2/M3.
