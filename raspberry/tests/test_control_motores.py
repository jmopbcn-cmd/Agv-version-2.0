"""Pruebas sin hardware del control manual y su watchdog."""
import asyncio
import fcntl
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2] / 'src'))
from control_motores import ControlMotores, validar_orden
from motores_worker import ejecutar, validar

class Validacion(unittest.TestCase):
    def test_limites_en_ambas_capas(self):
        for p in [75.1,100,float('nan'),float('inf'),True,'25',None]:
            with self.assertRaises(ValueError):validar_orden('M0',True,p)
            with self.assertRaises(ValueError):validar(dict.fromkeys(('M0','M1','M2','M3'),p))
        with self.assertRaises(ValueError): validar_orden('M3',True,-1)
        with self.assertRaises(ValueError): validar(dict.fromkeys(('M0','M1','M2','M3'),-75.1))
        reversa = dict.fromkeys(('M0','M1','M2','M3'),-75)
        self.assertEqual(validar(reversa),reversa)
        self.assertEqual(validar_orden('M3',True,75),75)
        self.assertEqual(validar_orden('M0',False,25),0)
    def test_motor_y_tipo_activacion(self):
        for n,a in [('M4',True),('M0','true'),('M0',1)]:
            with self.assertRaises(ValueError):validar_orden(n,a,10)

class Simulado(ControlMotores):
    def __init__(self):
        self.t=0;self.envios=[]
        super().__init__(clock=lambda:self.t)
    async def enviar(self,potencias):self.envios.append(dict(potencias))

