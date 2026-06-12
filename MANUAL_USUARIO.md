# Manual de Usuario

## Conciliacion Tarjeta Habitualista CIEL

Este manual explica como usar la aplicacion de conciliacion de Tarjeta Habitualista. Esta pensado para capacitar a un usuario desde cero: que archivos debe cargar, para que sirve cada modulo, como leer los resultados y que controles realizar antes de tomar decisiones.

La aplicacion trabaja con bases consolidadas. Esto significa que no se usa solamente para una conciliacion aislada, sino para ir acumulando reportes importados, evitar duplicados, actualizar datos ya cargados y obtener un reporte total actualizado.

---

## 1. Objetivo general del sistema

La aplicacion permite controlar dos procesos:

1. **Conciliacion de Pagos y Ventas**
   - Cruza pagos realizados por Tarjeta Habitualista contra operaciones de venta.
   - Sirve para detectar que pagos corresponden a ventas y cuales requieren revision.

2. **Conciliacion Contable de Tarjeta Habitualista S/ Contabilidad**
   - Cruza los movimientos informados por Tarjeta Habitualista contra la contabilidad de Quiter.
   - Sirve para verificar que pagos y depositos esten registrados contablemente.

Ademas, la app incluye:

- **Historial**: permite ver importaciones realizadas y descargar reportes consolidados.
- **Backups**: permite generar o restaurar copias de seguridad.

---

## 2. Conceptos principales

### 2.1 Base consolidada

Una base consolidada es una base acumulativa. Cada vez que se importan archivos, el sistema:

- Agrega registros nuevos.
- Actualiza registros ya existentes.
- Evita duplicar informacion.
- Recalcula la conciliacion con toda la base disponible.

Esto permite trabajar con reportes de varios periodos. Por ejemplo, se puede comenzar cargando desde enero y luego agregar reportes nuevos de febrero, marzo, abril, etc.

### 2.2 Registro nuevo

Es una fila que no existia antes en la base. El sistema la incorpora.

### 2.3 Registro actualizado

Es una fila que el sistema ya conocia, pero que vuelve a aparecer en una nueva importacion. Si el nuevo archivo trae informacion mas completa o corregida, la app actualiza la fila.

### 2.4 Registro conciliado

Es un movimiento que el sistema pudo relacionar con otro movimiento del reporte contra el que se esta comparando.

### 2.5 Registro pendiente

Es un movimiento que todavia no tiene coincidencia. No necesariamente significa error; significa que debe revisarse.

---

## 3. Acceso a la aplicacion

### 3.1 Uso en Streamlit Cloud

El usuario accede desde la URL publicada de la app.

Si la app no carga o no refleja el ultimo cambio, desde Streamlit Cloud se puede usar:

```text
Manage app > Reboot app
```

### 3.2 Uso local

Desde la carpeta del proyecto:

```powershell
streamlit run app.py
```

La aplicacion se abre normalmente en:

```text
http://localhost:8501
```

---

## 4. Menu principal

El menu lateral contiene los modulos operativos:

- **Conciliacion de Pagos y Ventas**
- **Conciliacion Contable de Tarjeta Habitualista S/ Contabilidad**
- **Historial**
- **Backups**

Los modulos antiguos de pruebas fueron retirados del menu para evitar confusiones.

---

## 5. Modulo: Conciliacion de Pagos y Ventas

### 5.1 Para que sirve

Este modulo permite conciliar los pagos hechos por Tarjeta Habitualista contra las operaciones de venta.

Sirve para responder preguntas como:

- Que pagos ya se pudieron asociar a una venta.
- Que pagos no tienen venta detectada.
- Que ventas siguen sin pago detectado.
- Que base total de pagos y ventas tiene cargada la app.
- Que importaciones se realizaron.

### 5.2 Archivos que se cargan

En este modulo se pueden importar:

1. **Operaciones de pago**
   - Archivo descargado desde Tarjeta Habitualista.
   - Contiene los pagos realizados por gestores.

2. **Reportes de ventas**
   - Pueden ser uno o varios archivos.
   - Por ejemplo:
     - ventas 0 km
     - ventas usados

