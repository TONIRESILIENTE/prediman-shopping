# src/dashboard/app.py
# ─────────────────────────────────────────────
# CONCEITO: Dashboard profissional para o gestor de facilities.
#
# Consome a API PrediMan e exibe:
# - Cards de resumo (KPI)
# - Mapa do shopping com status dos equipamentos
# - Gráfico de tendência de anomalias
# - Tabela de últimas OS
#
# Streamlit: framework Python para dashboards interativos.
# Não precisa escrever HTML/CSS/JS — é tudo Python.
# ─────────────────────────────────────────────

from time import sleep
import numpy as np
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
import os

# ─── Configuração da página ─────────────────

st.set_page_config(
    page_title="PrediMan Shopping — Gestor",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# POR QUÊ: URL da API via ambiente = funciona local e em deploy
API_URL = os.getenv("API_URL", "http://api:8000/api/v1")

# ─── Cabeçalho ──────────────────────────────

st.title("🏢 PrediMan Shopping")
st.subheader("Painel de Controle — Gestor de Facilities")

# Botão de atualização manual
col_titulo, col_btn = st.columns([5, 1])
with col_btn:
    if st.button("🔄 Atualizar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Linha de status
col_status, col_loja = st.columns([1, 3])
with col_status:
    try:
        resp = requests.get(
            f"{API_URL.replace('/api/v1', '')}/health", timeout=3)
        if resp.status_code == 200:
            st.success("🟢 Sistema Online")
        else:
            st.warning("🟡 Sistema Degradado")
    except:
        st.error("🔴 API Offline")

st.markdown("---")

# ─── Dados da API ────────────────────────────


@st.cache_data(ttl=2)  # Cache de 2 segundos
def carregar_dados():
    """Busca dados da API para o dashboard."""
    dados = {
        "equipamentos": [],
        "ordens": [],
        "diagnosticos": {},
        "anomalias_historico": [],
    }

    try:
        # Equipamentos
        resp = requests.get(f"{API_URL}/equipamentos", timeout=5)
        if resp.status_code == 200:
            dados["equipamentos"] = resp.json()

        # Ordens de serviço
        resp = requests.get(f"{API_URL}/ordens", timeout=5)
        if resp.status_code == 200:
            dados["ordens"] = resp.json()

    except:
        st.warning("Não foi possível conectar à API. Usando dados de exemplo.")

    return dados


dados = carregar_dados()

# ─── Cards KPI ───────────────────────────────

st.markdown("### 📊 Indicadores")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_equipamentos = len(
        dados["equipamentos"]) if dados["equipamentos"] else 6
    st.metric(
        label="🛠️ Equipamentos Monitorados",
        value=total_equipamentos,
    )

with col2:
    ordens_abertas = [o for o in dados["ordens"]
                      if o.get("status") in ["aberta", "em_andamento"]]
    st.metric(
        label="📋 OS Ativas",
        value=len(ordens_abertas) if dados["ordens"] else 0,
        delta="Nenhuma crítica" if len(ordens_abertas) < 3 else "⚠️ Atenção",
    )

with col3:
    criticos = [o for o in dados["ordens"] if o.get(
        "severidade") in ["alta", "critica"] and o.get("status") != "concluida"]
    st.metric(
        label="🔴 Alertas Críticos",
        value=len(criticos) if dados["ordens"] else 0,
        delta="OK" if len(criticos) == 0 else "🚨 Ação necessária",
    )

with col4:
    # Economia estimada (simulada)
    economia = 47300
    st.metric(
        label="💰 Economia Estimada/mês",
        value=f"R$ {economia:,}".replace(",", "."),
        delta="+12% vs. mês anterior",
    )

st.markdown("---")

# ─── Mapa do Shopping ────────────────────────

st.markdown("### 🗺️ Mapa do Shopping — Status dos Equipamentos")

# Dados dos equipamentos com localização simulada
mapa_equipamentos = [
    {"nome": "Chiller 1", "local": "Cobertura — Casa de Máquinas 2",
        "status": "🟢 Normal", "tipo": "chiller"},
    {"nome": "Subestação", "local": "Subsolo 1 — Sala Elétrica",
        "status": "🟢 Normal", "tipo": "subestacao"},
    {"nome": "Bomba Recalque G1", "local": "Subsolo 2 — Poço de Recalque",
        "status": "🟢 Normal", "tipo": "bomba"},
    {"nome": "Ilum. Praça Alimentação", "local": "Piso Térreo — QDL-03",
        "status": "🟢 Normal", "tipo": "iluminacao"},
    {"nome": "Ilum. Estacionamento G1", "local": "Subsolo 1 — QDL-05",
        "status": "🟢 Normal", "tipo": "iluminacao"},
    {"nome": "Ilum. Fachada", "local": "Área Externa — QDL-07",
        "status": "🟢 Normal", "tipo": "iluminacao"},
]

# Atualizar status com base nas OS abertas
for eq in mapa_equipamentos:
    for os_item in dados["ordens"]:
        if os_item.get("status") in ["aberta", "em_andamento"]:
            if eq["tipo"] in os_item.get("equipamento_id", "").lower() or eq["nome"].lower().replace(" ", "_") in os_item.get("equipamento_id", "").lower():
                if os_item.get("severidade") in ["alta", "critica"]:
                    eq["status"] = "🔴 Crítico"
                elif os_item.get("severidade") == "media":
                    eq["status"] = "🟡 Atenção"
                break

df_mapa = pd.DataFrame(mapa_equipamentos)
st.dataframe(
    df_mapa,
    use_container_width=True,
    hide_index=True,
    column_config={
        "nome": "Equipamento",
        "local": "Localização",
        "status": st.column_config.TextColumn("Status", width="small"),
    },
)

st.markdown("---")

# ─── Gráfico de Tendência ────────────────────

st.markdown("### 📈 Tendência de Anomalias (últimos 30 dias)")

# Dados simulados de tendência (no futuro, virão da API)
dias = pd.date_range(end=datetime.now(), periods=30, freq='D')
np.random.seed(42)
tendencia = pd.DataFrame({
    "Data": dias,
    "Anomalias Detectadas": np.random.poisson(2, 30) + np.sin(np.linspace(0, 3*np.pi, 30)) * 2,
})

# Garantir valores positivos
tendencia["Anomalias Detectadas"] = tendencia["Anomalias Detectadas"].clip(
    lower=0)

fig = px.area(
    tendencia,
    x="Data",
    y="Anomalias Detectadas",
    title=None,
    color_discrete_sequence=["#FF6B6B"],
)
fig.update_layout(
    height=300,
    margin=dict(l=0, r=0, t=0, b=0),
    xaxis_title=None,
    yaxis_title="Anomalias",
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ─── Tabela de Últimas OS ────────────────────

st.markdown("### 📋 Últimas Ordens de Serviço")

if dados["ordens"]:
    df_ordens = pd.DataFrame(dados["ordens"])

    # Formatar datas
    if "criado_em" in df_ordens.columns:
        df_ordens["criado_em"] = pd.to_datetime(
            df_ordens["criado_em"]).dt.strftime("%d/%m %H:%M")

    # Selecionar colunas para exibição
    colunas_exibir = ["equipamento_id", "titulo",
                      "severidade", "status", "criado_em", "pop_codigo"]
    colunas_disponiveis = [c for c in colunas_exibir if c in df_ordens.columns]

    st.dataframe(
        df_ordens[colunas_disponiveis].tail(10),
        use_container_width=True,
        hide_index=True,
        column_config={
            "equipamento_id": "Equipamento",
            "titulo": "Título",
            "severidade": st.column_config.TextColumn("Severidade", width="small"),
            "status": st.column_config.TextColumn("Status", width="small"),
            "criado_em": "Aberto em",
            "pop_codigo": "POP",
        },
    )
else:
    st.info("Nenhuma ordem de serviço registrada. Envie leituras via API para gerar OS.")

st.markdown("---")


# ─── Rodapé ──────────────────────────────────

st.caption(
    f"🕐 Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | PrediMan Shopping v0.2.0")
