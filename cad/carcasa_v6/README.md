# Carcasa modular AGV — V6

**Estado: PENDIENTE DE IMPRESIÓN Y VALIDACIÓN FÍSICA.**

Montaje de diseño actualizado el 27 de octubre de 2026. Aún no se ha impreso ni probado el ajuste de esta versión en el coche. No se considera un diseño validado para fabricación.

![Montaje completo de la carcasa V6](Montaje_V6_motores_ruedas.png)

## Archivos

- [Montaje completo editable en Autodesk Fusion](AGV_V6_Montado_motores_ruedas.f3d).
- [Comprobación geométrica del montaje](verificacion_montaje_motores_ruedas.json).

El archivo se entrega ensamblado. Los componentes con prefijo REF_ son referencias de hardware o auxiliares y no son piezas que se deban imprimir. Las copias auxiliares REF_IMPRESION permanecen ocultas. Esta entrega contiene el CAD y su vista previa; no incorpora G-code listo para ejecutar en una impresora.

## Diseño incluido

- Carcasa en tres tramos, con tornillos verticales en las esquinas y detalles naranjas y blancos.
- Alojamiento para Raspberry Pi 5 con refrigerador y Fusion HAT+, batería SunFounder y powerbank.
- Cámara frontal ESP32-CAM MB mediante cartucho deslizante, guías y pasador extraíble. La envolvente de referencia de la cámara es de 40 × 27 × 22 mm.
- Base superior blanca con la Pico 2 W horizontal, espacio de acceso al USB y reserva para los pines y el cableado superior de encoders y sensores.
- Pestañas de fijación al chasis y asa por encima de la batería, anclada a la carcasa.
- Cuatro motores TT, cuatro ruedas y tres placas verticales añadidas a la placa ya presente en el CAD del chasis.

## Alcance de las comprobaciones

La comprobación geométrica guardada no encuentra solapes de las cuatro pestañas de fijación con las ruedas de referencia ni con las tres placas verticales añadidas. Es una comprobación del modelo y no sustituye el montaje físico.

Las ruedas Mecanum son una representación visual aproximada de 60 × 27 mm con nueve rodillos; no son el CAD exacto del fabricante. Las tres placas añadidas son copias simétricas de la placa vertical del CAD aportado del chasis. Los motores TT proceden de una envolvente CAD basada en un plano previo, con algunas cotas estimadas. Las referencias de baterías, HAT y cámara también requieren cotejo con las piezas físicas.

## Pendiente antes de dar la versión por validada

1. Revisar el laminado y la orientación de cada pieza, empezando por una prueba pequeña de encajes. La preparación de impresión sigue siendo provisional.
2. Imprimir y comprobar tolerancias de las guías, el cartucho de cámara, el pasador y las uniones entre tramos.
3. Confirmar las medidas y los accesos reales de los conectores USB, alimentación, cámara y cableado de sensores.
4. Comprobar tornillos, tuercas, pestañas de fijación, separación respecto de motores y ruedas y ajuste al chasis físico.
5. Validar por separado la resistencia del asa y sus anclajes antes de usarla para levantar el vehículo. No se ha calculado ni ensayado una carga admisible.
6. Terminar la preparación de las piezas pequeñas unidas por puentes recortables tipo maqueta; no se considera validada en esta entrega.

## Referencias de terceros

El montaje incluye referencias aportadas para estudiar el encaje, no diseños propios de las placas electrónicas. Consultar [atribuciones y alcance de licencias](REFERENCIAS.md).
