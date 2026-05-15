from __future__ import annotations

import json
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from conciliacion import ResultadoConciliacion, conciliados_dataframe, pendientes_dataframe, resumen_dataframe


DATA_DIR = Path("data")
DB_PATH = DATA_DIR / "conciliaciones.sqlite3"
UPLOADS_DIR = DATA_DIR / "uploads"
REPORTS_DIR = DATA_DIR / "reports"


@dataclass(frozen=True)
class ConciliacionGuardada:
    id: str
    creada: str
    nombre: str
    desde: str
    hasta: str
    tolerancia_dias: int
    resumen: list[dict]
    reporte_path: Path
    conciliados_path: Path
    pendientes_path: Path


@dataclass(frozen=True)
class ConciliacionPagosVentasGuardada:
    id: str
    creada: str
    nombre: str
    resumen: list[dict]
    reporte_path: Path
    detectados_path: Path
    no_detectados_path: Path
    ventas_sin_pago_path: Path
    pagos_path: Path
    ventas_path: Path
    ventas_paths: list[Path]


@dataclass(frozen=True)
class OperacionesPagoGuardadas:
    etiqueta: str
    path: Path


def inicializar_storage() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with conectar() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conciliaciones (
                id TEXT PRIMARY KEY,
                creada TEXT NOT NULL,
                nombre TEXT NOT NULL,
                desde TEXT,
                hasta TEXT,
                tolerancia_dias INTEGER NOT NULL,
                resumen_json TEXT NOT NULL,
                reporte_path TEXT NOT NULL,
                conciliados_path TEXT NOT NULL,
                pendientes_path TEXT NOT NULL,
                movimientos_path TEXT NOT NULL,
                pagos_path TEXT NOT NULL,
                quiter_path TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conciliaciones_pagos_ventas (
                id TEXT PRIMARY KEY,
                creada TEXT NOT NULL,
                nombre TEXT NOT NULL,
                resumen_json TEXT NOT NULL,
                reporte_path TEXT NOT NULL,
                detectados_path TEXT NOT NULL,
                no_detectados_path TEXT NOT NULL,
                ventas_sin_pago_path TEXT NOT NULL,
                pagos_path TEXT NOT NULL,
                ventas_path TEXT NOT NULL
            )
            """
        )
        columnas = {
            row[1]
            for row in conn.execute("PRAGMA table_info(conciliaciones_pagos_ventas)").fetchall()
        }
        if "ventas_paths_json" not in columnas:
            conn.execute(
                "ALTER TABLE conciliaciones_pagos_ventas ADD COLUMN ventas_paths_json TEXT"
            )


def conectar() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def nueva_corrida_id() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid4().hex[:8]


def guardar_upload(uploaded_file, destino: Path) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("wb") as archivo:
        shutil.copyfileobj(uploaded_file, archivo)
    return destino


def guardar_conciliacion(
    *,
    nombre: str,
    desde: date | None,
    hasta: date | None,
    tolerancia_dias: int,
    movimientos_path: Path,
    pagos_path: Path,
    quiter_path: Path,
    resultado: ResultadoConciliacion,
    reporte_bytes: bytes,
) -> ConciliacionGuardada:
    inicializar_storage()
    corrida_id = nueva_corrida_id()
    carpeta = REPORTS_DIR / corrida_id
    carpeta.mkdir(parents=True, exist_ok=True)

    reporte_path = carpeta / "reporte_conciliacion.xlsx"
    conciliados_path = carpeta / "conciliados.csv"
    pendientes_path = carpeta / "no_conciliados.csv"

    reporte_path.write_bytes(reporte_bytes)
    conciliados_dataframe(resultado.conciliados).to_csv(conciliados_path, index=False, encoding="utf-8-sig")
    pendientes_dataframe(resultado).to_csv(pendientes_path, index=False, encoding="utf-8-sig")

    resumen = resumen_dataframe(resultado)
    resumen_json = resumen.to_json(orient="records", date_format="iso")
    creada = datetime.now().isoformat(timespec="seconds")

    with conectar() as conn:
        conn.execute(
            """
            INSERT INTO conciliaciones (
                id, creada, nombre, desde, hasta, tolerancia_dias, resumen_json,
                reporte_path, conciliados_path, pendientes_path,
                movimientos_path, pagos_path, quiter_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                corrida_id,
                creada,
                nombre,
                desde.isoformat() if desde else "",
                hasta.isoformat() if hasta else "",
                tolerancia_dias,
                resumen_json,
                str(reporte_path),
                str(conciliados_path),
                str(pendientes_path),
                str(movimientos_path),
                str(pagos_path),
                str(quiter_path),
            ),
        )

    return ConciliacionGuardada(
        id=corrida_id,
        creada=creada,
        nombre=nombre,
        desde=desde.isoformat() if desde else "",
        hasta=hasta.isoformat() if hasta else "",
        tolerancia_dias=tolerancia_dias,
        resumen=json.loads(resumen_json),
        reporte_path=reporte_path,
        conciliados_path=conciliados_path,
        pendientes_path=pendientes_path,
    )