Se puede cargar mas de un archivo de ventas en una misma importacion.

### 5.3 Primera carga recomendada

1. Ingresar al modulo **Conciliacion de Pagos y Ventas**.
2. En **Operaciones de pago**, subir el reporte de pagos.
3. En **Reportes de ventas**, subir todos los reportes disponibles de ventas.
4. Presionar **Importar y recalcular base**.
5. Esperar a que finalice el proceso.
6. Revisar las metricas superiores.
7. Revisar las solapas de resultados.
8. Descargar el Excel si se necesita documentar el control.

### 5.4 Cargas posteriores

Cuando se descarguen nuevos reportes:

1. Ingresar al modulo.
2. Subir los nuevos reportes de pagos y/o ventas.
3. Presionar **Importar y recalcular base**.

La app no reinicia la base. Agrega lo nuevo y actualiza lo repetido.

### 5.5 Que pasa si cargo un periodo repetido

Si se vuelve a cargar un archivo que contiene movimientos ya importados:

- No se duplican.
- Se actualizan si corresponde.
- La conciliacion se recalcula con la base total.

Esto permite importar reportes con periodos superpuestos sin romper la base.

### 5.6 Criterios de conciliacion pagos vs ventas

El sistema intenta relacionar los pagos con ventas usando datos encontrados en los reportes.

Los principales criterios son:

1. **OP del pago contra referencia de venta**
   - Se toma la OP detectada en la descripcion del pago.
   - Se compara contra la referencia de la venta.

2. **REF del pago contra referencia de venta**
   - Se toma la referencia detectada en el texto del pago.
   - Se compara contra la referencia de venta.

3. **Numeros encontrados en la descripcion**
   - Si en el texto del pago aparecen numeros que parecen referencias, el sistema intenta usarlos.

4. **Cliente encontrado en la descripcion**
   - Como respaldo, el sistema puede detectar si el nombre del cliente de la venta aparece dentro de la descripcion del pago.

### 5.7 Metricas del modulo

El modulo muestra indicadores resumidos, por ejemplo:

- **Pagos conciliados**
  - Cantidad de pagos que encontraron venta.

- **Total conciliado**
  - Importe total de pagos conciliados.

- **Pagos no conciliados**
  - Cantidad de pagos que no encontraron venta.

- **Ventas sin pago**
  - Ventas cargadas en la base para las cuales no se detecto pago.

### 5.8 Solapas del modulo

#### Resumen

Muestra cantidades e importes generales:

- Pagos en base.
- Pagos conciliados con ventas.
- Pagos no conciliados.
- Ventas en base.
- Ventas sin pago detectado.

#### Pagos conciliados

Muestra pagos que fueron relacionados con ventas.

Campos utiles:

- fecha del pago
- numero de pago
- importe del pago
- OP del pago
- referencia del pago
- referencia de venta
- cliente
- modelo
- saldo de la venta
- criterio de conciliacion

#### Pagos no conciliados

Muestra pagos que el sistema no pudo asociar con una venta.

Debe revisarse cuando:

- La venta aun no fue importada.
- La referencia no coincide.
- El pago no corresponde a una operacion de venta.
- Falta informacion en la descripcion del pago.

#### Ventas sin pago

Muestra ventas para las cuales no se detecto pago.

Debe revisarse cuando:

- El pago aun no fue cargado.
- El pago fue realizado por otro medio.
- Hay diferencias de referencia.
- La venta no deberia tener pago por Tarjeta Habitualista.

#### Base pagos

Muestra todos los pagos acumulados en la base.

Sirve para verificar:

- Que pagos fueron importados.
- De que archivo provienen.
- Si estan conciliados o pendientes.

#### Base ventas

Muestra todas las ventas acumuladas en la base.

Sirve para verificar:

- Que ventas fueron importadas.
- De que archivo provienen.
- Si tienen pago detectado.

#### Importaciones

Muestra el historial de cargas realizadas en este modulo.

Incluye:

- fecha de importacion
- archivos cargados
- cantidad de pagos insertados
- cantidad de pagos actualizados
- cantidad de ventas insertadas
- cantidad de ventas actualizadas

