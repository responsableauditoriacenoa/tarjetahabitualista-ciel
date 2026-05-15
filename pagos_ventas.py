from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from io import BytesIO
from pathlib import Path
from typing import Iterable

import pandas as pd


CENTAVOS = Decimal("0.01")

RESUMEN_COLUMNS = ["concepto", "cantidad", "importe_total"]
DETECTADOS_COLUMNS = [
    "criterio",
    "fecha_pago",
    "nro_pago",
    "importe_pago",
    "op_pago",
    "ref_pago",
    "descripcion_pago",
    "refer_venta",
    "idv",
    "matricula",
    "cliente",
    "vendedor",
    "modelo",
    "saldo_venta",
    "fecha_factura",
    "fecha_entrega",
    "fila_pago",
    "fila_venta",
]
PAGOS_NO_DETECTADOS_COLUMNS = [
    "fecha_pago",
    "nro_pago",
    "importe_pago",
    "op_pago",
    "ref_pago",
    "motivo_revision",
    "descripcion_pago",
    "fila_pago",
]
VENTAS_SIN_PAGO_COLUMNS = [
    "refer_venta",
    "idv",
    "matricula",
    "cliente",
    "vendedor",
    "modelo",
    "saldo_venta",
    "fecha_matricula",
    "fecha_factura",
    "fecha_entrega",
    "fila_venta",
]


@dataclass(frozen=True)
class PagoOperacion:
    fila: int
    fecha: date | None
    nro_pago: str
    total: Decimal
    op: str
    referencia: str
    cliente_texto: str
    descripcion: str


@dataclass(frozen=True)
class VentaOperacion:
    fila: int
    fecha_matricula: date | None
    fecha_factura: date | None
    fecha_entrega: date | None
    referencia: str
    idv: str
    matricula: str
    cuenta_facturacion: str
    cliente: str
    vendedor: str
    modelo: str
    saldo: Decimal


@dataclass(frozen=True)
class MatchPagoVenta:
    pago: PagoOperacion
    venta: VentaOperacion
    criterio: str


@dataclass
class ResultadoPagosVentas:
    detectados: list[MatchPagoVenta]
    pagos_no_detectados: list[PagoOperacion]
    ventas_sin_pago: list[VentaOperacion]


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
    fecha = pd.to_datetime(str(valor).strip(), dayfirst=True, errors="coerce")
    return fecha.date() if pd.notna(fecha) else None


def limpiar_numero(valor: object) -> str:
    if pd.isna(valor):
        return ""
    texto = str(valor).strip()
    if texto.endswith(".0"):
        texto = texto[:-2]
    return re.sub(r"\D", "", texto)


def extraer_op(texto: object) -> str:
    match = re.search(r"\bOP\s*(\d+)\b", str(texto or ""), re.IGNORECASE)
    return match.group(1) if match else ""


def extraer_ref(texto: object) -> str:
    match = re.search(r"\bREF\.?\s*(\d+)\b", str(texto or ""), re.IGNORECASE)
    return match.group(1) if match else ""


def extraer_referencias_numericas(texto: object) -> list[str]:
    referencias: list[str] = []
    for match in re.findall(r"\b\d{5,10}\b", str(texto or "")):
        limpio = limpiar_numero(match)
        if limpio and limpio not in referencias:
            referencias.append(limpio)
    return referencias


def normalizar_texto(texto: object) -> str:
    sin_acentos = unicodedata.normalize("NFKD", str(texto or ""))
    ascii_texto = "".join(ch for ch in sin_acentos if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]+", " ", ascii_texto.upper())).strip()


def cliente_en_descripcion(cliente: str, descripcion: str) -> bool:
    cliente_norm = normalizar_texto(cliente)
    descripcion_norm = normalizar_texto(descripcion)
    palabras = [p for p in cliente_norm.split() if len(p) >= 4]
    if not palabras:
        return False
    return all(palabra in descripcion_norm for palabra in palabras)


def texto_combinado(*valores: object) -> str:
    return " ".join(str(v).strip() for v in valores if not pd.isna(v) and str(v).strip())


def cargar_pagos(path: Path) -> list[PagoOperacion]:
    df = pd.read_excel(path)
    if "Estado" in df.columns:
        df = df[df["Estado"].astype(str).str.lower().eq("liquidado")]

    pagos: list[PagoOperacion] = []
    for indice, fila in df.iterrows():
        descripcion = texto_combinado(fila.get("Motivo pago"), fila.get("Observaciones"))
        pagos.append(
            PagoOperacion(
                fila=indice + 2,
                fecha=normalizar_fecha(fila.get("Fecha")),
                nro_pago=limpiar_numero(fila.get("Nro de pago")),
                total=normalizar_importe(fila.get("Total")),
                op=extraer_op(descripcion),
                referencia=extraer_ref(descripcion),
                cliente_texto=str(fila.get("Motivo pago") or "").strip(),
                descripcion=descripcion,
            )
        )
    return pagos


