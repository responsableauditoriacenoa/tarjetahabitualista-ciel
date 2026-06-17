from __future__ import annotations

import base64
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

import backups
import consolidado
import consolidado_contable
import pagos_ventas
from conciliacion import (
    conciliados_dataframe,
    ejecutar_conciliacion,
    excel_bytes,
    pendientes_dataframe,
    resumen_dataframe,
)

try:
    from conciliacion import ImportacionError
except ImportError:
    ImportacionError = ValueError

from storage import (
    UPLOADS_DIR,
    actualizar_conciliacion_pagos_ventas,
    cargar_dataframe,
    guardar_conciliacion,
    guardar_conciliacion_pagos_ventas,
    guardar_upload,
    inicializar_storage,
    listar_conciliaciones,
    listar_conciliaciones_pagos_ventas,
    listar_operaciones_pago_guardadas,
    nueva_corrida_id,
)


APP_TITLE = "Sistema de Conciliacion de Tarjeta Habitualista Ciel SA"
LOGO_PATH = Path("assets/logo_ciel.png")


st.set_page_config(
    page_title=APP_TITLE,
    page_icon="",
    layout="wide",
)


def aplicar_estilos() -> None:
    st.markdown(
        """
        <style>
        :root {
            --app-bg: #f3f6fa;
            --panel-bg: #ffffff;
            --text-main: #172033;
            --text-muted: #5f6b7a;
            --accent: #1667d9;
            --accent-dark: #0f4fa8;
            --border: #d9e1ec;
            --soft-border: #e7edf5;
            --input-bg: #ffffff;
        }

        .stApp {
            background: var(--app-bg);
            color: var(--text-main);
            font-size: 17px;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1480px;
        }

        h1 {
            font-size: 2.25rem !important;
            font-weight: 750 !important;
            color: var(--text-main);
            letter-spacing: 0;
            margin-bottom: 0.25rem !important;
        }

        h2, h3 {
            color: var(--text-main);
            letter-spacing: 0;
        }

        h3 {
            font-size: 1.45rem !important;
            font-weight: 700 !important;
            margin-top: 1.15rem !important;
        }

        label, .stMarkdown, .stCaption, .stTextInput label, .stDateInput label,
        .stNumberInput label, .stFileUploader label, .stMultiSelect label,
        .stSelectbox label {
            font-size: 1.02rem !important;
            color: var(--text-main) !important;
        }

        .stCaption, [data-testid="stCaptionContainer"] {
            color: var(--text-muted);
        }

        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--border);
        }

        [data-testid="stSidebar"] * {
            color: var(--text-main);
        }

        [data-testid="stSidebar"] .stButton > button {
            width: 100%;
            min-height: 48px;
            justify-content: flex-start;
            border-radius: 8px;
            border: 1px solid var(--border);
            background: #ffffff;
            color: var(--text-main);
            font-size: 1rem;
            font-weight: 650;
            margin-bottom: 0.55rem;
            white-space: normal;
            text-align: left;
            line-height: 1.2;
        }

        [data-testid="stSidebar"] .stButton > button:hover {
            border-color: var(--accent);
            background: #f0f6ff;
            color: var(--accent-dark);
        }

        .nav-active {
            width: 100%;
            min-height: 48px;
            display: flex;
            align-items: center;
            padding: 0 0.9rem;
            margin-bottom: 0.55rem;
            border-radius: 8px;
            background: #1667d9;
            color: #ffffff;
            font-size: 1rem;
            font-weight: 750;
            border: 1px solid #1667d9;
            box-shadow: 0 6px 14px rgba(22, 103, 217, 0.18);
            line-height: 1.2;
        }

        .app-hero {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.2rem 1.35rem;
            margin-bottom: 1.1rem;
            display: flex;
            align-items: center;
            gap: 1.25rem;
        }

        .app-logo {
            width: 112px;
            max-width: 24vw;
            height: auto;
            object-fit: contain;
            flex: 0 0 auto;
        }

        .app-hero-text {
            min-width: 0;
        }

        .app-hero p {
            color: var(--text-muted);
            margin: 0.25rem 0 0;
            font-size: 1.08rem;
        }

        @media (max-width: 720px) {
            .app-hero {
                align-items: flex-start;
                gap: 0.85rem;
            }

            .app-logo {
                width: 76px;
            }
        }

        [data-testid="stMetric"] {
            background: var(--panel-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem 1.05rem;
        }

        [data-testid="stMetricLabel"] {
            font-size: 1rem;
            color: var(--text-muted);
        }

        [data-testid="stMetricValue"] {
            font-size: 1.65rem;
            font-weight: 750;
            color: var(--text-main);
        }

        .stButton > button, .stDownloadButton > button,
        .stFormSubmitButton > button {
            min-height: 46px;
            border-radius: 8px;
            font-size: 1.03rem;
            font-weight: 700;
        }

        .stDownloadButton > button, .stFormSubmitButton > button {
            background: var(--accent);
            border-color: var(--accent);
            color: #ffffff;
        }

        .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {
            background: var(--accent-dark);
            border-color: var(--accent-dark);
            color: #ffffff;
        }

        .stTextInput input, .stDateInput input, .stNumberInput input {
            min-height: 44px;
            font-size: 1rem;
            background: var(--input-bg) !important;
            color: var(--text-main) !important;
            border-color: var(--border) !important;
            -webkit-text-fill-color: var(--text-main) !important;
        }

        [data-baseweb="select"] > div {
            min-height: 44px;
            background: var(--input-bg) !important;
            border-color: var(--border) !important;
            color: var(--text-main) !important;
        }

        [data-baseweb="select"] span,
        [data-baseweb="select"] input,
        [data-baseweb="select"] div {
            color: var(--text-main) !important;
            -webkit-text-fill-color: var(--text-main) !important;
        }

        [data-testid="stFileUploader"] section {
            background: #f8fafc !important;
            border: 1px dashed #b9c6d8 !important;
            border-radius: 8px !important;
            color: var(--text-main) !important;
        }

        [data-testid="stFileUploader"] section * {
            color: var(--text-main) !important;
        }

        [data-testid="stFileUploader"] button {
            background: #ffffff !important;
            border: 1px solid var(--border) !important;
            color: var(--accent-dark) !important;
        }

        [data-testid="stFileUploader"] button {
            font-size: 0 !important;
        }

        [data-testid="stFileUploader"] button::after {
            content: "Subir archivo";
            font-size: 1rem;
            color: var(--accent-dark);
            font-weight: 700;
            margin-left: 0.45rem;
        }

        [data-testid="stFileUploaderDropzoneInstructions"] span,
        [data-testid="stFileUploaderDropzoneInstructions"] small {
            font-size: 0 !important;
        }

        [data-testid="stFileUploaderDropzoneInstructions"] span::after {
            content: "Arrastrar y soltar archivos";
            font-size: 1rem;
            color: var(--text-main);
            font-weight: 700;
        }

        [data-testid="stFileUploaderDropzoneInstructions"] small::after {
            content: "Maximo 200MB por archivo";
            font-size: 0.92rem;
            color: var(--text-muted);
        }

        [data-testid="stDataFrame"] {
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
            background: #ffffff;
        }

        [data-testid="stDataFrame"] * {
            font-size: 0.98rem;
        }

        .stTabs [data-baseweb="tab"] {
            font-size: 1.05rem;
            font-weight: 700;
            padding-top: 0.85rem;
            padding-bottom: 0.85rem;
            color: var(--text-muted);
        }

        .stTabs [aria-selected="true"] {
            color: var(--accent) !important;
        }

        div[data-testid="stForm"] {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.25rem;
        }

        div[data-testid="stAlert"] {
            border-radius: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def logo_data_uri() -> str:
    if not LOGO_PATH.exists():
        return ""
    data = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


def render_header() -> None:
    logo_src = logo_data_uri()
    logo_html = f'<img class="app-logo" src="{logo_src}" alt="Ciel SA">' if logo_src else ""
    st.markdown(
        f"""
        <div class="app-hero">
            {logo_html}
            <div class="app-hero-text">
                <h1>{APP_TITLE}</h1>
                <p>Importacion, conciliacion y revision de movimientos contra Quiter.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def boton_navegacion(label: str, value: str) -> None:
    activo = st.session_state.get("pantalla", "Conciliacion de Pagos y Ventas") == value
    if activo:
        st.sidebar.markdown(f'<div class="nav-active">{label}</div>', unsafe_allow_html=True)
        return
    if st.sidebar.button(label, key=f"nav_{value}", use_container_width=True):
        st.session_state["pantalla"] = value
        st.rerun()


def formato_importe(valor: float) -> str:
    return f"$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formato_numero(valor: object) -> str:
    if pd.isna(valor):
        return ""
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return str(valor)
    if numero.is_integer():
        return f"{int(numero):,}".replace(",", ".")
    return f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def es_columna_importe(columna: str) -> bool:
    nombre = columna.lower()
    palabras_importe = ("importe", "total", "debe", "haber", "saldo", "monto")
    return any(palabra in nombre for palabra in palabras_importe)


def dataframe_para_pantalla(df: pd.DataFrame) -> pd.DataFrame:
    visible = df.copy()
    for columna in visible.columns:
        if pd.api.types.is_numeric_dtype(visible[columna]):
            if es_columna_importe(columna):
                visible[columna] = visible[columna].map(formato_importe)
            else:
                visible[columna] = visible[columna].map(formato_numero)
    return visible


def mostrar_metricas(resumen: pd.DataFrame) -> None:
    totales = resumen.sum(numeric_only=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Conciliados", formato_numero(totales.get("conciliados_cantidad", 0)))
    col2.metric("Total conciliado", formato_importe(float(totales.get("conciliados_total", 0))))
    col3.metric("Pendientes portal", formato_numero(totales.get("pendientes_portal_cantidad", 0)))
    col4.metric("Pendientes Quiter", formato_numero(totales.get("pendientes_quiter_cantidad", 0)))


def mostrar_metricas_pagos_ventas(resumen: pd.DataFrame) -> None:
    valores = resumen.set_index("concepto") if not resumen.empty else pd.DataFrame()

    def valor(concepto: str, columna: str) -> float:
        if concepto not in valores.index or columna not in valores.columns:
            return 0
        return float(valores.loc[concepto, columna])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Pagos detectados",
        formato_numero(valor("Pagos detectados en ventas", "cantidad")),
    )
    col2.metric(
        "Importe detectado",
        formato_importe(valor("Pagos detectados en ventas", "importe_total")),
    )
    col3.metric(
        "Pagos no detectados",
        formato_numero(valor("Pagos no detectados", "cantidad")),
    )
    col4.metric(
        "Importe no detectado",
        formato_importe(valor("Pagos no detectados", "importe_total")),
    )


def mostrar_metricas_consolidado(resumen: pd.DataFrame) -> None:
    valores = resumen.set_index("concepto") if not resumen.empty else pd.DataFrame()

    def valor(concepto: str, columna: str) -> float:
        if concepto not in valores.index or columna not in valores.columns:
            return 0
        return float(valores.loc[concepto, columna])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Pagos en base", formato_numero(valor("Pagos en base", "cantidad")))
    col2.metric("Pagos conciliados", formato_numero(valor("Pagos conciliados con ventas", "cantidad")))
    col3.metric("Pagos sin venta", formato_numero(valor("Pagos no conciliados", "cantidad")))
    col4.metric("Total pagos", formato_importe(valor("Pagos en base", "importe_total")))


def mostrar_metricas_contable(resumen: pd.DataFrame) -> None:
    totales = resumen.sum(numeric_only=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Mov. portal", formato_numero(totales.get("portal_cantidad", 0)))
    col2.metric("Mov. Quiter", formato_numero(totales.get("quiter_cantidad", 0)))
    col3.metric("Conciliados", formato_numero(totales.get("conciliados_cantidad", 0)))
    col4.metric("Total conciliado", formato_importe(float(totales.get("conciliados_total", 0))))


def mostrar_tabla(df: pd.DataFrame, key: str) -> None:
    if df.empty:
        st.info("No hay movimientos para mostrar.")
        return

    filtrado = df
    if "tipo" in df.columns:
        tipo = st.multiselect(
            "Tipo",
            sorted(df["tipo"].dropna().unique()),
            default=sorted(df["tipo"].dropna().unique()),
            key=f"{key}_tipo",
        )
        filtrado = df[df["tipo"].isin(tipo)] if tipo else df

    if "estado" in filtrado.columns:
        estado = st.multiselect(
            "Estado",
            sorted(filtrado["estado"].dropna().unique()),
            default=sorted(filtrado["estado"].dropna().unique()),
            key=f"{key}_estado",
        )
        filtrado = filtrado[filtrado["estado"].isin(estado)] if estado else filtrado

    busqueda = st.text_input("Buscar en descripcion, OP o referencia", key=f"{key}_buscar")
    if busqueda:
        texto = busqueda.lower()
        columnas = [c for c in filtrado.columns if filtrado[c].dtype == "object"]
        mascara = filtrado[columnas].fillna("").apply(
            lambda row: row.astype(str).str.lower().str.contains(texto).any(),
            axis=1,
        )
        filtrado = filtrado[mascara]

    st.dataframe(dataframe_para_pantalla(filtrado), use_container_width=True, hide_index=True)


def guardar_uploads_corrida(corrida_id: str, movimientos, pagos, quiter) -> tuple[Path, Path, Path]:
    carpeta = UPLOADS_DIR / corrida_id
    movimientos_path = guardar_upload(movimientos, carpeta / movimientos.name)
    pagos_path = guardar_upload(pagos, carpeta / pagos.name)
    quiter_path = guardar_upload(quiter, carpeta / quiter.name)
    return movimientos_path, pagos_path, quiter_path


def guardar_uploads_pagos_ventas(corrida_id: str, pagos, ventas) -> tuple[Path, Path]:
    carpeta = UPLOADS_DIR / "pagos_ventas" / corrida_id
    pagos_path = guardar_upload(pagos, carpeta / pagos.name)
    ventas_path = guardar_upload(ventas, carpeta / ventas.name)
    return pagos_path, ventas_path


def guardar_venta_pagos_ventas(corrida_id: str, ventas) -> Path:
    carpeta = UPLOADS_DIR / "pagos_ventas" / corrida_id
    return guardar_upload(ventas, carpeta / ventas.name)


def guardar_ventas_pagos_ventas(corrida_id: str, ventas_files) -> list[Path]:
    carpeta = UPLOADS_DIR / "pagos_ventas" / corrida_id
    return [guardar_upload(ventas, carpeta / ventas.name) for ventas in ventas_files]


def pantalla_importacion() -> None:
    st.subheader("Importar reportes")

    with st.form("form_importacion"):
        nombre = st.text_input("Nombre de la conciliacion", value=f"Conciliacion {date.today().isoformat()}")
        col1, col2, col3 = st.columns(3)
        with col1:
            movimientos = st.file_uploader("Movimientos de cuenta", type=["xlsx"])
        with col2:
            pagos = st.file_uploader("Operaciones de pago", type=["xlsx"])
        with col3:
            quiter = st.file_uploader("Mayor contable Quiter", type=["xls", "xlsx"])

        col_fecha1, col_fecha2, col_tol = st.columns([1, 1, 1])
        with col_fecha1:
            desde = st.date_input("Desde", value=date(2026, 4, 1))
        with col_fecha2:
            hasta = st.date_input("Hasta", value=date(2026, 4, 30))
        with col_tol:
            tolerancia = st.number_input("Tolerancia dias depositos", min_value=0, max_value=30, value=3)

        ejecutar = st.form_submit_button("Conciliar", type="primary")

    if not ejecutar:
        return

    if not movimientos or not pagos or not quiter:
        st.error("Cargue los tres reportes para ejecutar la conciliacion.")
        return

    with st.spinner("Procesando conciliacion..."):
        try:
            corrida_id = nueva_corrida_id()
            movimientos_path, pagos_path, quiter_path = guardar_uploads_corrida(
                corrida_id, movimientos, pagos, quiter
            )
            resultado = ejecutar_conciliacion(
                movimientos_path,
                pagos_path,
                quiter_path,
                desde=desde,
                hasta=hasta,
                tolerancia_dias=int(tolerancia),
            )
            reporte_bytes = excel_bytes(resultado)
            guardada = guardar_conciliacion(
                nombre=nombre,
                desde=desde,
                hasta=hasta,
                tolerancia_dias=int(tolerancia),
                movimientos_path=movimientos_path,
                pagos_path=pagos_path,
                quiter_path=quiter_path,
                resultado=resultado,
                reporte_bytes=reporte_bytes,
            )
        except ImportacionError as exc:
            st.error(str(exc))
            return

    st.session_state["conciliacion_actual"] = guardada.id
    st.success("Conciliacion generada y guardada.")
    backup_path = backups.crear_backup("conciliacion_puntual")
    st.info(f"Backup automatico generado: {backup_path.name}")
    mostrar_resultado_actual(
        resumen_dataframe(resultado),
        conciliados_dataframe(resultado.conciliados),
        pendientes_dataframe(resultado),
        reporte_bytes,
        f"reporte_conciliacion_{guardada.id}.xlsx",
    )


def mostrar_resultado_actual(
    resumen: pd.DataFrame,
    conciliados: pd.DataFrame,
    pendientes: pd.DataFrame,
    reporte_bytes: bytes,
    nombre_archivo: str,
) -> None:
    mostrar_metricas(resumen)
    st.download_button(
        "Descargar reporte Excel",
        data=reporte_bytes,
        file_name=nombre_archivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    tab_resumen, tab_conciliados, tab_pendientes = st.tabs(
        ["Resumen", "Conciliados", "No conciliados"]
    )
    with tab_resumen:
        st.dataframe(dataframe_para_pantalla(resumen), use_container_width=True, hide_index=True)
    with tab_conciliados:
        mostrar_tabla(conciliados, "actual_conciliados")
    with tab_pendientes:
        mostrar_tabla(pendientes, "actual_pendientes")


def pantalla_historial() -> None:
    st.subheader("Historial y descargas")
    st.caption(
        "El historial registra las importaciones realizadas y permite descargar los reportes "
        "consolidados vigentes de cada conciliacion."
    )

    col_ventas, col_contable = st.columns(2)
    with col_ventas:
        st.markdown("### Conciliacion de Pagos y Ventas")
        st.download_button(
            "Descargar consolidado pagos y ventas",
            data=consolidado.excel_bytes_consolidado(),
            file_name="reporte_consolidado_ventas_pagos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="historial_download_consolidado_ventas",
            use_container_width=True,
        )
    with col_contable:
        st.markdown("### Conciliacion Contable")
        st.download_button(
            "Descargar ultima conciliacion contable visible",
            data=consolidado_contable.excel_bytes_consolidado(),
            file_name="reporte_contable_consolidado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="historial_download_consolidado_contable",
            use_container_width=True,
        )

    tabs = st.tabs(
        [
            "Importaciones pagos y ventas",
            "Conciliaciones contables guardadas",
            "Importaciones contables",
        ]
    )

    with tabs[0]:
        mostrar_tabla(consolidado.historial_importaciones(), "historial_importaciones_consolidado")

    with tabs[1]:
        historial_contable = consolidado_contable.historial_conciliaciones()
        if historial_contable.empty:
            st.info("Todavia no hay conciliaciones contables guardadas.")
        else:
            opciones = {
                f"{row.creada} | {row.id}": row.id
                for row in historial_contable.itertuples(index=False)
            }
            seleccion = st.selectbox(
                "Seleccionar conciliacion contable",
                list(opciones.keys()),
                key="historial_contable_select",
            )
            conciliacion_id = opciones[seleccion]
            st.download_button(
                "Descargar conciliacion contable seleccionada",
                data=consolidado_contable.reporte_conciliacion_bytes(conciliacion_id),
                file_name=f"reporte_contable_{conciliacion_id}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"historial_download_contable_{conciliacion_id}",
            )
            mostrar_tabla(historial_contable, "historial_conciliaciones_contables")

    with tabs[2]:
        mostrar_tabla(consolidado_contable.historial_importaciones(), "historial_importaciones_contable")


def mostrar_resultado_pagos_ventas(
    resumen: pd.DataFrame,
    detectados: pd.DataFrame,
    no_detectados: pd.DataFrame,
    ventas_sin_pago: pd.DataFrame,
    reporte_bytes: bytes,
    nombre_archivo: str,
    key_prefix: str,
) -> None:
    mostrar_metricas_pagos_ventas(resumen)
    st.download_button(
        "Descargar reporte Excel",
        data=reporte_bytes,
        file_name=nombre_archivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"{key_prefix}_download",
    )

    tab_resumen, tab_detectados, tab_no_detectados, tab_ventas = st.tabs(
        ["Resumen", "Detectados", "Pagos no detectados", "Ventas sin pago"]
    )
    with tab_resumen:
        st.dataframe(dataframe_para_pantalla(resumen), use_container_width=True, hide_index=True)
    with tab_detectados:
        mostrar_tabla(detectados, f"{key_prefix}_detectados")
    with tab_no_detectados:
        mostrar_tabla(no_detectados, f"{key_prefix}_no_detectados")
    with tab_ventas:
        mostrar_tabla(ventas_sin_pago, f"{key_prefix}_ventas_sin_pago")


def pantalla_pagos_ventas() -> None:
    st.subheader("Pagos relacionados a operaciones de ventas")
    bases_pagos = listar_operaciones_pago_guardadas()
    historial = listar_conciliaciones_pagos_ventas()

    with st.form("form_pagos_ventas"):
        nombre = st.text_input(
            "Nombre de la conciliacion",
            value=f"Pagos vs ventas {date.today().isoformat()}",
            key="nombre_pagos_ventas",
        )

        modos = []
        if historial:
            modos.append("Actualizar control guardado")
        if bases_pagos:
            modos.append("Usar operaciones de pago guardadas")
        modos.append("Subir nuevas operaciones de pago")
        modo = st.radio(
            "Base de operaciones de pago",
            modos,
            horizontal=True,
        )

        pagos = None
        pagos_guardados_path: Path | None = None
        control_base = None

        if modo == "Actualizar control guardado":
            opciones_control = {f"{c.creada} | {c.nombre} | {c.id}": c for c in historial}
            seleccion_control = st.selectbox("Control a actualizar", list(opciones_control.keys()))
            control_base = opciones_control[seleccion_control]
            pagos_guardados_path = control_base.pagos_path
            ventas_acumuladas = len([p for p in control_base.ventas_paths if p.exists()])
            st.caption(
                f"Base: {pagos_guardados_path.name} | Reportes de ventas acumulados: {ventas_acumuladas}"
            )
        elif modo == "Usar operaciones de pago guardadas":
            opciones_pagos = {base.etiqueta: base for base in bases_pagos}
            seleccion_pagos = st.selectbox("Operaciones de pago guardadas", list(opciones_pagos.keys()))
            pagos_guardados_path = opciones_pagos[seleccion_pagos].path
            st.caption(f"Archivo base: {pagos_guardados_path.name}")

        col1, col2 = st.columns(2)
        with col1:
            if modo == "Subir nuevas operaciones de pago":
                pagos = st.file_uploader("Operaciones de pago", type=["xlsx"], key="pagos_ventas_pagos")
            else:
                st.text_input(
                    "Operaciones de pago",
                    value=pagos_guardados_path.name if pagos_guardados_path else "",
                    disabled=True,
                )
        with col2:
            ventas = st.file_uploader(
                "Nuevo reporte de ventas",
                type=["xls", "xlsx"],
                key="pagos_ventas_ventas",
                accept_multiple_files=True,
            )

        ejecutar = st.form_submit_button("Detectar operaciones de venta", type="primary")

    if ejecutar:
        if not ventas:
            st.error("Cargue al menos un reporte de ventas para ejecutar el control.")
            return
        if modo in ("Usar operaciones de pago guardadas", "Actualizar control guardado") and not pagos_guardados_path:
            st.error("Seleccione una base de operaciones de pago guardada.")
            return
        if modo == "Subir nuevas operaciones de pago" and not pagos:
            st.error("Cargue Operaciones de pago para crear o reemplazar la base.")
            return

        with st.spinner("Detectando pagos relacionados a ventas..."):
            corrida_id = nueva_corrida_id()
            if modo == "Actualizar control guardado" and control_base:
                pagos_path = control_base.pagos_path
                nuevos_ventas_paths = guardar_ventas_pagos_ventas(corrida_id, ventas)
                ventas_paths = [path for path in control_base.ventas_paths if path.exists()]
                ventas_paths.extend(nuevos_ventas_paths)
                ventas_path = nuevos_ventas_paths[-1]
            elif modo == "Usar operaciones de pago guardadas":
                pagos_path = pagos_guardados_path
                ventas_paths = guardar_ventas_pagos_ventas(corrida_id, ventas)
                ventas_path = ventas_paths[-1]
            else:
                carpeta = UPLOADS_DIR / "pagos_ventas" / corrida_id
                pagos_path = guardar_upload(pagos, carpeta / pagos.name)
                ventas_paths = guardar_ventas_pagos_ventas(corrida_id, ventas)
                ventas_path = ventas_paths[-1]
            resultado = pagos_ventas.ejecutar_conciliacion_pagos_ventas(pagos_path, ventas_paths)
            resumen = pagos_ventas.resumen_dataframe(resultado)
            detectados = pagos_ventas.detectados_dataframe(resultado.detectados)
            no_detectados = pagos_ventas.pagos_no_detectados_dataframe(resultado.pagos_no_detectados)
            ventas_sin_pago = pagos_ventas.ventas_sin_pago_dataframe(resultado.ventas_sin_pago)
            reporte_bytes = pagos_ventas.excel_bytes(resultado)
            if modo == "Actualizar control guardado" and control_base:
                guardada = actualizar_conciliacion_pagos_ventas(
                    guardada=control_base,
                    ventas_path=ventas_path,
                    ventas_paths=ventas_paths,
                    resumen=resumen,
                    detectados=detectados,
                    no_detectados=no_detectados,
                    ventas_sin_pago=ventas_sin_pago,
                    reporte_bytes=reporte_bytes,
                )
            else:
                guardada = guardar_conciliacion_pagos_ventas(
                    nombre=nombre,
                    pagos_path=pagos_path,
                    ventas_path=ventas_path,
                    resumen=resumen,
                    detectados=detectados,
                    no_detectados=no_detectados,
                    ventas_sin_pago=ventas_sin_pago,
                    reporte_bytes=reporte_bytes,
                    ventas_paths=ventas_paths,
                )

        st.success("Control actualizado y guardado." if modo == "Actualizar control guardado" else "Control generado y guardado.")
        backup_path = backups.crear_backup("pagos_vs_ventas")
        st.info(f"Backup automatico generado: {backup_path.name}")
        mostrar_resultado_pagos_ventas(
            resumen,
            detectados,
            no_detectados,
            ventas_sin_pago,
            reporte_bytes,
            f"reporte_pagos_ventas_{guardada.id}.xlsx",
            "pagos_ventas_actual",
        )

    st.markdown("### Historial de pagos vs ventas")
    historial = listar_conciliaciones_pagos_ventas()
    if not historial:
        st.info("Todavia no hay controles de pagos vs ventas guardados.")
        return

    opciones = {f"{c.creada} | {c.nombre} | {c.id}": c for c in historial}
    seleccion = st.selectbox("Seleccionar control guardado", list(opciones.keys()))
    guardada = opciones[seleccion]

    resumen = pd.DataFrame(guardada.resumen)
    detectados = cargar_dataframe(guardada.detectados_path)
    no_detectados = cargar_dataframe(guardada.no_detectados_path)
    ventas_sin_pago = cargar_dataframe(guardada.ventas_sin_pago_path)
    reporte_bytes = guardada.reporte_path.read_bytes() if guardada.reporte_path.exists() else b""

    st.caption(f"ID: {guardada.id}")
    mostrar_resultado_pagos_ventas(
        resumen,
        detectados,
        no_detectados,
        ventas_sin_pago,
        reporte_bytes,
        f"reporte_pagos_ventas_{guardada.id}.xlsx",
        f"pagos_ventas_{guardada.id}",
    )


def pantalla_base_consolidada() -> None:
    st.subheader("Conciliacion de Pagos y Ventas")

    with st.form("form_base_consolidada"):
        col1, col2 = st.columns(2)
        with col1:
            pagos_files = st.file_uploader(
                "Operaciones de pago",
                type=["xlsx"],
                accept_multiple_files=True,
                key="consolidado_pagos",
            )
        with col2:
            ventas_files = st.file_uploader(
                "Reportes de ventas",
                type=["xls", "xlsx"],
                accept_multiple_files=True,
                key="consolidado_ventas",
            )

        ejecutar = st.form_submit_button("Importar y recalcular base", type="primary")

    if ejecutar:
        if not pagos_files and not ventas_files:
            st.error("Cargue al menos un reporte de pagos o ventas.")
            return

        with st.spinner("Importando, actualizando duplicados y recalculando conciliacion total..."):
            stats = consolidado.importar_a_base(pagos_files or [], ventas_files or [])

        st.success(
            "Base actualizada: "
            f"pagos nuevos {stats['pagos_insertados']}, pagos actualizados {stats['pagos_actualizados']}, "
            f"ventas nuevas {stats['ventas_insertadas']}, ventas actualizadas {stats['ventas_actualizadas']}."
        )
        backup_path = backups.crear_backup("base_ventas_pagos")
        st.info(f"Backup automatico generado: {backup_path.name}")

    dfs = consolidado.dataframes_consolidados()
    resumen = dfs["resumen"]
    mostrar_metricas_consolidado(resumen)

    reporte_bytes = consolidado.excel_bytes_consolidado()
    st.download_button(
        "Descargar reporte consolidado Excel",
        data=reporte_bytes,
        file_name="reporte_consolidado_ventas_pagos.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download_consolidado",
    )

    tabs = st.tabs(
        [
            "Resumen",
            "Pagos conciliados",
            "Pagos no conciliados",
            "Ventas sin pago",
            "Base pagos",
            "Base ventas",
            "Importaciones",
        ]
    )
    with tabs[0]:
        st.dataframe(dataframe_para_pantalla(resumen), use_container_width=True, hide_index=True)
    with tabs[1]:
        mostrar_tabla(dfs["pagos_detectados"], "consolidado_pagos_detectados")
    with tabs[2]:
        mostrar_tabla(dfs["pagos_no_detectados"], "consolidado_pagos_no_detectados")
    with tabs[3]:
        mostrar_tabla(dfs["ventas_sin_pago"], "consolidado_ventas_sin_pago")
    with tabs[4]:
        mostrar_tabla(dfs["pagos"], "consolidado_base_pagos")
    with tabs[5]:
        mostrar_tabla(dfs["ventas"], "consolidado_base_ventas")
    with tabs[6]:
        mostrar_tabla(consolidado.historial_importaciones(), "consolidado_importaciones")


def pantalla_base_contable() -> None:
    st.subheader("Conciliacion Contable de Tarjeta Habitualista S/ Contabilidad")
    st.caption(
        "Este modulo concilia solo los archivos cargados en cada corrida. "
        "La conciliacion actual se reemplaza con cada nueva importacion y el resultado queda guardado en Historial."
    )

    with st.form("form_base_contable"):
        col1, col2, col3 = st.columns(3)
        with col1:
            pagos_files = st.file_uploader(
                "Operaciones de pago",
                type=["xlsx"],
                accept_multiple_files=True,
                key="contable_pagos",
            )
        with col2:
            movimientos_files = st.file_uploader(
                "Movimientos de cuenta",
                type=["xlsx"],
                accept_multiple_files=True,
                key="contable_movimientos",
            )
        with col3:
            quiter_files = st.file_uploader(
                "Contabilidad Quiter",
                type=["xls", "xlsx"],
                accept_multiple_files=True,
                key="contable_quiter",
            )

        col_fecha1, col_fecha2, col_tol = st.columns(3)
        with col_fecha1:
            desde = st.date_input("Desde Quiter", value=date(2026, 1, 1), key="contable_desde")
        with col_fecha2:
            hasta = st.date_input("Hasta Quiter", value=date.today(), key="contable_hasta")
        with col_tol:
            tolerancia = st.number_input(
                "Tolerancia dias",
                min_value=0,
                max_value=30,
                value=3,
                key="contable_tolerancia",
            )

        ejecutar = st.form_submit_button("Conciliar archivos y guardar historial", type="primary")

    if ejecutar:
        if not quiter_files:
            st.error("Cargue el mayor de Contabilidad Quiter para ejecutar la conciliacion.")
            return
        if not pagos_files and not movimientos_files:
            st.error("Cargue al menos Operaciones de pago o Movimientos de cuenta.")
            return
        with st.spinner("Conciliando solo los archivos cargados y guardando el resultado en historial..."):
            try:
                stats = consolidado_contable.importar_a_base(
                    pagos_files or [],
                    movimientos_files or [],
                    quiter_files or [],
                    desde=desde,
                    hasta=hasta,
                    tolerancia_dias=int(tolerancia),
                )
            except ImportacionError as exc:
                st.error(str(exc))
                return
        st.success(
            "Conciliacion contable guardada: "
            f"movimientos portal {stats['portal_insertados']}, "
            f"movimientos Quiter {stats['quiter_insertados']}."
        )
        backup_path = backups.crear_backup("base_contable")
        st.info(f"Backup automatico generado: {backup_path.name}")

    dfs = consolidado_contable.dataframes_consolidados()
    resumen = dfs["resumen"]
    mostrar_metricas_contable(resumen)
    reporte_bytes = consolidado_contable.excel_bytes_consolidado()
    st.download_button(
        "Descargar conciliacion contable actual Excel",
        data=reporte_bytes,
        file_name="reporte_contable_consolidado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download_contable_consolidado",
    )

    tabs = st.tabs(
        [
            "Resumen",
            "Conciliados",
            "Pendientes portal",
            "Pendientes Quiter",
            "Base portal",
            "Base Quiter",
            "Historial guardado",
        ]
    )
    with tabs[0]:
        st.dataframe(dataframe_para_pantalla(resumen), use_container_width=True, hide_index=True)
    with tabs[1]:
        mostrar_tabla(dfs["conciliados"], "contable_conciliados")
    with tabs[2]:
        mostrar_tabla(dfs["portal_pendiente"], "contable_portal_pendiente")
    with tabs[3]:
        mostrar_tabla(dfs["quiter_pendiente"], "contable_quiter_pendiente")
    with tabs[4]:
        mostrar_tabla(dfs["portal"], "contable_base_portal")
    with tabs[5]:
        mostrar_tabla(dfs["quiter"], "contable_base_quiter")
    with tabs[6]:
        historial = consolidado_contable.historial_conciliaciones()
        if historial.empty:
            st.info("Todavia no hay conciliaciones contables guardadas.")
        else:
            opciones = {
                f"{row.creada} | {row.id}": row.id
                for row in historial.itertuples(index=False)
            }
            seleccion = st.selectbox(
                "Seleccionar conciliacion guardada",
                list(opciones.keys()),
                key="contable_historial_select",
            )
            conciliacion_id = opciones[seleccion]
            st.download_button(
                "Descargar conciliacion guardada",
                data=consolidado_contable.reporte_conciliacion_bytes(conciliacion_id),
                file_name=f"reporte_contable_{conciliacion_id}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"download_contable_historial_{conciliacion_id}",
            )
            mostrar_tabla(historial, "contable_importaciones")


def pantalla_backups() -> None:
    st.subheader("Backups y restauracion")
    st.caption(
        "El backup guarda la carpeta data completa: base SQLite, archivos importados y reportes generados."
    )

    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("Crear backup ahora", type="primary", use_container_width=True):
            backup_path = backups.crear_backup("manual")
            st.success(f"Backup creado: {backup_path.name}")

    with col2:
        restore_file = st.file_uploader("Restaurar desde backup ZIP", type=["zip"], key="restore_backup")
        confirmar = st.checkbox("Confirmo que quiero reemplazar la base actual por este backup")
        if restore_file and confirmar and st.button("Restaurar backup", use_container_width=True):
            backups.restaurar_backup(restore_file)
            st.success("Backup restaurado. Recargue la app para ver los datos restaurados.")

    st.markdown("### Backups disponibles")
    archivos = backups.listar_backups()
    if not archivos:
        st.info("Todavia no hay backups generados.")
        return

    for path in archivos:
        col_name, col_download = st.columns([3, 1])
        with col_name:
            st.write(f"{path.name} ({path.stat().st_size / 1024:.1f} KB)")
        with col_download:
            st.download_button(
                "Descargar",
                data=path.read_bytes(),
                file_name=path.name,
                mime="application/zip",
                key=f"download_{path.name}",
                use_container_width=True,
            )


def main() -> None:
    inicializar_storage()
    aplicar_estilos()

    if "pantalla" not in st.session_state:
        st.session_state["pantalla"] = "Conciliacion de Pagos y Ventas"
    if st.session_state["pantalla"] in ("Importar y conciliar", "Pagos vs ventas"):
        st.session_state["pantalla"] = "Conciliacion de Pagos y Ventas"

    st.sidebar.markdown("### Menu")
    boton_navegacion("Conciliacion de Pagos y Ventas", "Conciliacion de Pagos y Ventas")
    boton_navegacion("Conciliacion Contable de Tarjeta Habitualista S/ Contabilidad", "Conciliacion Contable de Tarjeta Habitualista S/ Contabilidad")
    boton_navegacion("Historial", "Historial")
    boton_navegacion("Backups", "Backups")
    st.sidebar.markdown("---")
    st.sidebar.caption("Los datos se guardan localmente en la carpeta data.")

    render_header()
    pantalla = st.session_state["pantalla"]
    if pantalla in ("Base consolidada", "Conciliacion de Pagos y Ventas"):
        pantalla_base_consolidada()
    elif pantalla in ("Base contable", "Conciliacion Contable de Tarjeta Habitualista S/ Contabilidad"):
        pantalla_base_contable()
    elif pantalla == "Backups":
        pantalla_backups()
    else:
        pantalla_historial()


if __name__ == "__main__":
    main()
