import asyncio, csv, json, math, statistics, sys
from pathlib import Path
from websockets.asyncio.client import connect

ROOT = Path('/home/olmos/Agv-version-2.0')
sys.path.insert(0, str(ROOT / 'raspberry'))
from pid_velocidad import PID

WORK = Path(__file__).resolve().parent
MOTORS = ('M0', 'M1', 'M2', 'M3')
CAP = 75
LEVELS = (25, 35, 45, 60, CAP)

async def receive(ws, kind=None):
    async with asyncio.timeout(2.4):
        while True:
            message = json.loads(await ws.recv())
            if message.get('tipo') == 'error_control':
                raise RuntimeError(message['error'])
            if kind and message.get('tipo') == kind:
                return message
            if not kind and 'encoders' in message:
                if (not message['pico_conectada'] or not message['fusion_hat'] or
                    not 0 <= message['edad_encoders_s'] <= 1.25):
                    raise RuntimeError('Se perdió la telemetría de los encoders o la HAT+')
                return message

async def command(ws, motor, power):
    await ws.send(json.dumps(dict(tipo='motor', motor=motor, activo=power > 0, potencia=power)))
    response = await receive(ws, 'control_motores')
    actual = response['estado']['potencias'][motor]
    if abs(actual-power) > 0.0001:
        raise RuntimeError(f'{motor}: potencia confirmada {actual}, solicitada {power}')

async def measure(ws, motor, writer, phase, samples, power, pid=None, target=None):
    result = []
    try:
        initial = await receive(ws)
        if any(initial['control_motores']['potencias'].values()):
            raise RuntimeError('Hay un motor ocupado antes de iniciar la prueba')
        previous = initial['muestra_encoders']
        await command(ws, motor, power)
        for i in range(samples):
            data = await receive(ws)
            current = data['muestra_encoders']
            dt = current - previous
            if not 0 < dt <= 2:
                raise RuntimeError(f'{motor}: intervalo de encoder inválido')
            rpm = data['encoders'][motor]['rpm']
            if type(rpm) not in (int, float) or not math.isfinite(rpm) or rpm < 0:
                raise RuntimeError(f'{motor}: RPM inválidas')
            if i >= 2 and rpm <= 0:
                raise RuntimeError(f'{motor}: sin pulsos durante la prueba')
            result.append(rpm)
            writer.writerow([motor, phase, i+1, target if target is not None else '', round(power, 4), rpm, data.get('voltaje')])
            previous = current
            power = pid.step(target, rpm, dt) if pid else power
            if i + 1 < samples:
                await command(ws, motor, power)
    finally:
        await command(ws, motor, 0)
    await asyncio.sleep(1.2)
    return result

async def main():
    first = json.loads((WORK / "resultado.json").read_text())
    curves = {m: {int(p): v for p, v in levels.items()} for m, levels in first["curvas_rpm"].items()}
    repeat_m1 = {}
    results = {}
    with (WORK / 'validacion.csv').open('w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['motor', 'fase', 'muestra', 'consigna_rpm', 'pwm_porcentaje', 'rpm', 'voltaje'])
        async with connect('ws://127.0.0.1:8765', open_timeout=3) as ws:
            for motor in MOTORS:
                powers = (25, 35, 45, CAP) if motor == "M1" else (25, 35)
                for power in powers:
                    readings = await measure(ws, motor, writer, f'pwm_{power}', 6, power)
                    file.flush()
                    measured = statistics.median(readings[-4:])
                    if motor == "M1" and power in (45, CAP):
                        repeat_m1[power] = measured
                        measured = statistics.mean((curves[motor][power], measured))
                    curves[motor][power] = measured
                print(f'{motor} curva RPM: {curves[motor]}', flush=True)
            target = first['consigna_rpm']
            if target <= 0:
                raise RuntimeError('No se encontró una consigna común')
            print(f'Consigna común: {target} RPM', flush=True)
            for motor in MOTORS:
                points = [(p, curves[motor][p]) for p in LEVELS]
                brackets = [(low, high) for low, high in zip(points, points[1:])
                            if low[1] <= target <= high[1] and high[1] - low[1] >= 10]
                if not brackets:
                    results[motor] = dict(validado=False, motivo='Consigna fuera del intervalo medido entre 25 y 75 %')
                    print(motor, results[motor], flush=True)
                    continue
                (lo, lo_rpm), (hi, hi_rpm) = brackets[0]
                slope = (hi_rpm-lo_rpm)/(hi-lo)
                base = lo + (target-lo_rpm)/slope
                kp = min(.1, .25/slope)
                ki = kp/8
                pid = PID(kp, ki, 0, limit=CAP, base=base)
                readings = (await measure(ws, motor, writer, 'validacion_pi', 20, base, pid, target))[-12:]
                file.flush()
                mean = statistics.mean(readings)
                count = sum(abs(x-target) <= .25*target for x in readings)
                results[motor] = dict(kp=round(kp,6), ki=round(ki,6), kd=0, base=round(base,3),
                                      media_rpm=round(mean,1), muestras_en_rango=count,
                                      validado=abs(mean-target)<=.15*target and count >= 10)
                print(f'{motor} validación: {results[motor]}', flush=True)
    (WORK / 'resultado_pi.json').write_text(json.dumps(dict(
        pwm_maximo=CAP, consigna_rpm=target, curvas_rpm=curves, repeticion_M1_rpm=repeat_m1, motores=results), indent=2)+'\n')
    print('PRUEBA TERMINADA', flush=True)

asyncio.run(main())
