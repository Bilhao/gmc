"""GMC Enterprise Management Platform - Plataforma Completa de Gestão Estratégica.

Construída para a competição Global Management Challenge (GMC).
Design System: Dark Dashboard Executivo (fiel ao estilo plataforma_gestao_gmc.html).
"""
from __future__ import annotations

import copy
import io
import json
import os
import sys
from pathlib import Path

# Garantir que a raiz do projeto está no sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# Importar módulos do motor GMC (suporta execução como pacote ou raiz do repo)
try:
    from gmc_app.data import (
        Quarter,
        admin_frame,
        companies_frame,
        kpi_frame,
        load_folder,
        product_frame,
        product_market_frame,
    )
    from gmc_app.engine import (
        Alert,
        SimulationResult,
        get_aggressive_decisions,
        get_conservative_decisions,
        get_recommended_decisions,
        simulate_quarter,
    )
    from gmc_app.params import (
        ASSEMBLY_MIN_MIN,
        INSURANCE,
        MACHINE_MIN,
        MARKETS,
        MP_PER_UNIT,
        PRODUCT_NAMES,
        PRODUCTS,
        REJECT_VALUE,
        WARRANTY_COST,
    )
except ImportError:
    from data import (
        Quarter,
        admin_frame,
        companies_frame,
        kpi_frame,
        load_folder,
        product_frame,
        product_market_frame,
    )
    from engine import (
        Alert,
        SimulationResult,
        get_aggressive_decisions,
        get_conservative_decisions,
        get_recommended_decisions,
        simulate_quarter,
    )
    from params import (
        ASSEMBLY_MIN_MIN,
        INSURANCE,
        MACHINE_MIN,
        MARKETS,
        MP_PER_UNIT,
        PRODUCT_NAMES,
        PRODUCTS,
        REJECT_VALUE,
        WARRANTY_COST,
    )

