
from machine import Pin, disable_irq, enable_irq
from time import sleep_ms, ticks_ms, ticks_diff

# ==========================================
# AGB CAR INTELIGENT
# Raspberry Pi Pico 2 W
# Lectura simultanea de 4 encoders
# ==========================================

PULSOS_POR_VUELTA = 20
INTERVALO_MS = 500

# Motor: (GPIO, posicion)
CONFIG = {
    "M0": (2, "TI"),
    "M1": (3, "TD"),
    "M2": (4, "DD"),
    "M3": (5, "DI")
}

pulsos = [0, 0, 0, 0]

# Interrupciones independientes
def irq_m0(pin):
    pulsos[0] += 1

def irq_m1(pin):
    pulsos[1] += 1

def irq_m2(pin):
    pulsos[2] += 1

def irq_m3(pin):
    pulsos[3] += 1

callbacks = [irq_m0, irq_m1, irq_m2, irq_m3]
sensores = []

# Configurar cada sensor
for i, (motor, (gpio, posicion)) in enumerate(CONFIG.items()):
    sensor = Pin(gpio, Pin.IN, Pin.PULL_UP)
    sensor.irq(
        trigger=Pin.IRQ_FALLING,
        handler=callbacks[i]
    )
    sensores.append(sensor)

anteriores = [0, 0, 0, 0]
tiempo_anterior = ticks_ms()

print("AGB CAR - 4 ENCODERS INICIADOS")
print("20 pulsos por vuelta")
print("----------------------------------------")

try:
    while True:
        sleep_ms(INTERVALO_MS)

        # Copiar contadores sin interrupciones
        estado_irq = disable_irq()
        actuales = pulsos[:]
        enable_irq(estado_irq)

        ahora = ticks_ms()
        intervalo = ticks_diff(ahora, tiempo_anterior)

        print("\n========== ENCODERS ==========")

        for i, (motor, (gpio, posicion)) in enumerate(CONFIG.items()):
            diferencia = actuales[i] - anteriores[i]

            pulsos_segundo = diferencia * 1000 / intervalo
            rpm = pulsos_segundo * 60 / PULSOS_POR_VUELTA

            estado = "GIRANDO" if diferencia > 0 else "PARADO"

            print(
                f"{motor} ({posicion}) | "
                f"{estado:7} | "
                f"RPM: {rpm:6.1f} | "
                f"P/s: {pulsos_segundo:6.1f} | "
                f"Total: {actuales[i]}"
            )

            anteriores[i] = actuales[i]

        tiempo_anterior = ahora

except KeyboardInterrupt:
    for sensor in sensores:
        sensor.irq(handler=None)

    print("\nLectura de encoders detenida")
