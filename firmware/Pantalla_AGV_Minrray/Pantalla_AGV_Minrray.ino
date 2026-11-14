#include <SPI.h>
#include <WiFi.h>
#include <WebServer.h>
#include <Preferences.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <XPT2046_Touchscreen.h>
#include "JoystickConfig.h"
#define TFT_CS    15
#define TFT_DC     2
#define TFT_MOSI  13
#define TFT_MISO  12
#define TFT_SCLK  14
#define TFT_BL    21

// Pines tactiles confirmados
#define TOUCH_CS    33
#define TOUCH_IRQ   36
#define TOUCH_SCLK  25
#define TOUCH_MOSI  32
#define TOUCH_MISO  39

// Hardware
Adafruit_ST7789 tft(&SPI, TFT_CS, TFT_DC, -1);
SPIClass touchSPI(HSPI);
XPT2046_Touchscreen touch(TOUCH_CS, TOUCH_IRQ);


String cameraHost="192.168.1.163",rpiHost="192.168.1.11";
uint16_t cameraPort=1259,rpiPort=8765;
Preferences prefs;
WebServer server(80);
String wifiName,wifiKey,setupKey;
bool portal=false,awaitRelease=false,previousTouch=false,applyNetwork=false;
unsigned long homeAt=0;
enum App {HOME,AGV,MINRRAY,SETTINGS};
App app=HOME;
#include "AppAGV.h"
#include "AppMinrray.h"
void text(int x,int y,const String& s,int size=1){tft.setCursor(x,y);tft.setTextColor(0xFFFF);tft.setTextSize(size);tft.setTextWrap(false);tft.print(s);}
void homeButton(){tft.fillRoundRect(260,2,58,29,4,0x2188);text(267,12,"INICIO");}
void home(){
 app=HOME;tft.fillScreen(0x0863);text(25,16,"ELIGE UNA APP",2);
 tft.fillRoundRect(15,56,140,103,10,0x137F);text(47,90,"AGV",3);text(28,136,"Panel del vehiculo");
 tft.fillRoundRect(165,56,140,103,10,0x2188);text(181,90,"MINRRAY",2);text(185,136,"Mando de camara");
 tft.fillRoundRect(15,175,290,34,6,0x2188);text(96,187,"CONFIGURACION");
 homeAt=0;
}
String escapeHTML(String s){s.replace("&","&amp;");s.replace("<","&lt;");s.replace(">","&gt;");s.replace(String(char(34)),"&quot;");s.replace("'","&#39;");return s;}
void settings(){
 app=SETTINGS;portal=true;WiFi.mode(WIFI_AP_STA);
 uint32_t key=esp_random();setupKey=String(key,HEX);while(setupKey.length()<8)setupKey="0"+setupKey;
 WiFi.softAP("Panel-AGV-Minrray",setupKey.c_str());
 server.on("/",HTTP_GET,[]{
 String html="<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>AGV y Minrray</title><style>body{font:18px sans-serif;max-width:500px;margin:24px;background:#101c2b;color:white}input,button{box-sizing:border-box;width:100%;padding:12px;margin:8px 0}button{background:#6aa9e9}</style><h1>AGV y Minrray</h1><form method='post' action='/guardar'>Wi-Fi (2,4 GHz)<input name='ssid' maxlength='32' required value='"+escapeHTML(wifiName)+"'>Clave Wi-Fi<input name='password' type='password' maxlength='63' placeholder='Vacio: conservar clave guardada'>IP camara<input name='camera' required value='"+escapeHTML(cameraHost)+"'>Puerto VISCA TCP<input name='cport' type='number' min='1' max='65535' value='"+String(cameraPort)+"'>IP Raspberry<input name='rpi' required value='"+escapeHTML(rpiHost)+"'>Puerto AGV<input name='rport' type='number' min='1' max='65535' value='"+String(rpiPort)+"'><button>Guardar</button></form>";
 server.sendHeader("Cache-Control","no-store");server.send(200,"text/html; charset=utf-8",html);
 });
 server.on("/guardar",HTTP_POST,[]{
 IPAddress a,b;long cp=server.arg("cport").toInt(),rp=server.arg("rport").toInt();String ssid=server.arg("ssid"),password=server.arg("password");
 if(ssid.isEmpty()||ssid.length()>32||password.length()>63||!a.fromString(server.arg("camera"))||!b.fromString(server.arg("rpi"))||cp<1||cp>65535||rp<1||rp>65535){server.send(400,"text/plain","Revisa Wi-Fi, direcciones IP y puertos.");return;}
 if(!password.isEmpty()&&password.length()<8){server.send(400,"text/plain","La clave Wi-Fi debe tener al menos 8 caracteres.");return;}
 if(ssid!=wifiName&&password.isEmpty()){server.send(400,"text/plain","Introduce la clave de la nueva red.");return;}
 wifiName=ssid;if(!password.isEmpty())wifiKey=password;
 cameraHost=a.toString();rpiHost=b.toString();cameraPort=cp;rpiPort=rp;
 bool ok=prefs.putString("ssid",wifiName)>0;ok=(prefs.putString("key",wifiKey)>0)&&ok;
 ok=(prefs.putString("camera",cameraHost)>0)&&ok;ok=(prefs.putString("rpi",rpiHost)>0)&&ok;
 ok=(prefs.putUShort("cport",cameraPort)>0)&&ok;ok=(prefs.putUShort("rport",rpiPort)>0)&&ok;
 if(!ok){server.send(500,"text/plain","No se pudo guardar. Vuelve a intentarlo.");return;}
 server.sendHeader("Cache-Control","no-store");server.send(200,"text/plain; charset=utf-8","Guardado. Vuelve a INICIO en la pantalla y elige AGV o Minrray.");applyNetwork=true;
 });server.begin();
 tft.fillScreen(0x0863);text(12,12,"CONFIGURACION",2);homeButton();
 text(12,53,"1. Conecta el movil a la Wi-Fi:");text(12,76,"Panel-AGV-Minrray",2);
 text(12,109,"Clave temporal:");text(12,128,setupKey,2);
 text(12,166,"2. Abre http://192.168.4.1");text(12,194,"3. Guarda y vuelve a INICIO");
}
void leave(){
 if(app==MINRRAY)AppMinrray::stopAll();
 if(app==AGV)AppAGV::leave();
 if(portal){server.stop();WiFi.softAPdisconnect(true);WiFi.mode(WIFI_STA);portal=false;setupKey="";}
 awaitRelease=true;previousTouch=true;home();
}
void setup(){
 Serial.begin(115200);pinMode(TFT_BL,OUTPUT);digitalWrite(TFT_BL,HIGH);
 SPI.begin(TFT_SCLK,TFT_MISO,TFT_MOSI,TFT_CS);tft.init(240,320);tft.setRotation(1);tft.invertDisplay(false);
 touchSPI.begin(TOUCH_SCLK,TOUCH_MISO,TOUCH_MOSI,TOUCH_CS);touch.begin(touchSPI);touch.setRotation(1);
 prefs.begin("agv-minrray",false);wifiName=prefs.getString("ssid","");wifiKey=prefs.getString("key","");
 cameraHost=prefs.getString("camera","192.168.1.163");rpiHost=prefs.getString("rpi","192.168.1.11");cameraPort=prefs.getUShort("cport",1259);rpiPort=prefs.getUShort("rport",8765);
 WiFi.mode(WIFI_STA);WiFi.setAutoReconnect(true);if(!wifiName.isEmpty())WiFi.begin(wifiName.c_str(),wifiKey.c_str());home();
}
void loop(){
 if(portal)server.handleClient();
 if(applyNetwork){applyNetwork=false;WiFi.begin(wifiName.c_str(),wifiKey.c_str());}
 bool down=touch.touched();int x=0,y=0;
 if(down){TS_Point p=touch.getPoint();x=constrain(map(p.x,3551,346,16,303),0,319);y=constrain(map(p.y,3646,440,12,227),0,239);}
 if(awaitRelease){if(!down){awaitRelease=false;previousTouch=false;}delay(10);return;}
 bool edge=down&&!previousTouch;previousTouch=down;
 if(app!=HOME&&edge&&x>=260&&y<=33){leave();return;}
 if(app==HOME){
 if(millis()-homeAt>1000){homeAt=millis();tft.fillRect(0,215,320,25,0x0863);text(12,222,WiFi.status()==WL_CONNECTED?"Wi-Fi: "+WiFi.localIP().toString():wifiName.isEmpty()?"Configura la Wi-Fi para empezar":"Conectando Wi-Fi...");}
 if(edge){if(y>=56&&y<159){app=x<160?AGV:MINRRAY;if(app==AGV)AppAGV::enter();else AppMinrray::enter();homeButton();awaitRelease=true;}else if(y>=175&&y<=209){settings();awaitRelease=true;}}
 }else if(app==AGV){AppAGV::loop(down,edge,x,y);homeButton();}else if(app==MINRRAY){AppMinrray::loop();homeButton();}
 delay(5);
}
