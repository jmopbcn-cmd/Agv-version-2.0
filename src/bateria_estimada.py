"""Porcentaje visual por tension: estable bajo carga, sin estimar amperios."""
import math
from collections import deque
from statistics import median

class EstimadorBateria:
    def __init__(self):
        self.valor = None
        self.ultima_muestra = None
        self.ultimo_movimiento = None
        self.reposo = deque()

    def actualizar(self, porcentaje, estado, motores_activos, ahora):
        if (isinstance(porcentaje, bool) or not isinstance(porcentaje, (int, float))
                or not math.isfinite(porcentaje) or not 0 <= porcentaje <= 100):
            return None
        if self.valor is None:
            self.valor = float(porcentaje)
            self.ultima_muestra = ahora
        if motores_activos:
            self.ultimo_movimiento = ahora
            self.reposo.clear()
        dt = max(0.0, ahora - self.ultima_muestra)
        if dt < 1.0:
            return round(self.valor)
        self.ultima_muestra = ahora
        if motores_activos or (self.ultimo_movimiento is not None and ahora - self.ultimo_movimiento < 20):
            return round(self.valor)
        self.reposo.append((ahora, float(porcentaje)))
        while self.reposo and ahora - self.reposo[0][0] > 15:
            self.reposo.popleft()
        if len(self.reposo) < 5:
            return round(self.valor)
        objetivo = median(x[1] for x in self.reposo)
        if estado not in ('Charging', 'Full'):
            objetivo = min(objetivo, self.valor)
        paso = (objetivo - self.valor) * (1 - math.exp(-min(dt, 5.0) / 45.0))
        limite = min(dt, 5.0) / 15.0
        self.valor = max(0.0, min(100.0, self.valor + max(-limite, min(limite, paso))))
        return round(self.valor)
