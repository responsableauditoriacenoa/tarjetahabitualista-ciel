# Manual de Usuario

## Conciliacion Tarjeta Habitualista CIEL

Este manual explica como usar la aplicacion Streamlit para cargar reportes, mantener bases consolidadas y descargar reportes de conciliacion.

## 1. Acceso a la aplicacion

Una vez publicada en Streamlit, se accede desde la URL de la app.

En uso local:

```powershell
streamlit run app.py
```

La aplicacion se abre en:

```text
http://localhost:8501
```

## 2. Estructura general

La app tiene estos modulos principales en el menu lateral:

- `Importar y conciliar`
- `Conciliacion de Pagos y Ventas`
- `Conciliacion Contable de Tarjeta Habitualista S/ Contabilidad`
- `Pagos vs ventas`
- `Historial`
- `Backups`

Los modulos mas importantes para uso diario son:

- `Conciliacion de Pagos y Ventas`
- `Conciliacion Contable de Tarjeta Habitualista S/ Contabilidad`
- `Backups`

## 3. Conciliacion de Pagos y Ventas

Este modulo mantiene una base consolidada entre:

- Operaciones de pago de Tarjeta Habitualista.
- Reportes de ventas, por ejemplo ventas 0 km y ventas usados.

### Objetivo

Detectar que pagos de Tarjeta Habitualista corresponden a operaciones de venta.

### Archivos que se deben importar

En el formulario se pueden cargar:

- Uno o varios reportes de `Operaciones de pago`.
- Uno o varios reportes de `Reportes de ventas`.

Se pueden cargar varios archivos de ventas al mismo tiempo. Esto sirve cuando existen reportes separados para 0 km y usados.

### Como hacer la primera carga

1. Ir al modulo `Conciliacion de Pagos y Ventas`.
2. En `Operaciones de pago`, subir el archivo o archivos descargados desde Tarjeta Habitualista.
3. En `Reportes de ventas`, subir los reportes de ventas correspondientes.
4. Presionar `Importar y recalcular base`.
5. Revisar el resumen y las tablas.
6. Descargar el reporte consolidado si se necesita.

### Como hacer cargas nuevas

Cuando se descarguen nuevos reportes:

1. Volver al modulo `Conciliacion de Pagos y Ventas`.
2. Subir los nuevos reportes de pagos y/o ventas.
3. Presionar `Importar y recalcular base`.

El sistema no duplica registros ya cargados. Si detecta datos repetidos, actualiza la fila existente. Si detecta datos nuevos, los agrega.

### Como detecta coincidencias

La aplicacion intenta relacionar pagos y ventas con estas reglas:

1. `OP` del pago contra `Refer.` de ventas.
2. `REF` del pago contra `Refer.` de ventas.
3. Numeros largos encontrados en la descripcion del pago contra `Refer.` de ventas.
4. Como respaldo, cliente de la venta encontrado en la descripcion del pago.

### Como leer el reporte

El reporte tiene estas secciones:

- `Resumen`: totales generales.
- `Pagos conciliados`: pagos que fueron relacionados con una venta.
- `Pagos no conciliados`: pagos que no se pudieron relacionar con ventas.
- `Ventas sin pago`: ventas que no tienen un pago detectado.
- `Base pagos`: todos los pagos importados a la base.
- `Base ventas`: todas las ventas importadas a la base.
- `Importaciones`: historial de importaciones realizadas.

### Que revisar

Revisar principalmente:

- `Pagos no conciliados`
- `Ventas sin pago`

Un pago no conciliado puede significar:

- La venta todavia no fue importada.
- El pago no corresponde a una venta.
- El dato de referencia no coincide.
- Falta informacion en alguno de los reportes.

Una venta sin pago puede significar:

- El pago todavia no fue importado.
- El pago fue realizado por otro medio.
- Hay diferencias en la referencia o descripcion.

## 4. Conciliacion Contable de Tarjeta Habitualista S/ Contabilidad

Este modulo mantiene una base consolidada entre:

- Operaciones de pago de Tarjeta Habitualista.
- Movimientos de cuenta de Tarjeta Habitualista.
- Mayor contable de Quiter.

### Objetivo

Conciliar lo informado por Tarjeta Habitualista contra lo registrado contablemente en Quiter.

### Criterio contable

En Quiter, la cuenta funciona como un pasivo:

- Movimientos al `Debe`: depositos realizados a la cuenta.
- Movimientos al `Haber`: pagos realizados con Tarjeta Habitualista.

En Tarjeta Habitualista:

- `Operaciones de pago`: pagos realizados por gestores.
- `Movimientos de cuenta` tipo `CREDIT`: depositos realizados a la cuenta.

### Archivos que se deben importar

En este modulo se pueden cargar:

- Uno o varios archivos de `Operaciones de pago`.
- Uno o varios archivos de `Movimientos de cuenta`.
- Uno o varios archivos de `Contabilidad Quiter`.

### Como hacer la primera carga

1. Ir al modulo `Conciliacion Contable de Tarjeta Habitualista S/ Contabilidad`.
2. Subir los reportes de `Operaciones de pago`.
3. Subir los reportes de `Movimientos de cuenta`.
4. Subir el mayor de `Contabilidad Quiter`.
5. Seleccionar el periodo `Desde Quiter` y `Hasta Quiter`.
6. Definir la tolerancia de dias para depositos.
7. Presionar `Importar y recalcular contabilidad`.

### Como hacer cargas incrementales

Cuando haya reportes nuevos:

