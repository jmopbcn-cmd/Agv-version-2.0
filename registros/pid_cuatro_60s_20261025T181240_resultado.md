# Intento de PID conjunto de 60 segundos

25/10/2026. Consigna 120 RPM, cuatro motores, limite 25 %, configuracion guardada sin cambios. Duracion prevista 60 s; prueba abortada por RuntimeError: Sin pulsos durante 3 segundos: M1. Salida del cliente 1. M1 publico 0 RPM en todas sus filas. Otros canales registraron picos de hasta 431.1 RPM. No se completo el minuto ni se obtuvieron muestras de regimen desde 10 s. El cliente solicito parada en finally; diagnostico final repetido confirma dos muestras de cuatro canales a 0 RPM. No se repitio automaticamente, ni se modificaron ganancias, mapa, firmware o servicios. Telemetria no equivale a observacion fisica.

CSV: pid_cuatro_60s_20261025T181240.csv
