# Archivo previo al nuevo comienzo del coche

Revisión del 20 de noviembre de 2026. Se conserva material auxiliar encontrado fuera del repositorio activo de la Raspberry y ausente de sus objetos Git locales, junto con una variante del mando que estaba en otra carpeta del PC. Estos archivos son históricos; no se instalan ni sustituyen los programas activos. Algunos scripts modifican código o ejecutan motores: conservarlos no implica ejecutarlos.

El proyecto activo de la Raspberry y GitHub coincidían en `93b29009af535bd3ccd545b889a459029f0c5c1c`. Los servicios web y WebSocket estaban activos. La telemetría reconocía la Fusion HAT, informaba de batería al 47 % (7,359 V) y los cuatro motores a potencia cero. No recibía muestras de la Pico por la UART configurada; no se leyó su memoria ni la del ESP32.

La versión vigente del mando en `firmware/Pantalla_AGV_Minrray/` conserva la corrección de avance/retroceso y el deslizador compartido de potencia del 25 al 75 %. La copia en `variante_mando_pc/` es una variante distinta sin dicho deslizador; se archiva para preservar el trabajo, sin adoptarla.

Se inspeccionaron los archivos de código, configuración y documentación de las carpetas auxiliares del usuario olmos, excluyendo dependencias y cachés. Las copias ya presentes en el historial Git no se duplicaron. No se incluyeron credenciales, entornos virtuales ni la biblioteca externa fusion-hat. El inventario contiene procedencia y SHA-256 de las copias conservadas. Esta revisión no certifica que el firmware instalado en las placas coincida con los archivos del repositorio.
