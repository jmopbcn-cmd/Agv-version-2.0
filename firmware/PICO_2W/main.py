
from machine import Pin, UART, disable_irq, enable_irq
from time import sleep_ms, ticks_ms, ticks_diff
import json


# Lee los cuatro encoders y envía la misma línea JSON por USB y UART.
# AGB CAR - Pico 2 W
# 20 pulsos por vuelta, un flanco por ranura
PULSOS_VUELTA = 20
INTERVALO_MS = 500

NOMBRES = ("M0", "M1", "M2", "M3")
GPIOS = (2, 3, 4, 5)
uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1), timeout=100, timeout_char=10)

pulsos = [0, 0, 0, 0]
sensores = []

def irq_m0(pin):
    pulsos[0] += 1

def irq_m1(pin):
    pulsos[1] += 1

def irq_m2(pin):
    pulsos[2] += 1

def irq_m3(pin):
    pulsos[3] += 1

callbacks = (irq_m0, irq_m1, irq_m2, irq_m3)

for gpio, callback in zip(GPIOS, callbacks):
    pin = Pin(gpio, Pin.IN, Pin.PULL_UP)
    pin.irq(trigger=Pin.IRQ_FALLING, handler=callback)
    sensores.append(pin)

anteriores = [0, 0, 0, 0]
tiempo_anterior = ticks_ms()

while True:
    sleep_ms(INTERVALO_MS)

    estado_irq = disable_irq()
    actuales = pulsos[:]
    enable_irq(estado_irq)

    ahora = ticks_ms()
    intervalo = ticks_diff(ahora, tiempo_anterior)

    if intervalo <= 0:
        continue

    datos = {"tipo": "encoders"}

    for i, motor in enumerate(NOMBRES):
        diferencia = actuales[i] - anteriores[i]
        pps = diferencia * 1000 / intervalo
        rpm = pps * 60 / PULSOS_VUELTA

        datos[motor] = {
            "rpm": round(rpm, 1),
            "pulsos_s": round(pps, 1),
            "total": actuales[i],
            "estado": "GIRANDO" if diferencia else "PARADO"
        }
        anteriores[i] = actuales[i]

    tiempo_anterior = ahora

    linea = json.dumps(datos)
    uart.write(linea.encode() + bytes([10]))
    print(linea)
