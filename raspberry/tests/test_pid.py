import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pid_velocidad import PID

class PIDTests(unittest.TestCase):
    def test_saturation_does_not_accumulate(self):
        pid=PID(kp=1,ki=1,limit=20)
        for _ in range(100): self.assertEqual(pid.step(100,0,0.5),20)
        self.assertEqual(pid.integral,0)
        self.assertEqual(pid.step(100,110,0.5),0)
    def test_base_stops_and_saturates(self):
        pid=PID(base=18,limit=25)
        self.assertLessEqual(pid.step(120,0,1),25)
        self.assertEqual(pid.step(0,0,1),0)

    def test_stop_resets(self):
        pid=PID()
        pid.step(60,20,1)
        self.assertEqual(pid.step(0,20,1),0)
        self.assertEqual(pid.integral,0)
    def test_invalid_feedback(self):
        for value in (float('nan'),float('inf'),-1):
            with self.assertRaises(ValueError): PID().step(60,value,1)
    def test_derivative_on_measurement(self):
        pid=PID(kp=0,ki=0,kd=1)
        pid.step(60,10,1)
        self.assertEqual(pid.step(100,10,1),0)

if __name__=='__main__': unittest.main()