1. Subir solo los archivos nuevos o actualizados.
2. Presionar `Importar y recalcular contabilidad`.

El sistema:

- Agrega movimientos nuevos.
- Actualiza movimientos existentes.
- Recalcula toda la conciliacion.

### Sincronizar periodo de Quiter

La opcion `Sincronizar periodo de Quiter` sirve cuando el archivo de Quiter que se importa representa la foto completa del periodo seleccionado.

Cuando esta activa:

- Si un asiento de Quiter existia en la base.
- Y corresponde al periodo seleccionado.
- Pero ya no aparece en el nuevo mayor importado.

Entonces el sistema lo elimina de la base.

Esto sirve cuando un asiento fue eliminado en Quiter por estar mal cargado.

### Cuidado con la sincronizacion

Usar esta opcion solo si el archivo importado contiene todo el periodo seleccionado.

Ejemplo correcto:

- Archivo importado: 10/05/2026 al 14/05/2026.
- Rango seleccionado: 10/05/2026 al 14/05/2026.
- Sincronizacion activa.

Ejemplo riesgoso:

- Archivo importado: 10/05/2026 al 14/05/2026.
- Rango seleccionado: 01/05/2026 al 14/05/2026.
- Sincronizacion activa.

En el segundo caso, el sistema podria interpretar que los asientos del 01/05 al 09/05 ya no existen y eliminarlos de la base.

### Como concilia pagos

Para pagos, el sistema cruza:

1. `OP + importe`.
2. Si no hay OP, `REF/Nro.docum + importe`.

### Como concilia depositos

Para depositos, el sistema cruza:

1. Importe exacto.
2. Si hay varias posibilidades, usa fechas dentro de la tolerancia configurada.

### Como leer el reporte contable

El reporte tiene estas secciones:

- `Resumen`: cantidades e importes por tipo de movimiento.
- `Conciliados`: movimientos encontrados en ambos lados.
- `Pendientes portal`: movimientos que estan en Tarjeta Habitualista pero no en Quiter.
- `Pendientes Quiter`: movimientos que estan en Quiter pero no en Tarjeta Habitualista.
- `Base portal`: todos los movimientos importados desde Tarjeta Habitualista.
- `Base Quiter`: todos los movimientos importados desde Quiter.
- `Importaciones`: historial de importaciones.

### Que revisar

Revisar principalmente:

- `Pendientes portal`
- `Pendientes Quiter`

`Pendientes portal` puede indicar:

- Pagos o depositos todavia no registrados en Quiter.
- Diferencias de fecha.
- Diferencias de importe.
- Faltan movimientos contables.

`Pendientes Quiter` puede indicar:

- Asientos duplicados.
- Asientos mal cargados.
- Movimientos fuera del periodo importado en Habitualista.
- Movimientos eliminados o corregidos que requieren sincronizacion.

## 5. Importar y conciliar

Este modulo permite hacer una conciliacion puntual sin trabajar necesariamente sobre la base consolidada.

Sirve para pruebas o controles aislados.

Para uso habitual se recomienda usar:

- `Conciliacion de Pagos y Ventas`
- `Conciliacion Contable de Tarjeta Habitualista S/ Contabilidad`

## 6. Pagos vs ventas

Este modulo es una version puntual o historica del cruce entre pagos y ventas.

Permite:

- Usar operaciones de pago guardadas.
- Subir nuevas operaciones de pago.
- Subir uno o varios reportes de ventas.
- Ver detectados y no detectados.

Para uso consolidado y acumulativo, usar preferentemente `Conciliacion de Pagos y Ventas`.

## 7. Backups

El modulo `Backups` permite proteger la informacion cargada.

### Que guarda un backup

Cada backup guarda la carpeta `data`, que contiene:

- La base SQLite.
- Los archivos importados.
- Los reportes generados.
- El historial de importaciones.

### Backup automatico

La aplicacion genera un backup automatico despues de cada importacion o cambio importante.

### Backup manual

Para crear un backup manual:

1. Ir al modulo `Backups`.
2. Presionar `Crear backup ahora`.
3. Descargar el ZIP generado si se desea conservar una copia externa.

### Restaurar backup

Para restaurar:

1. Ir al modulo `Backups`.
2. Subir el archivo ZIP de backup.
3. Marcar la confirmacion.
4. Presionar `Restaurar backup`.
5. Recargar la aplicacion.

### Recomendacion importante para Streamlit Cloud

En Streamlit Cloud, los archivos locales pueden perderse si la app se reinicia, hiberna o se redeploya.

Por eso se recomienda descargar backups periodicamente.

## 8. Buenas practicas de uso

- Cargar reportes con periodos amplios al iniciar la base.
- Luego cargar solo nuevos reportes o reportes corregidos.
- No preocuparse por duplicados: el sistema actualiza registros existentes.
- Usar `Sincronizar periodo de Quiter` solo cuando el mayor importado sea completo para ese rango.
- Descargar backups despues de cargas importantes.
- Revisar pendientes antes de tomar decisiones contables.
- Descargar el reporte consolidado total para documentar cierres o revisiones.

## 9. Formato de importes

En pantalla, los importes se muestran en formato pesos:

```text
$ 1.234.567,89
```

Los numeros que no son importes se muestran en formato general.

## 10. Datos persistentes

La informacion queda guardada localmente en:

```text
data/
```

Esta carpeta no se sube a GitHub porque contiene informacion sensible y esta incluida en `.gitignore`.

Los backups quedan en:

```text
backups/
```

Tambien estan ignorados por Git.