# ----------------------------------------------------------------------------------------
# Configuração da Página
# ----------------------------------------------------------------------------------------
st.set_page_config(
    page_title="GMC Enterprise | Plataforma 360º",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------------------
# Gestão de Tema Nativo do Streamlit (Sincronizado automaticamente via menu nativo)
# ----------------------------------------------------------------------------------------
try:
    from streamlit_theme import st_theme
    active_theme = st_theme()
except Exception:
    active_theme = None

if active_theme and "base" in active_theme:
    is_dark = active_theme["base"] == "dark"
    st.session_state["is_dark"] = is_dark
elif "is_dark" in st.session_state:
    is_dark = st.session_state["is_dark"]
else:
    # Padrão: Modo Escuro Executivo (Design System oficial GMC)
    is_dark = True

if is_dark:
    theme_css = """
    :root {
        --bg-main: #090d16;
        --bg-sidebar: #0f172a;
        --bg-card: #0f172a;
        --bg-card-subtle: #090d16;
        --border-color: #1e293b;
        --border-hover: #334155;
        --text-title: #ffffff;
        --text-main: #f8fafc;
        --text-muted: #94a3b8;
        --text-sub: #cbd5e1;
        --gauge-track: #1e293b;
        --input-bg: #0b1120;
        --input-border: #334155;
    }
    .stApp {
        background-color: #090d16 !important;
        color: #f8fafc !important;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid #1e293b !important;
    }
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] p {
        color: #cbd5e1 !important;
    }
    header[data-testid="stHeader"] {
        background-color: rgba(15, 23, 42, 0.75) !important;
        backdrop-filter: blur(8px) !important;
        border-bottom: 1px solid #1e293b !important;
    }
    .kpi-card, .gauge-card {
        background-color: #0f172a !important;
        border: 1px solid #1e293b !important;
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.25);
        margin-bottom: 12px;
        color: #f8fafc !important;
    }
    .kpi-card:hover, .gauge-card:hover {
        border-color: #334155 !important;
    }
    .kpi-header, .gauge-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }
    .kpi-label, .gauge-title {
        font-size: 0.75rem;
        font-weight: 600;
        color: #94a3b8 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-val-green { font-size: 1.85rem; font-weight: 800; color: #34d399 !important; line-height: 1.2; }
    .kpi-val-white { font-size: 1.85rem; font-weight: 800; color: #ffffff !important; line-height: 1.2; }
    .kpi-val-purple { font-size: 1.85rem; font-weight: 800; color: #c084fc !important; line-height: 1.2; }
    .kpi-val-amber { font-size: 1.85rem; font-weight: 800; color: #fbbf24 !important; line-height: 1.2; }
    .kpi-val-blue { font-size: 1.85rem; font-weight: 800; color: #60a5fa !important; line-height: 1.2; }
    .gauge-value { font-size: 1.45rem; font-weight: 800; color: #ffffff !important; margin-top: 4px; }
    .kpi-sub, .gauge-sub { font-size: 0.74rem; color: #94a3b8 !important; margin-top: 4px; }

    .badge-pill { font-size: 0.68rem; font-weight: 700; padding: 2px 8px; border-radius: 4px; display: inline-block; }
    .badge-green { background-color: #052e16 !important; color: #34d399 !important; border: 1px solid #166534 !important; }
    .badge-blue { background-color: #172554 !important; color: #60a5fa !important; border: 1px solid #1e40af !important; }
    .badge-purple { background-color: #3b0764 !important; color: #c084fc !important; border: 1px solid #6b21a8 !important; }
    .badge-amber { background-color: #451a03 !important; color: #fbbf24 !important; border: 1px solid #92400e !important; }
    .badge-red { background-color: #450a0a !important; color: #f87171 !important; border: 1px solid #991b1b !important; }

    .strategic-card-amber {
        background: linear-gradient(135deg, rgba(69, 26, 3, 0.45) 0%, #0f172a 100%) !important;
        border: 1px solid rgba(245, 158, 11, 0.45) !important; border-left: 4px solid #f59e0b !important;
        border-radius: 12px; padding: 16px 18px; margin-bottom: 14px;
    }
    .strategic-card-green {
        background: linear-gradient(135deg, rgba(6, 78, 59, 0.45) 0%, #0f172a 100%) !important;
        border: 1px solid rgba(16, 185, 129, 0.45) !important; border-left: 4px solid #10b981 !important;
        border-radius: 12px; padding: 16px 18px; margin-bottom: 14px;
    }
    .strategic-card-blue {
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.45) 0%, #0f172a 100%) !important;
        border: 1px solid rgba(59, 130, 246, 0.45) !important; border-left: 4px solid #3b82f6 !important;
        border-radius: 12px; padding: 16px 18px; margin-bottom: 14px;
    }
    .strategic-card-red {
        background: linear-gradient(135deg, rgba(69, 10, 10, 0.45) 0%, #0f172a 100%) !important;
        border: 1px solid rgba(239, 68, 68, 0.45) !important; border-left: 4px solid #ef4444 !important;
        border-radius: 12px; padding: 16px 18px; margin-bottom: 14px;
    }
    .strategic-title { font-size: 0.82rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
    .strategic-body { font-size: 0.8rem; color: #cbd5e1 !important; line-height: 1.55; }
    .gauge-track { width: 100%; background-color: #1e293b !important; height: 7px; border-radius: 4px; margin-top: 10px; overflow: hidden; }

    div[data-baseweb="input"] { background-color: #0b1120 !important; border: 1px solid #334155 !important; border-radius: 6px !important; }
    div[data-baseweb="input"] input { color: #f8fafc !important; }
    div[data-baseweb="input"] button { color: #94a3b8 !important; }
    div[data-baseweb="select"] { background-color: #0b1120 !important; border: 1px solid #334155 !important; border-radius: 6px !important; }
    div[data-baseweb="select"] * { color: #f8fafc !important; }
    div[data-testid="stRadio"] label span { color: #cbd5e1 !important; font-size: 0.82rem !important; }
    div[data-testid="stRadio"] > label { color: #94a3b8 !important; font-size: 0.72rem !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.5px !important; }
    button[kind="secondary"] { background-color: #1e293b !important; color: #f8fafc !important; border: 1px solid #334155 !important; border-radius: 8px !important; }
    button[kind="secondary"]:hover { background-color: #334155 !important; color: #ffffff !important; }
    button[kind="primary"] { background-color: #2563eb !important; color: #ffffff !important; border: none !important; border-radius: 8px !important; }
    button[kind="primary"]:hover { background-color: #3b82f6 !important; }
    button[data-baseweb="tab"] { color: #94a3b8 !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #60a5fa !important; border-bottom: 2px solid #3b82f6 !important; }
    div[data-testid="stDataFrame"] { border: 1px solid #1e293b !important; }
    """
else:
    theme_css = """
    :root {
        --bg-main: #f8fafc;
        --bg-sidebar: #ffffff;
        --bg-card: #ffffff;
        --bg-card-subtle: #f1f5f9;
        --border-color: #e2e8f0;
        --border-hover: #cbd5e1;
        --text-title: #0f172a;
        --text-main: #0f172a;
        --text-muted: #64748b;
        --text-sub: #334155;
        --gauge-track: #e2e8f0;
        --input-bg: #ffffff;
        --input-border: #cbd5e1;
    }
    .stApp {
        background-color: #f8fafc !important;
        color: #0f172a !important;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] p {
        color: #334155 !important;
    }
    header[data-testid="stHeader"] {
        background-color: rgba(255, 255, 255, 0.85) !important;
        backdrop-filter: blur(8px) !important;
        border-bottom: 1px solid #e2e8f0 !important;
    }
    .kpi-card, .gauge-card {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
        margin-bottom: 12px;
        color: #0f172a !important;
    }
    .kpi-card:hover, .gauge-card:hover {
        border-color: #cbd5e1 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
    }
    .kpi-header, .gauge-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }
    .kpi-label, .gauge-title {
        font-size: 0.75rem;
        font-weight: 600;
        color: #64748b !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-val-green { font-size: 1.85rem; font-weight: 800; color: #059669 !important; line-height: 1.2; }
    .kpi-val-white { font-size: 1.85rem; font-weight: 800; color: #0f172a !important; line-height: 1.2; }
    .kpi-val-purple { font-size: 1.85rem; font-weight: 800; color: #7c3aed !important; line-height: 1.2; }
    .kpi-val-amber { font-size: 1.85rem; font-weight: 800; color: #d97706 !important; line-height: 1.2; }
    .kpi-val-blue { font-size: 1.85rem; font-weight: 800; color: #2563eb !important; line-height: 1.2; }
    .gauge-value { font-size: 1.45rem; font-weight: 800; color: #0f172a !important; margin-top: 4px; }
    .kpi-sub, .gauge-sub { font-size: 0.74rem; color: #64748b !important; margin-top: 4px; }

    .badge-pill { font-size: 0.68rem; font-weight: 700; padding: 2px 8px; border-radius: 4px; display: inline-block; }
    .badge-green { background-color: #dcfce7 !important; color: #15803d !important; border: 1px solid #86efac !important; }
    .badge-blue { background-color: #dbeafe !important; color: #1d4ed8 !important; border: 1px solid #93c5fd !important; }
    .badge-purple { background-color: #f3e8ff !important; color: #7e22ce !important; border: 1px solid #d8b4fe !important; }
    .badge-amber { background-color: #fef3c7 !important; color: #b45309 !important; border: 1px solid #fcd34d !important; }
    .badge-red { background-color: #fee2e2 !important; color: #b91c1c !important; border: 1px solid #fca5a5 !important; }

    .strategic-card-amber {
        background: #fffbeb !important; border: 1px solid #fde68a !important; border-left: 4px solid #f59e0b !important;
        border-radius: 12px; padding: 16px 18px; margin-bottom: 14px;
    }
    .strategic-card-green {
        background: #f0fdf4 !important; border: 1px solid #bbf7d0 !important; border-left: 4px solid #10b981 !important;
        border-radius: 12px; padding: 16px 18px; margin-bottom: 14px;
    }
    .strategic-card-blue {
        background: #eff6ff !important; border: 1px solid #bfdbfe !important; border-left: 4px solid #3b82f6 !important;
        border-radius: 12px; padding: 16px 18px; margin-bottom: 14px;
    }
    .strategic-card-red {
        background: #fef2f2 !important; border: 1px solid #fecaca !important; border-left: 4px solid #ef4444 !important;
        border-radius: 12px; padding: 16px 18px; margin-bottom: 14px;
    }
    .strategic-title { font-size: 0.82rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
    .strategic-body { font-size: 0.8rem; color: #334155 !important; line-height: 1.55; }
    .gauge-track { width: 100%; background-color: #e2e8f0 !important; height: 7px; border-radius: 4px; margin-top: 10px; overflow: hidden; }

    div[data-baseweb="input"] { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; border-radius: 6px !important; }
    div[data-baseweb="input"] input { color: #0f172a !important; }
    div[data-baseweb="input"] button { color: #64748b !important; }
    div[data-baseweb="select"] { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; border-radius: 6px !important; }
    div[data-baseweb="select"] * { color: #0f172a !important; }
    div[data-testid="stRadio"] label span { color: #1e293b !important; font-size: 0.82rem !important; }
    div[data-testid="stRadio"] > label { color: #64748b !important; font-size: 0.72rem !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.5px !important; }
    button[kind="secondary"] { background-color: #f1f5f9 !important; color: #0f172a !important; border: 1px solid #cbd5e1 !important; border-radius: 8px !important; }
    button[kind="secondary"]:hover { background-color: #e2e8f0 !important; color: #0f172a !important; }
    button[kind="primary"] { background-color: #2563eb !important; color: #ffffff !important; border: none !important; border-radius: 8px !important; }
    button[kind="primary"]:hover { background-color: #3b82f6 !important; }
    button[data-baseweb="tab"] { color: #64748b !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #2563eb !important; border-bottom: 2px solid #2563eb !important; }
    div[data-testid="stDataFrame"] { border: 1px solid #e2e8f0 !important; }
    """

st.markdown(f"<style>{theme_css}</style>", unsafe_allow_html=True)


# ----------------------------------------------------------------------------------------
# Função de Tema Dinâmico para Gráficos Plotly
# ----------------------------------------------------------------------------------------
def apply_theme(fig: go.Figure, is_dark: bool = True, height: int = 300, title: str = "") -> go.Figure:
    paper_bg = "#0f172a" if is_dark else "#ffffff"
    grid_color = "#1e293b" if is_dark else "#e2e8f0"
    text_color = "#94a3b8" if is_dark else "#64748b"
    title_color = "#f8fafc" if is_dark else "#0f172a"

    fig.update_layout(
        title=dict(text=title, font=dict(color=title_color, size=13, family="system-ui")),
        paper_bgcolor=paper_bg,
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=text_color, family="system-ui, -apple-system, sans-serif"),
        height=height,
        margin=dict(l=20, r=20, t=40, b=25),
        xaxis=dict(gridcolor=grid_color, zerolinecolor=grid_color, color=text_color),
        yaxis=dict(gridcolor=grid_color, zerolinecolor=grid_color, color=text_color),
        legend=dict(font=dict(color=text_color)),
    )
    return fig