### 5.9 Reporte Excel del modulo

El boton **Descargar reporte consolidado Excel** genera un archivo con la conciliacion completa vigente.

El Excel contiene:

- Resumen
- Pagos conciliados
- Pagos no conciliados
- Ventas sin pago
- Base pagos
- Base ventas
- Importaciones

---

## 6. Modulo: Conciliacion Contable de Tarjeta Habitualista S/ Contabilidad

### 6.1 Para que sirve

Este modulo compara los movimientos de Tarjeta Habitualista contra la contabilidad registrada en Quiter.

Sirve para responder preguntas como:

- Que pagos de Habitualista estan registrados en Quiter.
- Que depositos de Habitualista estan registrados en Quiter.
- Que movimientos aparecen en Habitualista pero no en Quiter.
- Que movimientos aparecen en Quiter pero no en Habitualista.
- Si la cuenta contable esta limpia y correctamente conciliada.

### 6.2 Logica contable de la cuenta

La cuenta de Tarjeta Habitualista se controla como una cuenta contable vinculada a movimientos de pagos y depositos.

En Quiter:

- **Debe**
  - Representa depositos realizados a la cuenta.

- **Haber**
  - Representa pagos realizados con Tarjeta Habitualista.

En Habitualista:

- **Movimientos de cuenta tipo CREDIT**
  - Representan depositos.

- **Operaciones de pago**
  - Representan pagos realizados por gestores.

### 6.3 Archivos que se cargan

El modulo permite importar:

1. **Operaciones de pago**
   - Reporte de pagos de Tarjeta Habitualista.

2. **Movimientos de cuenta**
   - Reporte de cuenta corriente de Tarjeta Habitualista.
   - El sistema considera solamente movimientos tipo `CREDIT`.

3. **Contabilidad Quiter**
   - Mayor contable de la cuenta.
   - Debe contener movimientos al Debe y Haber.

Se puede cargar uno o varios archivos por cada tipo.

### 6.4 Primera carga recomendada

1. Ingresar a **Conciliacion Contable de Tarjeta Habitualista S/ Contabilidad**.
2. Subir **Operaciones de pago**.
3. Subir **Movimientos de cuenta**.
4. Subir **Contabilidad Quiter**.
5. Seleccionar **Desde Quiter**.
6. Seleccionar **Hasta Quiter**.
7. Definir **Tolerancia dias depositos**.
8. Revisar si corresponde activar **Sincronizar periodo de Quiter**.
9. Presionar **Importar y recalcular contabilidad**.
10. Revisar resultados.
11. Descargar el Excel si corresponde.

### 6.5 Cargas posteriores

Cuando se descarguen nuevos reportes:

1. Subir los reportes nuevos o corregidos.
2. Elegir el rango de fechas correcto para Quiter.
3. Presionar **Importar y recalcular contabilidad**.

La base se mantiene acumulada. No se borra todo por una nueva importacion.

### 6.6 Criterio de conciliacion contable

La conciliacion contable **no usa OP ni referencia** para cruzar movimientos.

Esto es importante porque:

- La OP de Quiter y la OP de Tarjeta Habitualista pueden no ser iguales.
- La referencia contable puede ser solamente un codigo de asiento.
- Por lo tanto, esos campos pueden confundir el cruce contable.

El sistema cruza con esta logica:

1. **Tipo + importe**
   - El tipo debe coincidir:
     - pago con pago
     - deposito con deposito
   - El importe debe coincidir.

2. **Si hay un solo candidato**
   - Si existe un unico movimiento del mismo tipo e importe, se concilia.

3. **Si hay varios candidatos con el mismo importe**
   - El sistema busca cercania de fechas.
   - Usa la tolerancia configurada.
   - Elige el movimiento con fecha mas cercana dentro de esa tolerancia.

4. **Si no encuentra coincidencia**
   - El movimiento queda pendiente.

### 6.7 Tolerancia de dias

La tolerancia de dias permite resolver casos donde Habitualista y Quiter registran el mismo movimiento con fechas cercanas pero no identicas.

Ejemplo:

