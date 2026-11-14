#pragma once
namespace AppMinrray {
const char* zoom_in = "81 01 04 07 27 FF";
const char* zoom_out = "81 01 04 07 37 FF";
const char* zoom_stop = "81 01 04 07 00 FF";
const char* home = "81 01 06 04 FF";
const char* focus_auto = "81 01 04 38 02 FF";
const char* focus_manual = "81 01 04 38 03 FF";
const char* focus_near = "81 01 04 08 03 FF";
const char* focus_far = "81 01 04 08 02 FF";
const char* focus_stop = "81 01 04 08 00 FF";
const char* exposure_auto = "81 01 04 39 00 FF";
const char* bright_mode = "81 01 04 39 0D FF";
const char* bright_up = "81 01 04 0D 02 FF";
const char* bright_down = "81 01 04 0D 03 FF";
const char* ev_mode = "81 01 04 3E 02 FF";
const char* ev_up = "81 01 04 0E 02 FF";
const char* ev_down = "81 01 04 0E 03 FF";
const char* wb_auto = "81 01 04 35 00 FF";
const char* wb_3000 = "81 01 04 35 01 FF";
const char* wb_4000 = "81 01 04 35 02 FF";
const char* wb_one_push = "81 01 04 35 03 FF";
const char* wb_5000 = "81 01 04 35 04 FF";
const char* wb_6500 = "81 01 04 35 06 FF";
const char* blc_on = "81 01 04 33 02 FF";
const char* blc_off = "81 01 04 33 03 FF";
const char* menu_open = "81 01 04 06 06 02 FF";
const char* menu_close = "81 01 04 06 06 03 FF";
int page=0, preset=1, speedPTZ=8;
int lastPan=3,lastTilt=3,lastSpeed=0;
unsigned long sampleAt=0, statusAt=0;
int cx=2048,cy=2048;
bool armed=false, connectedBefore=false, stopPending=true, touchWas=false;
int held=-1;
bool swWas=false;
const uint16_t BG=0x0863, PANEL=0x2188, WHITE=0xFFFF;
// No cola: una orden antigua de movimiento nunca se ejecuta tras recuperar Wi-Fi.
bool sendHex(const char* hex) {
 if(WiFi.status()!=WL_CONNECTED) return false;
 WiFiClient client; client.setTimeout(100);
 if(!client.connect(cameraHost.c_str(),cameraPort,100)) return false;
 uint8_t bytes[32]; size_t n=0; const char* p=hex;
 while(*p && n<sizeof(bytes)){while(*p==' ')++p;if(!*p)break;char* end;bytes[n++]=strtoul(p,&end,16);if(end==p)return false;p=end;}
 bool ok=client.write(bytes,n)==n; client.stop(); return ok;
}
void stopAll(){
 bool a=sendHex("81 01 06 01 08 08 03 03 FF");
 bool b=sendHex(zoom_stop),c=sendHex(focus_stop);
 stopPending=!(a&&b&&c);lastPan=lastTilt=3;lastSpeed=0;armed=false;
}
void movePTZ(int pan,int tilt,int speed){
 if(stopPending)return;
 if(pan==lastPan && tilt==lastTilt && speed==lastSpeed)return;
 char b[80];snprintf(b,sizeof(b),"81 01 06 01 %02X %02X %02X %02X FF",speed,speed,pan,tilt);
 if(sendHex(b)){lastPan=pan;lastTilt=tilt;lastSpeed=speed;}else{stopPending=true;armed=false;}
}
void label(int x,int y,const char* s,int size=1){tft.setCursor(x,y);tft.setTextColor(WHITE);tft.setTextSize(size);tft.print(s);}
void btn(int i,const char* s){int x=(i%3)*106+3,y=42+(i/3)*43;tft.fillRoundRect(x,y,102,38,4,PANEL);label(x+5,y+14,s);}
const char* titles[]={"MOVIMIENTO","IMAGEN","FOCO / OSD","PRESETS"};
const char* names[4][9]={
 {"ARRIBA","STOP","CENTRO","IZQUIERDA","ABAJO","DERECHA","ZOOM -","ZOOM +","VELOCIDAD"},
 {"EXP AUTO","BRILLO +","BRILLO -","EV +","EV -","WB AUTO","WB 3000","WB 5000","BLC ON/OFF"},
 {"FOCO CERCA","FOCO LEJOS","FOCO AUTO","ABRIR OSD","CERRAR OSD","OSD ARRIBA","OSD IZQ","OSD ABAJO","OSD DER"},
 {"PRESET -","PRESET +","IR PRESET","GUARDAR*","CONFIRMAR","CANCELAR","1","2","3"}};
bool confirmSave=false,blc=false;
void draw(){tft.fillScreen(BG);label(5,5,"MINRRAY",2);label(5,27,titles[page]);for(int i=0;i<9;i++)btn(i,names[page][i]);for(int i=0;i<4;i++){tft.fillRect(i*80,202,78,36,i==page?0x137F:PANEL);const char* tabs[]={"MOVER","IMAGEN","FOCO/OSD","PRESETS"};label(i*80+5,215,tabs[i]);}char b[50];snprintf(b,sizeof(b),"P:%d V:%d %s",preset,speedPTZ,confirmSave?"CONFIRMAR GUARDADO":"");label(5,178,b);}
void presetCommand(bool save){char b[50];snprintf(b,sizeof(b),"81 01 04 3F %02X %02X FF",save?1:2,preset);sendHex(b);}
void action(int i){
 if(stopPending)return;
 if(page==0){
 if(i==0)movePTZ(3,1,speedPTZ);if(i==1)stopAll();if(i==2)sendHex(home);
 if(i==3)movePTZ(1,3,speedPTZ);if(i==4)movePTZ(3,2,speedPTZ);if(i==5)movePTZ(2,3,speedPTZ);
 if(i==6)sendHex(zoom_out);if(i==7)sendHex(zoom_in);if(i==8){speedPTZ=speedPTZ%20+1;draw();}
 }else if(page==1){
 const char* commands[]={exposure_auto,bright_up,bright_down,ev_up,ev_down,wb_auto,wb_3000,wb_5000,blc_on};
 if(i==1||i==2)sendHex(bright_mode);if(i==3||i==4)sendHex(ev_mode);
 if(i==8){blc=!blc;sendHex(blc?blc_on:blc_off);}else sendHex(commands[i]);
 }else if(page==2){
 if(i<2){sendHex(focus_manual);sendHex(i==0?focus_near:focus_far);}if(i==2)sendHex(focus_auto);
 if(i==3)sendHex(menu_open);if(i==4)sendHex(menu_close);
 if(i==5)movePTZ(3,1,4);if(i==6)movePTZ(1,3,4);if(i==7)movePTZ(3,2,4);if(i==8)movePTZ(2,3,4);
 }else{
 if(i==0){preset=preset==1?255:preset-1;confirmSave=false;}if(i==1){preset=preset%255+1;confirmSave=false;}
 if(i==2)presetCommand(false);if(i==3)confirmSave=true;
 if(i==4&&confirmSave){presetCommand(true);confirmSave=false;}if(i==5)confirmSave=false;
 if(i>=6){preset=i-5;presetCommand(false);confirmSave=false;}draw();
 }
}
void enter(){
 lastPan=lastTilt=3;lastSpeed=0;stopPending=true;armed=false;touchWas=false;swWas=false;page=0;
 if(JOY_ENABLED){pinMode(JOY_SW,INPUT_PULLUP);analogReadResolution(12);long sx=0,sy=0;for(int i=0;i<32;i++){sx+=analogRead(JOY_X);sy+=analogRead(JOY_Y);delay(5);}cx=sx/32;cy=sy/32;}
 draw();
}
void loop(){
 bool online=WiFi.status()==WL_CONNECTED;
 if(!online){stopPending=true;armed=false;}
 if(online&&!connectedBefore){stopPending=true;held=-1;}
 connectedBefore=online;
 if(millis()-statusAt>1000){statusAt=millis();if(online&&stopPending)stopAll();tft.fillRect(100,0,155,25,BG);label(100,5,!online?"SIN WIFI":stopPending?"SIN CAMARA / STOP":"RED OK",1);}
 if(millis()-sampleAt<40)return;sampleAt=millis();
 bool pressed=touch.touched();
 if(swWas && pressed){touchWas=true;return;}
 if(pressed){TS_Point p=touch.getPoint();int x=constrain(map(p.x,3551,346,16,303),0,319),y=constrain(map(p.y,3646,440,12,227),0,239);
 if(!touchWas){stopAll();if(y>=202){page=min(3,x/80);confirmSave=false;draw();held=-1;}else if(y>=42&&y<171){held=((y-42)/43)*3+min(2,x/106);action(held);}}
 }else if(touchWas){stopAll();held=-1;}
 touchWas=pressed;
 if(JOY_ENABLED){
 int dx=(analogRead(JOY_X)-cx)*(JOY_INVERT_X?-1:1),dy=(analogRead(JOY_Y)-cy)*(JOY_INVERT_Y?-1:1);
 bool centered=abs(dx)<450&&abs(dy)<450;
 bool sw=digitalRead(JOY_SW)==LOW;
 if(sw){if(!swWas)stopAll();swWas=true;armed=false;return;}
 swWas=false;
 if(pressed||stopPending){armed=false;return;}
 if(centered){if(lastPan!=3||lastTilt!=3)movePTZ(3,3,8);armed=true;}
 else if(armed){int pan=abs(dx)<450?3:dx<0?1:2,tilt=abs(dy)<450?3:dy<0?1:2;int speed=constrain(map(max(abs(dx),abs(dy)),450,2000,2,20),2,20);movePTZ(pan,tilt,speed);}
 }
 delay(2);
}

}
