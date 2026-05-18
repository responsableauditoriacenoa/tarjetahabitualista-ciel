# Conciliacion Tarjeta Habitualista

Herramienta para conciliar los reportes reales de Tarjeta Habitualista contra la contabilidad de Quiter.

## Aplicacion local

La forma recomendada de uso es con Streamlit:

```powershell
pip install -r requirements.txt
streamlit run app.py
```

## Persistencia en Neon

Para Streamlit Cloud se recomienda usar Neon/PostgreSQL como base persistente.

En Streamlit Cloud, ir a:

```text
App > Settings > Secrets
```

Y agregar:

```toml
DATABASE_URL = "postgresql://usuario:password@host.neon.tech/dbname?sslmode=require"
```

Si `DATABASE_URL` no esta configurado, la app usa SQLite local en `data/`.

La app permite:

- Importar los tres reportes.
- Ejecutar la conciliacion.
- Ver resumen, conciliados y no conciliados en pantalla.
- Descargar el reporte de conciliacion en Excel.
- Consultar conciliaciones anteriores desde el historial.
- En el modulo `Pagos vs ventas`, reutilizar operaciones de pago ya guardadas y subir solo un nuevo reporte de ventas.
- En el modulo `Base consolidada`, importar incrementalmente operaciones de pago y multiples reportes de ventas, actualizar duplicados y descargar un reporte total consolidado.
- En el modulo `Base contable`, importar incrementalmente operaciones de pago, movimientos de cuenta y Quiter, actualizar duplicados y descargar un reporte contable consolidado.
- En `Base contable`, la opcion `Sincronizar periodo de Quiter` elimina de la base los asientos del periodo seleccionado que ya no aparezcan en el nuevo mayor importado.

Los datos quedan persistidos localmente en `data/`:

- `data/conciliaciones.sqlite3`: historial y metadatos.
- `data/uploads/`: archivos importados por corrida.
- `data/reports/`: Excel y tablas generadas por corrida.

## Criterio contable

En Quiter la cuenta funciona como un pasivo:

- Los depositos se registran en el **Debe**.
- Los pagos realizados con Tarjeta Habitualista se registran en el **Haber**.

La conciliacion compara los movimientos reales del reporte de Tarjeta Habitualista contra el mayor contable de Quiter y separa:

- Movimientos conciliados.
- Movimientos que existen solo en Tarjeta Habitualista.
- Movimientos que existen solo en Quiter.

## Reportes de entrada

El sistema lee directamente:

- `Movimientos de cuenta`: se toman solo movimientos `CREDIT`, que representan depositos realizados a la cuenta.
- `Operaciones de pago`: se toman pagos liquidados realizados por los gestores.
- `LSTEXT...xls` de Quiter: los movimientos al `Debe` se interpretan como depositos y los movimientos al `Haber` como pagos.

## Uso

Tambien se puede ejecutar por linea de comandos:

```powershell
python conciliacion.py `
  --movimientos-cuenta "C:\Users\Usuario\Downloads\Movimientos de cuenta (2026-04-01 - 2026-04-30).xlsx" `
  --operaciones-pago "C:\Users\Usuario\Downloads\Operaciones de pago (2026-04-01 - 2026-04-30) (2).xlsx" `
  --quiter "C:\Users\Usuario\Desktop\LSTEXT_lpalacios1061_1_21131011_36148-2026-05-11.xls" `
  --salida reporte_conciliacion.xlsx
```

## Reglas iniciales de conciliacion

1. Depositos: `CREDIT` de Habitualista contra `Debe` de Quiter.
2. Pagos: Operaciones de Pago contra `Haber` de Quiter.
3. En pagos primero cruza por `OP + importe`.
4. Si no hay `OP`, cruza por `REF/Nro.docum + importe`.
5. Como respaldo usa `importe unico` o `importe + fecha` dentro de una tolerancia configurable.
6. Todo lo que no se encuentra conciliado queda en la hoja `No conciliados`.

## Salida

El archivo Excel generado contiene:

- `Resumen`: cantidades e importes conciliados y pendientes.
- `Conciliados`: detalle de movimientos cruzados.
- `No conciliados`: tabla para revision manual.
