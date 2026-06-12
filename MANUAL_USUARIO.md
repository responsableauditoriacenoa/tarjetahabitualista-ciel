# Manual de Usuario

## Sistema de Conciliacion Tarjeta Habitualista CIEL

Este manual corresponde a la version actual de la aplicacion. Describe unicamente los modulos visibles y vigentes:

- Conciliacion de Pagos y Ventas
- Conciliacion Contable de Tarjeta Habitualista S/ Contabilidad
- Historial
- Backups

El objetivo es que un usuario pueda comenzar desde cero, entender que archivos debe importar, como funciona cada conciliacion, que significan los resultados y como descargar la informacion para revision.

---

## 1. Que hace la aplicacion

La aplicacion permite mantener bases consolidadas de conciliacion. Esto significa que la informacion se va acumulando con cada importacion y no se reinicia cada vez que se cargan reportes nuevos.

El sistema permite:

- Importar reportes de Tarjeta Habitualista.
- Importar reportes de ventas.
- Importar mayor contable de Quiter.
- Detectar movimientos conciliados.
- Detectar movimientos pendientes de revision.
- Descargar reportes consolidados en Excel.
- Consultar historial de importaciones.
- Crear y restaurar backups.

---

## 2. Conceptos basicos

### 2.1 Base consolidada

Es la base acumulada de datos que guarda la app.

Cuando se cargan nuevos archivos, la app:

- agrega registros nuevos;
- actualiza registros repetidos si traen informacion nueva;
- evita duplicar datos;
- recalcula la conciliacion con toda la informacion disponible.

### 2.2 Movimiento conciliado

Es un movimiento que la app pudo relacionar con otro movimiento del reporte correspondiente.

Ejemplos:

- un pago de Habitualista asociado a una venta;
- un pago de Habitualista asociado a un asiento de Quiter;
- un deposito de Habitualista asociado a un movimiento al Debe de Quiter.

### 2.3 Movimiento pendiente

Es un movimiento que no encontro coincidencia.

No siempre significa error. Significa que debe revisarse.

### 2.4 Registro insertado

Es un registro nuevo que no existia en la base.

### 2.5 Registro actualizado

Es un registro que ya existia y fue actualizado por una nueva importacion.

---

## 3. Menu principal

El menu lateral de la aplicacion contiene:

1. **Conciliacion de Pagos y Ventas**
2. **Conciliacion Contable de Tarjeta Habitualista S/ Contabilidad**
3. **Historial**
4. **Backups**

Estos son los unicos modulos que debe usar el usuario.

---

## 4. Conciliacion de Pagos y Ventas

### 4.1 Objetivo del modulo

Este modulo cruza los pagos realizados mediante Tarjeta Habitualista contra las operaciones de venta.

Permite saber:

- que pagos ya fueron relacionados con ventas;
- que pagos no tienen venta detectada;
- que ventas no tienen pago detectado;
- que archivos fueron importados;
- cual es la base total acumulada de pagos y ventas.

### 4.2 Archivos que se importan

El modulo tiene dos cargas:

1. **Operaciones de pago**
   - Reporte descargado desde Tarjeta Habitualista.
   - Contiene pagos realizados por gestores.

2. **Reportes de ventas**
   - Reportes descargados desde Quiter u origen operativo de ventas.
   - Se pueden subir varios archivos a la vez.
   - Ejemplos: ventas 0 km y ventas usados.

### 4.3 Como hacer la primera carga

1. Entrar a **Conciliacion de Pagos y Ventas**.
2. En **Operaciones de pago**, cargar el archivo de pagos.
3. En **Reportes de ventas**, cargar uno o mas archivos de ventas.
4. Presionar **Importar y recalcular base**.
5. Esperar el mensaje de confirmacion.
6. Revisar las metricas superiores.
7. Revisar las solapas de detalle.
8. Descargar el Excel si se necesita respaldar la revision.

### 4.4 Como hacer cargas posteriores

Cuando se obtienen nuevos reportes:

1. Entrar al mismo modulo.
2. Subir los nuevos archivos de pagos y/o ventas.
3. Presionar **Importar y recalcular base**.

La app no borra la base. Agrega lo nuevo y actualiza lo existente.

### 4.5 Que pasa si se importa un periodo repetido

Si se importa un archivo que contiene registros ya cargados:

- la app reconoce los duplicados;
- no los duplica;
- actualiza datos si corresponde;
- recalcula la conciliacion total.