class Propiedad(unittest.IsolatedAsyncioTestCase):
    async def test_independencia_y_propietario(self):
        c=Simulado();a=object();b=object()
        await c.ordenar(a,'M0',True,25);await c.ordenar(a,'M2',True,75)
        self.assertEqual(c.potencias,{'M0':25,'M1':0,'M2':75,'M3':0})
        with self.assertRaises(ValueError):await c.ordenar(b,'M1',True,10)
        await c.parar(b);self.assertEqual(c.potencias['M0'],25)
        await c.ordenar(a,'M0',False,0);self.assertEqual(c.potencias['M2'],75)
        await c.parar();self.assertFalse(any(c.potencias.values()))
    async def test_desconexion_del_propietario(self):
        c=Simulado();a=object();await c.ordenar(a,'M1',True,30)
        await c.parar(a);self.assertIsNone(c.propietario)
        self.assertFalse(any(c.potencias.values()))
    async def test_watchdog_sin_renovacion(self):
        c=Simulado();a=object();await c.ordenar(a,'M1',True,30);c.t=4
        t=asyncio.create_task(c.vigilar());await asyncio.sleep(.45);t.cancel()
        await asyncio.gather(t,return_exceptions=True)
        self.assertFalse(any(c.potencias.values()))
    async def test_marcha_en_ambos_sentidos_y_parada(self):
        c = Simulado()
        cliente = object()
        for sentido, potencia in (('adelante', 25), ('atras', -25)):
            await c.conducir(cliente, sentido)
            self.assertEqual(c.estado(cliente)['marcha'], sentido)
            self.assertEqual(set(c.potencias.values()), {potencia})
            await c.parar(cliente)
            self.assertFalse(any(c.potencias.values()))

    async def test_joystick_gira_sin_invertir_mientras_avanza(self):
        c = Simulado()
        cliente = object()
        await c.conducir(cliente, 'joystick', 0, .8)
        await c.conducir(cliente, 'joystick', .6, .8)
        self.assertGreater(c.objetivos['M0'], 3 * c.objetivos['M1'])
        await c.conducir(cliente, 'joystick', -.8, .05)
        self.assertEqual(c.objetivos['M0'], 0)
        self.assertEqual(c.objetivos['M3'], 0)
        self.assertGreater(c.objetivos['M1'], 0)
        await c.conducir(cliente, 'joystick', .8, .05)
        self.assertGreater(c.objetivos['M0'], 0)
        self.assertEqual(c.objetivos['M1'], 0)
        self.assertIs(c.propietario, cliente)
        with self.assertRaisesRegex(ValueError, 'invertir'):
            await c.conducir(cliente, 'joystick', 0, -.8)
        await c.conducir(cliente, 'joystick', 0, 0)
        self.assertFalse(any(c.potencias.values()))

    async def test_joystick_tactil_arranca_en_minimo_y_respeta_el_tope(self):
        c = Simulado()
        cliente = object()
        await c.conducir(cliente, 'joystick', 0, .8, 75)
        self.assertEqual(set(c.potencias.values()), {25.0})
        self.assertEqual(set(c.potencias_joystick().values()), {30.0})
        for _ in range(12):
            potencias = c.potencias_joystick()
        self.assertEqual(set(potencias.values()), {75.0})
        await c.conducir(cliente, 'joystick', .8, .8, 50)
        self.assertEqual(c.potencias_joystick(), {'M0': 50, 'M1': 0, 'M2': 0, 'M3': 50})
        await c.conducir(cliente, 'joystick', 0, 0, 50)
        self.assertFalse(any(c.potencias.values()))

    async def test_potencia_compartida_no_mueve_y_se_publica(self):
        c = Simulado()
        cliente = object()
        self.assertEqual(c.estado(cliente)['potencia_joysticks'], 25)
        c.fijar_potencia_joysticks(75)
        self.assertEqual(c.estado(object())['potencia_joysticks'], 75)
        self.assertFalse(c.envios)
        with self.assertRaisesRegex(ValueError, 'fuera de rango'):
            c.fijar_potencia_joysticks(80)
        self.assertEqual(c.potencia_joysticks, 75)

    async def test_joystick_tactil_rechaza_potencias_fuera_de_rango(self):
        c = Simulado()
        for potencia in (24, 76, True, '75', float('nan')):
            with self.assertRaisesRegex(ValueError, 'fuera de rango'):
                await c.conducir(object(), 'joystick', 0, .8, potencia)
        self.assertFalse(c.envios)

    async def test_joystick_conserva_el_giro_en_sitio_desde_parado(self):
        c = Simulado()
        await c.conducir(object(), 'joystick', .8, 0)
        self.assertGreater(c.objetivos['M0'], 0)
        self.assertEqual(c.objetivos['M1'], -c.objetivos['M0'])

    async def test_marcha_se_detiene_sin_pulsos(self):
        c = Simulado()
        cliente = object()
        await c.conducir(cliente, 'adelante')
        c.t = 3
        c.renovar(cliente)
        telemetria = {'fusion_hat': True, 'pico_conectada': True, 'encoders': {}}
        tarea = asyncio.create_task(c.vigilar(lambda: telemetria))
        try:
            await asyncio.sleep(.45)
            self.assertIsNone(c.marcha)
            self.assertFalse(any(c.potencias.values()))
            self.assertIn('falta señal', c.error)
        finally:
            tarea.cancel()
            await asyncio.gather(tarea, return_exceptions=True)

    async def test_renovar_no_reactiva_y_no_admite_otro(self):
        c=Simulado();a=object();b=object();c.renovar(a);self.assertIsNone(c.propietario)
        await c.ordenar(a,'M0',True,20);c.t=1;c.renovar(b);self.assertEqual(c.ultima_renovacion,0)
        c.renovar(a);self.assertEqual(c.ultima_renovacion,1)
        await c.parar(a);c.renovar(a);self.assertFalse(any(c.potencias.values()))

    async def test_encender_todos_niveles_y_cambio_atomico(self):
        c = Simulado(); cliente = object()
        for potencia in (25, 50, 75):
            previos = len(c.envios)
            await c.encender_todos(cliente, potencia)
            self.assertEqual(len(c.envios), previos + 1)
            self.assertEqual(c.potencias, dict.fromkeys(('M0','M1','M2','M3'), potencia))
            self.assertIs(c.propietario, cliente)
        with self.assertRaises(ValueError):
            await c.encender_todos(object(), 25)
        await c.parar(cliente)
        self.assertFalse(any(c.potencias.values()))

    async def test_encender_todos_rechaza_valores_y_marcha(self):
        c = Simulado(); cliente = object()
        for valor in (0, 24, 26, 76, True, '50', None, float('nan')):
            with self.assertRaises(ValueError): await c.encender_todos(cliente, valor)
        self.assertFalse(c.envios)
        await c.conducir(cliente, 'adelante')
        with self.assertRaises(ValueError): await c.encender_todos(cliente, 50)
        await c.parar(cliente)

    async def test_encender_todos_watchdog_y_desconexion(self):
        c = Simulado(); cliente = object()
        await c.encender_todos(cliente, 75)
        c.t = 4
        tarea = asyncio.create_task(c.vigilar())
        try:
            await asyncio.sleep(.45)
            self.assertFalse(any(c.potencias.values()))
        finally:
            tarea.cancel(); await asyncio.gather(tarea, return_exceptions=True)
        await c.encender_todos(cliente, 50)
        await c.parar(cliente)
        self.assertFalse(any(c.potencias.values()))

