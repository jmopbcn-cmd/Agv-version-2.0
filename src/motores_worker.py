"""Proceso de potencia fija con watchdog propio; nunca se importa hardware al importar."""
import fcntl
import json
import math
import selectors
import signal
import sys
import time

NOMBRES = ('M0', 'M1', 'M2', 'M3')

def validar(potencias):
    """Comprueba los cuatro canales y el PWM firmado entre −75 y 75 %."""
    if not isinstance(potencias, dict) or set(potencias) != set(NOMBRES):
        raise ValueError('Lista de motores no valida')
    if any(type(x) not in (int, float) or not math.isfinite(x) or not -75 <= x <= 75 for x in potencias.values()):
        raise ValueError('Potencia fuera del intervalo -75 a 75 %')
    return potencias

def ejecutar(factory=None, entrada=None, salida=None, lockpath='/tmp/agv-pid.lock', caducidad=3):
    """Lee órdenes JSON por entrada, responde por salida y detiene motores tras caducidad segundos."""
    # factory crea el motor por nombre. lockpath excluye pruebas PI simultáneas.
    entrada = entrada or sys.stdin
    salida = salida or sys.stdout
    motores = {}
    bloqueo = open(lockpath, 'w')
    selector = selectors.DefaultSelector()
    def responder(d):
        """Escribe y envía de inmediato una respuesta JSON al servidor."""
        salida.write(json.dumps(d) + '\n'); salida.flush()
    try:
        try:
            fcntl.flock(bloqueo, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Hay otra prueba de motores en ejecucion')
        selector.register(entrada, selectors.EVENT_READ)
        ultimo = time.monotonic()
        while time.monotonic() - ultimo < caducidad:
            if not selector.select(0.1):
                continue
            linea = entrada.readline(4097)
            if not linea:
                break
            if len(linea) > 4096:
                raise ValueError('Orden demasiado larga')
            potencias = validar(json.loads(linea)['potencias'])
            if any(potencias.values()) and factory is None:
                from fusion_hat.motor import Motor
                factory = lambda n: Motor(n, is_reversed=n in ('M0', 'M2'))
            for n, p in potencias.items():
                if p and n not in motores:
                    motores[n] = factory(n)
                if n in motores:
                    if p: motores[n].power(p)
                    else: motores[n].stop()
            ultimo = time.monotonic()
            responder({'ok': True})
            if not any(potencias.values()):
                break
    except Exception as error:
        responder({'ok': False, 'error': str(error)})
    finally:
        for motor in motores.values():
            try: motor.stop()
            except Exception as error:
                print('ERROR DE PARADA:', error, file=sys.stderr, flush=True)
        selector.close()
        bloqueo.close()

if __name__ == '__main__':
    def terminar(signum, frame): raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, terminar)
    try: ejecutar()
    except KeyboardInterrupt: pass
