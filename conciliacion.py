from __future__ import annotations

import argparse
from io import BytesIO
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable

import pandas as pd


CENTAVOS = Decimal("0.01")


class ImportacionError(ValueError):
    pass


@dataclass(frozen=True)
class Movimiento:
    origen: str
    tipo: str
    fila: int
    fecha: date | None
    importe: Decimal
    descripcion: str
    op: str = ""
    referencia: str = ""
    documento: str = ""
    fecha_referencia: date | None = None


@dataclass(frozen=True)
class Match:
    portal: Movimiento
    quiter: Movimiento
    criterio: str


@dataclass
class ResultadoConciliacion:
    conciliados: list[Match]
    pendientes_portal: list[Movimiento]
    pendientes_quiter: list[Movimiento]


def normalizar_importe(valor: object) -> Decimal:
    if pd.isna(valor):
        return Decimal("0.00")
    if isinstance(valor, Decimal):
        return valor.quantize(CENTAVOS)
    if isinstance(valor, int | float):
        return Decimal(str(valor)).quantize(CENTAVOS, rounding=ROUND_HALF_UP)

    limpio = str(valor).strip().replace("$", "").replace(" ", "")
    if not limpio:
        return Decimal("0.00")
    if "," in limpio and "." in limpio:
        limpio = limpio.replace(".", "").replace(",", ".")
    elif "," in limpio:
        limpio = limpio.replace(",", ".")
    try:
        return Decimal(limpio).quantize(CENTAVOS, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError(f"Importe invalido: {valor!r}") from exc


def normalizar_fecha(valor: object) -> date | None:
    if pd.isna(valor):
        return None
    if isinstance(valor, pd.Timestamp):
        return valor.date()
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor

    texto = str(valor).strip()
    if not texto:
        return None
    texto = re.sub(r"\s+TRAD\b", "", texto, flags=re.IGNORECASE)

    for dayfirst in (True, False):
        fecha = pd.to_datetime(texto, dayfirst=dayfirst, errors="coerce")
        if pd.notna(fecha):
            return fecha.date()
    return None


def extraer_op(texto: object) -> str:
    match = re.search(r"\bOP\s*(\d+)\b", str(texto or ""), re.IGNORECASE)
    return match.group(1) if match else ""


def extraer_ref(texto: object) -> str:
    match = re.search(r"\bREF\.?\s*(\d+)\b", str(texto or ""), re.IGNORECASE)
    return match.group(1) if match else ""


def extraer_fecha_th(texto: object) -> date | None:
    match = re.search(r"TH\s+(\d{1,2}/\d{1,2}/\d{4})", str(texto or ""), re.IGNORECASE)
    return normalizar_fecha(match.group(1)) if match else None


def limpiar_documento(valor: object) -> str:
    if pd.isna(valor):
        return ""
    texto = str(valor).strip()
    if not texto:
        return ""
    texto = texto.split("/")[0]
    if texto.endswith(".0"):
        texto = texto[:-2]
    return re.sub(r"\D", "", texto)


def texto_combinado(*valores: object) -> str:
    return " ".join(str(v).strip() for v in valores if not pd.isna(v) and str(v).strip())


def normalizar_nombre_columna(nombre: object) -> str:
    texto = unicodedata.normalize("NFKD", str(nombre or ""))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "_", texto.lower()).strip("_")


def mapa_columnas(df: pd.DataFrame) -> dict[str, str]:
    return {normalizar_nombre_columna(columna): columna for columna in df.columns}


def columna_requerida(
    df: pd.DataFrame,
    path: Path,
    nombre_reporte: str,
    *opciones: str,
) -> str:
    columnas = mapa_columnas(df)
    for opcion in opciones:
        clave = normalizar_nombre_columna(opcion)
        if clave in columnas:
            return columnas[clave]
    disponibles = ", ".join(str(col) for col in df.columns)
    esperadas = ", ".join(opciones)
    raise ImportacionError(
        f"El archivo '{path.name}' no parece ser {nombre_reporte}. "
        f"Falta la columna requerida: {esperadas}. "
        f"Columnas encontradas: {disponibles}"
    )


def columna_opcional(df: pd.DataFrame, *opciones: str) -> str | None:
    columnas = mapa_columnas(df)
    for opcion in opciones:
        clave = normalizar_nombre_columna(opcion)
        if clave in columnas:
            return columnas[clave]
    return None


def rango_desde_nombres(paths: Iterable[Path]) -> tuple[date | None, date | None]:
    texto = " ".join(path.name for path in paths)
    fechas = re.findall(r"\d{4}-\d{2}-\d{2}", texto)
    if len(fechas) >= 2:
        return datetime.strptime(fechas[0], "%Y-%m-%d").date(), datetime.strptime(fechas[1], "%Y-%m-%d").date()
    return None, None


