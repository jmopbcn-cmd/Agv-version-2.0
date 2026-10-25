"""Control manual: propietario unico, limite 75 % y parada por desconexion."""
import asyncio
import json
import math
from pathlib import Path

MOTORES = ('M0', 'M1', 'M2', 'M3')
MAX_POTENCIA = 75
CADUCIDAD = 2.5

def validar_orden(motor, activo, potencia):
    if motor not in MOTORES or type(activo) is not bool:
        raise ValueError('Motor o activacion no validos')
    if type(potencia) not in (int, float) or not math.isfinite(potencia) or not 0 <= potencia <= MAX_POTENCIA:
        raise ValueError('La potencia debe estar entre 0 y 75 %')
    return float(potencia) if activo else 0.0

class ControlMotores:
    def __init__(self, python='/usr/bin/python3', clock=None):
        self.python = python
        self.clock = clock
        self.potencias = dict.fromkeys(MOTORES, 0.0)
        self.propietario = None
        self.ultima_renovacion = 0
        self.proceso = None
        self.error = None
        self.mutex = asyncio.Lock()

    def ahora(self):
        return self.clock() if self.clock else asyncio.get_running_loop().time()

    def estado(self, cliente):
        return {'potencias': dict(self.potencias), 'propio': self.propietario is cliente,
                'ocupado': self.propietario is not None and self.propietario is not cliente,
                'error': self.error, 'limite': MAX_POTENCIA}

    async def enviar(self, potencias):
        if not any(potencias.values()) and self.proceso is None:
            return
        if self.proceso is None:
            self.proceso = await asyncio.create_subprocess_exec(
                self.python, '-u', str(Path(__file__).with_name('motores_worker.py')),
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL)
        proc = self.proceso
        proc.stdin.write((json.dumps({'potencias': potencias}) + '\n').encode())
        await proc.stdin.drain()
        linea = await asyncio.wait_for(proc.stdout.readline(), 1.5)
        if not linea:
            raise RuntimeError('El controlador de motores no esta disponible')
        respuesta = json.loads(linea)
        if not respuesta.get('ok'):
            raise RuntimeError(respuesta.get('error', 'No se pudo aplicar la potencia'))
        if not any(potencias.values()):
            await asyncio.wait_for(proc.wait(), 2)
            self.proceso = None

    async def fallo(self, error):
        self.error = str(error)
        proc, self.proceso = self.proceso, None
        if proc and proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), 3)
            except asyncio.TimeoutError:
                # El watchdog independiente deja de recibir renovaciones.
                pass
        self.potencias = dict.fromkeys(MOTORES, 0.0)
        self.propietario = None

    async def ordenar(self, cliente, motor, activo, potencia):
        valor = validar_orden(motor, activo, potencia)
        async with self.mutex:
            if self.propietario is not None and self.propietario is not cliente:
                raise ValueError('Los motores estan controlados desde otro panel')
            nuevas = dict(self.potencias)
            nuevas[motor] = valor
            try:
                await self.enviar(nuevas)
            except Exception as error:
                await self.fallo(error)
                raise ValueError(self.error) from error
            self.potencias = nuevas
            self.propietario = cliente if any(nuevas.values()) else None
            self.ultima_renovacion = self.ahora()
            self.error = None

    def renovar(self, cliente):
        if self.propietario is cliente:
            self.ultima_renovacion = self.ahora()

    async def parar(self, cliente=None):
        async with self.mutex:
            if cliente is not None and self.propietario is not cliente:
                return
            try:
                await self.enviar(dict.fromkeys(MOTORES, 0.0))
            except Exception as error:
                await self.fallo(error)
            self.potencias = dict.fromkeys(MOTORES, 0.0)
            self.propietario = None

    async def vigilar(self):
        while True:
            await asyncio.sleep(0.4)
            async with self.mutex:
                if self.propietario is None:
                    continue
                nuevas = self.potencias if self.ahora() - self.ultima_renovacion < CADUCIDAD else dict.fromkeys(MOTORES, 0.0)
                try:
                    await self.enviar(nuevas)
                    self.potencias = dict(nuevas)
                    if not any(nuevas.values()):
                        self.propietario = None
                except Exception as error:
                    await self.fallo(error)
