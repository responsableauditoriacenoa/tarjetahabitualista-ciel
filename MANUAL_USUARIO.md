# Manual de Usuario

## Sistema de Conciliacion Tarjeta Habitualista CIEL

Este manual explica la version actual de la aplicacion, con ejemplos practicos de como la app interpreta los datos y como debe leerlos el usuario.

Modulos vigentes:

- Conciliacion de Pagos y Ventas
- Conciliacion Contable de Tarjeta Habitualista S/ Contabilidad
- Historial
- Backups

---

## 1. Idea general de la aplicacion

La app sirve para cargar reportes, detectar coincidencias entre archivos y guardar reportes de conciliacion.

En **Conciliacion de Pagos y Ventas**, la app mantiene una base consolidada acumulativa.

En **Conciliacion Contable**, la app trabaja por corrida: concilia solamente los archivos subidos en ese momento y guarda el resultado en historial.

### Ejemplo practico

En Pagos y Ventas, el lunes se cargan pagos y ventas de enero a abril.

El viernes se carga otro reporte que contiene abril y mayo.

La app:

- no duplica abril;
- actualiza abril si encuentra datos mas completos;
- agrega mayo;
- recalcula la conciliacion total.

### Como debe leerlo el usuario

En Pagos y Ventas, el usuario debe pensar que la app construye una base historica.

En Contabilidad, el usuario debe pensar que cada importacion genera una conciliacion nueva e independiente, guardada en historial.

---

## 2. Menu principal

El menu lateral muestra cuatro modulos.

### Conciliacion de Pagos y Ventas

Sirve para controlar si los pagos realizados con Tarjeta Habitualista corresponden a ventas.

### Conciliacion Contable de Tarjeta Habitualista S/ Contabilidad

Sirve para controlar si los pagos y depositos informados por Tarjeta Habitualista estan registrados en la contabilidad de Quiter.

### Historial

Sirve para consultar importaciones y descargar los reportes consolidados actuales.

### Backups

Sirve para crear o restaurar copias de seguridad.

---

## 3. Conciliacion de Pagos y Ventas

## 3.1 Para que sirve

Este modulo cruza:

- Operaciones de pago de Tarjeta Habitualista.
- Reportes de ventas.

El objetivo es saber que pagos se relacionan con ventas y cuales quedan pendientes de revision.

### Ejemplo practico

Un gestor paga una operacion por Tarjeta Habitualista. En el reporte de pagos aparece:

```text
OP 4282962 TRANSFERENCIA POBLETE JORGE REF.4287418
```

En el reporte de ventas aparece:

| Referencia venta | Cliente |
| --- | --- |
| 4282962 | POBLETE CIRIANNI JORGE AGUSTIN |

La app detecta que la OP del pago coincide con la referencia de venta. Entonces marca el pago como conciliado.

### Como debe leerlo el usuario

El usuario debe revisar si el pago que aparece como conciliado corresponde realmente a la venta que muestra el sistema.

La tabla de conciliados muestra el pago y la venta encontrada.

---

## 3.2 Archivos que se cargan

El modulo tiene dos cargas.

### Operaciones de pago

Es el archivo descargado desde Tarjeta Habitualista. Contiene los pagos realizados por gestores.

La app toma datos como:

- fecha del pago;
- numero de pago;
- importe;
- descripcion;
- OP detectada en el texto;
- REF detectada en el texto.

### Reportes de ventas

Son los archivos de ventas. Se puede subir mas de un archivo en la misma importacion.

Ejemplo:

- ventas 0 km;
- ventas usados.

La app toma datos como:

- referencia de venta;
- cliente;
- vendedor;
- modelo;
- saldo;
- fechas de venta o entrega;
- IDV;
- matricula.

---

## 3.3 Como hacer una carga

1. Entrar a **Conciliacion de Pagos y Ventas**.
2. Subir el archivo de **Operaciones de pago**.
3. Subir uno o varios **Reportes de ventas**.
4. Presionar **Importar y recalcular base**.
5. Esperar el mensaje de confirmacion.
6. Revisar las metricas.
7. Revisar las solapas.
8. Descargar el Excel si se necesita respaldar la revision.