def listar_conciliaciones() -> list[ConciliacionGuardada]:
    inicializar_storage()
    with conectar() as conn:
        rows = conn.execute(
            """
            SELECT id, creada, nombre, desde, hasta, tolerancia_dias, resumen_json,
                   reporte_path, conciliados_path, pendientes_path
            FROM conciliaciones
            ORDER BY creada DESC
            """
        ).fetchall()

    return [
        ConciliacionGuardada(
            id=row[0],
            creada=row[1],
            nombre=row[2],
            desde=row[3],
            hasta=row[4],
            tolerancia_dias=row[5],
            resumen=json.loads(row[6]),
            reporte_path=Path(row[7]),
            conciliados_path=Path(row[8]),
            pendientes_path=Path(row[9]),
        )
        for row in rows
    ]


def cargar_dataframe(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def guardar_conciliacion_pagos_ventas(
    *,
    nombre: str,
    pagos_path: Path,
    ventas_path: Path,
    resumen: pd.DataFrame,
    detectados: pd.DataFrame,
    no_detectados: pd.DataFrame,
    ventas_sin_pago: pd.DataFrame,
    reporte_bytes: bytes,
    ventas_paths: list[Path] | None = None,
) -> ConciliacionPagosVentasGuardada:
    inicializar_storage()
    corrida_id = nueva_corrida_id()
    carpeta = REPORTS_DIR / "pagos_ventas" / corrida_id
    carpeta.mkdir(parents=True, exist_ok=True)

    reporte_path = carpeta / "reporte_pagos_ventas.xlsx"
    detectados_path = carpeta / "detectados.csv"
    no_detectados_path = carpeta / "pagos_no_detectados.csv"
    ventas_sin_pago_path = carpeta / "ventas_sin_pago.csv"

    reporte_path.write_bytes(reporte_bytes)
    detectados.to_csv(detectados_path, index=False, encoding="utf-8-sig")
    no_detectados.to_csv(no_detectados_path, index=False, encoding="utf-8-sig")
    ventas_sin_pago.to_csv(ventas_sin_pago_path, index=False, encoding="utf-8-sig")

    resumen_json = resumen.to_json(orient="records", date_format="iso")
    ventas_paths = ventas_paths or [ventas_path]
    ventas_paths_json = json.dumps([str(path) for path in ventas_paths])
    creada = datetime.now().isoformat(timespec="seconds")

    with conectar() as conn:
        conn.execute(
            """
            INSERT INTO conciliaciones_pagos_ventas (
                id, creada, nombre, resumen_json, reporte_path,
                detectados_path, no_detectados_path, ventas_sin_pago_path,
                pagos_path, ventas_path, ventas_paths_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                corrida_id,
                creada,
                nombre,
                resumen_json,
                str(reporte_path),
                str(detectados_path),
                str(no_detectados_path),
                str(ventas_sin_pago_path),
                str(pagos_path),
                str(ventas_path),
                ventas_paths_json,
            ),
        )

    return ConciliacionPagosVentasGuardada(
        id=corrida_id,
        creada=creada,
        nombre=nombre,
        resumen=json.loads(resumen_json),
        reporte_path=reporte_path,
        detectados_path=detectados_path,
        no_detectados_path=no_detectados_path,
        ventas_sin_pago_path=ventas_sin_pago_path,
        pagos_path=pagos_path,
        ventas_path=ventas_path,
        ventas_paths=ventas_paths,
    )


def listar_conciliaciones_pagos_ventas() -> list[ConciliacionPagosVentasGuardada]:
    inicializar_storage()
    with conectar() as conn:
        rows = conn.execute(
            """
            SELECT id, creada, nombre, resumen_json, reporte_path,
                   detectados_path, no_detectados_path, ventas_sin_pago_path,
                   pagos_path, ventas_path, ventas_paths_json
            FROM conciliaciones_pagos_ventas
            ORDER BY creada DESC
            """
        ).fetchall()

    return [
        ConciliacionPagosVentasGuardada(
            id=row[0],
            creada=row[1],
            nombre=row[2],
            resumen=json.loads(row[3]),
            reporte_path=Path(row[4]),
            detectados_path=Path(row[5]),
            no_detectados_path=Path(row[6]),
            ventas_sin_pago_path=Path(row[7]),
            pagos_path=Path(row[8]),
            ventas_path=Path(row[9]),
            ventas_paths=[Path(path) for path in json.loads(row[10] or "[]")] or [Path(row[9])],
        )
        for row in rows
    ]


def listar_operaciones_pago_guardadas() -> list[OperacionesPagoGuardadas]:
    inicializar_storage()
    registros: list[OperacionesPagoGuardadas] = []
    vistos: set[str] = set()

    with conectar() as conn:
        rows_principal = conn.execute(
            """
            SELECT creada, nombre, pagos_path
            FROM conciliaciones
            WHERE pagos_path IS NOT NULL AND pagos_path != ''
            ORDER BY creada DESC
            """
        ).fetchall()
        rows_pagos_ventas = conn.execute(
            """
            SELECT creada, nombre, pagos_path
            FROM conciliaciones_pagos_ventas
            WHERE pagos_path IS NOT NULL AND pagos_path != ''
            ORDER BY creada DESC
            """
        ).fetchall()

    for origen, rows in (
        ("Conciliacion principal", rows_principal),
        ("Pagos vs ventas", rows_pagos_ventas),
    ):
        for creada, nombre, path_texto in rows:
            path = Path(path_texto)
            clave = str(path.resolve()) if path.exists() else str(path)
            if clave in vistos or not path.exists():
                continue
            vistos.add(clave)
            registros.append(
                OperacionesPagoGuardadas(
                    etiqueta=f"{creada} | {origen} | {nombre} | {path.name}",
                    path=path,
                )
            )

    return registros


def actualizar_conciliacion_pagos_ventas(
    *,
    guardada: ConciliacionPagosVentasGuardada,
    ventas_path: Path,
    ventas_paths: list[Path],
    resumen: pd.DataFrame,
    detectados: pd.DataFrame,
    no_detectados: pd.DataFrame,
    ventas_sin_pago: pd.DataFrame,
    reporte_bytes: bytes,
) -> ConciliacionPagosVentasGuardada:
    inicializar_storage()

    guardada.reporte_path.parent.mkdir(parents=True, exist_ok=True)
    guardada.reporte_path.write_bytes(reporte_bytes)
    detectados.to_csv(guardada.detectados_path, index=False, encoding="utf-8-sig")
    no_detectados.to_csv(guardada.no_detectados_path, index=False, encoding="utf-8-sig")
    ventas_sin_pago.to_csv(guardada.ventas_sin_pago_path, index=False, encoding="utf-8-sig")

    resumen_json = resumen.to_json(orient="records", date_format="iso")
    ventas_paths_json = json.dumps([str(path) for path in ventas_paths])

    with conectar() as conn:
        conn.execute(
            """
            UPDATE conciliaciones_pagos_ventas
            SET resumen_json = ?,
                ventas_path = ?,
                ventas_paths_json = ?
            WHERE id = ?
            """,
            (
                resumen_json,
                str(ventas_path),
                ventas_paths_json,
                guardada.id,
            ),
        )

    return ConciliacionPagosVentasGuardada(
        id=guardada.id,
        creada=guardada.creada,
        nombre=guardada.nombre,
        resumen=json.loads(resumen_json),
        reporte_path=guardada.reporte_path,
        detectados_path=guardada.detectados_path,
        no_detectados_path=guardada.no_detectados_path,
        ventas_sin_pago_path=guardada.ventas_sin_pago_path,
        pagos_path=guardada.pagos_path,
        ventas_path=ventas_path,
        ventas_paths=ventas_paths,
    )