def cargar_ventas(path: Path) -> list[VentaOperacion]:
    df = pd.read_excel(path)
    columnas = {normalizar_texto(col): col for col in df.columns}
    columna_referencia = (
        columnas.get("REFER")
        or columnas.get("REFERENCIA")
        or columnas.get("REF")
        or columnas.get("REFER.")
    )
    ventas: list[VentaOperacion] = []
    for indice, fila in df.iterrows():
        referencia = limpiar_numero(fila.get(columna_referencia)) if columna_referencia else ""
        if not referencia:
            referencia = detectar_referencia_venta(fila)
        if not referencia:
            continue
        ventas.append(
            VentaOperacion(
                fila=indice + 2,
                fecha_matricula=normalizar_fecha(fila.get("F.matric")),
                fecha_factura=normalizar_fecha(fila.get("Fec.fact")),
                fecha_entrega=normalizar_fecha(fila.get("Fec.entr")),
                referencia=referencia,
                idv=limpiar_numero(fila.get("IDV")),
                matricula=str(fila.get("Matricula") or "").strip(),
                cuenta_facturacion=limpiar_numero(fila.get("Cta.factur")),
                cliente=str(fila.get("Nombre cliente") or "").strip(),
                vendedor=str(fila.get("Vendedor") or "").strip(),
                modelo=str(fila.get("Modelo V.N.") or "").strip(),
                saldo=normalizar_importe(fila.get("Saldo")),
            )
        )
    return ventas


def detectar_referencia_venta(fila: pd.Series) -> str:
    candidatos: list[str] = []
    for valor in fila.values:
        numero = limpiar_numero(valor)
        if 100000 <= int(numero or "0") <= 9999999:
            candidatos.append(numero)

    # En los reportes de ventas, IDV y cuenta suelen ser de 5 digitos;
    # la referencia de operacion suele ser el primer numero de 7 digitos.
    for candidato in candidatos:
        if len(candidato) >= 7:
            return candidato
    return ""


def cargar_ventas_multiples(paths: Iterable[Path]) -> list[VentaOperacion]:
    ventas: list[VentaOperacion] = []
    vistos: set[tuple[str, str, str]] = set()
    for path in paths:
        for venta in cargar_ventas(path):
            clave = (venta.referencia, venta.idv, venta.matricula)
            if clave in vistos:
                continue
            vistos.add(clave)
            ventas.append(venta)
    return ventas


def conciliar_pagos_ventas(
    pagos: list[PagoOperacion],
    ventas: list[VentaOperacion],
) -> ResultadoPagosVentas:
    ventas_por_referencia: dict[str, list[VentaOperacion]] = {}
    for venta in ventas:
        ventas_por_referencia.setdefault(venta.referencia, []).append(venta)

    ventas_usadas: set[tuple[str, str, str]] = set()
    detectados: list[MatchPagoVenta] = []
    pagos_no_detectados: list[PagoOperacion] = []

    for pago in pagos:
        referencias_pago = referencias_posibles_pago(pago)
        opciones: list[VentaOperacion] = []
        criterio = ""
        for referencia_pago, origen_referencia in referencias_pago:
            opciones = ventas_por_referencia.get(referencia_pago, [])
            if opciones:
                criterio = f"{origen_referencia} = Refer. venta"
                break
        if not opciones:
            opciones = [
                venta
                for venta in ventas
                if len(venta.referencia) >= 5 and venta.referencia in referencias_pago_texto(pago)
            ]
            criterio = "Refer. venta encontrada en descripcion del pago"
        if not opciones:
            opciones = [
                venta
                for venta in ventas
                if cliente_en_descripcion(venta.cliente, pago.descripcion)
            ]
            criterio = "Cliente de venta encontrado en descripcion del pago"
            if len(opciones) != 1:
                opciones = []
        venta = opciones[0] if opciones else None
        if not venta:
            pagos_no_detectados.append(pago)
            continue

        ventas_usadas.add((venta.referencia, venta.idv, venta.matricula))
        detectados.append(MatchPagoVenta(pago=pago, venta=venta, criterio=criterio))

    ventas_sin_pago = [
        venta
        for venta in ventas
        if (venta.referencia, venta.idv, venta.matricula) not in ventas_usadas
    ]
    return ResultadoPagosVentas(detectados, pagos_no_detectados, ventas_sin_pago)


def referencias_posibles_pago(pago: PagoOperacion) -> list[tuple[str, str]]:
    referencias: list[tuple[str, str]] = []

    for valor, origen in (
        (pago.op, "OP del pago"),
        (pago.referencia, "REF del pago"),
    ):
        if valor and (valor, origen) not in referencias:
            referencias.append((valor, origen))

    for numero in extraer_referencias_numericas(pago.descripcion):
        item = (numero, "Numero en descripcion del pago")
        if item not in referencias:
            referencias.append(item)

    return referencias


def referencias_pago_texto(pago: PagoOperacion) -> set[str]:
    return {referencia for referencia, _origen in referencias_posibles_pago(pago)}


