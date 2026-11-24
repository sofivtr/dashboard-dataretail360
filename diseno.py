import streamlit as st

# Paleta accesible oficial DataRetail 360 (PPT 3.1.1 — WCAG 2.2 AA, sin rojo/verde)
NAVY = "#0F2C4C"         # 14,1:1 vs blanco (títulos, KPIs, serie principal)
TEAL_GRAF = "#0E8C84"    # 4,1:1 (gráficos / meta)
TEAL_TXT = "#0A6B65"     # 6,4:1 (texto estado Meta)
DORADO_TXT = "#8A5D00"   # 5,8:1 (texto estado Vigilar)
ALERTA = "#A84F00"       # 5,6:1 (alerta en gráficos y texto)
GRIS = "#9AA7B2"         # Barras de contexto atenuadas


def aplicar_estilos():
    """Carga los estilos visuales para lograr el acabado limpio de las PPT."""
    st.markdown(
        """
        <style>
        div[data-testid="stMainBlockContainer"],
        .block-container {
            padding-top: 4.5rem !important;
            padding-bottom: 1.5rem !important;
        }
        .kpi-card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            padding: 16px 18px;
        }
        .kpi-label {
            font-size: 0.85rem;
            color: #64748B;
            font-weight: 600;
            margin-bottom: 4px;
        }
        .kpi-value {
            font-size: 1.9rem;
            color: #0F2C4C;
            font-weight: 800;
            line-height: 1.15;
            margin-bottom: 6px;
        }
        .kpi-status {
            font-size: 0.85rem;
            font-weight: 700;
        }
        div[data-testid="stPlotlyChart"] {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            padding: 8px 10px;
            overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def tarjeta_kpi(titulo: str, valor: str, texto_estado: str, tipo: str = "meta"):
    """Dibuja una tarjeta KPI limpia con símbolo + color accesible (PPT 3.3.1)."""
    colores = {
        "meta": TEAL_TXT,
        "vigilar": DORADO_TXT,
        "alerta": ALERTA,
    }
    color = colores.get(tipo, NAVY)
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{titulo}</div>
            <div class="kpi-value">{valor}</div>
            <div class="kpi-status" style="color:{color};">{texto_estado}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def formato_grafico(fig, titulo: str, alto: int = 340):
    """Aplica depuración anti-chartjunk (PPT 3.1.1 y 3.3.1): fondo blanco, sin grillas ni ruido."""
    fig.update_layout(
        template="simple_white",
        title=dict(text=titulo, font=dict(size=15, color=NAVY), x=0),
        font=dict(color=NAVY, size=12),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        height=alto,
        margin=dict(l=14, r=28, t=50, b=14),
    )
    fig.update_xaxes(showgrid=False, linecolor="#CBD5E1")
    fig.update_yaxes(showgrid=False, linecolor="#CBD5E1")
    return fig