### Ejemplo practico

Se cargan:

- `Operaciones de pago enero a mayo.xlsx`
- `Ventas 0km enero a mayo.xls`
- `Ventas usados enero a mayo.xls`

La app importa los tres archivos, une ventas 0 km y usados en una sola base y cruza todos los pagos contra todas las ventas.

### Como debe leerlo el usuario

Si despues se carga otro archivo de ventas, la app no reinicia todo. Lo suma a la base y vuelve a recalcular.

---

## 3.4 Que pasa si cargo datos repetidos

Si se carga un reporte con un periodo que ya estaba importado, la app no duplica registros.

### Ejemplo practico

Ya estaba cargado abril.

Luego se importa un reporte de pagos desde el 15/04 al 15/05.

La app:

- reconoce pagos de abril ya cargados;
- actualiza esos pagos si corresponde;
- agrega los pagos nuevos de mayo;
- recalcula el cruce total.

### Como debe leerlo el usuario

No hay problema en importar periodos superpuestos. Es preferible eso antes que dejar informacion incompleta.

---

## 3.5 Como hace el cruce de pagos con ventas

La app intenta encontrar una venta para cada pago. Lo hace en este orden:

1. OP del pago = referencia de venta.
2. REF del pago = referencia de venta.
3. Numero dentro de la descripcion del pago = referencia de venta.
4. Cliente de la venta encontrado en la descripcion del pago.

---

## 3.5.1 Ejemplo: OP del pago = referencia de venta

Pago:

```text
OP 4282962 TRANSFERENCIA POBLETE JORGE REF.4287418
```

La app extrae:

```text
OP del pago = 4282962
REF del pago = 4287418
```

Venta:

| Referencia venta | Cliente |
| --- | --- |
| 4282962 | POBLETE CIRIANNI JORGE AGUSTIN |

Resultado:

```text
OP del pago = Refer. venta
```

### Como debe leerlo el usuario

El pago se concilio porque la OP `4282962` coincide con la referencia de venta `4282962`.

Aunque el pago tenga tambien `REF.4287418`, la app primero prueba con la OP.

---

## 3.5.2 Ejemplo: REF del pago = referencia de venta

Pago:

```text
TRANSFERENCIA CLIENTE GOMEZ REF.5012345
```

La app extrae:

```text
REF del pago = 5012345
```

Venta:

| Referencia venta | Cliente |
| --- | --- |
| 5012345 | GOMEZ MARIA |

Resultado:

```text
REF del pago = Refer. venta
```

### Como debe leerlo el usuario

El pago no se pudo conciliar por OP, pero si por REF. La referencia del pago coincide con la referencia de la venta.

---

## 3.5.3 Ejemplo: numero en descripcion = referencia de venta

Pago:

```text
TRANSFERENCIA UNIDAD 4282962 POBLETE
```

La app detecta el numero:

```text
4282962
```

Venta:

| Referencia venta | Cliente |
| --- | --- |
| 4282962 | POBLETE CIRIANNI JORGE AGUSTIN |

Resultado:

```text
Numero en descripcion del pago = Refer. venta
```

### Como debe leerlo el usuario

El texto no tenia OP ni REF formal, pero tenia un numero que coincide con una referencia de venta.

---

## 3.5.4 Ejemplo: cliente encontrado en descripcion

Pago:

```text
TRANSFERENCIA POBLETE CIRIANNI JORGE AGUSTIN
```

Venta:

| Referencia venta | Cliente |
| --- | --- |
| 4282962 | POBLETE CIRIANNI JORGE AGUSTIN |

Resultado:

```text
Cliente de venta encontrado en descripcion del pago
```

### Como debe leerlo el usuario

La app no encontro una referencia clara, pero encontro el nombre del cliente. Este criterio debe revisarse con mas cuidado porque es menos exacto que una referencia numerica.

---

## 3.6 Metricas de Pagos y Ventas

### Pagos conciliados

Cantidad de pagos que encontraron una venta.

Ejemplo:

```text
Pagos conciliados: 40
```

Significa que 40 pagos fueron asociados a ventas.

### Total conciliado

Suma de los importes de pagos conciliados.