def ejecutar_conciliacion_pagos_ventas(
    operaciones_pago: Path,
    ventas_path: Path | Iterable[Path],
) -> ResultadoPagosVentas:
    pagos = cargar_pagos(operaciones_pago)
    if isinstance(ventas_path, Path):
        ventas = cargar_ventas(ventas_path)
    else:
        ventas = cargar_ventas_multiples(ventas_path)
    return conciliar_pagos_ventas(pagos, ventas)


def decimal_a_float(valor: Decimal) -> float:
    return float(valor.quantize(CENTAVOS))


def resumen_dataframe(resultado: ResultadoPagosVentas) -> pd.DataFrame:
    total_detectado = sum((m.pago.total for m in resultado.detectados), Decimal("0"))
    total_no_detectado = sum((p.total for p in resultado.pagos_no_detectados), Decimal("0"))
    saldo_ventas_sin_pago = sum((v.saldo for v in resultado.ventas_sin_pago), Decimal("0"))
    return pd.DataFrame(
        [
            {
                "concepto": "Pagos detectados en ventas",
                "cantidad": len(resultado.detectados),
                "importe_total": decimal_a_float(total_detectado),
            },
            {
                "concepto": "Pagos no detectados",
                "cantidad": len(resultado.pagos_no_detectados),
                "importe_total": decimal_a_float(total_no_detectado),
            },
            {
                "concepto": "Ventas sin pago detectado",
                "cantidad": len(resultado.ventas_sin_pago),
                "importe_total": decimal_a_float(saldo_ventas_sin_pago),
            },
        ],
        columns=RESUMEN_COLUMNS,
    )


def detectados_dataframe(matches: list[MatchPagoVenta]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "criterio": match.criterio,
                "fecha_pago": match.pago.fecha,
                "nro_pago": match.pago.nro_pago,
                "importe_pago": decimal_a_float(match.pago.total),
                "op_pago": match.pago.op,
                "ref_pago": match.pago.referencia,
                "descripcion_pago": match.pago.descripcion,
                "refer_venta": match.venta.referencia,
                "idv": match.venta.idv,
                "matricula": match.venta.matricula,
                "cliente": match.venta.cliente,
                "vendedor": match.venta.vendedor,
                "modelo": match.venta.modelo,
                "saldo_venta": decimal_a_float(match.venta.saldo),
                "fecha_factura": match.venta.fecha_factura,
                "fecha_entrega": match.venta.fecha_entrega,
                "fila_pago": match.pago.fila,
                "fila_venta": match.venta.fila,
            }
            for match in matches
        ],
        columns=DETECTADOS_COLUMNS,
    )


def pagos_no_detectados_dataframe(pagos: list[PagoOperacion]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "fecha_pago": pago.fecha,
                "nro_pago": pago.nro_pago,
                "importe_pago": decimal_a_float(pago.total),
                "op_pago": pago.op,
                "ref_pago": pago.referencia,
                "motivo_revision": "Sin OP en pago" if not pago.op else "OP no encontrado en ventas",
                "descripcion_pago": pago.descripcion,
                "fila_pago": pago.fila,
            }
            for pago in pagos
        ],
        columns=PAGOS_NO_DETECTADOS_COLUMNS,
    )


def ventas_sin_pago_dataframe(ventas: list[VentaOperacion]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "refer_venta": venta.referencia,
                "idv": venta.idv,
                "matricula": venta.matricula,
                "cliente": venta.cliente,
                "vendedor": venta.vendedor,
                "modelo": venta.modelo,
                "saldo_venta": decimal_a_float(venta.saldo),
                "fecha_matricula": venta.fecha_matricula,
                "fecha_factura": venta.fecha_factura,
                "fecha_entrega": venta.fecha_entrega,
                "fila_venta": venta.fila,
            }
            for venta in ventas
        ],
        columns=VENTAS_SIN_PAGO_COLUMNS,
    )


def escribir_hojas_excel(resultado: ResultadoPagosVentas, writer: pd.ExcelWriter) -> None:
    resumen_dataframe(resultado).to_excel(writer, sheet_name="Resumen", index=False)
    detectados_dataframe(resultado.detectados).to_excel(writer, sheet_name="Detectados", index=False)
    pagos_no_detectados_dataframe(resultado.pagos_no_detectados).to_excel(
        writer,
        sheet_name="Pagos no detectados",
        index=False,
    )
    ventas_sin_pago_dataframe(resultado.ventas_sin_pago).to_excel(
        writer,
        sheet_name="Ventas sin pago",
        index=False,
    )

    for sheet in writer.book.worksheets:
        sheet.freeze_panes = "A2"
        for column_cells in sheet.columns:
            width = min(max(len(str(cell.value or "")) for cell in column_cells) + 2, 70)
            sheet.column_dimensions[column_cells[0].column_letter].width = width


def excel_bytes(resultado: ResultadoPagosVentas) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        escribir_hojas_excel(resultado, writer)
    return buffer.getvalue()