- Habitualista: 10/05/2026
- Quiter: 12/05/2026
- Tolerancia: 3 dias

El sistema puede conciliarlos porque la diferencia esta dentro del rango permitido.

Si la tolerancia fuera 1 dia, ese movimiento podria quedar pendiente.

### 6.8 Sincronizar periodo de Quiter

La opcion **Sincronizar periodo de Quiter** sirve para limpiar la base cuando un nuevo mayor de Quiter reemplaza a uno anterior.

Cuando esta activa, el sistema:

1. Mira los movimientos de Quiter dentro del periodo seleccionado.
2. Compara lo que ya estaba guardado contra lo que viene en el nuevo archivo.
3. Si un asiento estaba en la base pero ya no aparece en el nuevo mayor del mismo periodo, lo elimina.

Esto sirve cuando:

- Un asiento fue eliminado en Quiter.
- Un asiento fue corregido.
- Se vuelve a importar una foto actualizada del mismo periodo.

### 6.9 Cuidado al sincronizar Quiter

La sincronizacion debe usarse solamente cuando el archivo importado contiene todo el periodo seleccionado.

#### Ejemplo correcto

- Archivo de Quiter cargado: 10/05/2026 al 14/05/2026.
- Rango seleccionado en la app: 10/05/2026 al 14/05/2026.
- Sincronizacion activa.

Resultado esperado:

- La app limpia solo ese periodo.

#### Ejemplo riesgoso

- Archivo de Quiter cargado: 10/05/2026 al 14/05/2026.
- Rango seleccionado en la app: 01/05/2026 al 14/05/2026.
- Sincronizacion activa.

Riesgo:

- La app puede interpretar que los asientos del 01/05 al 09/05 ya no existen y eliminarlos de la base.

### 6.10 Boton Recalcular conciliacion contable

El boton **Recalcular conciliacion contable** sirve para recalcular la base ya cargada sin volver a importar archivos.

Usarlo cuando:

- Cambio una regla de conciliacion.
- Se quiere forzar un nuevo calculo.
- Se importaron datos y se quiere refrescar el resultado.

No agrega archivos nuevos. Solo recalcula la conciliacion existente.

### 6.11 Metricas del modulo

El modulo muestra indicadores como:

- **Conciliados**
  - Cantidad total de movimientos que encontraron match.

- **Total conciliado**
  - Importe total conciliado.

- **Pendientes portal**
  - Movimientos que estan en Habitualista pero no fueron encontrados en Quiter.

- **Pendientes Quiter**
  - Movimientos que estan en Quiter pero no fueron encontrados en Habitualista.

### 6.12 Solapas del modulo contable

#### Resumen

Muestra cantidades e importes por tipo:

- deposito
- pago

Y separa:

- movimientos en portal
- movimientos en Quiter
- conciliados
- pendientes portal
- pendientes Quiter

#### Conciliados

Muestra los movimientos que fueron conciliados.

Esta solapa es clave porque muestra el movimiento de origen y el movimiento contra el que se matcheo.

Columnas importantes:

- `tipo`
- `importe`
- `criterio`
- `fecha_origen`
- `fuente_origen`
- `archivo_origen`
- `fila_origen`
- `descripcion_origen`
- `fecha_conciliada`
- `fuente_conciliada`
- `archivo_conciliado`
- `fila_conciliada`
- `descripcion_conciliada`

La columna `descripcion_origen` muestra la descripcion del movimiento de Habitualista.

La columna `descripcion_conciliada` muestra la descripcion del movimiento de Quiter contra el que fue conciliado.

Esto permite revisar visualmente contra que asiento o movimiento se hizo el match.

#### Pendientes portal

Muestra movimientos que estan en Tarjeta Habitualista pero no estan conciliados contra Quiter.

Puede indicar:

- Pago todavia no contabilizado.
- Deposito todavia no registrado.
- Diferencia de importe.
- Diferencia de fecha fuera de tolerancia.
- Archivo de Quiter incompleto.

#### Pendientes Quiter

Muestra movimientos que estan en Quiter pero no estan conciliados contra Habitualista.

Puede indicar:

