from pathlib import Path
p=Path('src/control_motores.py')
c=p.read_text()
old="            nuevas = dict.fromkeys(MOTORES, 15.0 if sentido == 'adelante' else -15.0)"
assert old in c
c=c.replace("('adelante', 'atras')","('adelante', 'atras', 'izquierda', 'derecha')").replace(old,'''            lado_izquierdo = 15.0 if sentido in ('adelante', 'derecha') else -15.0
            lado_derecho = 15.0 if sentido in ('adelante', 'izquierda') else -15.0
            nuevas = {motor: lado_izquierdo if motor in ('M0', 'M3') else lado_derecho
                      for motor in MOTORES}''')
h=Path('web/index.html')
s=h.read_text()
s=s.replace('    <h2>Estado del sistema</h2>', '''    <nav class="control-bar" aria-label="Pestañas del AGV">
      <button type="button" data-panel="inicio">Inicio</button>
      <button type="button" data-panel="ruedas">Motores</button>
      <button type="button" data-panel="sistema">Sistema</button>
      <button type="button" data-panel="conducir">Conducir</button>
    </nav>
    <section id="inicio" class="vista">
      <h2>Inicio</h2>
      <div class="grid">
        <div class="card">Batería <div class="value" id="inicio-bateria">--</div></div>
        <div class="card">Voltaje <div class="value" id="inicio-voltaje">--</div></div>
        <div class="card">Motores en giro <div class="value" id="inicio-motores">--</div></div>
      </div>
    </section>
    <div id="sistema" class="vista" hidden>
    <h2>Estado del sistema</h2>''')
s=s.replace('    <h2>Encoders · Velocidad de ruedas</h2>','''    </div>
    <section id="conducir" class="vista" hidden>
    <h2>Conducir</h2>''')
s=s.replace('      <button id="parar-todos"', '''      <button id="izquierda" style="touch-action:none" disabled>Izquierda</button>
      <button id="derecha" style="touch-action:none" disabled>Derecha</button>
      <button id="parar-todos"''')
s=s.replace('Mantén pulsado Adelante o Atrás para mover el AGV al 15 %.','Mantén pulsada una dirección para mover el AGV al 15 %.')
s=s.replace('    <p class="subtitle">Pruebas a potencia fija', '''    </section>
    <section id="ruedas" class="vista" hidden>
    <h2>Encoders · Velocidad de ruedas</h2>
    <button id="parar-ruedas" type="button">PARAR TODOS</button>
    <p class="subtitle">Pruebas a potencia fija''')
s=s.replace('    <footer>','    </section>\n    <footer>')
s=s.replace('    let marchaPulsada = null;', '''    let marchaPulsada = null;
    const direcciones = ["adelante", "atras", "izquierda", "derecha"];
    const pestanas = document.querySelectorAll("[data-panel]");
    function abrirPanel(id) {
      soltarMarcha();\n      for (const vista of document.querySelectorAll(".vista")) vista.hidden = vista.id !== id;\n      for (const boton of pestanas) boton.setAttribute("aria-pressed", String(boton.dataset.panel === id));
    }
    for (const boton of pestanas) boton.addEventListener("click", () => abrirPanel(boton.dataset.panel));
    abrirPanel("inicio");
    $("parar-ruedas").addEventListener("click", () => enviarOrden({tipo: "parar_motores"}));''')
s=s.replace('      $("adelante").disabled = $("atras").disabled = true;', '      for (const sentido of direcciones) $(sentido).disabled = true;\n      $("parar-ruedas").disabled = true;\n      for (const id of ["inicio-bateria", "inicio-voltaje", "inicio-motores"]) $(id).textContent = "--";')
s=s.replace('      $("parar-todos").disabled = false;', '      $("parar-todos").disabled = $("parar-ruedas").disabled = false;')
s=s.replace('of ["adelante", "atras"]','of direcciones')
s=s.replace('            actualizar(datos);','''            actualizar(datos);
            $("inicio-bateria").textContent = mostrar(datos.bateria, " %");
            $("inicio-voltaje").textContent = mostrar(datos.voltaje, " V");
            $("inicio-motores").textContent = datos.pico_conectada ?
              mostrar(Object.values(datos.encoders || {}).filter(rueda => rueda.rpm > 0).length, " / 4") : "--";''')
s=s.replace('</style>', '    nav button[aria-pressed="true"] { outline: 2px solid #38bdf8; }\n  </style>')
assert 'id="izquierda"' in s and s.count('of direcciones')>=3
compile(c,str(p),'exec')
p.write_text(c)
h.write_text(s)