Esto permite importar reportes con periodos superpuestos.

### 4.6 Criterios de cruce entre pagos y ventas

La app busca relacionar pagos con ventas usando referencias presentes en los reportes.

Los criterios son:

1. **OP del pago contra referencia de venta**
2. **REF del pago contra referencia de venta**
3. **Numeros encontrados en la descripcion del pago**
4. **Cliente de la venta encontrado en la descripcion del pago**

El criterio utilizado queda informado en la tabla de pagos conciliados.

### 4.7 Metricas principales

El modulo muestra tarjetas resumen con informacion clave:

- **Pagos conciliados**
  - cantidad de pagos que encontraron venta.

- **Total conciliado**
  - importe total de pagos conciliados.

- **Pagos no conciliados**
  - pagos que no encontraron venta.

- **Ventas sin pago**
  - ventas cargadas que no tienen pago detectado.

### 4.8 Solapas de resultado

#### Resumen

Muestra cantidades e importes generales:

- pagos en base;
- pagos conciliados con ventas;
- pagos no conciliados;
- ventas en base;
- ventas sin pago detectado.

#### Pagos conciliados

Muestra los pagos que fueron asociados a ventas.

Campos utiles:

- fecha del pago;
- numero de pago;
- importe del pago;
- OP del pago;
- referencia del pago;
- descripcion del pago;
- referencia de venta;
- cliente;
- vendedor;
- modelo;
- saldo de venta;
- criterio de conciliacion.

#### Pagos no conciliados

Muestra pagos que no encontraron venta.

Se deben revisar para detectar:

- ventas aun no importadas;
- referencias mal informadas;
- pagos que no corresponden a ventas;
- descripciones incompletas.

#### Ventas sin pago

Muestra ventas sin pago detectado.

Se deben revisar para detectar:

- pagos aun no importados;
- pagos realizados por otro medio;
- referencias incorrectas;
- ventas que no deberian tener pago por Habitualista.

#### Base pagos

Muestra todos los pagos cargados en la base.

Sirve para verificar origen, archivo, datos del pago y estado de conciliacion.

#### Base ventas

Muestra todas las ventas cargadas en la base.

Sirve para verificar ventas importadas y si tienen pago detectado.

#### Importaciones

Muestra el historial de cargas de este modulo.

Incluye:

- fecha de importacion;
- archivos cargados;
- pagos insertados;
- pagos actualizados;
- ventas insertadas;
- ventas actualizadas.

### 4.9 Descarga Excel

El boton **Descargar reporte consolidado Excel** genera el reporte total vigente.

Incluye:

- Resumen
- Pagos conciliados
- Pagos no conciliados
- Ventas sin pago
- Base pagos
- Base ventas
- Importaciones

---

## 5. Conciliacion Contable de Tarjeta Habitualista S/ Contabilidad

### 5.1 Objetivo del modulo

Este modulo cruza Tarjeta Habitualista contra la contabilidad de Quiter.

Permite saber:

- que pagos de Habitualista estan registrados en Quiter;
- que depositos estan registrados en Quiter;
- que movimientos estan en Habitualista y no en Quiter;
- que movimientos estan en Quiter y no en Habitualista;
- que asiento o descripcion contable fue usada para conciliar cada movimiento.

### 5.2 Logica contable

En Quiter:

- **Debe**: depositos realizados a la cuenta.
- **Haber**: pagos realizados con Tarjeta Habitualista.

En Habitualista:

- **Movimientos de cuenta tipo CREDIT**: depositos.
- **Operaciones de pago**: pagos realizados por gestores.

### 5.3 Archivos que se importan

El modulo tiene tres cargas:

1. **Operaciones de pago**
   - Reporte de pagos de Tarjeta Habitualista.

2. **Movimientos de cuenta**
   - Reporte de cuenta corriente de Tarjeta Habitualista.
   - La app considera solamente movimientos tipo `CREDIT`.

3. **Contabilidad Quiter**
   - Mayor contable de la cuenta.
   - Debe contener Debe y Haber.

Se pueden cargar varios archivos en cada bloque.

### 5.4 Primera carga

1. Entrar a **Conciliacion Contable de Tarjeta Habitualista S/ Contabilidad**.
2. Cargar **Operaciones de pago**.
3. Cargar **Movimientos de cuenta**.
4. Cargar **Contabilidad Quiter**.
5. Seleccionar **Desde Quiter**.
6. Seleccionar **Hasta Quiter**.
7. Definir **Tolerancia dias depositos**.
8. Revisar la opcion **Sincronizar periodo de Quiter**.
9. Presionar **Importar y recalcular contabilidad**.
10. Revisar metricas y solapas.
11. Descargar el Excel contable si corresponde.

