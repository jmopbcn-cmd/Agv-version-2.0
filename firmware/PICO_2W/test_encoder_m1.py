
from machine import Pin, disable_irq, enable_irq
from time import sleep_ms, ticks_ms, ticks_diff

# =====================================
# ENCODER M1 - TRASERA DERECHA
# =====================================
GPIO_ENCODER = 3
PULSOS_POR_VUELTA = 20
INTERVALO_MS = 500

encoder = Pin(GPIO_ENCODER, Pin.IN, Pin.PULL_UP)
pulsos_totales = 0

def contar(pin):
    global pulsos_totales
    pulsos_totales += 1

encoder.irq(
    trigger=Pin.IRQ_FALLING,
    handler=contar
)

anterior = 0
tiempo_anterior = ticks_ms()

print("Encoder M1 iniciado")

try:
    while True:
        sleep_ms(INTERVALO_MS)

        irq = disable_irq()
        actual = pulsos_totales
        enable_irq(irq)

        ahora = ticks_ms()
        intervalo = ticks_diff(ahora, tiempo_anterior)

        diferencia = actual - anterior
        pulsos_segundo = diferencia * 1000 / intervalo
        rpm = pulsos_segundo * 60 / PULSOS_POR_VUELTA

        estado = "GIRANDO" if diferencia > 0 else "PARADO"

        print(
            f"M1 | {estado} | "
            f"RPM: {rpm:.1f} | "
            f"Pulsos/s: {pulsos_segundo:.1f} | "
            f"Total: {actual}"
        )

        anterior = actual
        tiempo_anterior = ahora

except KeyboardInterrupt:
    encoder.irq(handler=None)
    print("Encoder M1 detenido")
