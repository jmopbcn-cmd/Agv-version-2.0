from pathlib import Path
import tempfile
import os

def change(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)

paths = [Path(p) for p in ('src/control_motores.py','src/motores_worker.py','src/servidor_ws.py','web/index.html')]
c,w,s,h = [p.read_text() for p in paths]
w = change(w,'not 0 <= x <= 75','not -75 <= x <= 75')
w = change(w,'intervalo 0-75 %','intervalo -75 a 75 %')
c = change(c,'        self.mutex = asyncio.Lock()','        self.mutex = asyncio.Lock()\n        self.marcha = None\n        self.inicio_marcha = 0')
c = change(c,"'error': self.error, 'limite': MAX_POTENCIA","'error': self.error, 'limite': MAX_POTENCIA, 'marcha': self.marcha")
c = change(c,'            nuevas = dict(self.potencias)','            if self.marcha:\n                raise ValueError("Suelta el botón de marcha primero")\n            nuevas = dict(self.potencias)')
c = change(c,'    def renovar(self, cliente):', '''    async def conducir(self, cliente, sentido):
        if sentido not in ('adelante', 'atras'):
            raise ValueError('Sentido no válido')
        async with self.mutex:
            if self.propietario is not None:
                raise ValueError('Para los motores antes de iniciar otra marcha')
            nuevas = dict.fromkeys(MOTORES, 15.0 if sentido == 'adelante' else -15.0)
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

    def renovar(self, cliente):''')
c = c.replace('        self.propietario = None\n\n    async def ordenar','        self.propietario = None\n        self.marcha = None\n\n    async def ordenar')
c = change(c,'            self.propietario = None\n\n    async def vigilar(self):','            self.propietario = None\n            self.marcha = None\n\n    async def vigilar(self, telemetria=None):')
c = change(c,'                nuevas = self.potencias if self.ahora() - self.ultima_renovacion < CADUCIDAD else dict.fromkeys(MOTORES, 0.0)', '''                ahora = self.ahora()
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
'''.rstrip())
c = change(c,'                    if not any(nuevas.values()):\n                        self.propietario = None','                    if not any(nuevas.values()):\n                        self.propietario = None\n                        self.marcha = None')
s = change(s,"                elif tipo == 'renovar_motores':",'''                elif tipo == 'marcha':
                    datos = obtener_datos()
                    if not datos['fusion_hat'] or not datos['pico_conectada']:
                        raise ValueError('Se necesita telemetría de la Fusion HAT y la Pico')
                    await control_motores.conducir(websocket, orden.get('sentido'))
                elif tipo == 'soltar_marcha':
                    await control_motores.parar(websocket)
                elif tipo == 'renovar_motores':''')
s = change(s,'control_motores.vigilar()','control_motores.vigilar(obtener_datos)')
h = change(h,'      <button id="parar-todos"', '''      <button id="adelante" style="touch-action:none" disabled>Adelante</button>
      <button id="atras" style="touch-action:none" disabled>Atrás</button>
      <button id="parar-todos"''')
h = change(h,'    let ultimoEstado = null;','    let ultimoEstado = null;\n    let marchaPulsada = null;')
h = change(h,'      controlPropio = false;','      controlPropio = false;\n      marchaPulsada = null;\n      $("adelante").disabled = $("atras").disabled = true;')
h = change(h,'      $("parar-todos").disabled = false;','''      $("parar-todos").disabled = false;
      const parada = !estado.propio && !estado.ocupado;
      for (const sentido of ["adelante", "atras"]) {
        $(sentido).disabled = !parada && marchaPulsada !== sentido;
      }''')
h = h.replace('estado.potencias[motor] || 0','Math.abs(estado.potencias[motor] || 0)').replace('.disabled = estado.ocupado;', '.disabled = estado.ocupado || Boolean(estado.marcha);')
h = h.replace('estado.propio ? "Control manual activo','estado.marcha ? "Marcha activa · Suelta para parar." : estado.propio ? "Control manual activo')
h = change(h,'    $("parar-todos").addEventListener("click", () => enviarOrden({tipo: "parar_motores"}));','''    function soltarMarcha() {
      if (!marchaPulsada) return;
      marchaPulsada = null;
      enviarOrden({tipo: "soltar_marcha"});
    }
    for (const sentido of ["adelante", "atras"]) {
      const boton = $(sentido);
      function iniciar(evento) {
        evento.preventDefault();
        if (marchaPulsada || boton.disabled || ultimoEstado?.propio || ultimoEstado?.ocupado) return;
        if (evento.type === "pointerdown") boton.setPointerCapture(evento.pointerId);
        if (enviarOrden({tipo: "marcha", sentido})) marchaPulsada = sentido;
      }
      boton.addEventListener("pointerdown", evento => { if (evento.button === 0) iniciar(evento); });
      for (const tipo of ["pointerup", "pointercancel", "lostpointercapture", "blur"]) {
        boton.addEventListener(tipo, () => { if (marchaPulsada === sentido) soltarMarcha(); });
      }
      boton.addEventListener("keydown", evento => {
        if ([" ", "Enter"].includes(evento.key) && !evento.repeat) iniciar(evento);
      });
      boton.addEventListener("keyup", evento => {
        if ([" ", "Enter"].includes(evento.key) && marchaPulsada === sentido) soltarMarcha();
      });
      boton.addEventListener("contextmenu", evento => evento.preventDefault());
    }
    window.addEventListener("blur", soltarMarcha);
    $("parar-todos").addEventListener("click", () => {
      marchaPulsada = null;
      enviarOrden({tipo: "parar_motores"});
    });''')
h = change(h,'      if (controlPropio) enviarOrden','      soltarMarcha();\n      if (controlPropio) enviarOrden')
h = change(h,'if (controlPropio && !document.hidden) enviarOrden','if (controlPropio && (!ultimoEstado?.marcha || marchaPulsada) && !document.hidden) enviarOrden')
h = change(h,'Conecta para usar el control manual.','Mantén pulsado Adelante o Atrás para mover el AGV al 15 %.')
h = change(h,'if (datos.tipo === "error_control") $("control-aviso").textContent = datos.error;','if (datos.tipo === "error_control") {\n              marchaPulsada = null;\n              $("control-aviso").textContent = datos.error;\n            }')
for p,text in zip(paths,[c,w,s,h]):
    if p.suffix == '.py':
        compile(text, str(p), 'exec')
    with tempfile.NamedTemporaryFile(dir=p.parent, delete=False) as f:
        f.write(text.encode())
    os.chmod(f.name, p.stat().st_mode & 0o777)
    os.replace(f.name,p)