### 5.5 Cargas posteriores

Para agregar informacion nueva:

1. Subir los reportes nuevos o corregidos.
2. Seleccionar el periodo correcto de Quiter.
3. Presionar **Importar y recalcular contabilidad**.

La base queda acumulada. No se reinicia con cada carga.

### 5.6 Criterio actual de conciliacion contable

La conciliacion contable **no usa OP ni referencia**.

Motivo:

- la OP de Quiter puede ser distinta a la OP de Habitualista;
- la referencia de Quiter puede ser solo un codigo de asiento;
- usar esos datos puede generar cruces incorrectos.

La regla actual es:

1. Coincidir por **tipo + importe**.
   - pago con pago;
   - deposito con deposito.

2. Si hay un unico candidato con el mismo tipo e importe, se concilia.

3. Si hay varios candidatos con el mismo importe, se usa cercania de fecha.

4. Si no hay candidato dentro de la tolerancia de fechas, queda pendiente.

### 5.7 Tolerancia de dias

La tolerancia permite aceptar diferencias razonables de fecha entre Habitualista y Quiter.

Ejemplo:

- Habitualista: 10/05/2026
- Quiter: 12/05/2026
- Tolerancia: 3 dias

El movimiento puede conciliarse porque la diferencia es de 2 dias.

### 5.8 Sincronizar periodo de Quiter

Esta opcion sirve cuando el archivo de Quiter representa la foto completa del periodo seleccionado.

Si esta activa, la app:

1. toma los movimientos de Quiter del periodo seleccionado;
2. compara la base actual contra el nuevo archivo;
3. elimina de la base los asientos que ya no aparecen en el nuevo mayor.

Sirve para limpiar asientos corregidos o eliminados en Quiter.

### 5.9 Cuidado con la sincronizacion

Usar sincronizacion solo cuando el archivo contiene todo el periodo seleccionado.

Ejemplo correcto:

- Archivo: 10/05/2026 al 14/05/2026.
- Rango en app: 10/05/2026 al 14/05/2026.

Ejemplo riesgoso:

- Archivo: 10/05/2026 al 14/05/2026.
- Rango en app: 01/05/2026 al 14/05/2026.

En el caso riesgoso, la app podria eliminar asientos del 01/05 al 09/05 porque no aparecen en el archivo cargado.

### 5.10 Recalcular conciliacion contable

El boton **Recalcular conciliacion contable** recalcula la base ya cargada sin importar archivos nuevos.

Usarlo cuando:

- se quiere refrescar el resultado;
- se importaron datos y se desea recalcular;
- se aplico una nueva regla de conciliacion.

### 5.11 Metricas principales

El modulo muestra:

- **Conciliados**
  - movimientos que encontraron coincidencia.

- **Total conciliado**
  - importe total conciliado.

- **Pendientes portal**
  - movimientos de Habitualista sin match en Quiter.

- **Pendientes Quiter**
  - movimientos de Quiter sin match en Habitualista.

### 5.12 Solapas del modulo contable

#### Resumen

Muestra por tipo de movimiento:

- cantidad e importe en portal;
- cantidad e importe en Quiter;
- cantidad e importe conciliado;
- pendientes portal;
- pendientes Quiter.

#### Conciliados

Muestra los movimientos conciliados y contra que movimiento fueron conciliados.

Columnas clave:

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

La columna `descripcion_origen` muestra el movimiento de Habitualista.

La columna `descripcion_conciliada` muestra el movimiento de Quiter contra el que fue matcheado.

Esta solapa permite auditar visualmente cada cruce.

#### Pendientes portal

Movimientos de Habitualista que no tienen coincidencia en Quiter.

Puede indicar:

- pago sin contabilizar;
- deposito sin registrar;
- diferencia de importe;
- diferencia de fecha fuera de tolerancia;
- mayor de Quiter incompleto.

#### Pendientes Quiter

Movimientos de Quiter que no tienen coincidencia en Habitualista.

Puede indicar:

- asiento duplicado;
- importe incorrecto;
- movimiento sin respaldo;
- reporte de Habitualista incompleto;
- periodo mal seleccionado.

#### Base portal

Base acumulada de movimientos de Habitualista.

Incluye:

