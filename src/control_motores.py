"""Control manual: propietario unico, limite 75 % y parada por desconexion."""
import asyncio
import sys
import json
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'raspberry'))
from pid_velocidad import PID

PWM_MINIMO = 25.0
PWM_MAXIMO_MARCHA = 35.0
RPM_MARCHA = 400.0

MOTORES = ('M0', 'M1', 'M2', 'M3')
MAX_POTENCIA = 75
# Segundos sin renovación del control individual.
CADUCIDAD = 2.5

def validar_orden(motor, activo, potencia):
    """Valida el motor M0–M3, el booleano activo y el PWM individual de 0 a 75 %."""
    if motor not in MOTORES or type(activo) is not bool:
        raise ValueError('Motor o activacion no validos')
    if type(potencia) not in (int, float) or not math.isfinite(potencia) or not 0 <= potencia <= MAX_POTENCIA:
        raise ValueError('La potencia debe estar entre 0 y 75 %')
    return float(potencia) if activo else 0.0

class ControlMotores:
    def __init__(self, python='/usr/bin/python3', clock=None):
        """Configura el intérprete del proceso auxiliar y, opcionalmente, un reloj monotónico de prueba."""
        self.python = python
        self.clock = clock
        self.potencias = dict.fromkeys(MOTORES, 0.0)
        self.propietario = None
        self.ultima_renovacion = 0
        self.proceso = None
        self.error = None
        self.mutex = asyncio.Lock()
        self.marcha = None
        self.inicio_marcha = 0
        self.reguladores = {}
        self.ultima_muestra = None

    def ahora(self):
        """Devuelve el tiempo monotónico en segundos para medir los plazos de control."""
        return self.clock() if self.clock else asyncio.get_running_loop().time()

    def estado(self, cliente):
        """Devuelve el PWM y la titularidad del control desde la perspectiva de cliente."""
        return {'potencias': dict(self.potencias), 'propio': self.propietario is cliente,
                'ocupado': self.propietario is not None and self.propietario is not cliente,
                'error': self.error, 'limite': MAX_POTENCIA, 'marcha': self.marcha}

    async def enviar(self, potencias):
        """Envía un mapa de PWM firmado para M0–M3 y espera la confirmación del proceso auxiliar."""
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
        """Registra el error, intenta cerrar el proceso auxiliar y libera el control."""
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
        self.marcha = None

    async def ordenar(self, cliente, motor, activo, potencia):
        """Aplica el PWM de un motor para el cliente WebSocket que posee o solicita el control."""
        valor = validar_orden(motor, activo, potencia)
        async with self.mutex:
            if self.propietario is not None and self.propietario is not cliente:
                raise ValueError('Los motores estan controlados desde otro panel')
            if self.marcha:
                raise ValueError("Suelta el botón de marcha primero")
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

    async def conducir(self, cliente, sentido):
        """Inicia la marcha del cliente WebSocket con PWM inicial del 25 % y regulación por rueda."""
        if sentido not in ('adelante', 'atras', 'izquierda', 'derecha'):
            raise ValueError('Sentido no válido')
        async with self.mutex:
            if self.propietario is not None:
                raise ValueError('Para los motores antes de iniciar otra marcha')
            lado_izquierdo = PWM_MINIMO if sentido in ('adelante', 'derecha') else -PWM_MINIMO
            lado_derecho = PWM_MINIMO if sentido in ('adelante', 'izquierda') else -PWM_MINIMO
            config = json.loads(Path(__file__).with_name('pi_marcha.json').read_text())
            self.reguladores = {
                motor: PID(config[motor]['kp'], config[motor]['ki'], 0,
                           limit=PWM_MAXIMO_MARCHA - PWM_MINIMO)
                for motor in MOTORES
            }
            self.ultima_muestra = None
            nuevas = {motor: lado_izquierdo if motor in ('M0', 'M3') else lado_derecho
                      for motor in MOTORES}
            try:
                await self.enviar(nuevas)
            except Exception as error:
                await self.fallo(error)
                raise ValueError(self.error) from error
            self.potencias = nuevas
            self.propietario = cliente
            self.marcha = sentido
            self.inicio_marcha = self.ultima_renovacion = self.ahora()
            self.error = None

    def renovar(self, cliente):
        """Actualiza el plazo de control solo cuando cliente es el propietario actual."""
        if self.propietario is cliente:
            self.ultima_renovacion = self.ahora()

    async def parar(self, cliente=None):
        """Ordena PWM cero al propietario indicado o a todos si cliente es None."""
        async with self.mutex:
            if cliente is not None and self.propietario is not cliente:
                return
            try:
                await self.enviar(dict.fromkeys(MOTORES, 0.0))
            except Exception as error:
                await self.fallo(error)
            self.potencias = dict.fromkeys(MOTORES, 0.0)
            self.propietario = None
            self.marcha = None

    async def vigilar(self, telemetria=None):
        """Renueva el proceso auxiliar y corta la marcha al caducar el control o faltar telemetría."""
        while True:
            await asyncio.sleep(0.4)
            async with self.mutex:
                if self.propietario is None:
                    continue
                ahora = self.ahora()
                # La marcha exige renovar cada 1,25 s y deja 3 s para detectar giro al arrancar.
                caducidad = 1.25 if self.marcha else CADUCIDAD
                nuevas = self.potencias if ahora - self.ultima_renovacion < caducidad else dict.fromkeys(MOTORES, 0.0)
                if self.marcha and telemetria and any(nuevas.values()):
                    datos = telemetria()
                    encoders = datos['encoders']
                    falta_giro = ahora - self.inicio_marcha >= 3 and any(
                        not (encoders.get(motor, {}).get('rpm', 0) or 0) > 0 for motor in MOTORES
                    )
                    if not datos['fusion_hat'] or not datos['pico_conectada'] or falta_giro:
                        nuevas = dict.fromkeys(MOTORES, 0.0)
                        self.error = 'Marcha detenida: falta señal de la Pico o de una rueda'
                    else:
                        muestra = datos.get('muestra_encoders')
                        if muestra is not None and muestra != self.ultima_muestra:
                            previa, self.ultima_muestra = self.ultima_muestra, muestra
                            rpm = [encoders.get(motor, {}).get('rpm') for motor in MOTORES]
                            if (previa is not None and 0 < muestra - previa <= 2.5 and
                                all(type(v) in (int, float) and math.isfinite(v) and v > 0 for v in rpm)):
                                nuevas = {
                                    motor: math.copysign(PWM_MINIMO + self.reguladores[motor].step(
                                        RPM_MARCHA, medida, muestra - previa), nuevas[motor])
                                    for motor, medida in zip(MOTORES, rpm)
                                }
                try:
                    await self.enviar(nuevas)
                    self.potencias = dict(nuevas)
                    if not any(nuevas.values()):
                        self.propietario = None
                        self.marcha = None
                except Exception as error:
                    await self.fallo(error)