Ejemplo:

```text
Total conciliado: $ 120.000.000,00
```

Significa que ese es el total de dinero de pagos que la app pudo relacionar con ventas.

### Pagos no conciliados

Pagos que no encontraron venta.

Ejemplo:

```text
Pagos no conciliados: 8
```

El usuario debe revisar esos 8 pagos.

Posibles causas:

- la venta todavia no fue importada;
- la referencia esta mal escrita;
- el pago no corresponde a una venta;
- falta informacion en la descripcion.

### Ventas sin pago

Ventas que no tienen pago detectado.

Posibles causas:

- el pago todavia no fue importado;
- la venta fue pagada por otro medio;
- la referencia de venta no aparece en el pago;
- no corresponde pago por Tarjeta Habitualista.

---

## 3.7 Solapas de Pagos y Ventas

### Resumen

Muestra totales agrupados.

Ejemplo de lectura:

Si dice:

```text
Pagos en base: 100
Pagos conciliados con ventas: 80
Pagos no conciliados: 20
```

Entonces el usuario sabe que de 100 pagos importados, 80 encontraron venta y 20 deben revisarse.

### Pagos conciliados

Muestra el detalle de pagos que encontraron venta.

Se debe revisar:

- descripcion del pago;
- referencia de venta;
- cliente;
- criterio de conciliacion.

### Pagos no conciliados

Muestra pagos sin venta encontrada.

Ejemplo:

```text
Motivo revision: OP no encontrado en ventas
Descripcion: OP 4282962 TRANSFERENCIA POBLETE
```

Lectura:

La app detecto una OP, pero no encontro esa OP como referencia en ventas. Puede faltar importar el reporte de ventas correcto o puede haber diferencia en la referencia.

### Ventas sin pago

Muestra ventas que no fueron relacionadas con ningun pago.

Lectura:

Si aparece una venta en esta solapa, el usuario debe verificar si el pago existe, si fue por otro medio o si todavia no fue cargado.

### Base pagos

Muestra todos los pagos importados.

Sirve para auditar si un pago existe en la base.

### Base ventas

Muestra todas las ventas importadas.

Sirve para auditar si una venta existe en la base.

### Importaciones

Muestra cada carga realizada.

Ejemplo de lectura:

```text
pagos_insertados: 20
pagos_actualizados: 5
ventas_insertadas: 10
ventas_actualizadas: 2
```

Significa que la importacion agrego 20 pagos nuevos, actualizo 5 pagos existentes, agrego 10 ventas nuevas y actualizo 2 ventas ya cargadas.

---

## 4. Conciliacion Contable de Tarjeta Habitualista S/ Contabilidad

## 4.1 Para que sirve

Este modulo cruza Tarjeta Habitualista contra Quiter.

Compara:

- pagos de Tarjeta Habitualista contra movimientos al Haber de Quiter;
- depositos de Tarjeta Habitualista contra movimientos al Debe de Quiter.

La conciliacion contable trabaja **por corrida**. Esto quiere decir que cada vez que se suben archivos, la app concilia solamente esos archivos.

El resultado se guarda en historial para poder descargarlo luego.

### Ejemplo practico

Se cargan archivos de mayo y se ejecuta la conciliacion.

La app muestra mayo y guarda el reporte de mayo en historial.

Luego se cargan archivos de junio y se ejecuta otra conciliacion.

La pantalla pasa a mostrar junio, pero mayo sigue disponible para descargar desde historial.

---

## 4.2 Como interpreta cada archivo

### Operaciones de pago

La app interpreta cada operacion de pago como un **pago**.

### Movimientos de cuenta

La app toma solamente movimientos tipo `CREDIT`.

Cada `CREDIT` se interpreta como **deposito**.

### Contabilidad Quiter

La app interpreta:

- Debe = deposito;
- Haber = pago.

### Ejemplo practico

Habitualista movimientos de cuenta:

| Tipo | Monto |
| --- | --- |
| CREDIT | 10.000.000 |

Quiter:

| Debe | Haber |
| --- | --- |
| 10.000.000 | 0 |

La app entiende que ambos son depositos por el mismo importe y puede conciliarlos.

