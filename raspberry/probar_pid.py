"""Prueba manual limitada. Sin --mover no importa ni inicializa motores."""
import argparse
import asyncio
import csv
import fcntl
import json
import math
import signal
import tempfile
from statistics import median
import time
from pathlib import Path
from websockets.asyncio.client import connect
from pid_velocidad import PID

def save_config(config_path, config):
    """Sustituye config_path de forma atómica, conservando sus permisos."""
    with tempfile.NamedTemporaryFile(mode='w', dir=config_path.parent, delete=False) as output:
        temporary_path = Path(output.name)
        try:
            json.dump(config, output, indent=2)
            output.write('\n')
            output.close()
            temporary_path.chmod(config_path.stat().st_mode & 0o777)
            temporary_path.replace(config_path)
        finally:
            temporary_path.unlink(missing_ok=True)

class NoEncoderPulses(RuntimeError):
    """Se agotó el margen de giro sin pulsos del encoder."""

    pass


async def run(args):
    """Ejecuta una prueba con las opciones CLI args y escribe las muestras en un CSV nuevo."""
    motors = {}
    names = args.motores.split(',')
    config_path = Path(args.config).resolve()
    config = json.loads(config_path.read_text())
    overrides = {key: getattr(args, key) for key in ('kp', 'ki', 'kd', 'base')
                 if getattr(args, key) is not None}
    controllers = {}
    for name in names:
        gains = config['motores'][name]
        values = [getattr(args,key) if getattr(args,key) is not None else gains[key] for key in ('kp','ki','kd')]
        if any(not isinstance(x,(int,float)) or not math.isfinite(x) or x < 0 or x > cap for x,cap in zip(values,(2,1,1))):
            raise ValueError('Ganancias fuera de limites')
        controllers[name] = PID(*values, limit=args.potencia_max, base=args.base if args.base is not None else gains.get("base",0))
    start = time.monotonic()
    last_sample = None
    stall = {name: None for name in names}
    path = Path(args.registro)
    path.parent.mkdir(parents=True, exist_ok=True)
    moving_samples = dict.fromkeys(names, 0)
    starting = set(names) if args.autoajuste else set()
    stop_errors = []
    try:
        async with connect('ws://127.0.0.1:8765/', open_timeout=3) as ws, asyncio.timeout(args.segundos+4):
            with path.open('x', newline='') as output:
                writer = csv.writer(output)
                writer.writerow(['segundos','motor','consigna_rpm','rpm','potencia','mover'])
                while time.monotonic()-start < args.segundos:
                    data = json.loads(await asyncio.wait_for(ws.recv(), 1.5))
                    if time.monotonic()-start >= args.segundos: break
                    age = data.get('edad_encoders_s')
                    sample = data.get('muestra_encoders')
                    if data.get('fusion_hat') is not True or not data.get('pico_conectada'):
                        raise RuntimeError('Fusion HAT o Pico sin datos')
                    if not isinstance(age, (int,float)) or not math.isfinite(age) or not 0 <= age <= 1.25:
                        raise RuntimeError('Lectura encoder caducada')
                    if not isinstance(sample,(int,float)) or not math.isfinite(sample):
                        raise RuntimeError('Falta identificador de muestra')
                    if sample == last_sample:
                        raise RuntimeError('Muestra encoder repetida')
                    dt = 1.0 if last_sample is None else sample-last_sample
                    if not 0 < dt <= 1.5:
                        raise RuntimeError('Intervalo encoder no valido')
                    readings = {}
                    for name in names:
                        rpm = data.get('encoders',{}).get(name,{}).get('rpm')
                        if isinstance(rpm,bool) or not isinstance(rpm,(int,float)) or not math.isfinite(rpm) or not 0 <= rpm <= 2000:
                            raise RuntimeError('RPM no validas: '+name)
                        readings[name] = rpm
                    if args.mover and not motors:
                        from fusion_hat.motor import Motor
                        for name in names:
                            motors[name] = Motor(name, is_reversed=name in ('M0','M2'))
                    last_sample = sample
                    elapsed = time.monotonic()-start
                    for name in names:
                        rpm = readings[name]
                        if rpm > 0:
                            moving_samples[name] += 1
                        power = controllers[name].step(args.rpm, rpm, dt)
                        if name in starting:
                            starting.remove(name)
                            motors[name].power(args.arranque_pwm)
                            print(name, 'impulso de arranque:', args.arranque_pwm, '% PWM', flush=True)
                            await asyncio.sleep(0.25)
                            motors[name].power(power)
                        monitoring = power >= 10 or (args.autoajuste and power > 0)
                        if args.mover and monitoring and rpm == 0:
                            if stall[name] is None: stall[name] = time.monotonic()
                            if time.monotonic()-stall[name] >= 3:
                                raise NoEncoderPulses('Sin pulsos durante 3 segundos: '+name)
                        else:
                            stall[name] = None
                        if args.mover: motors[name].power(power)
                        writer.writerow([round(elapsed,3),name,args.rpm,rpm,round(power,3),args.mover])
                        output.flush()
                        print(name, 'RPM',rpm,'potencia',round(power,1),flush=True)
    finally:
        for name,motor in motors.items():
            try: motor.stop()
            except Exception as error:
                stop_errors.append(name)
                print('ERROR AL DETENER', name, str(error), flush=True)
        print('Prueba terminada. Registro:',path,flush=True)

        if stop_errors and args.autoajuste:
            raise RuntimeError('Falló la orden de parada')
    if args.guardar:
        if stop_errors or any(count < 2 for count in moving_samples.values()):
            raise RuntimeError('Ajustes sin guardar: falta confirmar giro o parada')
        for name in names:
            config['motores'][name].update(overrides)
        config['estado'] = 'Ajuste manual provisional'
        save_config(config_path, config)
        print('Ajustes guardados en', config_path, flush=True)