class Worker(unittest.TestCase):
    def escenario(self,ordenes,close=True,bloqueado=False):
        eventos=[]
        class MotorFalso:
            def __init__(self,n):self.n=n
            def power(self,p):eventos.append((self.n,'power',p))
            def stop(self):eventos.append((self.n,'stop'))
        with tempfile.TemporaryDirectory() as tmp:
            lockpath=str(Path(tmp)/'motor.lock');held=open(lockpath,'w') if bloqueado else None
            if held:fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB)
            ri,wi=os.pipe();ro,wo=os.pipe()
            entrada=os.fdopen(ri);salida=os.fdopen(wo,'w',buffering=1)
            escritor=os.fdopen(wi,'w',buffering=1);lector=os.fdopen(ro)
            def worker():
                try:ejecutar(MotorFalso,entrada,salida,lockpath=lockpath,caducidad=.25)
                finally:entrada.close();salida.close()
            t=threading.Thread(target=worker);t.start()
            respuestas=[]
            for orden in ordenes:
                escritor.write(json.dumps({'potencias':orden})+'\n');escritor.flush()
                respuestas.append(json.loads(lector.readline()))
                if not respuestas[-1]['ok']:break
            if close:escritor.close()
            t.join(2);self.assertFalse(t.is_alive())
            if not close:escritor.close()
            lector.close()
            if held:held.close()
            return eventos,respuestas
    def test_cierre_stdin_detiene(self):
        e,r=self.escenario([{'M0':25,'M1':0,'M2':0,'M3':0}])
        self.assertTrue(r[0]['ok']);self.assertEqual(e[-1],('M0','stop'))
    def test_watchdog_independiente(self):
        e,r=self.escenario([{'M0':0,'M1':30,'M2':0,'M3':0}],close=False)
        self.assertEqual(e[-1],('M1','stop'))
    def test_bloqueo_no_inicializa_motores(self):
        e,r=self.escenario([{'M0':25,'M1':0,'M2':0,'M3':0}],bloqueado=True)
        self.assertFalse(r[0]['ok']);self.assertEqual(e,[])
    def test_invalido_detiene_orden_previa(self):
        e,r=self.escenario([{'M0':25,'M1':0,'M2':0,'M3':0},{'M0':76,'M1':0,'M2':0,'M3':0}])
        self.assertFalse(r[-1]['ok']);self.assertEqual(e[-1],('M0','stop'))
    def test_parada_general(self):
        e,r=self.escenario([{'M0':25,'M1':75,'M2':0,'M3':0},dict.fromkeys(('M0','M1','M2','M3'),0)])
        self.assertTrue(r[-1]['ok']);self.assertIn(('M0','stop'),e);self.assertIn(('M1','stop'),e)
if __name__=='__main__':unittest.main()
