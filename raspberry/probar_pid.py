"""Prueba manual limitada. Sin --mover no importa ni inicializa motores."""
import argparse
import asyncio
import csv
import fcntl
import json
import math
import signal
import time
from pathlib import Path
from websockets.asyncio.client import connect
from pid_velocidad import PID

async def run(args):
    motors = {}
    lockfile = open('/tmp/agb-pid.lock', 'w')
    fcntl.flock(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
    names = args.motores.split(',')
    config = json.loads(Path(args.config).read_text())
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
                        power = controllers[name].step(args.rpm, rpm, dt)
                        if args.mover and power >= 10 and rpm == 0:
                            if stall[name] is None: stall[name] = time.monotonic()
                            if time.monotonic()-stall[name] >= 3:
                                raise RuntimeError('Sin pulsos durante 3 segundos: '+name)
                        else:
                            stall[name] = None
                        if args.mover: motors[name].power(power)
                        writer.writerow([round(elapsed,3),name,args.rpm,rpm,round(power,3),args.mover])
                        output.flush()
                        print(name, 'RPM',rpm,'potencia',round(power,1),flush=True)
    finally:
        for name,motor in motors.items():
            try: motor.stop()
            except Exception as error: print('ERROR AL DETENER',name,str(error),flush=True)
        lockfile.close()
        print('Prueba terminada. Registro:',path,flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=float)
    parser.add_argument('--mover',action='store_true')
    parser.add_argument('--motores',default='M0')
    parser.add_argument('--rpm',type=float,default=60)
    parser.add_argument('--segundos',type=float,default=5)
    parser.add_argument('--potencia-max',type=float,default=25)
    parser.add_argument('--config',default=str(Path(__file__).resolve().parents[1]/'config/pid_motores.json'))
    parser.add_argument('--kp',type=float)
    parser.add_argument('--ki',type=float)
    parser.add_argument('--kd',type=float)
    parser.add_argument('--registro',required=True)
    args=parser.parse_args()
    names=args.motores.split(',')
    if len(names)!=len(set(names)) or any(n not in ('M0','M1','M2','M3') for n in names): parser.error('Motores no validos')
    for value,low,high in [(args.base,0,25),(args.rpm,0,120),(args.segundos,1,60),(args.potencia_max,1,35),(args.kp,0,2),(args.ki,0,1),(args.kd,0,1)]:
        if value is not None and (not math.isfinite(value) or not low <= value <= high): parser.error('Parametro fuera de limites')
    def terminate(signum,frame): raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM,terminate)
    try: asyncio.run(run(args))
    except KeyboardInterrupt: print('Interrumpido')
