
import asyncio
import json
from datetime import datetime
from pathlib import Path

from websockets.asyncio.server import serve

# Rutas de lectura del sistema
TEMPERATURA = Path("/sys/class/thermal/thermal_zone0/temp")
BATERIA = Path("/sys/class/power_supply/fusion-hat")


def leer_numero(nombre):
    # Leer un valor de la Fusion HAT+
    try:
        return int((BATERIA / nombre).read_text().strip())
    except (OSError, ValueError):
        return None


def leer_estado():
    try:
        return (BATERIA / "status").read_text().strip()
    except OSError:
        return "Unknown"


def obtener_datos():
    # Temperatura real de la Raspberry Pi
    temperatura = round(
        int(TEMPERATURA.read_text().strip()) / 1000, 1
    )

    # Datos de bateria
    porcentaje = leer_numero("capacity")
    microvoltios = leer_numero("voltage_now")

    voltaje = (
        round(microvoltios / 1_000_000, 3)
        if microvoltios is not None
        else None
    )

    return {
        "dispositivo": "agv-mc100",
        "temperatura_cpu": temperatura,
        "bateria": porcentaje,
        "voltaje": voltaje,
        "estado_bateria": leer_estado(),
        "fusion_hat": porcentaje is not None,
        "hora": datetime.now().isoformat(timespec="seconds")
    }


async def atender_cliente(websocket):
    print(f"Cliente conectado: {websocket.remote_address}")

    try:
        while True:
            datos = obtener_datos()
            await websocket.send(json.dumps(datos))
            await asyncio.sleep(1)

    except Exception as error:
        print(f"Cliente desconectado: {error}")


async def main():
    async with serve(atender_cliente, "0.0.0.0", 8765):
        print("Servidor AGV MC100 iniciado en puerto 8765")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
