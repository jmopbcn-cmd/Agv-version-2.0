from pathlib import Path
import json
p=Path('src/control_motores.py')
s=p.read_text()
s=s.replace('import asyncio','import asyncio\nimport sys')
s=s.replace("MOTORES = ", "sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'raspberry'))\nfrom pid_velocidad import PID\n\nPWM_MINIMO = 25.0\nPWM_MAXIMO_MARCHA = 35.0\nRPM_MARCHA = 400.0\n\nMOTORES = ",1)
s=s.replace('        self.inicio_marcha = 0','        self.inicio_marcha = 0\n        self.reguladores = {}\n        self.ultima_muestra = None')
s=s.replace('PWM fijo de +15 o −15 % según sentido.','PWM inicial del 25 % y regulación por rueda.')
s=s.replace("            lado_izquierdo = 15.0 if sentido in ('adelante', 'derecha') else -15.0","            lado_izquierdo = PWM_MINIMO if sentido in ('adelante', 'derecha') else -PWM_MINIMO")
s=s.replace("            lado_derecho = 15.0 if sentido in ('adelante', 'izquierda') else -15.0","            lado_derecho = PWM_MINIMO if sentido in ('adelante', 'izquierda') else -PWM_MINIMO")
needle="            nuevas = {motor: lado_izquierdo"
idx=s.index(needle)
s=s[:idx]+'''            config = json.loads(Path(__file__).with_name('pi_marcha.json').read_text())
            self.reguladores = {
                motor: PID(config[motor]['kp'], config[motor]['ki'], 0,
                           limit=PWM_MAXIMO_MARCHA - PWM_MINIMO)
                for motor in MOTORES
            }
            self.ultima_muestra = None
'''+s[idx:]
needle="                        self.error = 'Marcha detenida: falta señal de la Pico o de una rueda'"
s=s.replace(needle,needle+'''
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
'''.rstrip())
compile(s,str(p),'exec')
saved=json.loads((Path.home()/'Agv-version-2.0-1/config/pid_motores.json').read_text())['motores']
Path('src/pi_marcha.json').write_text(json.dumps({n:{'kp':g['kp'],'ki':g['ki']} for n,g in saved.items()},indent=2)+'\n')
p.write_text(s)
h=Path('web/index.html')
h.write_text(h.read_text().replace('mover el AGV al 15 %.','mover el AGV con PI (25–35 % PWM, objetivo 400 RPM).'))