def cargar_depositos_habitualista(path: Path) -> list[Movimiento]:
    df = pd.read_excel(path)
    col_tipo = columna_requerida(df, path, "Movimientos de cuenta", "Tipo")
    col_descripcion = columna_requerida(df, path, "Movimientos de cuenta", "Descripcion")
    col_fecha = columna_requerida(df, path, "Movimientos de cuenta", "Fecha acreditacion")
    col_monto = columna_requerida(df, path, "Movimientos de cuenta", "Monto")
    col_referencia = columna_opcional(df, "Cod referencia")

    creditos = df[df[col_tipo].astype(str).str.strip().str.upper().eq("CREDIT")]
    movimientos: list[Movimiento] = []

    for indice, fila in creditos.iterrows():
        descripcion = texto_combinado(fila.get(col_descripcion))
        movimientos.append(
            Movimiento(
                origen="Habitualista - movimientos de cuenta",
                tipo="deposito",
                fila=indice + 2,
                fecha=normalizar_fecha(fila.get(col_fecha)),
                fecha_referencia=normalizar_fecha(fila.get(col_referencia)) if col_referencia else None,
                importe=normalizar_importe(fila.get(col_monto)),
                descripcion=descripcion,
                documento=extraer_boleta(descripcion),
            )
        )
    return movimientos


def extraer_boleta(texto: object) -> str:
    match = re.search(r"Nro:\s*0*(\d+)", str(texto or ""), re.IGNORECASE)
    return match.group(1) if match else ""


def cargar_pagos_habitualista(path: Path) -> list[Movimiento]:
    df = pd.read_excel(path)
    col_fecha = columna_requerida(df, path, "Operaciones de pago", "Fecha")
    col_total = columna_requerida(df, path, "Operaciones de pago", "Total")
    col_nro_pago = columna_requerida(df, path, "Operaciones de pago", "Nro de pago", "Nro. de pago")
    col_motivo = columna_requerida(df, path, "Operaciones de pago", "Motivo pago")
    col_observaciones = columna_opcional(df, "Observaciones")
    col_estado = columna_opcional(df, "Estado")
    if col_estado:
        df = df[df[col_estado].astype(str).str.lower().eq("liquidado")]

    movimientos: list[Movimiento] = []
    for indice, fila in df.iterrows():
        descripcion = texto_combinado(
            fila.get(col_motivo),
            fila.get(col_observaciones) if col_observaciones else "",
        )
        movimientos.append(
            Movimiento(
                origen="Habitualista - operaciones de pago",
                tipo="pago",
                fila=indice + 2,
                fecha=normalizar_fecha(fila.get(col_fecha)),
                importe=normalizar_importe(fila.get(col_total)),
                descripcion=descripcion,
                op=extraer_op(descripcion),
                referencia=extraer_ref(descripcion),
                documento=limpiar_documento(fila.get(col_nro_pago)),
            )
        )
    return movimientos


def cargar_quiter(path: Path, desde: date | None, hasta: date | None) -> list[Movimiento]:
    df = pd.read_excel(path)
    col_concepto = columna_requerida(df, path, "Contabilidad Quiter", "Concepto del apunte")
    col_fecha = columna_requerida(df, path, "Contabilidad Quiter", "Fecha")
    col_debe = columna_requerida(df, path, "Contabilidad Quiter", "Debe")
    col_haber = columna_requerida(df, path, "Contabilidad Quiter", "Haber")
    col_referencia = columna_opcional(df, "Referencia")
    col_documento = columna_opcional(df, "Nro.docum", "Nro docum", "Nro documento")
    movimientos: list[Movimiento] = []

    for indice, fila in df.iterrows():
        concepto = texto_combinado(fila.get(col_concepto))
        if not concepto or re.search(r"\b(saldos?|total)\b", concepto, re.IGNORECASE):
            continue

        fecha = normalizar_fecha(fila.get(col_fecha))
        if desde and fecha and fecha < desde:
            continue
        if hasta and fecha and fecha > hasta:
            continue

        debe = normalizar_importe(fila.get(col_debe))
        haber = normalizar_importe(fila.get(col_haber))
        if debe and haber:
            continue
        if not debe and not haber:
            continue

        tipo = "deposito" if debe else "pago"
        referencia = (
            limpiar_documento(fila.get(col_referencia)) if col_referencia else ""
        ) or (
            limpiar_documento(fila.get(col_documento)) if col_documento else ""
        )
        documento = limpiar_documento(fila.get(col_documento)) if col_documento else ""
        movimientos.append(
            Movimiento(
                origen="Quiter",
                tipo=tipo,
                fila=indice + 2,
                fecha=fecha,
                fecha_referencia=extraer_fecha_th(concepto),
                importe=debe or haber,
                descripcion=concepto,
                op=extraer_op(concepto),
                referencia=referencia,
                documento=documento,
            )
        )
    return movimientos


