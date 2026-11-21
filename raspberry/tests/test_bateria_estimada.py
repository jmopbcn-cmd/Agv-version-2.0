import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from bateria_estimada import EstimadorBateria
class Bateria(unittest.TestCase):
 def test_arranque_y_ausencia(self):
  e=EstimadorBateria();self.assertIsNone(e.actualizar(None,'Discharging',False,0));self.assertEqual(e.actualizar(70,'Discharging',False,1),70)
  for v in (-1,101,True,float('nan')):self.assertIsNone(e.actualizar(v,'Discharging',False,2))
 def test_carga_motor_y_rebote(self):
  e=EstimadorBateria();e.actualizar(70,'Discharging',False,0)
  for t in range(1,61):self.assertEqual(e.actualizar(30,'Discharging',True,t),70)
  for t in range(61,80):self.assertEqual(e.actualizar(50,'Discharging',False,t),70)
  for t in range(80,141):e.actualizar(50,'Discharging',False,t)
  anterior=e.valor;self.assertLess(anterior,70);self.assertGreater(anterior,65)
  for t in range(141,180):e.actualizar(90,'Discharging',False,t)
  self.assertLessEqual(e.valor,anterior)
 def test_recarga_si_sube(self):
  e=EstimadorBateria();e.actualizar(50,'Charging',False,0)
  for t in range(1,121):e.actualizar(80,'Charging',False,t)
  self.assertGreater(e.valor,50);self.assertLessEqual(e.valor,58)
 def test_independiente_de_numero_de_clientes(self):
  a=EstimadorBateria();b=EstimadorBateria()
  a.actualizar(70,'Discharging',False,0);b.actualizar(70,'Discharging',False,0)
  for t in range(1,121):
   a.actualizar(50,'Discharging',False,t)
   for _ in range(20):b.actualizar(50,'Discharging',False,t)
  self.assertAlmostEqual(a.valor,b.valor)
if __name__=='__main__':unittest.main()
