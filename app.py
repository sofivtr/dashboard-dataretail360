import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from diseno import (
    NAVY, TEAL_GRAF, TEAL_TXT,
    aplicar_estilos, formato_grafico, tarjeta_kpi,
)

# 1. Configuración y estilos
st.set_page_config(page_title="DataRetail 360 | Desempeño Comercial Ene–Mar 2025", layout="wide")
aplicar_estilos()

DB_PATH = Path(__file__).resolve().parent / "dataretail360_dwh.db"


def fmt_mm(valor: float) -> str:
    return f"${valor:,.0f} MM".replace(",", ".")


def fmt_pct(valor: float, dec: int = 1) -> str:
    return f"{valor:.{dec}f}%".replace(".", ",")


@st.cache_data(ttl=300)
def cargar_ventas() -> pd.DataFrame:
    with sqlite3.connect(str(DB_PATH)) as con:
        df = pd.read_sql_query("SELECT * FROM vw_ventas_dashboard", con)
    df["fecha_dt"] = pd.to_datetime(df["fecha"])
    return df


df_total = cargar_ventas()


# ==============================================================================
# 2. ENCABEZADO + 2 FILTROS CLAROS (MES Y REGIÓN)
# ==============================================================================
col_titulo, col_f1, col_f2 = st.columns([2.5, 1.5, 2.0], vertical_alignment="top")

with col_titulo:
    st.markdown(
        f"<div style='color:{NAVY}; font-size:1.7rem; font-weight:700; line-height:1.2; margin-top:6px;'>DataRetail 360 · Desempeño comercial</div>",
        unsafe_allow_html=True,
    )
    st.caption("Ene–Mar 2025 · Fuente: DWH Capa Oro (fact_ventas y dimensiones conformadas)")

meses_disp = ["Enero", "Febrero", "Marzo"]
regiones_disp = sorted(df_total["region"].unique())

with col_f1:
    sel_mes = st.multiselect("Mes", meses_disp, default=[], placeholder="Todos los meses")
with col_f2:
    sel_region = st.multiselect("Región", regiones_disp, default=[], placeholder="Todas las regiones")
# Si dejan un filtro vacío, se consideran todas las opciones
meses_activos = sel_mes if sel_mes else meses_disp
regiones_activas = sel_region if sel_region else regiones_disp

df = df_total[
    df_total["nombre_mes"].isin(meses_activos)
    & df_total["region"].isin(regiones_activas)
].copy()


# ==============================================================================
# 3. FILA SUPERIOR: 4 TARJETAS KPI (SITUACIÓN)
# ==============================================================================
venta_neta_mm = df["monto_neto"].sum() / 1e6

# Meta proporcional al período y a la cantidad de sucursales de las regiones elegidas
prop_tiempo = df["fecha"].nunique() / 90
prop_sucursales = df["sucursal"].nunique() / df_total["sucursal"].nunique()
meta_venta_mm = 48_000 * prop_tiempo * prop_sucursales
var_venta = round(((venta_neta_mm / meta_venta_mm) - 1) * 100, 1) if meta_venta_mm else 0.0

venta_digital = df.loc[df["canal"].isin(["E-commerce", "App"]), "monto_neto"].sum()
share_digital = round((venta_digital / df["monto_neto"].sum() * 100), 1) if df["monto_neto"].sum() else 0.0
diff_dig = round(share_digital - 50.0, 1)
if diff_dig == 0:
    diff_dig = 0.0

tx_ok = (df["estado"] == "OK").sum()
ticket_prom = (df["monto_neto"].sum() / tx_ok) if tx_ok > 0 else 0
var_ticket = round(((ticket_prom / 500_000) - 1) * 100, 1)

tasa_dev = round((df["estado"] == "DEVUELTA").mean() * 100, 2)

c1, c2, c3, c4 = st.columns(4)
with c1:
    tipo = "meta" if var_venta >= 0 else "alerta"
    simb = "▲" if var_venta >= 0 else "▼"
    tarjeta_kpi("Ventas netas", fmt_mm(venta_neta_mm), f"{simb} {var_venta:+.1f}% vs meta".replace(".", ","), tipo)
with c2:
    tipo = "meta" if share_digital >= 50.0 else "vigilar"
    simb = "▲" if diff_dig >= 0 else "•"
    txt_dig = "▲ En meta (50%)" if diff_dig == 0 else f"{simb} {diff_dig:+.1f} pp vs meta 50%".replace(".", ",")
    tarjeta_kpi("Participación digital", fmt_pct(share_digital, 1), txt_dig, tipo)
