"""Diagnostico sin control de motores. Ejecutar con .venv/bin/python."""
import asyncio
import json
import subprocess
import urllib.request
from pathlib import Path
from websockets.asyncio.client import connect

async def main():
    print('Arranque del sistema:', subprocess.check_output(['uptime', '-s'], text=True).strip())
    for unit in ('agb-websocket.service', 'agb-web.service'):
        for action in ('is-enabled', 'is-active'):
            r = subprocess.run(['systemctl', action, unit], capture_output=True, text=True)
            print(unit, action, r.stdout.strip())
            if r.returncode:
                raise RuntimeError(unit + ': ' + action + ' no correcto')
    with urllib.request.urlopen('http://127.0.0.1:8080/', timeout=5) as response:
        actual = response.read()
    expected = (Path(__file__).resolve().parents[1] / 'web/index.html').read_bytes()
    if actual != expected:
        raise RuntimeError('El HTTP no sirve el panel esperado')
    print('Panel HTTP: coincide con web/index.html')
    async with connect('ws://127.0.0.1:8765/', open_timeout=5) as ws:
        for _ in range(2):
            data = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
            if not data.get('pico_conectada'):
                raise RuntimeError('Pico sin telemetria reciente')
            channels = data.get('encoders', {})
            for name in ('M0', 'M1', 'M2', 'M3'):
                if not isinstance(channels.get(name, {}).get('rpm'), (int, float)):
                    raise RuntimeError('Falta lectura RPM: ' + name)
            print('Telemetria:', {name: channels[name]['rpm'] for name in channels})
    print('OK: servicios, panel y cuatro canales disponibles. Pantalla fisica: verificar visualmente.')

if __name__ == '__main__':
    asyncio.run(main())
