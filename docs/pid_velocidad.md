# PID de velocidad — desarrollo

## Archivos reutilizables

- config/pid_motores.json: ganancias kp, ki y kd independientes por motor. Estado provisional, sin ajuste validado.
- raspberry/pid_velocidad.py: clase PID pura importable desde otro programa.
- raspberry/probar_pid.py: cliente de prueba manual del servidor local; no se instala al arranque.
- registros/: medidas CSV reales. Columna potencia indica la orden calculada; mover indica si se aplicó.

Ejemplo sin movimiento, desde /home/olmos/Agv-version-2.0:

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

## Corrección confirmada de canales y prueba de 30 segundos completada

Giro individual antes de corregir: motor M2 incrementa etiqueta Pico M3 en 257 pulsos; motor M3 incrementa etiqueta Pico M2 en 222 pulsos. Se confirma correspondencia cruzada respecto a los nombres de los puertos del HAT; no se determina dónde se originó físicamente.

Se añade config/canales_encoders.json: motor HAT M0->etiqueta Pico M0, M1->M1, M2->M3, M3->M2. El servidor aplica la conversión antes de publicar datos, de modo que web y PID usan nombres de puerto HAT coherentes. La Pico y los cables no se modifican. Con el firmware guardado actual, esto corresponde a GP2, GP3, GP5 y GP4 respectivamente; no confundir con número físico de pin. Los contadores mostrados de M2/M3 cambian de origen al aplicar el mapa, no se han reiniciado en placa.

Verificación individual posterior: M2 suma 136 pulsos solo en M2, M3 suma 107 solo en M3. Ambos vuelven a 0 RPM. M0/M1 previamente verificados sin cambios de mapa.

Prueba conjunta posterior: 30 segundos completados sin errores, consigna 120 RPM, kp=0.03 ki=0.02 kd=0 y base=18, potencia máxima 25 %. Pico inicial de hasta 305.4 RPM. Estadísticas siguientes excluyen los primeros 10 segundos y describen muestras cada segundo, no promedio continuo ni estabilidad bajo carga:

{
  "M0": {
    "n": 20,
    "media": 121.16,
    "desviacion": 14.64,
    "min": 89.6,
    "max": 149.7,
    "error_absoluto_medio": 12.22
  },
  "M1": {
    "n": 20,
    "media": 123.24,
    "desviacion": 11.63,
    "min": 101.6,
    "max": 149.7,
    "error_absoluto_medio": 9.65
  },
  "M2": {
    "n": 20,
    "media": 119.96,
    "desviacion": 16.25,
    "min": 71.7,
    "max": 155.7,
    "error_absoluto_medio": 11.14
  },
  "M3": {
    "n": 20,
    "media": 121.74,
    "desviacion": 14.32,
    "min": 89.6,
    "max": 149.7,
    "error_absoluto_medio": 11.62
  }
}

Configuración todavía provisional. Validación solo con ruedas libres; no prueba trayectoria recta ni respuesta en suelo, carga o batería diferente. kd=0: control PI con base, no derivada ajustada. Próximo ajuste: reducir sobreimpulso de arranque y variación, repetir bajo condiciones documentadas. PID sigue sin activarse automáticamente.

## Prueba de 40 segundos para observacion de pantallas
Completada sin errores a consigna 120 RPM y limite 25 %, configuracion guardada. Estadisticas de muestras posteriores a 10 segundos: {"M0": {"muestras": 30, "media": 121.04, "desviacion": 16.82, "min": 95.8, "max": 161.7}, "M1": {"muestras": 30, "media": 120.44, "desviacion": 13.71, "min": 95.8, "max": 161.7}, "M2": {"muestras": 30, "media": 120.45, "desviacion": 13.27, "min": 89.8, "max": 143.7}, "M3": {"muestras": 30, "media": 121.24, "desviacion": 12.04, "min": 95.6, "max": 143.4}}. Registro pid_cuatro_40s_pantallas_01.csv. Observacion visual de web y ESP32 pendiente de confirmacion del usuario.

## Ajuste vigente del 25/10/2026, tras alinear sensores

La configuracion guardada usa kp=0.005, ki=0.005, kd=0 y base=18 en los cuatro motores. Sustituye las ganancias historicas anteriores; es PI provisional para ejes libres a 120 RPM, limite 25 %. Dos pruebas de 60 s completadas; no es un ajuste validado en suelo ni a otras consignas. Sobreimpulso inicial y oscilacion residual pendientes. Ver [informe](../registros/ajuste_20261025T182255_informe.md).

## Prueba de 60 segundos por UART del 12/11/2026

M0–M3, ruedas levantadas, consigna de 120 RPM, límite de potencia del 25 %.
Se utilizó el PI guardado (Kp 0,005, Ki 0,005, Kd 0, base 18 %). La Pico
estaba alimentada por VSYS sin USB y el panel recibía los cuatro canales
por la UART de la Fusion HAT+.

| Motor | Media desde 10 s (RPM) | Rango desde 10 s (RPM) | Pico total (RPM) |
|---|---:|---:|---:|
| M0 | 134,8 | 88,9–189,7 | 260,9 |
| M1 | 139,2 | 71,1–213,4 | 284,6 |
| M2 | 137,8 | 88,9–243,1 | 314,2 |
| M3 | 139,3 | 94,9–207,5 | 266,8 |

Se registraron 60 muestras por motor sin corte. Los cuatro encoders
volvieron a 0 RPM al terminar. Las medias superaron la consigna y las RPM
siguieron oscilando. El ajuste continúa siendo provisional para ejes libres.
[Registro CSV](../registros/pid_uart_60s_20261112_085148.csv).