async def autotune(args):
    """Ajusta un PI por motor y guarda las ganancias tras validar todos los motores solicitados."""
    config_path = Path(args.config).resolve()
    initial_config = config_path.read_text()
    config = json.loads(initial_config)
    log_path = Path(args.registro)

    async def measure(name, phase, gains, duration):
        """Mide name durante duration segundos con gains y guarda un CSV por fase phase."""
        path = log_path.with_name(f'{log_path.stem}_{name}_{phase}.csv')
        trial = argparse.Namespace(**vars(args))
        trial.motores = name
        trial.registro = str(path)
        trial.segundos = duration
        trial.guardar = False
        for key, value in gains.items():
            setattr(trial, key, value)
        try:
            await run(trial)
        except NoEncoderPulses:
            with path.open(newline='') as output:
                had_motion = any(float(row['rpm']) > 0 for row in csv.DictReader(output))
            if phase == 'validacion' or not had_motion:
                raise
            return []
        with path.open(newline='') as output:
            readings = [float(row['rpm']) for row in csv.DictReader(output)]
        if phase != 'validacion' and len(readings) >= 5 and max(readings[-5:]) == 0:
            return []
        if len(readings) < 5 or min(readings[-3:]) <= 0:
            raise RuntimeError(f'{name}: faltan lecturas de giro estables en {phase}')
        return readings

    for name in args.motores.split(','):
        fixed = dict(kp=0.0, ki=0.0, kd=0.0)
        upper = None
        for power in (args.potencia_max, 18, 15, 12, 10, 9, 8, 7, 6):
            readings = await measure(name, f'pwm_{power:g}', dict(fixed, base=power), 8)
            await asyncio.sleep(3)
            if not readings:
                if upper is None:
                    raise RuntimeError(f'{name}: sin pulsos en el primer escalón al {power:g} % de PWM')
                continue
            rpm = median(readings[-5:])
            if rpm >= args.rpm:
                upper = (power, rpm)
            elif upper and upper[1] - rpm >= 10:
                low, low_rpm = power, rpm
                high, high_rpm = upper
                break
        else:
            raise RuntimeError(
                f'{name}: no se encontró giro estable por ambos lados de '
                f'{args.rpm:g} RPM dentro del límite de potencia'
            )
        # Interpola el PWM base entre las dos velocidades medidas que encierran la consigna.
        slope = (high_rpm - low_rpm) / (high - low)
        kp = min(0.1, 0.25 / slope)
        gains = dict(kp=round(kp, 6), ki=round(kp / 8, 6), kd=0.0,
                     base=round(low + (args.rpm - low_rpm) / slope, 3))
        await asyncio.sleep(3)
        readings = (await measure(name, 'validacion', gains, 30))[-12:]
        mean_rpm = sum(readings) / len(readings)
        in_range = sum(abs(rpm - args.rpm) <= 0.25 * args.rpm for rpm in readings)
        print(f'{name}: media {mean_rpm:.1f} RPM; {in_range}/{len(readings)} muestras dentro de ±25 %',
              flush=True)
        if (len(readings) < 12 or min(readings) <= 0 or
                abs(mean_rpm - args.rpm) > 0.15 * args.rpm or in_range < 10):
            raise RuntimeError(f'{name}: regulación fuera de tolerancia: {readings}')
        config['motores'][name].update(gains)
        print(f'{name}: {gains}, RPM finales: {readings}', flush=True)
        await asyncio.sleep(3)

    if config_path.read_text() != initial_config:
        raise RuntimeError('La configuración cambió durante el autoajuste')
    config['estado'] = f'Autoajuste PI provisional a {args.rpm:g} RPM'
    save_config(config_path, config)
    print('Ajustes guardados en', config_path, flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=float, help='PWM base en porcentaje (0–25), antes de la corrección PI.')
    parser.add_argument('--mover',action='store_true', help='Habilita la salida física a motores.')
    parser.add_argument('--autoajuste', action='store_true', help='Mide y valida un PI por motor, luego guarda las ganancias.')
    parser.add_argument('--arranque-pwm', type=float, default=25.0,
                        help='PWM del impulso de 250 ms para autoajuste')
    parser.add_argument('--guardar', action='store_true',
                        help='Guarda las ganancias indicadas tras una prueba con movimiento')
    parser.add_argument('--motores',default='M0', help='Canales separados por comas (por ejemplo, M0,M1).')
    parser.add_argument('--rpm',type=float,default=60, help='Consigna en RPM (hasta 120 en prueba manual o 350 en autoajuste).')
    parser.add_argument('--segundos',type=float,default=5, help='Duración de la prueba manual en segundos (1–60).')
    parser.add_argument('--potencia-max',type=float,default=25, help='Techo de PWM tras el impulso, en porcentaje.')
    parser.add_argument('--config',default=str(Path(__file__).resolve().parents[1]/'config/pid_motores.json'), help='Ruta al JSON de ganancias por motor.')
    parser.add_argument('--kp',type=float, help='Ganancia proporcional, en puntos de PWM por RPM.')
    parser.add_argument('--ki',type=float, help='Ganancia integral, en puntos de PWM por RPM·s.')
    parser.add_argument('--kd',type=float, help='Ganancia derivativa, en puntos de PWM por RPM/s.')
    parser.add_argument('--registro',required=True, help='Ruta nueva para el CSV, o prefijo de los CSV de autoajuste.')
    args=parser.parse_args()
    if args.guardar and (not args.mover or args.rpm <= 0 or
                         all(getattr(args, key) is None for key in ('kp', 'ki', 'kd', 'base'))):
        parser.error('--guardar requiere --mover, RPM positivas y al menos un ajuste explicito')
    names=args.motores.split(',')
    if len(names)!=len(set(names)) or any(n not in ('M0','M1','M2','M3') for n in names): parser.error('Motores no validos')
    for value,low,high in [(args.base,0,25),(args.rpm,0,350 if args.autoajuste else 120),(args.arranque_pwm,1,75),(args.segundos,1,60),(args.potencia_max,1,35),(args.kp,0,2),(args.ki,0,1),(args.kd,0,1)]:
        if value is not None and (not math.isfinite(value) or not low <= value <= high): parser.error('Parametro fuera de limites')
    if args.autoajuste and (not args.mover or not 20 <= args.potencia_max <= 25 or
                             args.rpm <= 0 or args.guardar or
                             any(getattr(args, key) is not None for key in ('kp', 'ki', 'kd', 'base'))):
        parser.error('--autoajuste requiere --mover, RPM positivas y límite de potencia entre 20 y 25')
    def terminate(signum,frame): raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM,terminate)
    try:
        with open('/tmp/agv-pid.lock', 'w') as lockfile:
            fcntl.flock(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
            asyncio.run(autotune(args) if args.autoajuste else run(args))
    except KeyboardInterrupt:
        print('Interrumpido')