- operaciones de pago;
- depositos CREDIT;
- archivo de origen;
- fila de origen;
- match encontrado.

#### Base Quiter

Base acumulada del mayor contable de Quiter.

Incluye:

- fecha;
- debe/haber interpretado como deposito o pago;
- importe;
- descripcion;
- archivo de origen;
- fila de origen;
- match encontrado.

#### Importaciones

Historial de cargas contables.

Incluye:

- fecha;
- archivos importados;
- portal insertados;
- portal actualizados;
- Quiter insertados;
- Quiter actualizados;
- Quiter eliminados por sincronizacion.

### 5.13 Descarga Excel contable

El boton **Descargar reporte contable consolidado Excel** genera un archivo con:

- Resumen
- Conciliados
- Pendientes portal
- Pendientes Quiter
- Base portal
- Base Quiter
- Importaciones

---

## 6. Historial

### 6.1 Objetivo

El modulo **Historial** concentra descargas y registros de importacion.

No se usa para importar archivos. Se usa para consultar y descargar.

### 6.2 Descargas superiores

El modulo muestra dos descargas:

1. **Descargar consolidado pagos y ventas**
   - Exporta el estado vigente de la conciliacion de pagos y ventas.

2. **Descargar consolidado contable**
   - Exporta el estado vigente de la conciliacion contable.

### 6.3 Solapas visibles

#### Importaciones pagos y ventas

Muestra el historial de importaciones de pagos y ventas:

- fecha;
- archivos de pagos;
- archivos de ventas;
- registros insertados;
- registros actualizados.

#### Importaciones contables

Muestra el historial de importaciones contables:

- fecha;
- archivos de pagos;
- archivos de movimientos de cuenta;
- archivos de Quiter;
- registros insertados;
- registros actualizados;
- registros eliminados por sincronizacion.

---

## 7. Backups

### 7.1 Objetivo

El modulo **Backups** permite crear y restaurar copias de seguridad.

### 7.2 Crear backup

1. Entrar a **Backups**.
2. Presionar **Crear backup ahora**.
3. Descargar el ZIP generado si se quiere conservar una copia externa.

### 7.3 Restaurar backup

1. Entrar a **Backups**.
2. Subir el ZIP de backup.
3. Marcar la confirmacion.
4. Presionar **Restaurar backup**.
5. Recargar la aplicacion.

### 7.4 Importante

En Streamlit Cloud se recomienda usar Neon para que la base sea persistente.

Los backups locales sirven principalmente cuando se usa almacenamiento local.

---

## 8. Persistencia de datos

### 8.1 En Streamlit Cloud

Para persistencia real se recomienda usar Neon/PostgreSQL.

En Streamlit Cloud configurar:

```toml
DATABASE_URL = "postgresql://usuario:password@host.neon.tech/dbname?sslmode=require"
```

Luego reiniciar la app.

### 8.2 En uso local

Si no hay `DATABASE_URL`, la app usa SQLite local en la carpeta:

```text
data/
```

---

## 9. Formato de importes

Los importes se muestran en formato pesos:

```text
$ 1.234.567,89
```

Los numeros que no representan dinero se muestran en formato general.

---

## 10. Recomendaciones de uso

### 10.1 Pagos y ventas

- Cargar pagos y ventas de un periodo amplio al iniciar.
- Importar ventas 0 km y usados si estan en archivos separados.
- Revisar pagos no conciliados.
- Revisar ventas sin pago.
- Descargar el consolidado luego de cada cierre.

### 10.2 Contabilidad

- Cargar operaciones de pago, movimientos de cuenta y mayor de Quiter.
- Controlar bien el rango Desde/Hasta de Quiter.
- Usar sincronizacion solo si el archivo de Quiter cubre todo el periodo seleccionado.
- Revisar pendientes portal y pendientes Quiter.
- Usar la solapa Conciliados para ver descripcion origen contra descripcion conciliada.
- Descargar el consolidado contable luego de cada revision.

### 10.3 Seguridad de datos

- Usar Neon en Streamlit Cloud.
- Descargar reportes consolidados periodicamente.
- Crear backups antes de cambios importantes si se trabaja localmente.

---

## 11. Cierre recomendado de una revision

1. Importar los archivos correspondientes.
2. Revisar metricas.
3. Revisar pendientes.
4. Corregir reportes o datos si corresponde.
5. Reimportar archivos corregidos.
6. Descargar el reporte consolidado.
7. Guardar el Excel como respaldo.
