#pragma once

namespace AppRadar {
constexpr int RX_PIN = 19;
constexpr int TX_PIN = 18;
constexpr uint32_t BAUD_PRESENCE = 115200;
constexpr uint32_t BAUD_TRACKING = 256000;
constexpr uint8_t TRACKING_HEADER[] = {0xAA, 0xFF, 0x03, 0x00};
struct Target {
    int16_t x;
    int16_t y;
    int16_t speed;
    uint16_t resolution;
};
Target targets[3];
uint8_t trackingFrame[30];
size_t trackingUsed = 0;
bool tracking = true;
uint32_t scanStarted = 0;
constexpr uint16_t BG = 0x0863;
constexpr uint8_t HEADER[] = {0xF4, 0xF3, 0xF2, 0xF1};
constexpr uint8_t FOOTER[] = {0xF8, 0xF7, 0xF6, 0xF5};
constexpr size_t FRAME_SIZE = 45;

HardwareSerial port(2);
WebServer dashboard(8080);
IPAddress servedAddress;
uint16_t levels[16];
bool hasLevels = false;

const char PAGE[] PROGMEM = R"radar(<!doctype html>
<html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Radar de presencia</title>
<style>
:root{color-scheme:dark;font:16px system-ui;background:#111820;color:#edf5fa}body{max-width:770px;margin:48px auto;padding:0 20px}
h1{margin:0 0 26px;font-size:clamp(1.8rem,5vw,2.6rem)}h2{font-size:1rem;margin:0 0 14px;color:#aabac8}
section{border:1px solid #304251;border-radius:12px;background:#18232d;padding:20px;margin:14px 0}
strong{display:block;font-size:1.25rem}output{display:block;font-weight:700;font-size:3rem;margin:8px 0;color:#72ebbe}
canvas{width:100%;height:180px;display:block}#map{height:clamp(240px,53vw,440px)}#targets{padding-left:20px}#tracking[hidden],#history[hidden]{display:none}#gates{display:flex;align-items:end;height:88px;gap:4px;margin-bottom:8px}
#bars[hidden]{display:none}i{flex:1;border-radius:3px 3px 0 0;background:#72ebbe}small{color:#aabac8}
</style>
<main><h1 id="heading">Radar de presencia</h1><section aria-live="polite"><strong id="state">Conectando</strong><output id="distance">—</output></section>
<section id="history"><h2>Distancia durante el último minuto</h2><canvas id="plot" aria-label="Historial de distancia"></canvas></section>
<section id="tracking" hidden><h2>Posición de los objetivos · vista desde arriba</h2><canvas id="map" aria-label="Mapa XY en metros"></canvas><ul id="targets"></ul></section><section id="bars" hidden><h2>Intensidad por tramo</h2><div id="gates"></div><small>Tramos 0 a 15, desde el más cercano</small></section></main>
<script>
const state=document.querySelector('#state'), distance=document.querySelector('#distance');
const canvas=document.querySelector('#plot'), context=canvas.getContext('2d');
const bars=document.querySelector('#bars'), gates=document.querySelector('#gates');
const points=[];
const heading=document.querySelector('#heading'), historyPanel=document.querySelector('#history');
const trackingPanel=document.querySelector('#tracking'), map=document.querySelector('#map');
const targetList=document.querySelector('#targets');
const colors=['#72ebbe','#77bbff','#fdc968'];
function drawMap(targets){
  const w=map.width=map.clientWidth,h=map.height=map.clientHeight,c=map.getContext('2d');
  const scale=Math.min((w-50)/12,(h-40)/6), ox=w/2, oy=h-24;
  c.font='12px system-ui';c.strokeStyle='#304251';c.fillStyle='#aabac8';
  c.beginPath();c.moveTo(ox,oy);c.lineTo(ox,oy-6*scale);c.stroke();
  for(let m=1;m<=6;m++){
    c.beginPath();c.arc(ox,oy,m*scale,-Math.PI*5/6,-Math.PI/6);c.stroke();
    c.fillText(m+' m',ox+5,oy-m*scale+12);
  }
  c.fillText('Sensor',ox-19,h-5);c.fillText('Izquierda',12,h-5);c.fillText('Derecha',w-57,h-5);
  for(const t of targets){
    const x=ox+t.xMm*scale/1000,y=oy-t.yMm*scale/1000;
    c.fillStyle=colors[t.id-1];c.beginPath();c.arc(x,y,6,0,Math.PI*2);c.fill();
    c.fillText(String(t.id),x+9,y+4);
  }
  targetList.replaceChildren(...targets.map(t=>{
    const item=document.createElement('li');
    item.style.color=colors[t.id-1];
    item.textContent='Objetivo '+t.id+' · X '+(t.xMm/1000).toFixed(2)+' m · Y '+(t.yMm/1000).toFixed(2)+' m · '+t.speedCmS+' cm/s';
    return item;
  }));
}
function graph(now){
  while(points.length && points[0][0]<now-60000) points.shift();
  const width=canvas.width=canvas.clientWidth, height=canvas.height=canvas.clientHeight;
  const high=Math.max(100,Math.ceil(Math.max(0,...points.map(p=>p[1]||0))/100)*100);
  const left=58, bottom=height-24;
  context.font='12px system-ui';
  for(let i=0;i<=4;i++){
    const y=10+(bottom-10)*i/4;
    context.fillStyle='#aabac8';context.fillText(Math.round(high*(1-i/4))+' cm',0,y+4);
    context.beginPath();context.moveTo(left,y);context.lineTo(width,y);context.strokeStyle='#304251';context.stroke();
  }
  context.fillText('−60 s',left,bottom+20);context.fillText('ahora',width-38,bottom+20);
  context.strokeStyle='#72ebbe';context.lineWidth=2;context.beginPath();
  let joined=false;
  for(const [at,value] of points){
    if(value===null){joined=false;continue;}
    const x=left+(1-(now-at)/60000)*(width-left), y=bottom-(bottom-10)*value/high;
    if(joined)context.lineTo(x,y);else context.moveTo(x,y);
    joined=true;
  }
  context.stroke();
}
async function update(){
  let value=null;
  try {
    const response=await fetch('/api/radar',{cache:'no-store',signal:AbortSignal.timeout(3000)});
    if(!response.ok)throw new Error('HTTP '+response.status);
    const data=await response.json();
    const xy=data.model==='LD2450';
    heading.textContent=data.online?'Radar '+data.model:'Radar de presencia';
    trackingPanel.hidden=!xy;historyPanel.hidden=xy;
    if(xy)drawMap(data.targets||[]);
    state.textContent=!data.online?'Sin datos del radar':data.presence?'Presencia detectada':'Sin presencia';
    value=data.online&&data.presence?data.distanceCm:null;
    bars.hidden=!data.energy;
    if(data.energy){
      const peak=Math.max(1,...data.energy);
      gates.replaceChildren(...data.energy.map((level,index)=>{
        const bar=document.createElement('i');bar.style.height=Math.max(1,level/peak*100)+'%';
        bar.title='Tramo '+index+': '+level;return bar;
      }));
    }
  } catch {
    state.textContent='Pantalla sin conexión';bars.hidden=true;
  }
  distance.textContent=value===null?'—':value+' cm';
  const now=Date.now();points.push([now,value]);if(!historyPanel.hidden)graph(now);
  else while(points.length && points[0][0]<now-60000) points.shift();
  setTimeout(update,500);
}
update();
</script></html>)radar";
uint8_t frame[FRAME_SIZE];
size_t used = 0;
char line[48];
size_t lineUsed = 0;
bool occupied = false;
int distanceCm = -1;
uint32_t lastData = 0;
uint32_t lastDraw = 0;

bool fresh() {
    return lastData && millis() - lastData <= 2000;
}

void draw() {
    tft.fillRect(0, 42, 320, 198, BG);
    text(12, 220, WiFi.status() == WL_CONNECTED ?
        "PC: http://" + WiFi.localIP().toString() + ":8080" : "PC: conecta la pantalla a la Wi-Fi");
    if (!fresh()) {
        text(20, 76, "SIN DATOS", 3);
        text(20, 130, "Buscando LD2420 o LD2450");
        text(20, 151, "Entrada de datos: IO19");
        return;
    }
    if (tracking) {
        text(12, 54, "LD2450", 2);
        text(12, 87, occupied ? "PRESENCIA" : "SIN PRESENCIA", 1);
        if (occupied && distanceCm >= 0) text(12, 110, String(distanceCm) + " cm", 2);
        constexpr int ox = 227, oy = 198, pxPerMeter = 21;
        for (int r = pxPerMeter; r <= pxPerMeter * 3; r += pxPerMeter) {
            tft.drawCircle(ox, oy - 63, r, 0x39C7);
        }
        tft.drawFastVLine(ox, oy - 126, 126, 0x39C7);
        tft.fillCircle(ox, oy, 3, 0xFFFF);
        const uint16_t colors[] = {0x77D9, 0x7DFF, 0xFE4D};
        for (size_t i = 0; i < 3; ++i) {
            const Target &t = targets[i];
            if (!t.resolution) continue;
            const int x = ox + t.x * pxPerMeter / 1000;
            const int y = oy - t.y * pxPerMeter / 1000;
            if (x >= 110 && x < 315 && y >= 52 && y <= oy) tft.fillCircle(x, y, 5, colors[i]);
        }
        return;
    }
    text(20, 68, occupied ? "PRESENCIA" : "SIN PRESENCIA", 3);
    if (occupied && distanceCm >= 0) {
        text(20, 128, String(distanceCm) + " cm", 4);
    }
}

void enter() {
    lastDraw = millis();
    tft.fillScreen(BG);
    text(12, 12, "RADAR", 2);
    draw();
}

void publishStatus() {
    const bool online = fresh();
    JsonDocument data;
    data["online"] = online;
    data["model"] = tracking ? "LD2450" : "LD2420";
    if (tracking) {
        auto list = data["targets"].to<JsonArray>();
        if (online) {
            for (size_t i = 0; i < 3; ++i) {
                const Target &t = targets[i];
                if (!t.resolution) continue;
                auto target = list.add<JsonObject>();
                target["id"] = i + 1;
                target["xMm"] = t.x;
                target["yMm"] = t.y;
                target["speedCmS"] = t.speed;
            }
        }
    }
    data["presence"] = online && occupied;
    if (online && occupied && distanceCm >= 0) data["distanceCm"] = distanceCm;
    else data["distanceCm"] = nullptr;
    if (online && hasLevels) {
        auto energy = data["energy"].to<JsonArray>();
        for (uint16_t level : levels) energy.add(level);
    }
    String body;
    serializeJson(data, body);
    dashboard.sendHeader("Cache-Control", "no-store");
    dashboard.send(200, "application/json", body);
}

void begin() {
    port.begin(BAUD_TRACKING, SERIAL_8N1, RX_PIN, TX_PIN);
    scanStarted = millis();
    dashboard.on("/", HTTP_GET, [] {
        dashboard.send_P(200, "text/html; charset=utf-8", PAGE);
    });
    dashboard.on("/api/radar", HTTP_GET, publishStatus);
}

void readText(uint8_t byte) {
    if (byte == '\r' || byte == '\n') {
        line[lineUsed] = 0;
        const bool active = strcmp(line, "ON") == 0 || strncmp(line, "ON ", 3) == 0;
        const bool inactive = strcmp(line, "OFF") == 0 || strncmp(line, "OFF ", 4) == 0;
        if (active || inactive) {
            hasLevels = false;
            occupied = active;
            if (inactive) distanceCm = -1;
            lastData = millis();
        }
        const char* range = strstr(line, "Range ");
        if (range) {
            char* end;
            const char* number = range + 6;
            long cm = strtol(number, &end, 10);
            if (end != number && *end == 0 && cm >= 0 && cm <= 2000) {
                distanceCm = cm;
                lastData = millis();
            }
        }
        lineUsed = 0;
    } else if (byte >= 32 && byte <= 126 && lineUsed < sizeof(line) - 1) {
        line[lineUsed++] = byte;
    } else {
        lineUsed = 0;
    }
}

void readByte(uint8_t byte) {
    if (used < sizeof(HEADER) && byte != HEADER[used]) {
        used = 0;
        if (byte != HEADER[0]) {
            readText(byte);
            return;
        }
    }
    frame[used++] = byte;
    if (used != FRAME_SIZE) return;
    used = 0;
    lineUsed = 0;
    if (frame[4] != 35 || frame[5] != 0 || frame[6] > 1 ||
        memcmp(frame + FRAME_SIZE - sizeof(FOOTER), FOOTER, sizeof(FOOTER))) return;
    for (size_t i = 0; i < 16; ++i) {
        levels[i] = frame[9 + i * 2] | (frame[10 + i * 2] << 8);
    }
    hasLevels = true;
    occupied = frame[6] != 0;
    distanceCm = occupied ? (frame[7] | (frame[8] << 8)) : -1;
    lastData = millis();
}

uint16_t littleEndian(const uint8_t* data) {
    return data[0] | (static_cast<uint16_t>(data[1]) << 8);
}

int16_t trackingNumber(const uint8_t* data) {
    const uint16_t raw = littleEndian(data);
    const int16_t magnitude = raw & 0x7FFF;
    return raw & 0x8000 ? magnitude : -magnitude;
}

void readTracking(uint8_t byte) {
    if (trackingUsed < sizeof(TRACKING_HEADER) && byte != TRACKING_HEADER[trackingUsed]) {
        trackingUsed = 0;
        if (byte != TRACKING_HEADER[0]) return;
    }
    trackingFrame[trackingUsed++] = byte;
    if (trackingUsed != sizeof(trackingFrame)) return;
    trackingUsed = 0;
    if (trackingFrame[28] != 0x55 || trackingFrame[29] != 0xCC) return;

    occupied = false;
    distanceCm = -1;
    for (size_t i = 0; i < 3; ++i) {
        const uint8_t* slot = trackingFrame + 4 + i * 8;
        Target &t = targets[i];
        t = {trackingNumber(slot), trackingNumber(slot + 2),
             trackingNumber(slot + 4), littleEndian(slot + 6)};
        if (!t.resolution) continue;
        occupied = true;
        const int cm = lroundf(hypotf(t.x, t.y) / 10);
        if (distanceCm < 0 || cm < distanceCm) distanceCm = cm;
    }
    lastData = millis();
}

void loop(bool visible) {
    for (int i = 0; i < 256 && port.available(); ++i) {
        const int byte = port.read();
        if (byte < 0) break;
        if (tracking) readTracking(byte);
        else readByte(byte);
    }
    if (!fresh() && millis() - scanStarted > 2200) {
        tracking = !tracking;
        port.updateBaudRate(tracking ? BAUD_TRACKING : BAUD_PRESENCE);
        while (port.available()) port.read();
        used = lineUsed = trackingUsed = 0;
        lastData = 0;
        occupied = hasLevels = false;
        distanceCm = -1;
        scanStarted = millis();
    }
    const IPAddress address = WiFi.status() == WL_CONNECTED ? WiFi.localIP() : IPAddress();
    if (address != servedAddress) {
        if (servedAddress != IPAddress()) dashboard.stop();
        servedAddress = address;
        if (address != IPAddress()) {
            dashboard.begin();
            Serial.println("RADAR_WEB http://" + address.toString() + ":8080");
        }
    }
    if (servedAddress != IPAddress()) dashboard.handleClient();
    if (visible && millis() - lastDraw >= 250) {
        lastDraw = millis();
        draw();
    }
}
}