with c3:
    tipo = "meta" if ticket_prom >= 500_000 else "vigilar"
    simb = "▲" if var_ticket >= 0 else "•"
    tarjeta_kpi("Ticket promedio neto", f"${ticket_prom:,.0f}".replace(",", "."), f"{simb} {var_ticket:+.1f}% vs meta $500k".replace(".", ","), tipo)
with c4:
    tipo = "meta" if tasa_dev <= 4.0 else ("vigilar" if tasa_dev <= 5.0 else "alerta")
    txt_dev = "▲ Meta ≤ 4%" if tipo == "meta" else ("• Vigilar · Meta ≤ 4%" if tipo == "vigilar" else "▼ Alerta · > 5%")
    tarjeta_kpi("Tasa de devolución", fmt_pct(tasa_dev, 2), txt_dev, tipo)

st.write("")


# ==============================================================================
# 4. FILA CENTRAL: VENTAS EN LÍNEA (ADAPTATIVA) + CANALES EN BARRAS
# ==============================================================================
col_izq, col_der = st.columns([1.15, 1])

with col_izq:
    if len(meses_activos) > 1:
        # Vista mensual: meta prorrateada por días reales (misma regla que la tarjeta KPI)
        evol = (
            df.groupby(["mes", "nombre_mes"], as_index=False)
            .agg(
                valor_mm=("monto_neto", lambda s: s.sum() / 1e6),
                dias=("fecha", "nunique"),
            )
            .sort_values("mes")
        )
        evol["meta_mm"] = (48_000 / 90) * evol["dias"] * prop_sucursales
        evol["etiqueta"] = evol["valor_mm"].apply(fmt_mm)

        pos_real = ["top center" if r >= m else "bottom center" for r, m in zip(evol["valor_mm"], evol["meta_mm"])]
        pos_meta = ["bottom center" if r >= m else "top center" for r, m in zip(evol["valor_mm"], evol["meta_mm"])]

        mejor = evol.loc[evol["valor_mm"].idxmax()]
        titulo_linea = f"Ventas netas lideradas por {mejor['nombre_mes'].lower()} ({fmt_mm(mejor['valor_mm'])})"

        fig_linea = px.line(
            evol, x="nombre_mes", y="valor_mm", text="etiqueta", markers=True,
            color_discrete_sequence=[NAVY], labels={"nombre_mes": "", "valor_mm": "Venta neta (MM CLP)"},
        )
        fig_linea.update_traces(
            name="Venta neta", showlegend=True, textposition=pos_real,
            cliponaxis=False, line=dict(width=3), marker=dict(size=9),
        )
        fig_linea.add_scatter(
            x=evol["nombre_mes"],
            y=evol["meta_mm"],
            mode="lines+markers+text",
            name="Meta proporcional",
            line=dict(color=TEAL_GRAF, width=2, dash="dash"),
            marker=dict(size=6, color=TEAL_GRAF),
            text=evol["meta_mm"].apply(lambda v: f"Meta {fmt_mm(v)}"),
            textposition=pos_meta,
            textfont=dict(color=TEAL_TXT, size=10),
            cliponaxis=False,
        )
        y_min = min(evol["valor_mm"].min(), evol["meta_mm"].min()) * 0.84
        y_max = max(evol["valor_mm"].max(), evol["meta_mm"].max()) * 1.16
    else:
        # Vista semanal en promedio diario (misma meta diaria base: $48.000 MM / 90 días)
        df["semana"] = pd.cut(
            df["fecha_dt"].dt.day,
            bins=[0, 7, 14, 21, 31],
            labels=["Sem 1", "Sem 2", "Sem 3", "Sem 4"],
        )
        evol = (
            df.groupby("semana", as_index=False, observed=False)
            .agg(
                venta_total=("monto_neto", "sum"),
                dias=("fecha", "nunique"),
            )
        )
        evol["valor_mm"] = (evol["venta_total"] / evol["dias"]) / 1e6
        evol["etiqueta"] = evol["valor_mm"].apply(lambda v: f"{fmt_mm(v)}/día")

        meta_periodo = (48_000 / 90) * prop_sucursales
        pos_real = ["top center" if r >= meta_periodo else "bottom center" for r in evol["valor_mm"]]
        titulo_linea = f"Venta diaria promedio por semana en {meses_activos[0]}"

        fig_linea = px.line(
            evol, x="semana", y="valor_mm", text="etiqueta", markers=True,
            color_discrete_sequence=[NAVY], labels={"semana": "", "valor_mm": "Venta diaria prom. (MM CLP)"},
        )
        fig_linea.update_traces(
            textposition=pos_real, cliponaxis=False, line=dict(width=3), marker=dict(size=9),
        )
        pos_meta = "bottom left" if evol.iloc[0]["valor_mm"] >= meta_periodo else "top left"
        fig_linea.add_hline(
            y=meta_periodo, line_dash="dash", line_width=1.5, line_color=TEAL_GRAF,
            annotation_text=f"Meta diaria {fmt_mm(meta_periodo)}",
            annotation_font_color=TEAL_TXT,
            annotation_position=pos_meta,
        )
        y_min = min(evol["valor_mm"].min(), meta_periodo) * 0.84
        y_max = max(evol["valor_mm"].max(), meta_periodo) * 1.16

    fig_linea = formato_grafico(fig_linea, titulo_linea, alto=340)
    fig_linea.update_layout(
        margin=dict(l=14, r=42, t=58, b=14),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1, title=None),
    )
    fig_linea.update_yaxes(range=[y_min, y_max])
    st.plotly_chart(fig_linea, use_container_width=True)

