"""Comparacion manual a potencia fija; 60 s por motor, maximo 90 %, ejes libres."""
import asyncio,json,time,signal,fcntl,argparse
from pathlib import Path

async def run(output):
 from fusion_hat.motor import Motor
 from websockets.asyncio.client import connect
 motors={};state={};start=time.monotonic()
 lock=open('/tmp/agv-pid.lock','w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with Path(output).open('x') as log:
  def emit(d):
   d['total_s']=round(time.monotonic()-start,3);s=json.dumps(d);log.write(s+'\n');log.flush();print(s,flush=True)
  async def telemetry(ws):
   while True:
    d=json.loads(await asyncio.wait_for(ws.recv(),3))
    if d.get('pico_conectada') is not True or d.get('fusion_hat') is not True:raise RuntimeError('Pico/HAT sin datos')
    age=d.get('edad_encoders_s')
    if not isinstance(age,(float,int)) or not 0<=age<=1.25:raise RuntimeError('Telemetria caducada')
    emit({'evento':'muestra',**state,'fase_s':round(time.monotonic()-state.get('inicio_fase',time.monotonic()),3),'encoders':d.get('encoders'),'voltaje':d.get('voltaje')})
  async def drive():
   schedule=[('rapido',p,2.5) for p in [10,25,50,75]]+[('meseta',p,10) for p in [10,25,50,75]]+[('meseta',90,10)]
   for n in ['M0','M1','M2','M3']:
    motors[n]=Motor(n,is_reversed=n in ('M0','M2'))
    try:
     for kind,power,seconds in schedule:
      state.update(motor=n,tipo=kind,potencia=power,inicio_fase=time.monotonic())
      motors[n].power(power);emit({'evento':'cambio','motor':n,'tipo':kind,'potencia':power,'duracion_s':seconds})
      await asyncio.sleep(seconds)
    finally:motors[n].stop()
    state.update(motor=n,tipo='reposo',potencia=0,inicio_fase=time.monotonic());emit({'evento':'motor_detenido','motor':n})
    await asyncio.sleep(3)
  try:
   async with connect('ws://127.0.0.1:8765/',open_timeout=3) as ws:
    initial=json.loads(await asyncio.wait_for(ws.recv(),3))
    if initial.get('pico_conectada') is not True or initial.get('fusion_hat') is not True:raise RuntimeError('Prerrequisitos ausentes')
    emit({'evento':'inicio','duracion_por_motor_s':60,'potencia_max':90})
    t=asyncio.create_task(telemetry(ws));d=asyncio.create_task(drive())
    try:
     done,_=await asyncio.wait([t,d],return_when=asyncio.FIRST_COMPLETED)
     for task in done:task.result()
    finally:
     for task in [t,d]:task.cancel()
     await asyncio.gather(t,d,return_exceptions=True)
  except BaseException as e:
   emit({'evento':'interrumpido','detalle':repr(e)});raise
  finally:
   for n,m in motors.items():
    try:m.stop()
    except Exception as e:emit({'evento':'error_parada','motor':n,'detalle':str(e)})
   emit({'evento':'fin_motores_parados'});lock.close()

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--registro',required=True);args=p.parse_args()
 def stop(signum,frame):raise KeyboardInterrupt()
 signal.signal(signal.SIGTERM,stop)
 try:asyncio.run(run(args.registro))
 except KeyboardInterrupt:pass