def conciliar(
    portal: Iterable[Movimiento],
    quiter: Iterable[Movimiento],
    tolerancia_dias: int,
) -> ResultadoConciliacion:
    pendientes_quiter = list(quiter)
    conciliados: list[Match] = []
    pendientes_portal: list[Movimiento] = []

    for movimiento in portal:
        indice, criterio = buscar_match(movimiento, pendientes_quiter, tolerancia_dias)
        if indice is None:
            pendientes_portal.append(movimiento)
            continue

        conciliados.append(Match(movimiento, pendientes_quiter.pop(indice), criterio))

    return ResultadoConciliacion(conciliados, pendientes_portal, pendientes_quiter)


def buscar_match(
    movimiento: Movimiento,
    candidatos: list[Movimiento],
    tolerancia_dias: int,
) -> tuple[int | None, str]:
    candidatos_exactos = [
        (indice, candidato)
        for indice, candidato in enumerate(candidatos)
        if compatibles(movimiento, candidato)
    ]
    if len(candidatos_exactos) == 1:
        return candidatos_exactos[0][0], "Contable: tipo + importe unico"

    mejor_indice: int | None = None
    mejor_distancia: int | None = None
    for indice, candidato in candidatos_exactos:
        distancia = distancia_fechas(movimiento, candidato)
        if distancia is None or distancia > tolerancia_dias:
            continue
        if mejor_distancia is None or distancia < mejor_distancia:
            mejor_indice = indice
            mejor_distancia = distancia

    if mejor_indice is None:
        return None, ""
    return mejor_indice, f"Contable: tipo + importe + fecha +/- {tolerancia_dias} dias"


def compatibles(a: Movimiento, b: Movimiento) -> bool:
    return a.tipo == b.tipo and a.importe == b.importe


def distancia_fechas(a: Movimiento, b: Movimiento) -> int | None:
    fechas_a = [f for f in (a.fecha_referencia, a.fecha) if f]
    fechas_b = [f for f in (b.fecha_referencia, b.fecha) if f]
    if not fechas_a or not fechas_b:
        return None
    return min(abs((fa - fb).days) for fa in fechas_a for fb in fechas_b)


def escribir_excel(resultado: ResultadoConciliacion, salida: Path) -> None:
    salida.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(salida, engine="openpyxl") as writer:
        escribir_hojas_excel(resultado, writer)


def excel_bytes(resultado: ResultadoConciliacion) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        escribir_hojas_excel(resultado, writer)
    return buffer.getvalue()


def escribir_hojas_excel(
    resultado: ResultadoConciliacion,
    writer: pd.ExcelWriter,
) -> None:
    resumen_dataframe(resultado).to_excel(writer, sheet_name="Resumen", index=False)
    conciliados_dataframe(resultado.conciliados).to_excel(writer, sheet_name="Conciliados", index=False)
    pendientes_dataframe(resultado).to_excel(writer, sheet_name="No conciliados", index=False)

    for sheet in writer.book.worksheets:
        sheet.freeze_panes = "A2"
        for column_cells in sheet.columns:
            width = min(max(len(str(cell.value or "")) for cell in column_cells) + 2, 70)
            sheet.column_dimensions[column_cells[0].column_letter].width = width


def ejecutar_conciliacion(
    movimientos_cuenta: Path,
    operaciones_pago: Path,
    quiter_path: Path,
    desde: date | None = None,
    hasta: date | None = None,
    tolerancia_dias: int = 3,
) -> ResultadoConciliacion:
    if not desde or not hasta:
        desde_nombre, hasta_nombre = rango_desde_nombres(
            [movimientos_cuenta, operaciones_pago]
        )
        desde = desde or desde_nombre
        hasta = hasta or hasta_nombre

    depositos = cargar_depositos_habitualista(movimientos_cuenta)
    pagos = cargar_pagos_habitualista(operaciones_pago)
    quiter = cargar_quiter(quiter_path, desde, hasta)

    return conciliar(
        portal=[*depositos, *pagos],
        quiter=quiter,
        tolerancia_dias=tolerancia_dias,
    )