- Asiento contable duplicado.
- Asiento cargado con importe incorrecto.
- Movimiento contable sin respaldo en Habitualista.
- Movimiento de Habitualista no importado.
- Error de periodo.

#### Base portal

Muestra todos los movimientos acumulados desde Habitualista:

- operaciones de pago
- movimientos de cuenta CREDIT

Sirve para auditar que archivos y filas alimentan la base.

#### Base Quiter

Muestra todos los movimientos acumulados desde el mayor contable.

Sirve para auditar:

- movimientos al Debe
- movimientos al Haber
- archivo de origen
- fila de origen
- match encontrado

#### Importaciones

Muestra el historial de cargas del modulo contable.

Incluye:

- fecha
- archivos de pagos
- archivos de movimientos de cuenta
- archivos de Quiter
- portal insertados
- portal actualizados
- Quiter insertados
- Quiter actualizados
- Quiter eliminados por sincronizacion

### 6.13 Reporte Excel contable

El boton **Descargar reporte contable consolidado Excel** genera un archivo con:

- Resumen
- Conciliados
- Pendientes portal
- Pendientes Quiter
- Base portal
- Base Quiter
- Importaciones

Este archivo es el reporte recomendado para respaldar revisiones contables.

---

## 7. Modulo: Historial

### 7.1 Para que sirve

El modulo **Historial** concentra descargas y registros de importacion.

Sirve para:

- Descargar el consolidado total de pagos y ventas.
- Descargar el consolidado contable total.
- Consultar importaciones realizadas.
- Revisar conciliaciones historicas del modulo anterior si existieran.

### 7.2 Descargas disponibles

En la parte superior se muestran dos botones:

1. **Descargar consolidado pagos y ventas**
   - Descarga la base vigente del modulo Conciliacion de Pagos y Ventas.

2. **Descargar consolidado contable**
   - Descarga la base vigente del modulo contable.

### 7.3 Solapas del Historial

#### Importaciones pagos y ventas

Muestra las importaciones realizadas en la base de pagos y ventas.

Sirve para controlar:

- fecha de carga
- archivos importados
- registros nuevos
- registros actualizados

#### Importaciones contables

Muestra las importaciones realizadas en la base contable.

Sirve para controlar:

- archivos de pagos importados
- archivos de movimientos de cuenta importados
- archivos de Quiter importados
- registros insertados
- registros actualizados
- registros eliminados por sincronizacion

#### Conciliaciones anteriores

Esta solapa queda solo para consultar reportes historicos generados por el modulo antiguo, si existieran.

No es el flujo operativo recomendado.

---

## 8. Modulo: Backups

### 8.1 Para que sirve

El modulo **Backups** permite proteger la informacion cargada.

Sirve para:

- Crear una copia manual.
- Descargar backups existentes.
- Restaurar una copia anterior.

### 8.2 Que guarda un backup

El backup guarda la carpeta local `data`, que incluye:

- base SQLite local
- archivos importados
- reportes generados
- historial de importaciones

### 8.3 Backup automatico

La app genera backups automaticos despues de importaciones importantes.

### 8.4 Crear backup manual

1. Ingresar al modulo **Backups**.
2. Presionar **Crear backup ahora**.
3. Descargar el ZIP si se desea guardar fuera de la app.

### 8.5 Restaurar backup

1. Ingresar a **Backups**.
2. Subir el ZIP de backup.
3. Marcar la confirmacion.
4. Presionar **Restaurar backup**.
5. Recargar la app.

### 8.6 Importante en Streamlit Cloud

Si la app usa Neon como base de datos, la informacion principal queda en Neon.

Si la app usa almacenamiento local, la carpeta `data` puede perderse si Streamlit reinicia, hiberna o redeploya la app.

Por eso, para Streamlit Cloud se recomienda usar Neon.

---

## 9. Persistencia de datos

### 9.1 Uso local sin Neon

Si no existe `DATABASE_URL`, la app usa SQLite local.

La informacion queda en:

```text
data/
```

### 9.2 Uso en Streamlit Cloud con Neon

