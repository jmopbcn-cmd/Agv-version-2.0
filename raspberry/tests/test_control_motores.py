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
        for p in [-1,75.1,100,float('nan'),float('inf'),True,'25',None]:
            with self.assertRaises(ValueError):validar_orden('M0',True,p)
            with self.assertRaises(ValueError):validar(dict.fromkeys(('M0','M1','M2','M3'),p))
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
    async def test_renovar_no_reactiva_y_no_admite_otro(self):
        c=Simulado();a=object();b=object();c.renovar(a);self.assertIsNone(c.propietario)
        await c.ordenar(a,'M0',True,20);c.t=1;c.renovar(b);self.assertEqual(c.ultima_renovacion,0)
        c.renovar(a);self.assertEqual(c.ultima_renovacion,1)
        await c.parar(a);c.renovar(a);self.assertFalse(any(c.potencias.values()))

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
