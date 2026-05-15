from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pandas as pd

from conciliacion import (
    Movimiento,
    conciliar,
    conciliados_dataframe,
    cargar_depositos_habitualista,
    cargar_pagos_habitualista,
    cargar_quiter,
    decimal_a_float,
    pendientes_dataframe,
    resumen_dataframe,
)
from storage import REPORTS_DIR, UPLOADS_DIR, conectar, guardar_upload, inicializar_storage


UPLOADS_DIR_CONTABLE = UPLOADS_DIR / "base_contable"
REPORTS_DIR_CONTABLE = REPORTS_DIR / "base_contable"


def inicializar_base_contable() -> None:
    inicializar_storage()
    UPLOADS_DIR_CONTABLE.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR_CONTABLE.mkdir(parents=True, exist_ok=True)
    with conectar() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS contable_portal (
                movimiento_key TEXT PRIMARY KEY,
                origen TEXT NOT NULL,
                tipo TEXT NOT NULL,
                fecha TEXT,
                fecha_referencia TEXT,
                importe REAL NOT NULL,
                op TEXT,
                referencia TEXT,
                documento TEXT,
                descripcion TEXT,
                fila_origen INTEGER,
                archivo_origen TEXT,
                creado_en TEXT NOT NULL,
                actualizado_en TEXT NOT NULL,
                matched_quiter_key TEXT,
                criterio TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS contable_quiter (
                movimiento_key TEXT PRIMARY KEY,
                origen TEXT NOT NULL,
                tipo TEXT NOT NULL,
                fecha TEXT,
                fecha_referencia TEXT,
                importe REAL NOT NULL,
                op TEXT,
                referencia TEXT,
                documento TEXT,
                descripcion TEXT,
                fila_origen INTEGER,
                archivo_origen TEXT,
                creado_en TEXT NOT NULL,
                actualizado_en TEXT NOT NULL,
                matched_portal_key TEXT,
                criterio TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS contable_importaciones (
                id TEXT PRIMARY KEY,
                fecha TEXT NOT NULL,
                pagos_archivos TEXT NOT NULL,
                movimientos_archivos TEXT NOT NULL,
                quiter_archivos TEXT NOT NULL,
                portal_insertados INTEGER NOT NULL,
                portal_actualizados INTEGER NOT NULL,
                quiter_insertados INTEGER NOT NULL,
                quiter_actualizados INTEGER NOT NULL
            )
            """
        )
        columnas_importaciones = {
            row[1]
            for row in conn.execute("PRAGMA table_info(contable_importaciones)").fetchall()
        }
        if "quiter_eliminados" not in columnas_importaciones:
            conn.execute(
                "ALTER TABLE contable_importaciones ADD COLUMN quiter_eliminados INTEGER DEFAULT 0"
            )


def valor_no_vacio(valor: object) -> bool:
    if valor is None or pd.isna(valor):
        return False
    return str(valor).strip() != ""


def merge_dict(existente: dict, nuevo: dict) -> dict:
    salida = dict(existente)
    for clave, valor in nuevo.items():
        if clave in {"movimiento_key", "creado_en"}:
            continue
        if valor_no_vacio(valor):
            salida[clave] = valor
    return salida


def fecha_texto(valor) -> str:
    return valor.isoformat() if valor else ""


def movimiento_key(mov: Movimiento, archivo: Path, scope: str) -> str:
    if scope == "portal" and mov.tipo == "pago" and mov.documento:
        return f"portal|pago|doc|{mov.documento}"
    if scope == "portal" and mov.tipo == "deposito" and mov.documento:
        return f"portal|deposito|boleta|{mov.documento}"
    if scope == "quiter" and mov.documento:
        return f"quiter|{mov.tipo}|doc|{mov.documento}|{decimal_a_float(mov.importe):.2f}"
    if scope == "quiter" and mov.referencia:
        return f"quiter|{mov.tipo}|ref|{mov.referencia}|{decimal_a_float(mov.importe):.2f}"

    fecha = fecha_texto(mov.fecha)
    return "|".join(
        [
            scope,
            mov.tipo,
            fecha,
            f"{decimal_a_float(mov.importe):.2f}",
            mov.op,
            mov.referencia,
            mov.documento,
            str(abs(hash(mov.descripcion)) % 10_000_000),
        ]
    )


def movimiento_a_registro(mov: Movimiento, archivo: Path, scope: str) -> dict:
    ahora = datetime.now().isoformat(timespec="seconds")
    return {
        "movimiento_key": movimiento_key(mov, archivo, scope),
        "origen": mov.origen,
        "tipo": mov.tipo,
        "fecha": fecha_texto(mov.fecha),
        "fecha_referencia": fecha_texto(mov.fecha_referencia),
        "importe": decimal_a_float(mov.importe),
        "op": mov.op,
        "referencia": mov.referencia,
        "documento": mov.documento,
        "descripcion": mov.descripcion,
        "fila_origen": mov.fila,
        "archivo_origen": archivo.name,
        "creado_en": ahora,
        "actualizado_en": ahora,
        "matched_quiter_key": "",
        "matched_portal_key": "",
        "criterio": "",
    }


def upsert_registro(tabla: str, key_col: str, registro: dict) -> str:
    with conectar() as conn:
        columnas = [row[1] for row in conn.execute(f"PRAGMA table_info({tabla})").fetchall()]
        existente_row = conn.execute(
            f"SELECT * FROM {tabla} WHERE {key_col} = ?",
            (registro[key_col],),
        ).fetchone()
        registro_filtrado = {col: registro.get(col, "") for col in columnas}

        if existente_row:
            existente = dict(zip(columnas, existente_row))
            combinado = merge_dict(existente, registro_filtrado)
            combinado["creado_en"] = existente["creado_en"]
            combinado["actualizado_en"] = datetime.now().isoformat(timespec="seconds")
            set_clause = ", ".join(f"{col} = ?" for col in columnas if col != key_col)
            valores = [combinado[col] for col in columnas if col != key_col]
            valores.append(registro[key_col])
            conn.execute(f"UPDATE {tabla} SET {set_clause} WHERE {key_col} = ?", valores)
            return "actualizado"

        placeholders = ", ".join("?" for _ in columnas)
        conn.execute(
            f"INSERT INTO {tabla} ({', '.join(columnas)}) VALUES ({placeholders})",
            [registro_filtrado.get(col, "") for col in columnas],
        )
        return "insertado"


def importar_a_base(
    pagos_files,
    movimientos_files,
    quiter_files,
    desde=None,
    hasta=None,
    tolerancia_dias: int = 3,
    sincronizar_quiter_periodo: bool = False,
) -> dict:
    inicializar_base_contable()
    corrida_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid4().hex[:8]
    carpeta = UPLOADS_DIR_CONTABLE / corrida_id
    carpeta.mkdir(parents=True, exist_ok=True)

    pagos_paths = [guardar_upload(file, carpeta / file.name) for file in pagos_files]
    movimientos_paths = [guardar_upload(file, carpeta / file.name) for file in movimientos_files]
    quiter_paths = [guardar_upload(file, carpeta / file.name) for file in quiter_files]

    stats = {
        "portal_insertados": 0,
        "portal_actualizados": 0,
        "quiter_insertados": 0,
        "quiter_actualizados": 0,
        "quiter_eliminados": 0,
        "pagos_archivos": [p.name for p in pagos_paths],
        "movimientos_archivos": [p.name for p in movimientos_paths],
        "quiter_archivos": [p.name for p in quiter_paths],
    }

    for path in pagos_paths:
        for mov in cargar_pagos_habitualista(path):
            estado = upsert_registro("contable_portal", "movimiento_key", movimiento_a_registro(mov, path, "portal"))
            stats[f"portal_{estado}s"] += 1

    for path in movimientos_paths:
        for mov in cargar_depositos_habitualista(path):
            estado = upsert_registro("contable_portal", "movimiento_key", movimiento_a_registro(mov, path, "portal"))
            stats[f"portal_{estado}s"] += 1

    quiter_importados = []
    for path in quiter_paths:
        for mov in cargar_quiter(path, desde, hasta):
            quiter_importados.append((path, mov))

    if sincronizar_quiter_periodo and quiter_importados:
        stats["quiter_eliminados"] = sincronizar_quiter(quiter_importados, desde, hasta)

    for path, mov in quiter_importados:
            estado = upsert_registro("contable_quiter", "movimiento_key", movimiento_a_registro(mov, path, "quiter"))
            stats[f"quiter_{estado}s"] += 1

    reconciliar_base(tolerancia_dias=tolerancia_dias)
    registrar_importacion(corrida_id, stats)
    return stats


def registrar_importacion(corrida_id: str, stats: dict) -> None:
    with conectar() as conn:
        conn.execute(
            """
            INSERT INTO contable_importaciones (
                id, fecha, pagos_archivos, movimientos_archivos, quiter_archivos,
                portal_insertados, portal_actualizados, quiter_insertados,
                quiter_actualizados, quiter_eliminados
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                corrida_id,
                datetime.now().isoformat(timespec="seconds"),
                json.dumps(stats["pagos_archivos"], ensure_ascii=False),
                json.dumps(stats["movimientos_archivos"], ensure_ascii=False),
                json.dumps(stats["quiter_archivos"], ensure_ascii=False),
                stats["portal_insertados"],
                stats["portal_actualizados"],
                stats["quiter_insertados"],
                stats["quiter_actualizados"],
                stats.get("quiter_eliminados", 0),
            ),
        )


def sincronizar_quiter(quiter_importados: list[tuple[Path, Movimiento]], desde, hasta) -> int:
    fechas = [mov.fecha for _path, mov in quiter_importados if mov.fecha]
    if not fechas:
        return 0

    desde_efectivo = desde or min(fechas)
    hasta_efectivo = hasta or max(fechas)
    keys_importadas = {
        movimiento_key(mov, path, "quiter")
        for path, mov in quiter_importados
    }

    with conectar() as conn:
        rows = conn.execute(
            """
            SELECT movimiento_key
            FROM contable_quiter
            WHERE fecha >= ? AND fecha <= ?
            """,
            (desde_efectivo.isoformat(), hasta_efectivo.isoformat()),
        ).fetchall()
        keys_actuales = {row[0] for row in rows}
        keys_a_eliminar = sorted(keys_actuales - keys_importadas)
        for key in keys_a_eliminar:
            conn.execute("DELETE FROM contable_quiter WHERE movimiento_key = ?", (key,))

    return len(keys_a_eliminar)


def cargar_tabla(tabla: str) -> pd.DataFrame:
    inicializar_base_contable()
    with conectar() as conn:
        return pd.read_sql_query(f"SELECT * FROM {tabla}", conn)


def fecha_desde_texto(valor: str):
    if not valor:
        return None
    fecha = pd.to_datetime(valor, errors="coerce")
    return fecha.date() if pd.notna(fecha) else None


def row_a_movimiento(row: pd.Series, scope: str) -> Movimiento:
    return Movimiento(
        origen=str(row.get("origen", "")),
        tipo=str(row.get("tipo", "")),
        fila=int(row.get("fila_origen", 0) or 0),
        fecha=fecha_desde_texto(str(row.get("fecha", "") or "")),
        fecha_referencia=fecha_desde_texto(str(row.get("fecha_referencia", "") or "")),
        importe=Decimal(str(row.get("importe", 0) or 0)),
        descripcion=str(row.get("descripcion", "") or ""),
        op=str(row.get("op", "") or ""),
        referencia=str(row.get("referencia", "") or ""),
        documento=str(row.get("documento", "") or ""),
    )


def reconciliar_base(tolerancia_dias: int = 3) -> None:
    portal = cargar_tabla("contable_portal")
    quiter = cargar_tabla("contable_quiter")
    if portal.empty and quiter.empty:
        return

    portal_movs = [row_a_movimiento(row, "portal") for _, row in portal.iterrows()]
    quiter_movs = [row_a_movimiento(row, "quiter") for _, row in quiter.iterrows()]
    resultado = conciliar(portal_movs, quiter_movs, tolerancia_dias=tolerancia_dias)

    portal_keys = list(portal["movimiento_key"]) if not portal.empty else []
    quiter_keys = list(quiter["movimiento_key"]) if not quiter.empty else []
    portal_by_signature = {signature(row_a_movimiento(row, "portal")): key for key, (_, row) in zip(portal_keys, portal.iterrows())}
    quiter_by_signature = {signature(row_a_movimiento(row, "quiter")): key for key, (_, row) in zip(quiter_keys, quiter.iterrows())}

    portal_updates = {key: ("", "") for key in portal_keys}
    quiter_updates = {key: ("", "") for key in quiter_keys}
    for match in resultado.conciliados:
        pkey = portal_by_signature.get(signature(match.portal))
        qkey = quiter_by_signature.get(signature(match.quiter))
        if pkey and qkey:
            portal_updates[pkey] = (qkey, match.criterio)
            quiter_updates[qkey] = (pkey, match.criterio)

    with conectar() as conn:
        for key, (matched, criterio) in portal_updates.items():
            conn.execute(
                "UPDATE contable_portal SET matched_quiter_key = ?, criterio = ? WHERE movimiento_key = ?",
                (matched, criterio, key),
            )
        for key, (matched, criterio) in quiter_updates.items():
            conn.execute(
                "UPDATE contable_quiter SET matched_portal_key = ?, criterio = ? WHERE movimiento_key = ?",
                (matched, criterio, key),
            )


def signature(mov: Movimiento) -> tuple:
    return (
        mov.tipo,
        fecha_texto(mov.fecha),
        fecha_texto(mov.fecha_referencia),
        f"{decimal_a_float(mov.importe):.2f}",
        mov.op,
        mov.referencia,
        mov.documento,
        mov.descripcion,
    )


def dataframes_consolidados() -> dict[str, pd.DataFrame]:
    reconciliar_base()
    portal = cargar_tabla("contable_portal")
    quiter = cargar_tabla("contable_quiter")
    conciliados = portal[portal["matched_quiter_key"].astype(str).ne("")].copy() if not portal.empty else pd.DataFrame()
    portal_pendiente = portal[portal["matched_quiter_key"].astype(str).eq("")].copy() if not portal.empty else pd.DataFrame()
    quiter_pendiente = quiter[quiter["matched_portal_key"].astype(str).eq("")].copy() if not quiter.empty else pd.DataFrame()
    resumen = resumen_consolidado(portal, quiter, conciliados, portal_pendiente, quiter_pendiente)
    return {
        "resumen": resumen,
        "portal": portal,
        "quiter": quiter,
        "conciliados": conciliados,
        "portal_pendiente": portal_pendiente,
        "quiter_pendiente": quiter_pendiente,
    }


def suma(df: pd.DataFrame, col: str) -> float:
    if df.empty or col not in df.columns:
        return 0.0
    return float(pd.to_numeric(df[col], errors="coerce").fillna(0).sum())


def resumen_consolidado(
    portal: pd.DataFrame,
    quiter: pd.DataFrame,
    conciliados: pd.DataFrame,
    portal_pendiente: pd.DataFrame,
    quiter_pendiente: pd.DataFrame,
) -> pd.DataFrame:
    filas = []
    for tipo in ("deposito", "pago"):
        portal_tipo = portal[portal["tipo"].eq(tipo)] if not portal.empty else pd.DataFrame()
        quiter_tipo = quiter[quiter["tipo"].eq(tipo)] if not quiter.empty else pd.DataFrame()
        conc_tipo = conciliados[conciliados["tipo"].eq(tipo)] if not conciliados.empty else pd.DataFrame()
        portal_pend_tipo = portal_pendiente[portal_pendiente["tipo"].eq(tipo)] if not portal_pendiente.empty else pd.DataFrame()
        quiter_pend_tipo = quiter_pendiente[quiter_pendiente["tipo"].eq(tipo)] if not quiter_pendiente.empty else pd.DataFrame()
        filas.append(
            {
                "tipo": tipo,
                "portal_cantidad": len(portal_tipo),
                "portal_total": suma(portal_tipo, "importe"),
                "quiter_cantidad": len(quiter_tipo),
                "quiter_total": suma(quiter_tipo, "importe"),
                "conciliados_cantidad": len(conc_tipo),
                "conciliados_total": suma(conc_tipo, "importe"),
                "pendientes_portal_cantidad": len(portal_pend_tipo),
                "pendientes_portal_total": suma(portal_pend_tipo, "importe"),
                "pendientes_quiter_cantidad": len(quiter_pend_tipo),
                "pendientes_quiter_total": suma(quiter_pend_tipo, "importe"),
            }
        )
    return pd.DataFrame(filas)


def historial_importaciones() -> pd.DataFrame:
    inicializar_base_contable()
    with conectar() as conn:
        return pd.read_sql_query(
            "SELECT * FROM contable_importaciones ORDER BY fecha DESC",
            conn,
        )


def excel_bytes_consolidado() -> bytes:
    dfs = dataframes_consolidados()
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        dfs["resumen"].to_excel(writer, sheet_name="Resumen", index=False)
        dfs["conciliados"].to_excel(writer, sheet_name="Conciliados", index=False)
        dfs["portal_pendiente"].to_excel(writer, sheet_name="Pendientes portal", index=False)
        dfs["quiter_pendiente"].to_excel(writer, sheet_name="Pendientes Quiter", index=False)
        dfs["portal"].to_excel(writer, sheet_name="Base portal", index=False)
        dfs["quiter"].to_excel(writer, sheet_name="Base Quiter", index=False)
        historial_importaciones().to_excel(writer, sheet_name="Importaciones", index=False)
        for sheet in writer.book.worksheets:
            sheet.freeze_panes = "A2"
            for column_cells in sheet.columns:
                width = min(max(len(str(cell.value or "")) for cell in column_cells) + 2, 70)
                sheet.column_dimensions[column_cells[0].column_letter].width = width
    return buffer.getvalue()