with col_der:
    # Comparación por Canal (siempre muestra los 3 canales ordenados)
    can = (
        df.groupby("canal", as_index=False)
        .agg(venta_mm=("monto_neto", lambda s: s.sum() / 1e6))
        .sort_values("venta_mm", ascending=True)
    )
    total_v = can["venta_mm"].sum()
    can["pct"] = (can["venta_mm"] / total_v * 100) if total_v else 0
    can["etiqueta"] = can.apply(lambda r: f"{fmt_mm(r['venta_mm'])} ({fmt_pct(r['pct'], 1)})", axis=1)
    can["grupo"] = can["canal"].apply(lambda c: "Digital" if c in ["E-commerce", "App"] else "Físico")

    fig_barras = px.bar(
        can, x="venta_mm", y="canal", orientation="h", color="grupo", text="etiqueta",
        color_discrete_map={"Digital": TEAL_GRAF, "Físico": NAVY},
        labels={"venta_mm": "", "canal": ""},
    )
    fig_barras.update_traces(textposition="outside", cliponaxis=False, width=0.5)
    titulo_barras = f"Canales digitales aportan el {fmt_pct(share_digital, 1)} de la venta neta"
    fig_barras = formato_grafico(fig_barras, titulo_barras, alto=340)
    fig_barras.update_layout(showlegend=False, margin=dict(l=14, r=115, t=50, b=14))
    fig_barras.update_xaxes(visible=False, range=[0, can["venta_mm"].max() * 1.48])
    fig_barras.update_yaxes(linecolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_barras, use_container_width=True)

st.write("")


# ==============================================================================
# 5. FILA INFERIOR: TABLA COMERCIAL DE PRODUCTOS (DETALLE PARA ACTUAR)
# ==============================================================================
st.markdown(f"<strong style='color:{NAVY};'>Detalle comercial: desempeño por producto (SKU)</strong>", unsafe_allow_html=True)

prod = (
    df[df["estado"] == "OK"]
    .sort_values("es_categoria_vigente")
    .groupby(["sku", "producto"], as_index=False)
    .agg(
        categoria=("categoria_historica", "last"),
        unidades=("cantidad", "sum"),
        venta_mm=("monto_neto", lambda s: s.sum() / 1e6),
    )
    .sort_values("venta_mm", ascending=False)
)

total_prod_mm = prod["venta_mm"].sum()
prod["participacion"] = ((prod["venta_mm"] / total_prod_mm) * 100).round(1) if total_prod_mm else 0
prod["venta_mm"] = prod["venta_mm"].round(1)

prod.columns = ["SKU", "Producto", "Categoría", "Unidades vendidas", "Venta neta (MM CLP)", "% de la venta"]
tabla_estilizada = prod.style.format({
    "Unidades vendidas": lambda v: f"{v:,.0f}".replace(",", "."),
    "Venta neta (MM CLP)": lambda v: f"${v:,.1f} MM".replace(",", "X").replace(".", ",").replace("X", "."),
    "% de la venta": lambda v: f"{v:.1f}%".replace(".", ","),
})
st.dataframe(tabla_estilizada, use_container_width=True, hide_index=True)