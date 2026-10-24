"""PID de velocidad: logica pura, sin acceso a hardware."""
import math

class PID:
    def __init__(self, kp=0.15, ki=0.03, kd=0.0, limit=35.0):
        if not all(math.isfinite(x) and x >= 0 for x in (kp, ki, kd, limit)):
            raise ValueError('Ganancias y limite deben ser finitos y positivos')
        self.kp, self.ki, self.kd, self.limit = kp, ki, kd, limit
        self.integral = 0.0
        self.previous = None

    def step(self, target, measured, dt):
        if not all(math.isfinite(x) for x in (target, measured, dt)) or dt <= 0 or measured < 0 or target < 0:
            raise ValueError('Medida, consigna o intervalo no valido')
        if target == 0:
            self.integral, self.previous = 0.0, None
            return 0.0
        error = target - measured
        derivative = 0.0 if self.previous is None else -(measured-self.previous)/dt
        candidate = self.integral + error * dt
        raw = self.kp*error + self.ki*candidate + self.kd*derivative
        if 0 <= raw <= self.limit or (raw > self.limit and error < 0) or (raw < 0 and error > 0):
            self.integral = candidate
        self.previous = measured
        return max(0.0, min(self.limit, self.kp*error+self.ki*self.integral+self.kd*derivative))