Para que los datos sean persistentes en Streamlit Cloud, se recomienda configurar Neon/PostgreSQL.

En Streamlit Cloud:

```text
App > Settings > Secrets
```

Agregar:

```toml
DATABASE_URL = "postgresql://usuario:password@host.neon.tech/dbname?sslmode=require"
```

Luego reiniciar la app.

### 9.3 Como saber si se esta usando Neon

Si `DATABASE_URL` esta configurada, la app guarda las bases en Neon.

Si no esta configurada, usa SQLite local.

---

## 10. Formato de importes

Los importes se muestran en formato pesos:

```text
$ 1.234.567,89
```

Los numeros que no son importes se muestran en formato general.

---

## 11. Buenas practicas

### 11.1 Para comenzar una base

- Cargar un periodo amplio inicial.
- Incluir pagos, ventas y contabilidad segun corresponda.
- Verificar que las metricas tengan sentido.
- Descargar un primer consolidado.

### 11.2 Para cargas mensuales o semanales

- Importar solamente reportes nuevos o reportes corregidos.
- No preocuparse por periodos superpuestos: la app actualiza duplicados.
- Revisar siempre los pendientes.
- Descargar el consolidado luego de cada cierre.

### 11.3 Para conciliacion contable

- Revisar especialmente `Pendientes portal` y `Pendientes Quiter`.
- Usar tolerancia de fechas razonable.
- No usar sincronizacion de Quiter si el archivo no cubre todo el periodo seleccionado.
- Usar `Recalcular conciliacion contable` si se quiere refrescar la base sin importar archivos.

### 11.4 Para pagos y ventas

- Importar ventas 0 km y usados si existen reportes separados.
- Revisar pagos no conciliados.
- Revisar ventas sin pago.
- Verificar que las referencias y nombres de clientes sean correctos.

### 11.5 Para seguridad de informacion

- Usar Neon en Streamlit Cloud.
- Descargar reportes consolidados luego de cierres importantes.
- Generar backups manuales antes de cambios grandes.

---

## 12. Interpretacion rapida de pendientes

### 12.1 Pagos no conciliados en pagos y ventas

Puede significar:

- La venta aun no fue importada.
- La referencia no coincide.
- El pago no corresponde a venta.
- El cliente no aparece en la descripcion.

### 12.2 Ventas sin pago

Puede significar:

- El pago aun no fue importado.
- La venta fue pagada por otro medio.
- La referencia esta mal cargada.
- No corresponde pago por Tarjeta Habitualista.

### 12.3 Pendientes portal en contabilidad

Puede significar:

- Habitualista informa un pago o deposito que Quiter aun no tiene.
- Falta contabilizar.
- Hay diferencia de importe.
- Hay diferencia de fecha fuera de tolerancia.

### 12.4 Pendientes Quiter en contabilidad

Puede significar:

- Quiter tiene un asiento sin respaldo en Habitualista.
- Existe un asiento duplicado.
- Se cargo un importe incorrecto.
- Se importo un periodo incompleto de Habitualista.

---

## 13. Cierre recomendado de control

Para documentar una revision:

1. Importar los reportes correspondientes.
2. Revisar metricas.
3. Revisar pendientes.
4. Corregir datos si corresponde.
5. Reimportar archivos corregidos.
6. Descargar reporte consolidado.
7. Guardar el Excel como respaldo del cierre.
8. Crear backup manual si se esta usando almacenamiento local.

---

## 14. Resumen de uso diario

Para pagos y ventas:

1. Entrar a **Conciliacion de Pagos y Ventas**.
2. Subir pagos y ventas nuevos.
3. Importar y recalcular.
4. Revisar pagos no conciliados y ventas sin pago.
5. Descargar consolidado.

Para contabilidad:

1. Entrar a **Conciliacion Contable de Tarjeta Habitualista S/ Contabilidad**.
2. Subir operaciones de pago, movimientos de cuenta y mayor de Quiter.
3. Seleccionar periodo correcto.
4. Revisar sincronizacion de Quiter.
5. Importar y recalcular.
6. Revisar pendientes portal y pendientes Quiter.
7. Descargar consolidado contable.