def resumen_dataframe(resultado: ResultadoConciliacion) -> pd.DataFrame:
    filas = []
    for tipo in ("deposito", "pago"):
        conciliados = [m for m in resultado.conciliados if m.portal.tipo == tipo]
        portal = [m for m in resultado.pendientes_portal if m.tipo == tipo]
        quiter = [m for m in resultado.pendientes_quiter if m.tipo == tipo]
        filas.append(
            {
                "tipo": tipo,
                "conciliados_cantidad": len(conciliados),
                "conciliados_total": decimal_a_float(sum((m.portal.importe for m in conciliados), Decimal("0"))),
                "pendientes_portal_cantidad": len(portal),
                "pendientes_portal_total": decimal_a_float(sum((m.importe for m in portal), Decimal("0"))),
                "pendientes_quiter_cantidad": len(quiter),
                "pendientes_quiter_total": decimal_a_float(sum((m.importe for m in quiter), Decimal("0"))),
            }
        )
    return pd.DataFrame(filas)


def conciliados_dataframe(matches: list[Match]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "tipo": match.portal.tipo,
                "importe": decimal_a_float(match.portal.importe),
                "criterio": match.criterio,
                "fecha_portal": match.portal.fecha,
                "fecha_ref_portal": match.portal.fecha_referencia,
                "fila_portal": match.portal.fila,
                "op_portal": match.portal.op,
                "ref_portal": match.portal.referencia,
                "doc_portal": match.portal.documento,
                "descripcion_portal": match.portal.descripcion,
                "fecha_quiter": match.quiter.fecha,
                "fecha_ref_quiter": match.quiter.fecha_referencia,
                "fila_quiter": match.quiter.fila,
                "op_quiter": match.quiter.op,
                "ref_quiter": match.quiter.referencia,
                "doc_quiter": match.quiter.documento,
                "descripcion_quiter": match.quiter.descripcion,
            }
            for match in matches
        ]
    )


def pendientes_dataframe(resultado: ResultadoConciliacion) -> pd.DataFrame:
    movimientos = [
        ("Solo portal Habitualista", movimiento)
        for movimiento in resultado.pendientes_portal
    ] + [
        ("Solo Quiter", movimiento)
        for movimiento in resultado.pendientes_quiter
    ]
    return pd.DataFrame(
        [
            {
                "estado": estado,
                "origen": movimiento.origen,
                "tipo": movimiento.tipo,
                "importe": decimal_a_float(movimiento.importe),
                "fecha": movimiento.fecha,
                "fecha_referencia": movimiento.fecha_referencia,
                "fila_origen": movimiento.fila,
                "op": movimiento.op,
                "referencia": movimiento.referencia,
                "documento": movimiento.documento,
                "descripcion": movimiento.descripcion,
            }
            for estado, movimiento in movimientos
        ]
    )


def decimal_a_float(valor: Decimal) -> float:
    return float(valor.quantize(CENTAVOS))


def imprimir_resumen(resultado: ResultadoConciliacion, salida: Path) -> None:
    resumen = resumen_dataframe(resultado)
    print(resumen.to_string(index=False))
    print(f"Reporte generado: {salida}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Concilia Tarjeta Habitualista contra el mayor contable de Quiter."
    )
    parser.add_argument("--movimientos-cuenta", required=True, type=Path)
    parser.add_argument("--operaciones-pago", required=True, type=Path)
    parser.add_argument("--quiter", required=True, type=Path)
    parser.add_argument("--salida", default=Path("reporte_conciliacion.xlsx"), type=Path)
    parser.add_argument("--desde", type=lambda v: datetime.strptime(v, "%Y-%m-%d").date())
    parser.add_argument("--hasta", type=lambda v: datetime.strptime(v, "%Y-%m-%d").date())
    parser.add_argument("--tolerancia-dias", default=3, type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    desde, hasta = args.desde, args.hasta
    if not desde or not hasta:
        desde_nombre, hasta_nombre = rango_desde_nombres(
            [args.movimientos_cuenta, args.operaciones_pago]
        )
        desde = desde or desde_nombre
        hasta = hasta or hasta_nombre

    depositos = cargar_depositos_habitualista(args.movimientos_cuenta)
    pagos = cargar_pagos_habitualista(args.operaciones_pago)
    quiter = cargar_quiter(args.quiter, desde, hasta)

    resultado = conciliar(
        portal=[*depositos, *pagos],
        quiter=quiter,
        tolerancia_dias=args.tolerancia_dias,
    )
    escribir_excel(resultado, args.salida)
    imprimir_resumen(resultado, args.salida)


if __name__ == "__main__":
    main()
