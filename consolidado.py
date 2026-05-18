from __future__ import annotations

import json
import re
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pandas as pd

from pagos_ventas import (
    VentaOperacion,
    cargar_pagos,
    cargar_ventas,
    cliente_en_descripcion,
    decimal_a_float,
    extraer_referencias_numericas,
    normalizar_importe,
    referencias_posibles_pago,
)
from storage import DB_PATH, REPORTS_DIR, UPLOADS_DIR, conectar, guardar_upload, inicializar_storage


CONSOLIDADO_UPLOADS_DIR = UPLOADS_DIR / "base_consolidada"
CONSOLIDADO_REPORTS_DIR = REPORTS_DIR / "base_consolidada"


def inicializar_base_consolidada() -> None:
    inicializar_storage()
    CONSOLIDADO_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    CONSOLIDADO_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with conectar() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS base_pagos (
                pago_key TEXT PRIMARY KEY,
                fecha_pago TEXT,
                nro_pago TEXT,
                importe_pago REAL,
                op_pago TEXT,
                ref_pago TEXT,
                descripcion_pago TEXT,
                fila_origen INTEGER,
                archivo_origen TEXT,
                creado_en TEXT NOT NULL,
                actualizado_en TEXT NOT NULL,
                matched_venta_key TEXT,
                criterio TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS base_ventas (
                venta_key TEXT PRIMARY KEY,
                refer_venta TEXT,
                idv TEXT,
                matricula TEXT,
                cuenta_facturacion TEXT,
                cliente TEXT,
                vendedor TEXT,
                modelo TEXT,
                saldo_venta REAL,
                fecha_matricula TEXT,
                fecha_factura TEXT,
                fecha_entrega TEXT,
                fila_origen INTEGER,
                archivo_origen TEXT,
                creado_en TEXT NOT NULL,
                actualizado_en TEXT NOT NULL,
                matched_pago_keys TEXT,
                criterio TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS base_importaciones (
                id TEXT PRIMARY KEY,
                fecha TEXT NOT NULL,
                pagos_archivos TEXT NOT NULL,
                ventas_archivos TEXT NOT NULL,
                pagos_insertados INTEGER NOT NULL,
                pagos_actualizados INTEGER NOT NULL,
                ventas_insertadas INTEGER NOT NULL,
                ventas_actualizadas INTEGER NOT NULL
            )
            """
        )


def valor_no_vacio(valor: object) -> bool:
    if valor is None:
        return False
    if pd.isna(valor):
        return False
    return str(valor).strip() != ""


def merge_dict(existente: dict, nuevo: dict) -> dict:
    salida = dict(existente)
    for clave, valor in nuevo.items():
        if clave in {"pago_key", "venta_key", "creado_en"}:
            continue
        if valor_no_vacio(valor):
            salida[clave] = valor
    return salida


def pago_a_registro(pago, archivo: Path) -> dict:
    fecha = pago.fecha.isoformat() if pago.fecha else ""
    importe = decimal_a_float(pago.total)
    pago_key = pago.nro_pago or f"{pago.op}|{pago.referencia}|{fecha}|{importe:.2f}"
    ahora = datetime.now().isoformat(timespec="seconds")
    return {
        "pago_key": pago_key,
        "fecha_pago": fecha,
        "nro_pago": pago.nro_pago,
        "importe_pago": importe,
        "op_pago": pago.op,
        "ref_pago": pago.referencia,
        "descripcion_pago": pago.descripcion,
        "fila_origen": pago.fila,
        "archivo_origen": archivo.name,
        "creado_en": ahora,
        "actualizado_en": ahora,
        "matched_venta_key": "",
        "criterio": "",
    }


def venta_a_registro(venta: VentaOperacion, archivo: Path) -> dict:
    venta_key = "|".join(
        parte
        for parte in (venta.referencia, venta.idv, venta.matricula)
        if parte
    )
    if not venta_key:
        venta_key = f"{venta.referencia}|{venta.cliente}|{venta.modelo}"

    ahora = datetime.now().isoformat(timespec="seconds")
    return {
        "venta_key": venta_key,
        "refer_venta": venta.referencia,
        "idv": venta.idv,
        "matricula": venta.matricula,
        "cuenta_facturacion": venta.cuenta_facturacion,
        "cliente": venta.cliente,
        "vendedor": venta.vendedor,
        "modelo": venta.modelo,
        "saldo_venta": decimal_a_float(venta.saldo),
        "fecha_matricula": venta.fecha_matricula.isoformat() if venta.fecha_matricula else "",
        "fecha_factura": venta.fecha_factura.isoformat() if venta.fecha_factura else "",
        "fecha_entrega": venta.fecha_entrega.isoformat() if venta.fecha_entrega else "",
        "fila_origen": venta.fila,
        "archivo_origen": archivo.name,
        "creado_en": ahora,
        "actualizado_en": ahora,
        "matched_pago_keys": "",
        "criterio": "",
    }


def upsert_registro(tabla: str, key_col: str, registro: dict) -> str:
    with conectar() as conn:
        existente_row = conn.execute(
            f"SELECT * FROM {tabla} WHERE {key_col} = ?",
            (registro[key_col],),
        ).fetchone()
        columnas = [row[1] for row in conn.execute(f"PRAGMA table_info({tabla})").fetchall()]

        if existente_row:
            existente = dict(zip(columnas, existente_row))
            combinado = merge_dict(existente, registro)
            combinado["creado_en"] = existente["creado_en"]
            combinado["actualizado_en"] = datetime.now().isoformat(timespec="seconds")
            set_clause = ", ".join(f"{col} = ?" for col in columnas if col != key_col)
            valores = [combinado[col] for col in columnas if col != key_col]
            valores.append(registro[key_col])
            conn.execute(
                f"UPDATE {tabla} SET {set_clause} WHERE {key_col} = ?",
                valores,
            )
            return "actualizado"

        placeholders = ", ".join("?" for _ in columnas)
        conn.execute(
            f"INSERT INTO {tabla} ({', '.join(columnas)}) VALUES ({placeholders})",
            [registro.get(col, "") for col in columnas],
        )
        return "insertado"


def importar_a_base(
    pagos_files,
    ventas_files,
) -> dict:
    inicializar_base_consolidada()
    corrida_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid4().hex[:8]
    carpeta = CONSOLIDADO_UPLOADS_DIR / corrida_id
    carpeta.mkdir(parents=True, exist_ok=True)

    pagos_paths = [guardar_upload(file, carpeta / file.name) for file in pagos_files]
    ventas_paths = [guardar_upload(file, carpeta / file.name) for file in ventas_files]

    stats = {
        "pagos_insertados": 0,
        "pagos_actualizados": 0,
        "ventas_insertadas": 0,
        "ventas_actualizadas": 0,
        "pagos_archivos": [path.name for path in pagos_paths],
        "ventas_archivos": [path.name for path in ventas_paths],
    }

    for path in pagos_paths:
        for pago in cargar_pagos(path):
            estado = upsert_registro("base_pagos", "pago_key", pago_a_registro(pago, path))
            stats[f"pagos_{estado}s"] += 1

    for path in ventas_paths:
        for venta in cargar_ventas(path):
            estado = upsert_registro("base_ventas", "venta_key", venta_a_registro(venta, path))
            if estado == "insertado":
                stats["ventas_insertadas"] += 1
            else:
                stats["ventas_actualizadas"] += 1

    reconciliar_base()
    registrar_importacion(corrida_id, stats)
    return stats


def registrar_importacion(corrida_id: str, stats: dict) -> None:
    with conectar() as conn:
        conn.execute(
            """
            INSERT INTO base_importaciones (
                id, fecha, pagos_archivos, ventas_archivos,
                pagos_insertados, pagos_actualizados,
                ventas_insertadas, ventas_actualizadas
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                corrida_id,
                datetime.now().isoformat(timespec="seconds"),
                json.dumps(stats["pagos_archivos"], ensure_ascii=False),
                json.dumps(stats["ventas_archivos"], ensure_ascii=False),
                stats["pagos_insertados"],
                stats["pagos_actualizados"],
                stats["ventas_insertadas"],
                stats["ventas_actualizadas"],
            ),
        )


def cargar_tabla(tabla: str) -> pd.DataFrame:
    inicializar_base_consolidada()
    with conectar() as conn:
        return conn.read_sql(f"SELECT * FROM {tabla}")


def referencias_pago(row: pd.Series) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    for valor, origen in (
        (row.get("op_pago", ""), "OP del pago"),
        (row.get("ref_pago", ""), "REF del pago"),
    ):
        if valor and (str(valor), origen) not in refs:
            refs.append((str(valor), origen))

    for numero in extraer_referencias_numericas(row.get("descripcion_pago", "")):
        item = (numero, "Numero en descripcion del pago")
        if item not in refs:
            refs.append(item)
    return refs


def reconciliar_base() -> None:
    pagos = cargar_tabla("base_pagos")
    ventas = cargar_tabla("base_ventas")

    if pagos.empty:
        return

    pagos["matched_venta_key"] = ""
    pagos["criterio"] = ""
    if not ventas.empty:
        ventas["matched_pago_keys"] = ""
        ventas["criterio"] = ""

    ventas_por_referencia: dict[str, list[int]] = {}
    for idx, venta in ventas.iterrows():
        refer = str(venta.get("refer_venta", "") or "")
        if refer:
            ventas_por_referencia.setdefault(refer, []).append(idx)

    venta_matches: dict[str, list[str]] = {}
    venta_criterios: dict[str, str] = {}

    for idx, pago in pagos.iterrows():
        venta_idx = None
        criterio = ""

        for referencia, origen in referencias_pago(pago):
            opciones = ventas_por_referencia.get(referencia, [])
            if opciones:
                venta_idx = opciones[0]
                criterio = f"{origen} = Refer. venta"
                break

        if venta_idx is None and not ventas.empty:
            descripcion = str(pago.get("descripcion_pago", "") or "")
            opciones_cliente = [
                i
                for i, venta in ventas.iterrows()
                if cliente_en_descripcion(str(venta.get("cliente", "")), descripcion)
            ]
            if len(opciones_cliente) == 1:
                venta_idx = opciones_cliente[0]
                criterio = "Cliente de venta encontrado en descripcion del pago"

        if venta_idx is None:
            continue

        venta_key = str(ventas.at[venta_idx, "venta_key"])
        pago_key = str(pago.get("pago_key", ""))
        pagos.at[idx, "matched_venta_key"] = venta_key
        pagos.at[idx, "criterio"] = criterio
        venta_matches.setdefault(venta_key, []).append(pago_key)
        venta_criterios[venta_key] = criterio

    if not ventas.empty:
        for idx, venta in ventas.iterrows():
            venta_key = str(venta.get("venta_key", ""))
            matches = venta_matches.get(venta_key, [])
            ventas.at[idx, "matched_pago_keys"] = json.dumps(matches, ensure_ascii=False) if matches else ""
            ventas.at[idx, "criterio"] = venta_criterios.get(venta_key, "")

    with conectar() as conn:
        for _, pago in pagos.iterrows():
            conn.execute(
                """
                UPDATE base_pagos
                SET matched_venta_key = ?, criterio = ?
                WHERE pago_key = ?
                """,
                (pago["matched_venta_key"], pago["criterio"], pago["pago_key"]),
            )
        for _, venta in ventas.iterrows():
            conn.execute(
                """
                UPDATE base_ventas
                SET matched_pago_keys = ?, criterio = ?
                WHERE venta_key = ?
                """,
                (venta["matched_pago_keys"], venta["criterio"], venta["venta_key"]),
            )


def dataframes_consolidados() -> dict[str, pd.DataFrame]:
    reconciliar_base()
    pagos = cargar_tabla("base_pagos")
    ventas = cargar_tabla("base_ventas")

    if pagos.empty:
        pagos_detectados = pd.DataFrame()
        pagos_no_detectados = pd.DataFrame()
    else:
        pagos_detectados = pagos[pagos["matched_venta_key"].astype(str).ne("")].copy()
        pagos_no_detectados = pagos[pagos["matched_venta_key"].astype(str).eq("")].copy()

    if ventas.empty:
        ventas_sin_pago = pd.DataFrame()
    else:
        ventas_sin_pago = ventas[ventas["matched_pago_keys"].astype(str).eq("")].copy()

    resumen = resumen_consolidado(pagos, ventas, pagos_detectados, pagos_no_detectados, ventas_sin_pago)
    return {
        "resumen": resumen,
        "pagos": pagos,
        "ventas": ventas,
        "pagos_detectados": pagos_detectados,
        "pagos_no_detectados": pagos_no_detectados,
        "ventas_sin_pago": ventas_sin_pago,
    }


def resumen_consolidado(
    pagos: pd.DataFrame,
    ventas: pd.DataFrame,
    pagos_detectados: pd.DataFrame,
    pagos_no_detectados: pd.DataFrame,
    ventas_sin_pago: pd.DataFrame,
) -> pd.DataFrame:
    def suma(df: pd.DataFrame, col: str) -> float:
        if df.empty or col not in df.columns:
            return 0.0
        return float(pd.to_numeric(df[col], errors="coerce").fillna(0).sum())

    return pd.DataFrame(
        [
            {
                "concepto": "Pagos en base",
                "cantidad": len(pagos),
                "importe_total": suma(pagos, "importe_pago"),
            },
            {
                "concepto": "Pagos conciliados con ventas",
                "cantidad": len(pagos_detectados),
                "importe_total": suma(pagos_detectados, "importe_pago"),
            },
            {
                "concepto": "Pagos no conciliados",
                "cantidad": len(pagos_no_detectados),
                "importe_total": suma(pagos_no_detectados, "importe_pago"),
            },
            {
                "concepto": "Ventas en base",
                "cantidad": len(ventas),
                "importe_total": suma(ventas, "saldo_venta"),
            },
            {
                "concepto": "Ventas sin pago detectado",
                "cantidad": len(ventas_sin_pago),
                "importe_total": suma(ventas_sin_pago, "saldo_venta"),
            },
        ]
    )


def historial_importaciones() -> pd.DataFrame:
    inicializar_base_consolidada()
    with conectar() as conn:
        return conn.read_sql(
            "SELECT * FROM base_importaciones ORDER BY fecha DESC",
        )


def excel_bytes_consolidado() -> bytes:
    dfs = dataframes_consolidados()
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        dfs["resumen"].to_excel(writer, sheet_name="Resumen", index=False)
        dfs["pagos_detectados"].to_excel(writer, sheet_name="Pagos conciliados", index=False)
        dfs["pagos_no_detectados"].to_excel(writer, sheet_name="Pagos no conciliados", index=False)
        dfs["ventas_sin_pago"].to_excel(writer, sheet_name="Ventas sin pago", index=False)
        dfs["pagos"].to_excel(writer, sheet_name="Base pagos", index=False)
        dfs["ventas"].to_excel(writer, sheet_name="Base ventas", index=False)

        for sheet in writer.book.worksheets:
            sheet.freeze_panes = "A2"
            for column_cells in sheet.columns:
                width = min(max(len(str(cell.value or "")) for cell in column_cells) + 2, 70)
                sheet.column_dimensions[column_cells[0].column_letter].width = width

    return buffer.getvalue()
