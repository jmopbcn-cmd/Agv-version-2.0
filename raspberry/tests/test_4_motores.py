from fusion_hat.motor import Motor
from time import sleep

# Configuración comprobada del AGV
motores = {
    "M0": Motor("M0", is_reversed=True),   # Trasera izquierda
    "M1": Motor("M1"),                     # Trasera derecha
    "M2": Motor("M2", is_reversed=True),   # Delantera derecha
    "M3": Motor("M3")                      # Delantera izquierda
}

try:
    print("Iniciando prueba de los 4 motores")

    for motor in motores.values():
        motor.power(50)

    sleep(10)

finally:
    for motor in motores.values():
        motor.stop()

    print("Todos los motores detenidos")