---

## 4.3 Como se carga

1. Entrar a **Conciliacion Contable de Tarjeta Habitualista S/ Contabilidad**.
2. Subir **Operaciones de pago**.
3. Subir **Movimientos de cuenta**.
4. Subir **Contabilidad Quiter**.
5. Si hace falta limitar el mayor, activar **Filtrar Quiter por rango de fechas**.
6. Si el filtro esta activo, seleccionar **Desde Quiter** y **Hasta Quiter**.
7. Definir la tolerancia de dias.
8. Presionar **Conciliar archivos y guardar historial**.

### Como debe leerlo el usuario

Los archivos cargados en esa corrida son el universo completo de conciliacion.

Si el filtro de fechas de Quiter esta desactivado, la app toma todos los movimientos del mayor importado.

Si el filtro esta activado, la app toma solamente los movimientos de Quiter dentro del rango seleccionado.

Ejemplo:

Si se carga un mayor 2025 pero el filtro esta activo con fechas 2026, Quiter queda en cero movimientos. Para conciliar todo 2025, el filtro debe estar desactivado o configurado desde 01/01/2025 hasta 31/12/2025.

---

## 4.4 Como hace el cruce contable

La conciliacion contable no usa OP ni referencia.

La regla es:

```text
tipo + importe
```

Si hay mas de un candidato con el mismo importe, usa cercania de fecha.

---

## 4.4.1 Ejemplo: pago por importe unico

Habitualista:

| Tipo | Fecha | Importe | Descripcion |
| --- | --- | --- | --- |
| pago | 10/05/2026 | 500.000 | Pago gestor |

Quiter:

| Tipo | Fecha | Importe | Descripcion |
| --- | --- | --- | --- |
| pago | 10/05/2026 | 500.000 | Asiento contable |

Resultado:

```text
Contable: tipo + importe unico
```

### Como debe leerlo el usuario

La app encontro un solo pago en Quiter por el mismo importe. Por eso lo concilia.

---

## 4.4.2 Ejemplo: varios importes iguales y fecha cercana

Habitualista:

| Tipo | Fecha | Importe |
| --- | --- | --- |
| pago | 10/05/2026 | 500.000 |

Quiter:

| Tipo | Fecha | Importe |
| --- | --- | --- |
| pago | 02/05/2026 | 500.000 |
| pago | 11/05/2026 | 500.000 |

Tolerancia:

```text
3 dias
```

Resultado:

La app elige el movimiento del 11/05/2026 porque esta a 1 dia de diferencia.

Criterio:

```text
Contable: tipo + importe + fecha +/- 3 dias
```

### Como debe leerlo el usuario

Cuando hay importes repetidos, la fecha ayuda a elegir el candidato mas razonable.

---

## 4.4.3 Ejemplo: queda pendiente por fecha fuera de tolerancia

Habitualista:

| Tipo | Fecha | Importe |
| --- | --- | --- |
| pago | 10/05/2026 | 500.000 |

Quiter:

| Tipo | Fecha | Importe |
| --- | --- | --- |
| pago | 20/05/2026 | 500.000 |

Tolerancia:

```text
3 dias
```

Resultado:

El movimiento queda pendiente porque la diferencia es de 10 dias.

### Como debe leerlo el usuario

Debe revisarse si la fecha contable esta mal, si el movimiento corresponde a otro pago o si falta cargar un archivo.

---

## 4.5 Por que no usa OP ni referencia en contabilidad

En pagos y ventas, la OP puede coincidir con la referencia de venta.

En contabilidad eso no aplica.

La OP o referencia de Quiter puede ser:

- un numero interno;
- un codigo de asiento;
- un dato distinto al de Habitualista.

Por eso, para contabilidad se cruza por importe, tipo y fecha.

---

## 4.6 Historial de conciliaciones contables

Cada vez que se presiona **Conciliar archivos y guardar historial**, la app guarda un reporte historico.

Ese historial conserva el Excel de la corrida.

### Ejemplo practico

El usuario ejecuta tres conciliaciones:

- mayo;
- junio;
- julio.

La pantalla principal muestra la ultima conciliacion ejecutada.

