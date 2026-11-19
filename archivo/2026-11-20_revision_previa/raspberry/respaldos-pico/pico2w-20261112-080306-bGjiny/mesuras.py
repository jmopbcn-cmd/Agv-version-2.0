from machine import Pin, SoftI2C
import time


# ============================================================
# CONEXIONES: GY-521 / MPU6050 → RASPBERRY PI PICO 2 W
# ============================================================
#
# VCC → 3V3 OUT, pin físico 36.
# GND → GND, pin físico 38.
# SDA → GP4, pin físico 6.
# SCL → GP5, pin físico 7.
# AD0 → GND, pin físico 8.
#
# INT, XDA y XCL quedan sin conectar.
# ============================================================


# Usamos la comunicación que ha funcionado en la prueba:
# I2C por software a una velocidad de 10 kHz.
i2c = SoftI2C(
    sda=Pin(4),
    scl=Pin(5),
    freq=10_000,
    timeout=50_000
)

# Dirección del sensor con AD0 conectado a GND.
DIRECCION = 0x68


def escribir_registro(registro, valor):
    """Envía el número del registro y el valor que queremos guardar."""

    i2c.writeto(
        DIRECCION,
        bytes([registro, valor]),
        True
    )


def leer_registros(registro, cantidad):
    """Selecciona un registro y después lee los bytes solicitados."""

    # Terminamos esta operación con STOP, como en la prueba
    # que ha leído correctamente la identificación del sensor.
    i2c.writeto(
        DIRECCION,
        bytes([registro]),
        True
    )

    # Realizamos la lectura en una operación separada.
    return i2c.readfrom(DIRECCION, cantidad)


def entero_con_signo(byte_alto, byte_bajo):
    """Convierte dos bytes en un entero de 16 bits con signo."""

    valor = (byte_alto << 8) | byte_bajo

    # Interpretamos los valores negativos en complemento a dos.
    if valor >= 32768:
        valor -= 65536

    return valor


def iniciar_sensor():
    """Comprueba la identificación y configura el sensor."""

    time.sleep_ms(500)

    dispositivos = i2c.scan()
    print("Dispositivos I2C:", [hex(d) for d in dispositivos])

    if DIRECCION not in dispositivos:
        raise RuntimeError("No se detecta el sensor en 0x68.")

    # Leemos la identificación antes de escribir la configuración.
    identificacion = leer_registros(0x75, 1)[0]
    print("Identificación:", hex(identificacion))

    if identificacion != 0x68:
        raise RuntimeError(
            "Identificación inesperada: " + hex(identificacion)
        )

    # Despertamos el sensor y seleccionamos el reloj interno
    # de referencia del giroscopio X.
    escribir_registro(0x6B, 0x01)
    time.sleep_ms(100)

    # Activamos el filtro digital para reducir el ruido.
    escribir_registro(0x1A, 0x03)

    # Configuramos el muestreo interno a 100 Hz.
    escribir_registro(0x19, 9)

    # Giroscopio: rango de ±250 grados por segundo.
    escribir_registro(0x1B, 0x00)

    # Acelerómetro: rango de ±2 g.
    escribir_registro(0x1C, 0x00)

    # Comprobamos que el registro de alimentación puede leerse
    # después de configurar el sensor.
    alimentacion = leer_registros(0x6B, 1)[0]
    print("Registro de alimentación:", hex(alimentacion))

    if alimentacion != 0x01:
        raise RuntimeError(
            "No se ha confirmado la configuración de alimentación."
        )

    print()
    print("Sensor preparado.")
    print("Aceleración: g | Giro: grados/s")
    print("Pulsa Ctrl+C para detener.")
    print()


def leer_sensor():
    """Lee aceleración, temperatura y giro en un bloque de 14 bytes."""

    datos = leer_registros(0x3B, 14)

    # Aceleración: 16384 unidades equivalen a 1 g
    # con el rango de ±2 g que hemos seleccionado.
    ax = entero_con_signo(datos[0], datos[1]) / 16384.0
    ay = entero_con_signo(datos[2], datos[3]) / 16384.0
    az = entero_con_signo(datos[4], datos[5]) / 16384.0

    # Temperatura interna del chip en grados Celsius.
    temperatura_bruta = entero_con_signo(datos[6], datos[7])
    temperatura = temperatura_bruta / 340.0 + 36.53

    # Velocidad de giro: 131 unidades equivalen a 1 grado/s
    # con el rango de ±250 grados/s seleccionado.
    gx = entero_con_signo(datos[8], datos[9]) / 131.0
    gy = entero_con_signo(datos[10], datos[11]) / 131.0
    gz = entero_con_signo(datos[12], datos[13]) / 131.0

    return ax, ay, az, gx, gy, gz, temperatura


def main():
    """Configura el módulo y muestra dos lecturas por segundo."""

    iniciar_sensor()

    while True:
        ax, ay, az, gx, gy, gz, temperatura = leer_sensor()

        print(
            "Aceleración: X={:+.3f}  Y={:+.3f}  Z={:+.3f} g".format(
                ax, ay, az
            )
        )

        print(
            "Giro:        X={:+.2f}  Y={:+.2f}  Z={:+.2f} grados/s".format(
                gx, gy, gz
            )
        )

        print(
            "Temperatura del chip: {:.1f} C".format(temperatura)
        )

        print("-" * 60)
        time.sleep_ms(500)


# Ejecutamos el programa y mostramos cualquier fallo sin ocultarlo.
try:
    main()

except KeyboardInterrupt:
    print("\nLectura detenida.")

except OSError as error:
    print("\nError de comunicación:", error)

except RuntimeError as error:
    print("\nError de comprobación:", error)
    