# ----------------------------------------------------------------------------------------
# Carregamento de Dados com Cache
# ----------------------------------------------------------------------------------------
@st.cache_data
def load_history_data():
    candidates = [
        os.path.join(Path(__file__).resolve().parent, "History"),
        os.path.join(ROOT_DIR, "History"),
        "History",
    ]
    for folder in candidates:
        if os.path.exists(folder):
            qs = load_folder(folder)
            if qs:
                return qs
    st.error("Pasta 'History' não encontrada!")
    return []

quarters = load_history_data()

if not quarters:
    st.error("Não foram encontrados relatórios históricos na pasta History/")
    st.stop()

# Último trimestre concluído
last_quarter = quarters[-1]  # Y15Q1

# DataFrames analíticos
df_kpi = kpi_frame(quarters)
df_prod_mkt = product_market_frame(quarters)
df_prod = product_frame(quarters)
df_admin = admin_frame(quarters)
df_comp = companies_frame(last_quarter)


# ----------------------------------------------------------------------------------------
# Barra Lateral (Design Fiel à Sidebar da Plataforma)
# ----------------------------------------------------------------------------------------
with st.sidebar:
    # Header com Logótipo GMC
    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: space-between; padding-bottom: 12px; border-bottom: 1px solid var(--border-color); margin-bottom: 14px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 32px; height: 32px; border-radius: 8px; background: #2563eb; display: flex; align-items: center; justify-content: center; font-weight: 800; color: white; font-size: 13px; box-shadow: 0 4px 10px rgba(37,99,235,0.4);">GMC</div>
            <div>
                <div style="font-weight: 800; font-size: 14px; color: var(--text-title); line-height: 1.1;">GMC Enterprise</div>
                <div style="font-size: 10px; color: var(--text-muted); font-weight: 500;">Plataforma de Gestão 360º</div>
            </div>
        </div>
        <span class="badge-pill badge-green">Y15Q2</span>
    </div>
    """, unsafe_allow_html=True)

    menu = st.radio(
        "COCKPIT & DECISÕES",
        [
            "🏢 Visão Executiva & KPIs",
            "🎯 Simulador de Decisões Y15Q2",
            "📈 Marketing & Vendas",
            "🏭 Produção & Supply Chain",
            "👥 Recursos Humanos",
            "💰 Finanças & Balanço",
            "📜 Arquivo Histórico (5Q)",
            "👥 Inteligência Competitiva (Grupo)",
            "📚 Parâmetros Oficiais GMC",
        ],
        index=0,
    )

    st.markdown("---")
    
    # Rodapé da Barra Lateral com Dados da Empresa 1
    st.markdown(f"""
    <div style="background-color: var(--bg-card-subtle); border: 1px solid var(--border-color); border-radius: 8px; padding: 12px; font-size: 11px; color: var(--text-muted);">
        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>Empresa:</span> <strong style="color: var(--text-title);">Nº 1 (Grupo {last_quarter.group.get('group_no', 0)})</strong></div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>Cotação Atual:</span> <strong style="color: #34d399;">111.32 €</strong></div>
        <div style="display: flex; justify-content: space-between;"><span>Decisão Alvo:</span> <span style="color: #60a5fa; font-weight: 700;">Y15Q2 (1º Competição)</span></div>
    </div>
    """, unsafe_allow_html=True)


# ========================================================================================
# VISTA 1: COCKPIT EXECUTIVO & KPIS
# ========================================================================================
if menu == "🏢 Visão Executiva & KPIs":
    # Top App Bar
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 14px; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 14px; font-weight: 800; color: var(--text-title); text-transform: uppercase; letter-spacing: 0.5px;">Cockpit Executivo & Scorecard</span>
            <span style="color: var(--text-muted);">|</span>
            <span style="font-size: 12px; color: var(--text-muted);">Global Management Challenge 2026/2027</span>
        </div>
        <span class="badge-pill badge-blue">Y15Q1 Fechado</span>
    </div>
    """, unsafe_allow_html=True)

    # 1. Top 4 KPIs Banner (Exatamente igual a plataforma_gestao_gmc.html)
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-label">Cotação da Ação (Bolsa)</span>
                <span class="badge-pill badge-green">+4,3%</span>
            </div>
            <div class="kpi-val-green">111.32 €</div>
            <div class="kpi-sub">+26,4% de valorização desde Y14Q1</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_col2:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-label">Faturação Trimestral</span>
                <span class="badge-pill badge-blue">+8,3%</span>
            </div>
            <div class="kpi-val-white">€ 1.267.611</div>
            <div class="kpi-sub">Margem Bruta de 50,6% (€ 641.061)</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_col3:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-label">Resultado Operacional (EBIT)</span>
                <span class="badge-pill badge-purple">11,8% Margem</span>
            </div>
            <div class="kpi-val-purple">€ 149.635</div>
            <div class="kpi-sub">Lucro Líquido: € 151.779 (EPS: € 5,06)</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_col4:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-label">Tesouraria (Caixa Total)</span>
                <span class="badge-pill badge-amber">Atenção</span>
            </div>
            <div class="kpi-val-amber">€ 1.052.013</div>
            <div class="kpi-sub">€ 1,15M em depósito | € 98k a descoberto</div>
        </div>
        """, unsafe_allow_html=True)

    # 2. 3 Strategic Priority Cards (Estilo gradient com bordas coloridas)
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    c_a, c_b, c_c = st.columns(3)

    with c_a:
        st.markdown("""
        <div class="strategic-card-amber">
            <div class="strategic-title" style="color: #fbbf24;">
                <span>⚠️</span> ALERTA 1: Rutura de Matéria-Prima
            </div>
            <div class="strategic-body">
                Restam apenas <strong>1.468 unidades</strong> e não há encomendas a chegar em Q2. Se a produção consumir 4.850 unidades sem compras spot de 4.000 un, o simulador acionará compras automáticas com sobretaxas pesadas!
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c_b:
        st.markdown("""
        <div class="strategic-card-green">
            <div class="strategic-title" style="color: #34d399;">
                <span>⭐</span> ALERTA 2: Major Improvement no P1
            </div>
            <div class="strategic-body">
                O <strong>Produto 1 tem um Grande Melhoramento pronto a introduzir</strong>. Em Q1 teve 76 chamadas de garantia. Com apenas 44 un em stock, o risco de obsolescência é nulo. Ativar em Q2 disparará a procura e a cotação.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c_c:
        st.markdown("""
        <div class="strategic-card-blue">
            <div class="strategic-title" style="color: #60a5fa;">
                <span>👥</span> ALERTA 3: 21 Operários Disponíveis
            </div>
            <div class="strategic-body">
                A equipa de montagem passou de 17 para <strong>21 operários especializados</strong> (12.096 horas disponíveis). É fundamental subir a montagem para 125 min no P1 para eliminar avarias e evitar pagar horas ociosas.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 3. Gráficos de Tendência Histórica (Trajetória Financeira & Cotação em Bolsa)
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    g_col1, g_col2 = st.columns(2)

    with g_col1:
        fig_fin = go.Figure()
        fig_fin.add_trace(go.Scatter(
            x=df_kpi.index, y=df_kpi["Vendas"], name="Vendas (€)",
            line=dict(color="#3b82f6", width=3), mode="lines+markers",
            marker=dict(size=7, color="#3b82f6"),
        ))
        fig_fin.add_trace(go.Scatter(
            x=df_kpi.index, y=df_kpi["Resultado Líquido"], name="Lucro Líquido (€)",
            line=dict(color="#10b981", width=3), mode="lines+markers",
            marker=dict(size=7, color="#10b981"),
        ))
        apply_theme(fig_fin, is_dark=is_dark, height=310, title="Trajetória Financeira (Y14Q1 - Y15Q1)")
        st.plotly_chart(fig_fin, width="stretch")

    with g_col2:
        fig_share = go.Figure()
        fig_share.add_trace(go.Scatter(
            x=df_kpi.index, y=df_kpi["Cotação"], name="Cotação (€)",
            line=dict(color="#34d399", width=3), mode="lines+markers+text",
            marker=dict(size=8, color="#34d399"),
            text=[f"{v:.2f}" for v in df_kpi["Cotação"]],
            textposition="top center",
            textfont=dict(color="#f8fafc" if is_dark else "#0f172a", size=10),
        ))
        apply_theme(fig_share, is_dark=is_dark, height=310, title="Cotação da Ação em Bolsa (Share Price)")
        st.plotly_chart(fig_share, width="stretch")

    # 4. Análise DuPont e Rentabilidade
    st.markdown("""
    <div style="font-size: 13px; font-weight: 700; color: var(--text-title); text-transform: uppercase; margin-top: 10px; margin-bottom: 10px;">
        🔬 Decomposição DuPont do ROE (Y15Q1)
    </div>
    """, unsafe_allow_html=True)

    latest_kpi = df_kpi.loc[last_quarter.label]
    net_margin = (latest_kpi["Resultado Líquido"] / latest_kpi["Vendas"]) if latest_kpi["Vendas"] else 0
    asset_turnover = (latest_kpi["Vendas"] / latest_kpi["Activo Total"]) if latest_kpi["Activo Total"] else 0
    equity_multiplier = (latest_kpi["Activo Total"] / latest_kpi["Capitais Próprios"]) if latest_kpi["Capitais Próprios"] else 0
    calc_roe = (net_margin * asset_turnover * equity_multiplier) * 100

    dp1, dp2, dp3, dp4 = st.columns(4)
    with dp1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">1. Margem Líquida</div>
            <div class="kpi-val-blue">{net_margin * 100:.2f} %</div>
            <div class="kpi-sub">Resultado Líquido / Vendas</div>
        </div>
        """, unsafe_allow_html=True)
    with dp2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">2. Rotação do Ativo</div>
            <div class="kpi-val-white">{asset_turnover:.3f} x</div>
            <div class="kpi-sub">Vendas / Ativo Total</div>
        </div>
        """, unsafe_allow_html=True)
    with dp3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">3. Alavancagem Financeira</div>
            <div class="kpi-val-purple">{equity_multiplier:.2f} x</div>
            <div class="kpi-sub">Ativo Total / Capitais Próprios</div>
        </div>
        """, unsafe_allow_html=True)
    with dp4:
        st.markdown(f"""
        <div class="kpi-card" style="border-left: 4px solid #10b981;">
            <div class="kpi-label">ROE Consolidado</div>
            <div class="kpi-val-green">{calc_roe:.2f} %</div>
            <div class="kpi-sub">Retorno Trimestral dos Acionistas</div>
        </div>
        """, unsafe_allow_html=True)


# ========================================================================================
# VISTA 2: SIMULADOR DE DECISÕES Y15Q2 (DESIGN FIEL AO HTML)
# ========================================================================================
elif menu == "🎯 Simulador de Decisões Y15Q2":
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 14px; margin-bottom: 16px;">
        <div>
            <span style="font-size: 14px; font-weight: 800; color: var(--text-title); text-transform: uppercase; letter-spacing: 0.5px;">Simulador de Decisões Estratégicas</span>
            <span style="color: var(--text-muted); margin: 0 8px;">|</span>
            <span style="font-size: 12px; color: var(--text-muted);">Y15Q2 - Ciclo de Competição Ativo</span>
        </div>
        <span class="badge-pill badge-green">Restrições em Tempo Real</span>
    </div>
    """, unsafe_allow_html=True)

    if "decisions" not in st.session_state:
        st.session_state["decisions"] = get_recommended_decisions(last_quarter)

    cur_dec = st.session_state["decisions"]

    # 1. Preset Scenarios Selector (Idêntico ao painel de botões do HTML)
    st.markdown("""
    <div style="background-color: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 14px 18px; margin-bottom: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
            <div>
                <div style="font-size: 13px; font-weight: 700; color: var(--text-title);">🎮 Motor de Decisão com 3 Cenários Pré-Configurados</div>
                <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">Selecione uma estratégia e o simulador recalcula automaticamente todas as restrições fabris e projeções financeiras.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    btn_c1, btn_c2, btn_c3, btn_c4 = st.columns([1.2, 1.2, 1.2, 1.5])
    with btn_c1:
        if st.button("⚡ 1. Otimizado (Recomendado)", width="stretch"):
            st.session_state["decisions"] = get_recommended_decisions(last_quarter)
            st.rerun()
    with btn_c2:
        if st.button("🔥 2. Expansão Agressiva", width="stretch"):
            st.session_state["decisions"] = get_aggressive_decisions(last_quarter)
            st.rerun()
    with btn_c3:
        if st.button("🛡️ 3. Conservador", width="stretch"):
            st.session_state["decisions"] = get_conservative_decisions(last_quarter)
            st.rerun()
    with btn_c4:
        st.caption("👈 Carregue um preset para atualizar todos os parâmetros e testar.")

    # Executar a simulação determinística
    sim_res = simulate_quarter(last_quarter, cur_dec)

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # 2. 4 Real-Time Constraint Gauges (Idêntico ao grid de 4 caixas do HTML)
    g1, g2, g3, g4 = st.columns(4)

    mp_nec = sim_res.operations["mp_total_needed"]
    mp_disp = sim_res.operations["mp_start"] + sim_res.operations["mp_spot_ordered"]
    mp_pct = min(100.0, (mp_nec / mp_disp * 100.0)) if mp_disp else 100.0
    mp_ok = mp_disp >= mp_nec

    with g1:
        badge_cls = "badge-green" if mp_ok else "badge-red"
        badge_txt = "SUFICIENTE" if mp_ok else "ROTURA!"
        bar_color = "#10b981" if mp_ok else "#ef4444"
        st.markdown(f"""
        <div class="gauge-card" style="border-color: {'rgba(16, 185, 129, 0.5)' if mp_ok else 'rgba(239, 68, 68, 0.6)'};">
            <div class="gauge-header">
                <span class="gauge-title">Matéria-Prima (Supply)</span>
                <span class="badge-pill {badge_cls}">{badge_txt}</span>
            </div>
            <div class="gauge-value">{mp_nec:,.0f} un</div>
            <div class="gauge-sub">Disponível: <strong style="color: {'#34d399' if mp_ok else '#f87171'};">{mp_disp:,.0f} un</strong></div>
            <div class="gauge-track">
                <div style="background-color: {bar_color}; width: {min(100, mp_pct):.1f}%; height: 7px; border-radius: 4px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with g2:
        maq_nec = sim_res.operations["mach_hours_needed"]
        maq_cap = sim_res.operations["mach_hours_effective"]
        maq_pct = (maq_nec / maq_cap * 100.0) if maq_cap else 0
        maq_ok = maq_nec <= maq_cap
        badge_maq_cls = "badge-green" if maq_ok else "badge-red"
        badge_maq_txt = f"{maq_pct:.1f}% USO" if maq_ok else "SOBRECARGA!"
        bar_maq_color = "#10b981" if maq_pct <= 95 else ("#f59e0b" if maq_ok else "#ef4444")
        st.markdown(f"""
        <div class="gauge-card" style="border-color: {'rgba(16, 185, 129, 0.5)' if maq_ok else 'rgba(239, 68, 68, 0.6)'};">
            <div class="gauge-header">
                <span class="gauge-title">Horas de Máquina</span>
                <span class="badge-pill {badge_maq_cls}">{badge_maq_txt}</span>
            </div>
            <div class="gauge-value">{maq_nec:,.0f} h</div>
            <div class="gauge-sub">Capacidade (2 turnos): <strong>{maq_cap:,.0f} h</strong></div>
            <div class="gauge-track">
                <div style="background-color: {bar_maq_color}; width: {min(100, maq_pct):.1f}%; height: 7px; border-radius: 4px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with g3:
        mont_nec = sim_res.operations["asm_hours_needed"]
        mont_cap = sim_res.operations["asm_hours_normal_cap"]
        mont_pct = (mont_nec / mont_cap * 100.0) if mont_cap else 0
        mont_ok = mont_nec <= mont_cap * 1.35
        badge_mont_cls = "badge-green" if mont_pct <= 105 else "badge-amber"
        badge_mont_txt = f"{mont_pct:.1f}% NORMAL"
        st.markdown(f"""
        <div class="gauge-card" style="border-color: rgba(16, 185, 129, 0.5);">
            <div class="gauge-header">
                <span class="gauge-title">Montagem (21 Operários)</span>
                <span class="badge-pill {badge_mont_cls}">{badge_mont_txt}</span>
            </div>
            <div class="gauge-value">{mont_nec:,.0f} h</div>
            <div class="gauge-sub">Capacidade Normal: <strong>{mont_cap:,.0f} h</strong></div>
            <div class="gauge-track">
                <div style="background-color: #10b981; width: {min(100, mont_pct):.1f}%; height: 7px; border-radius: 4px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with g4:
        st.markdown(f"""
        <div class="gauge-card" style="border-color: rgba(59, 130, 246, 0.5);">
            <div class="gauge-header">
                <span class="gauge-title">Projeção EBIT (Y15Q2)</span>
                <span class="badge-pill badge-blue">Cotação: {sim_res.kpis['Cotação Estimada (€)']:.2f} €</span>
            </div>
            <div class="gauge-value" style="color: #34d399;">€ {sim_res.kpis['EBIT']:,.0f}</div>
            <div class="gauge-sub">Vendas Est.: <strong>€ {sim_res.kpis['Vendas']:,.0f}</strong></div>
            <div class="gauge-track">
                <div style="background-color: #3b82f6; width: 100%; height: 7px; border-radius: 4px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 3. Alertas Dinâmicos de Restrições
    criticals = [a for a in sim_res.alerts if a.severity == "CRITICAL"]
    warnings = [a for a in sim_res.alerts if a.severity == "WARNING"]
    if criticals:
        for a in criticals:
            st.markdown(f"""
            <div class="strategic-card-red">
                <div class="strategic-title" style="color: {'#f87171' if is_dark else '#dc2626'};">🚨 [{a.category}] {a.title}</div>
                <div class="strategic-body">
                    {a.message}<br>
                    <strong>Causa:</strong> {a.reason}<br>
                    <strong>Impacto:</strong> {a.impact}<br>
                    <strong>Ação Corretiva Obrigatória:</strong> <span style="color: {'#fca5a5' if is_dark else '#b91c1c'}; font-weight: 700;">{a.suggested_action}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    if warnings:
        with st.expander(f"⚠️ Ver {len(warnings)} Avisos de Otimização e Eficiência"):
            for a in warnings:
                st.markdown(f"""
                <div class="strategic-card-amber">
                    <div class="strategic-title" style="color: {'#fbbf24' if is_dark else '#d97706'};">⚠️ [{a.category}] {a.title}</div>
                    <div class="strategic-body">{a.message}<br><strong>Sugestão:</strong> {a.suggested_action}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # 4. Grelha de Decisão em 3 Colunas (Fiel a plataforma_gestao_gmc.html)
    st.markdown("""
    <div style="font-size: 13px; font-weight: 700; color: var(--text-title); text-transform: uppercase; margin-bottom: 10px;">
        ⚙️ Grelha Oficial de Parâmetros de Decisão (Y15Q2)
    </div>
    """, unsafe_allow_html=True)

    col_inp1, col_inp2, col_inp3 = st.columns(3)

    with col_inp1:
        st.markdown("""
        <div style="border-bottom: 1px solid var(--border-color); padding-bottom: 6px; margin-bottom: 10px;">
            <span style="font-size: 11px; font-weight: 700; color: #60a5fa; text-transform: uppercase;">1. Entregas & Vendas</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Produto 1
        st.caption("Produto 1 (Entregas UE | Nafta | Internet)")
        d_p1_ue, d_p1_nafta, d_p1_net = st.columns(3)
        cur_dec["deliv"]["UE"]["P1"] = d_p1_ue.number_input("P1 UE", value=float(cur_dec["deliv"]["UE"]["P1"]), step=50.0, key="in_p1_ue")
        cur_dec["deliv"]["Nafta"]["P1"] = d_p1_nafta.number_input("P1 Nafta", value=float(cur_dec["deliv"]["Nafta"]["P1"]), step=20.0, key="in_p1_nafta")
        cur_dec["deliv"]["Internet"]["P1"] = d_p1_net.number_input("P1 Net", value=float(cur_dec["deliv"]["Internet"]["P1"]), step=20.0, key="in_p1_net")

        # Produto 2
        st.caption("Produto 2 (Entregas UE | Nafta | Internet)")
        d_p2_ue, d_p2_nafta, d_p2_net = st.columns(3)
        cur_dec["deliv"]["UE"]["P2"] = d_p2_ue.number_input("P2 UE", value=float(cur_dec["deliv"]["UE"]["P2"]), step=50.0, key="in_p2_ue")
        cur_dec["deliv"]["Nafta"]["P2"] = d_p2_nafta.number_input("P2 Nafta", value=float(cur_dec["deliv"]["Nafta"]["P2"]), step=20.0, key="in_p2_nafta")
        cur_dec["deliv"]["Internet"]["P2"] = d_p2_net.number_input("P2 Net", value=float(cur_dec["deliv"]["Internet"]["P2"]), step=20.0, key="in_p2_net")

        # Produto 3
        st.caption("Produto 3 (Entregas UE | Nafta | Internet)")
        d_p3_ue, d_p3_nafta, d_p3_net = st.columns(3)
        cur_dec["deliv"]["UE"]["P3"] = d_p3_ue.number_input("P3 UE", value=float(cur_dec["deliv"]["UE"]["P3"]), step=20.0, key="in_p3_ue")
        cur_dec["deliv"]["Nafta"]["P3"] = d_p3_nafta.number_input("P3 Nafta", value=float(cur_dec["deliv"]["Nafta"]["P3"]), step=10.0, key="in_p3_nafta")
        cur_dec["deliv"]["Internet"]["P3"] = d_p3_net.number_input("P3 Net", value=float(cur_dec["deliv"]["Internet"]["P3"]), step=10.0, key="in_p3_net")

        # Preços de Venda
        st.caption("Preços de Venda (€ Base UE)")
        pr1, pr2, pr3 = st.columns(3)
        cur_dec["price"]["UE"]["P1"] = pr1.number_input("P1 Preço", value=float(cur_dec["price"]["UE"]["P1"]), step=5.0, key="pr_p1")
        cur_dec["price"]["UE"]["P2"] = pr2.number_input("P2 Preço", value=float(cur_dec["price"]["UE"]["P2"]), step=5.0, key="pr_p2")
        cur_dec["price"]["UE"]["P3"] = pr3.number_input("P3 Preço", value=float(cur_dec["price"]["UE"]["P3"]), step=10.0, key="pr_p3")

    with col_inp2:
        st.markdown("""
        <div style="border-bottom: 1px solid var(--border-color); padding-bottom: 6px; margin-bottom: 10px;">
            <span style="font-size: 11px; font-weight: 700; color: #fbbf24; text-transform: uppercase;">2. Matéria-Prima & Produção</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Produção Programada
        st.caption("Produção Programada (Unidades)")
        pr_c1, pr_c2, pr_c3 = st.columns(3)
        cur_dec["production"]["P1"] = pr_c1.number_input("Prod P1", value=float(cur_dec["production"]["P1"]), step=50.0, key="prd_p1")
        cur_dec["production"]["P2"] = pr_c2.number_input("Prod P2", value=float(cur_dec["production"]["P2"]), step=50.0, key="prd_p2")
        cur_dec["production"]["P3"] = pr_c3.number_input("Prod P3", value=float(cur_dec["production"]["P3"]), step=50.0, key="prd_p3")

        # Compras de Matéria-Prima
        st.caption("Compras de Matéria-Prima (Unidades)")
        cur_dec["mp_order"]["spot"] = st.number_input("MP Ocasião Spot (uso imediato)", value=float(cur_dec["mp_order"]["spot"]), step=500.0, key="in_mp_spot")
        mp_c1, mp_c2 = st.columns(2)
        cur_dec["mp_order"]["3m"] = mp_c1.number_input("MP 3 meses (p/ Q3)", value=float(cur_dec["mp_order"]["3m"]), step=500.0, key="in_mp_3m")
        cur_dec["mp_order"]["6m"] = mp_c2.number_input("MP 6 meses (p/ Q4)", value=float(cur_dec["mp_order"]["6m"]), step=500.0, key="in_mp_6m")

        # Turnos e Conservação
        t_c1, t_c2 = st.columns(2)
        cur_dec["shifts"] = t_c1.selectbox("Turnos de Trabalho", options=[1, 2, 3], index=cur_dec["shifts"]-1, key="in_turnos")
        cur_dec["maintenance_h"] = t_c2.number_input("Conservação (h)", value=float(cur_dec["maintenance_h"]), step=20.0, key="in_maint")

        # Tempos de Montagem
        st.caption("Tempos de Montagem (minutos/un)")
        tm1, tm2, tm3 = st.columns(3)
        cur_dec["assembly_min"]["P1"] = tm1.number_input("P1 (mín 100)", min_value=100.0, value=float(cur_dec["assembly_min"]["P1"]), step=5.0, key="tm_p1")
        cur_dec["assembly_min"]["P2"] = tm2.number_input("P2 (mín 150)", min_value=150.0, value=float(cur_dec["assembly_min"]["P2"]), step=5.0, key="tm_p2")
        cur_dec["assembly_min"]["P3"] = tm3.number_input("P3 (mín 300)", min_value=300.0, value=float(cur_dec["assembly_min"]["P3"]), step=10.0, key="tm_p3")

    with col_inp3:
        st.markdown("""
        <div style="border-bottom: 1px solid var(--border-color); padding-bottom: 6px; margin-bottom: 10px;">
            <span style="font-size: 11px; font-weight: 700; color: #34d399; text-transform: uppercase;">3. Qualidade, RH & Tesouraria</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Introdução de Melhoramentos
        st.caption("Introduzir Grande Melhoramento (0 ou 1)")
        im1, im2, im3 = st.columns(3)
        cur_dec["improve"]["P1"] = 1.0 if im1.checkbox("P1 Major", value=bool(cur_dec["improve"]["P1"])) else 0.0
        cur_dec["improve"]["P2"] = 1.0 if im2.checkbox("P2 Minor", value=bool(cur_dec["improve"]["P2"])) else 0.0
        cur_dec["improve"]["P3"] = 1.0 if im3.checkbox("P3 Minor", value=bool(cur_dec["improve"]["P3"])) else 0.0

        # Recursos Humanos
        rh_c1, rh_c2 = st.columns(2)
        cur_dec["wage_eur"] = rh_c1.number_input("Salário Especializado (€/h, mín 12.0)", min_value=12.0, value=float(cur_dec["wage_eur"]), step=0.10, key="in_wage")
        cur_dec["skilled_hire"] = rh_c2.number_input("Recrutar Especializados", min_value=0.0, max_value=5.0, value=float(cur_dec["skilled_hire"]), step=1.0, key="in_hire")

        # Tesouraria e Depósito a Prazo
        cur_dec["deposit"] = st.number_input("Movimento Depósito a Prazo (k€, negativo = resgate)", value=float(cur_dec["deposit"]), step=50.0, key="in_dep")
        st.caption("💡 Colocar -200 k€ resgata fundos e anula o descoberto de 97.987 €!")

        fin_c1, fin_c2 = st.columns(2)
        cur_dec["dividend"] = fin_c1.number_input("Dividendo (cêntimos)", min_value=0.0, max_value=50.0, value=float(cur_dec["dividend"]), step=1.0, key="in_div")
        cur_dec["insurance"] = fin_c2.selectbox("Seguro", options=[0, 1, 2, 3, 4], index=int(cur_dec["insurance"]), key="in_ins")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 5. Demonstração de Resultados Projetada Detalhada
    st.markdown("""
    <div style="font-size: 13px; font-weight: 700; color: var(--text-title); text-transform: uppercase; margin-bottom: 8px;">
        📑 Demonstração de Resultados (DRE) Projetada para Y15Q2
    </div>
    """, unsafe_allow_html=True)
    df_pnl_show = pd.DataFrame(list(sim_res.pnl.items()), columns=["Rubrica Contabilística", "Valor Projetado (€)"])
    st.dataframe(df_pnl_show.style.format({"Valor Projetado (€)": "{:,.0f} €"}), width="stretch")

    # 6. Folha Oficial de Decisão (Pronta para Submissão)
    st.markdown("""
    <div style="font-size: 13px; font-weight: 700; color: var(--text-title); text-transform: uppercase; margin-top: 14px; margin-bottom: 8px;">
        📋 Folha Oficial de Decisão GMC (Y15Q2)
    </div>
    """, unsafe_allow_html=True)
    dec_dict = {
        "Preços UE (P1, P2, P3)": f"{cur_dec['price']['UE']['P1']:.0f} €, {cur_dec['price']['UE']['P2']:.0f} €, {cur_dec['price']['UE']['P3']:.0f} €",
        "Preços Nafta (P1, P2, P3)": f"{cur_dec['price']['Nafta']['P1']:.0f} $, {cur_dec['price']['Nafta']['P2']:.0f} $, {cur_dec['price']['Nafta']['P3']:.0f} $",
        "Preços Internet (P1, P2, P3)": f"{cur_dec['price']['Internet']['P1']:.0f} €, {cur_dec['price']['Internet']['P2']:.0f} €, {cur_dec['price']['Internet']['P3']:.0f} €",
        "Entregas UE (P1, P2, P3)": f"{cur_dec['deliv']['UE']['P1']:.0f}, {cur_dec['deliv']['UE']['P2']:.0f}, {cur_dec['deliv']['UE']['P3']:.0f} un",
        "Entregas Nafta (P1, P2, P3)": f"{cur_dec['deliv']['Nafta']['P1']:.0f}, {cur_dec['deliv']['Nafta']['P2']:.0f}, {cur_dec['deliv']['Nafta']['P3']:.0f} un",
        "Entregas Internet (P1, P2, P3)": f"{cur_dec['deliv']['Internet']['P1']:.0f}, {cur_dec['deliv']['Internet']['P2']:.0f}, {cur_dec['deliv']['Internet']['P3']:.0f} un",
        "Grande Melhoramento (P1, P2, P3)": f"{int(cur_dec['improve']['P1'])}, {int(cur_dec['improve']['P2'])}, {int(cur_dec['improve']['P3'])}",
        "Tempos de Montagem (P1, P2, P3)": f"{cur_dec['assembly_min']['P1']:.0f}, {cur_dec['assembly_min']['P2']:.0f}, {cur_dec['assembly_min']['P3']:.0f} min",
        "Produção Programada": f"P1: {cur_dec['production']['P1']:.0f} | P2: {cur_dec['production']['P2']:.0f} | P3: {cur_dec['production']['P3']:.0f} un",
        "Compras de Matéria-Prima": f"Spot: {cur_dec['mp_order']['spot']:.0f} | 3m: {cur_dec['mp_order']['3m']:.0f} | 6m: {cur_dec['mp_order']['6m']:.0f} un",
        "Turnos & Manutenção": f"{cur_dec['shifts']} turnos | {cur_dec['maintenance_h']:.0f} h conservação",
        "Salário Especializado": f"{cur_dec['wage_eur']:.2f} €/h",
        "Movimento Depósito a Prazo": f"{cur_dec['deposit']:.0f} k€",
        "Dividendo por Ação": f"{cur_dec['dividend']:.0f} cêntimos",
    }
    st.table(pd.DataFrame(list(dec_dict.items()), columns=["Parâmetro GMC", "Valor Decidido"]))


# ========================================================================================
# VISTA 3: MARKETING & VENDAS
# ========================================================================================
elif menu == "📈 Marketing & Vendas":
    st.markdown("""
    <div style="border-bottom: 1px solid var(--border-color); padding-bottom: 12px; margin-bottom: 16px;">
        <span style="font-size: 14px; font-weight: 800; color: var(--text-title); text-transform: uppercase;">Marketing, Canais & Análise de Preços</span>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("1. Faturação por Mercado e Produto no Y15Q1")
    fig_mkt = px.bar(
        df_prod_mkt[df_prod_mkt["Trimestre"] == last_quarter.label],
        x="Produto", y="Receita", color="Mercado", barmode="group",
        color_discrete_map={"UE": "#3b82f6", "Nafta": "#10b981", "Internet": "#a855f7"},
    )
    apply_theme(fig_mkt, is_dark=is_dark, height=320, title="Receita por Produto e Canal de Venda (Y15Q1)")
    st.plotly_chart(fig_mkt, width="stretch")

    st.dataframe(df_prod_mkt[df_prod_mkt["Trimestre"] == last_quarter.label], width="stretch")


# ========================================================================================
# VISTA 4: PRODUÇÃO & SUPPLY CHAIN
# ========================================================================================
elif menu == "🏭 Produção & Supply Chain":
    st.markdown("""
    <div style="border-bottom: 1px solid var(--border-color); padding-bottom: 12px; margin-bottom: 16px;">
        <span style="font-size: 14px; font-weight: 800; color: var(--text-title); text-transform: uppercase;">Produção, Capacidade de Máquinas & Supply Chain</span>
    </div>
    """, unsafe_allow_html=True)

    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-label">Capacidade Nominal (4 Máquinas, 2 Turnos)</div>
            <div class="kpi-val-blue">4.272 h</div>
            <div class="kpi-sub">1.068 h por máquina × 4 máquinas</div>
        </div>
        """, unsafe_allow_html=True)
    with col_p2:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-label">Horas Efetivas Utilizadas (Y15Q1)</div>
            <div class="kpi-val-green">3.873 h</div>
            <div class="kpi-sub">Utilização: 90,7% | Eficiência: 95,2%</div>
        </div>
        """, unsafe_allow_html=True)
    with col_p3:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-label">Paragens por Avaria / Downtime</div>
            <div class="kpi-val-amber">54 h</div>
            <div class="kpi-sub">Mitigado com 160h de manutenção contratada</div>
        </div>
        """, unsafe_allow_html=True)

    st.subheader("Escada de Custos de Matéria-Prima (Cost Laddering)")
    mp_df = pd.DataFrame([
        {"Modalidade": "Spot (Imediato)", "Preço": "$ 13.50 / 1000", "Prazo": "Uso imediato em Q2", "Vantagem": "Garante sobrevivência imediata sem rotura."},
        {"Modalidade": "A 3 Meses", "Preço": "$ 11.50 / 1000", "Prazo": "Chegada em Q3", "Vantagem": "Poupança de ~15% face ao mercado Spot."},
        {"Modalidade": "A 6 Meses", "Preço": "$ 10.50 / 1000", "Prazo": "Chegada em Q4", "Vantagem": "Preço mais baixo possível (~22% desconto)."},
    ])
    st.table(mp_df)


# ========================================================================================
# VISTA 5: RECURSOS HUMANOS
# ========================================================================================
elif menu == "👥 Recursos Humanos":
    st.markdown("""
    <div style="border-bottom: 1px solid var(--border-color); padding-bottom: 12px; margin-bottom: 16px;">
        <span style="font-size: 14px; font-weight: 800; color: var(--text-title); text-transform: uppercase;">Recursos Humanos & Capacidade de Montagem</span>
    </div>
    """, unsafe_allow_html=True)

    rh1, rh2, rh3 = st.columns(3)
    with rh1:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-label">Operários no Q1</div>
            <div class="kpi-val-white">17</div>
            <div class="kpi-sub">Horas disponíveis: 9.792 h</div>
        </div>
        """, unsafe_allow_html=True)
    with rh2:
        st.markdown("""
        <div class="kpi-card" style="border-left: 4px solid #10b981;">
            <div class="kpi-label">Disponíveis no Q2</div>
            <div class="kpi-val-green">21 (+4)</div>
            <div class="kpi-sub">Entram em funções no início do trimestre</div>
        </div>
        """, unsafe_allow_html=True)
    with rh3:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-label">Capacidade Normal Base</div>
            <div class="kpi-val-blue">8.820 h</div>
            <div class="kpi-sub">21 operários × 420 horas base normais</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="strategic-card-blue">
        <div class="strategic-title" style="color: {'#60a5fa' if is_dark else '#2563eb'};">💡 Solução de Engenharia para os 21 Operários:</div>
        <div class="strategic-body">
            Com a entrada dos 4 novos operários qualificados, elevar os tempos de montagem para <strong>120 min no P1, 165 min no P2 e 320 min no P3</strong> absorve exatamente as 8.820 horas normais disponíveis sem gerar custos de horas ociosas e disparando a qualidade técnica (estrelas).
        </div>
    </div>
    """, unsafe_allow_html=True)


# ========================================================================================
# VISTA 6: FINANÇAS & BALANÇO
# ========================================================================================
elif menu == "💰 Finanças & Balanço":
    st.markdown("""
    <div style="border-bottom: 1px solid var(--border-color); padding-bottom: 12px; margin-bottom: 16px;">
        <span style="font-size: 14px; font-weight: 800; color: var(--text-title); text-transform: uppercase;">Finanças, Balanço & Otimização de Tesouraria</span>
    </div>
    """, unsafe_allow_html=True)

    bal = last_quarter.balance
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        st.markdown("#### Ativo Total: {:,.0f} €".format(bal['assets']))
        df_a = pd.DataFrame([
            {"Item": "Terrenos e Edifícios", "Valor (€)": bal["land"] + bal["buildings"]},
            {"Item": "Máquinas Fabris", "Valor (€)": bal["machines"]},
            {"Item": "Inventários (Produtos + MP)", "Valor (€)": bal["inv_products"] + bal["inv_mp"]},
            {"Item": "Clientes a Receber", "Valor (€)": bal["receivables"]},
            {"Item": "Depósito a Prazo", "Valor (€)": bal["cash"]},
        ])
        st.table(df_a.set_index("Item"))
    with b_col2:
        st.markdown("#### Passivo e Capitais Próprios: {:,.0f} €".format(bal['assets']))
        df_l = pd.DataFrame([
            {"Item": "Fornecedores e Credores", "Valor (€)": bal["payables"]},
            {"Item": "Descoberto Bancário", "Valor (€)": bal["overdraft"]},
            {"Item": "Empréstimos Médio/Longo Prazo", "Valor (€)": bal["term_loans"]},
            {"Item": "Capital Social Realizado", "Valor (€)": bal["share_capital"]},
            {"Item": "Resultados Transitados", "Valor (€)": bal["retained"]},
            {"Item": "TOTAL CAPITAIS PRÓPRIOS", "Valor (€)": bal["equity"]},
        ])
        st.table(df_l.set_index("Item"))


# ========================================================================================
# VISTA 7: ARQUIVO HISTÓRICO (5Q)
# ========================================================================================
elif menu == "📜 Arquivo Histórico (5Q)":
    st.markdown("""
    <div style="border-bottom: 1px solid var(--border-color); padding-bottom: 12px; margin-bottom: 16px;">
        <span style="font-size: 14px; font-weight: 800; color: var(--text-title); text-transform: uppercase;">Arquivo Histórico Completo da Empresa 1 (Y14Q1 - Y15Q1)</span>
    </div>
    """, unsafe_allow_html=True)

    st.dataframe(df_kpi, width="stretch")


# ========================================================================================
# VISTA 8: INTELIGÊNCIA COMPETITIVA (GRUPO)
# ========================================================================================
elif menu == "👥 Inteligência Competitiva (Grupo)":
    st.markdown("""
    <div style="border-bottom: 1px solid var(--border-color); padding-bottom: 12px; margin-bottom: 16px;">
        <span style="font-size: 14px; font-weight: 800; color: var(--text-title); text-transform: uppercase;">Benchmark Competitivo - Comparativo das 8 Empresas do Grupo</span>
    </div>
    """, unsafe_allow_html=True)

    fig_bench = px.bar(
        df_comp.reset_index(),
        x="Empresa", y="Cotação", text_auto=".2f",
        color="Cotação", color_continuous_scale="Blues",
    )
    apply_theme(fig_bench, is_dark=is_dark, height=330, title="Cotação da Ação por Empresa no Grupo (Y15Q1)")
    st.plotly_chart(fig_bench, width="stretch")

    highlight_color = "#1e3a8a" if is_dark else "#dbeafe"
    st.dataframe(
        df_comp[["Cotação", "Desempenho Inv.", "Capitais Próprios", "Caixa", "Financiamentos", "Publicidade", "I&D", "Empregados", "★ P1", "★ P2", "★ P3"]].style.highlight_max(axis=0, color=highlight_color),
        width="stretch",
    )


# ========================================================================================
# VISTA 9: PARÂMETROS OFICIAIS GMC
# ========================================================================================
elif menu == "📚 Parâmetros Oficiais GMC":
    st.markdown("""
    <div style="border-bottom: 1px solid var(--border-color); padding-bottom: 12px; margin-bottom: 16px;">
        <span style="font-size: 14px; font-weight: 800; color: var(--text-title); text-transform: uppercase;">Parâmetros Oficiais e Tabelas de Referência GMC</span>
    </div>
    """, unsafe_allow_html=True)

    tab_choice = st.selectbox(
        "Selecione uma Tabela de Parâmetros Oficial para Consultar:",
        [
            "Tabela 5: Parâmetros de Fabrico por Unidade",
            "Tabela 7: Horas Máximas por Máquina e Turnos",
            "Tabela 13: Compras e Armazenagem",
            "Tabela 20: Parâmetros Financeiros e Taxas",
            "Tabela 26: Requisitos de Espaço Fabril",
        ],
    )

    if "Tabela 5" in tab_choice:
        st.markdown("""
        | Produto | Minutos Maquinação | Tempo Mínimo Montagem | Matéria-Prima |
        | :--- | :---: | :---: | :---: |
        | **Produto 1** | 60 min (1,0 h) | 100 min | 1 unidade |
        | **Produto 2** | 75 min (1,25 h) | 150 min | 2 unidades |
        | **Produto 3** | 120 min (2,0 h) | 300 min | 3 unidades |
        """)
    elif "Tabela 7" in tab_choice:
        st.markdown("""
        | Turnos | Horas Máximas / Máquina | Operários Não Especializados |
        | :---: | :---: | :---: |
        | **1 Turno** | 576 h | 4 operários |
        | **2 Turnos** | 1.068 h | 8 operários |
        | **3 Turnos** | 1.602 h | 12 operários |
        """)
    elif "Tabela 13" in tab_choice:
        st.markdown("""
        - Sobretaxa de Compra de Emergência: **+10%** sobre o preço Spot.
        - Sobretaxa de Matéria-Prima Extra: **+50%** sobre o preço Spot.
        - Custo Fixo de Compras: **7.500 €** por trimestre.
        """)
    elif "Tabela 20" in tab_choice:
        st.markdown("""
        - Taxa de Imposto: **30%**.
        - Spread Descoberto Autorizado: **Taxa Base + 4%**.
        - Spread Descoberto Não Autorizado: **Taxa Base + 10%**.
        """)
    elif "Tabela 26" in tab_choice:
        st.markdown("""
        - Utilização Máxima da Fábrica: **75%** (25% é circulação fixa).
        - Área por Máquina: **25 m²**.
        - Área por Trabalhador Especializado: **10 m²**.
        - Área por 1.000 un de Matéria-Prima: **5 m²**.
        """)