Pero desde **Historial guardado** se puede descargar nuevamente mayo, junio o julio.

### Como debe leerlo el usuario

La app ya no acumula indefinidamente una base contable. Cada cierre queda como una conciliacion independiente guardada.

---

## 4.7 Solapas contables

### Resumen

Muestra depositos y pagos separados.

Ejemplo:

```text
tipo: pago
portal_cantidad: 100
quiter_cantidad: 98
conciliados_cantidad: 90
pendientes_portal_cantidad: 10
pendientes_quiter_cantidad: 8
```

Lectura:

Hay 100 pagos en Habitualista, 98 pagos en Quiter, 90 conciliados, 10 pendientes del lado Habitualista y 8 pendientes del lado Quiter.

### Conciliados

Muestra contra que movimiento se matcheo cada registro.

Columnas clave:

- `descripcion_origen`
- `descripcion_conciliada`
- `fecha_origen`
- `fecha_conciliada`
- `archivo_origen`
- `archivo_conciliado`

Ejemplo de lectura:

```text
descripcion_origen: OP 4282962 TRANSFERENCIA
descripcion_conciliada: ASIENTO HABITUALISTA MAYOR QUITER
```

Significa que ese pago de Habitualista fue conciliado contra ese asiento de Quiter.

### Pendientes portal

Movimientos que estan en Habitualista pero no tienen match en Quiter.

Puede indicar:

- falta contabilizar;
- diferencia de importe;
- fecha fuera de tolerancia;
- archivo de Quiter incompleto.

### Pendientes Quiter

Movimientos que estan en Quiter pero no tienen match en Habitualista.

Puede indicar:

- asiento duplicado;
- asiento mal cargado;
- falta importar Habitualista;
- periodo mal seleccionado.

### Base portal

Movimientos de Habitualista importados en la conciliacion actual.

### Base Quiter

Movimientos de Quiter importados en la conciliacion actual.

### Historial guardado

Listado de conciliaciones contables guardadas.

Desde esta solapa se puede seleccionar una conciliacion anterior y descargar su Excel.

---

## 5. Historial

El modulo **Historial** no importa archivos. Sirve para consultar y descargar.

### Descargas superiores

Tiene dos botones:

- Descargar consolidado pagos y ventas.
- Descargar ultima conciliacion contable visible.

### Ejemplo practico

Despues de cerrar una revision mensual, el usuario entra a Historial y descarga el consolidado de pagos y ventas o la conciliacion contable guardada que corresponda.

### Solapa Importaciones pagos y ventas

Muestra que archivos se cargaron y cuantos registros se insertaron o actualizaron.

### Solapa Importaciones contables

Muestra que archivos contables se cargaron en cada corrida.

### Solapa Conciliaciones contables guardadas

Permite seleccionar una conciliacion contable historica y descargar su Excel.

---

## 6. Backups

El modulo **Backups** permite guardar o restaurar copias.

### Crear backup

1. Entrar a **Backups**.
2. Presionar **Crear backup ahora**.
3. Descargar el ZIP si se quiere guardar una copia externa.

### Restaurar backup

1. Entrar a **Backups**.
2. Subir el ZIP.
3. Marcar la confirmacion.
4. Presionar **Restaurar backup**.
5. Recargar la app.

### Ejemplo practico

Antes de hacer una carga grande, el usuario genera un backup. Si algo sale mal, puede restaurar la copia anterior.

---

## 7. Persistencia de datos

En Streamlit Cloud se recomienda usar Neon.

Si la app tiene configurado `DATABASE_URL`, guarda los datos en Neon.

Si no tiene `DATABASE_URL`, usa una base local en `data/`.

### Ejemplo practico

Si Streamlit se reinicia y no se usa Neon, los datos locales pueden perderse.

Con Neon, la base permanece aunque la app se reinicie.

---

## 8. Recomendacion de cierre

Para cerrar una revision:

1. Importar archivos.
2. Revisar metricas.
3. Revisar pendientes.
4. Corregir o completar reportes si corresponde.
5. Reimportar.
6. Descargar consolidado.
7. Guardar Excel como respaldo.
8. Generar backup si corresponde.
