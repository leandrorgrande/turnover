import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# ---- CONFIGURAÇÃO GERAL ----
st.set_page_config(page_title="Dashboard de Turnover - Futurista", layout="wide")

# ---- ESTILO FUTURISTA ----
st.markdown("""
    <style>
    body {
        background-color: #0e1117;
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }
    .stMetric {
        background: linear-gradient(135deg, #1a1a1a, #222831);
        border-radius: 15px;
        padding: 15px;
        text-align: center;
        box-shadow: 0px 0px 12px rgba(0,255,255,0.2);
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Dashboard de Turnover - **People Analytics 4.0**")
st.caption("Visual futurista e interativo para análise de rotatividade, retenção e performance.")

# ---- UPLOAD DO ARQUIVO ----
uploaded_file = st.file_uploader("📂 Carregue a base de dados RH (.xlsx)", type=["xlsx"])

if uploaded_file:
    # Ler abas
    empresa = pd.read_excel(uploaded_file, sheet_name="empresa")
    colaboradores = pd.read_excel(uploaded_file, sheet_name="colaboradores")
    performance = pd.read_excel(uploaded_file, sheet_name="performance")

    # Preparação
    colaboradores["data de admissão"] = pd.to_datetime(colaboradores["data de admissão"], errors="coerce")
    colaboradores["data de desligamento"] = pd.to_datetime(colaboradores["data de desligamento"], errors="coerce")
    colaboradores["ativo"] = colaboradores["data de desligamento"].isna()
    colaboradores["motivo_voluntario"] = colaboradores["motivo de desligamento"].str.contains("Pedido", na=False)
    colaboradores["ano_desligamento"] = colaboradores["data de desligamento"].dt.year

    # ---- FILTROS ----
    st.sidebar.header("🔎 Filtros")
    empresa_sel = st.sidebar.selectbox("Empresa", empresa["nome empresa"].unique())
    departamentos = ["Todos"] + sorted(colaboradores["departamento"].dropna().unique().tolist())
    depto_sel = st.sidebar.selectbox("Departamento", departamentos)
    ano_sel = st.sidebar.selectbox("Ano de Desligamento", ["Todos"] + sorted(colaboradores["ano_desligamento"].dropna().unique().tolist()))

    # Aplicar filtros
    df = colaboradores.copy()
    if depto_sel != "Todos":
        df = df[df["departamento"] == depto_sel]
    if ano_sel != "Todos":
        df = df[df["ano_desligamento"] == ano_sel]

    # ---- KPIs ----
    total_colabs = len(df)
    desligados = len(df[~df["ativo"]])
    ativos = len(df[df["ativo"]])
    turnover = round((desligados / total_colabs) * 100, 1) if total_colabs > 0 else 0

    voluntario = len(df[df["motivo_voluntario"]])
    involuntario = desligados - voluntario
    perc_voluntario = round(voluntario / desligados * 100, 1) if desligados > 0 else 0
    perc_involuntario = 100 - perc_voluntario

    tempo_medio_casa = round(
        df.loc[~df["ativo"], "data de desligamento"].sub(df["data de admissão"]).dt.days.mean() / 30, 1
    ) if desligados > 0 else 0

    tempo_primeira_promocao = round(
        df["ultima promoção"].sub(df["data de admissão"]).dt.days.mean() / 30, 1
    )

    # ---- PERFORMANCE ----
    desligados_perf = df.merge(performance, on="matricula", how="left")
    desligados_bons = desligados_perf.loc[
        (~desligados_perf["ativo"]) & (desligados_perf["avaliação"].isin(["acima do esperado", "excepcional"]))
    ]
    perc_bons_desligados = round(len(desligados_bons) / desligados * 100, 1) if desligados > 0 else 0

    # ---- MÉTRICAS ----
    st.markdown("### 📈 Indicadores-Chave")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("👥 Total Colaboradores", total_colabs)
    c2.metric("📉 Turnover (%)", f"{turnover}%")
    c3.metric("📅 Tempo Médio de Casa", f"{tempo_medio_casa} meses")
    c4.metric("⏫ Tempo até 1ª Promoção", f"{tempo_primeira_promocao:.1f} meses")
    c5.metric("🔥 Voluntário (%)", f"{perc_voluntario}%")
    c6.metric("⭐ Alta Performance Desligada (%)", f"{perc_bons_desligados}%")

    st.divider()

    # ---- GRÁFICO: VOLUNTÁRIO VS INVOLUNTÁRIO ----
    st.subheader("📊 Distribuição de Tipos de Desligamento")
    tipo_df = pd.DataFrame({
        "Tipo": ["Voluntário", "Involuntário"],
        "Percentual": [perc_voluntario, perc_involuntario]
    })
    fig_tipo = px.pie(tipo_df, values="Percentual", names="Tipo",
                      color_discrete_sequence=["#00FFFF", "#9933FF"],
                      hole=0.4)
    fig_tipo.update_layout(template="plotly_dark", title_font_size=18)
    st.plotly_chart(fig_tipo, use_container_width=True)

    # ---- GRÁFICO: TURNOVER POR DEPARTAMENTO ----
    st.subheader("🏢 Turnover por Departamento")
    depto_turnover = (
        df.groupby("departamento")["ativo"]
        .apply(lambda x: 100 - x.mean() * 100)
        .reset_index(name="Turnover (%)")
    )
    fig_depto = px.bar(depto_turnover, x="departamento", y="Turnover (%)",
                       color="Turnover (%)", color_continuous_scale="plasma")
    fig_depto.update_layout(template="plotly_dark", xaxis_title=None, yaxis_title="%",
                            title_font_size=18)
    st.plotly_chart(fig_depto, use_container_width=True)

    # ---- GRÁFICO: PERFORMANCE DOS DESLIGADOS ----
    st.subheader("🎯 Performance dos Desligados")
    perf_counts = desligados_perf.loc[~desligados_perf["ativo"], "avaliação"].value_counts().reset_index()
    perf_counts.columns = ["Avaliação", "Quantidade"]
    fig_perf = px.bar(perf_counts, x="Avaliação", y="Quantidade",
                      color="Avaliação", color_discrete_sequence=px.colors.qualitative.Dark24)
    fig_perf.update_layout(template="plotly_dark")
    st.plotly_chart(fig_perf, use_container_width=True)

    # ---- GRÁFICO: TURNOVER AO LONGO DO TEMPO ----
    st.subheader("⏳ Evolução Mensal do Turnover")
    df["mes_desligamento"] = df["data de desligamento"].dt.to_period("M").astype(str)
    turnover_tempo = (
        df.loc[~df["ativo"]].groupby("mes_desligamento").size().reset_index(name="Desligamentos")
    )
    if not turnover_tempo.empty:
        fig_time = px.line(turnover_tempo, x="mes_desligamento", y="Desligamentos",
                           markers=True, line_shape="spline", color_discrete_sequence=["#00FFAA"])
        fig_time.update_layout(template="plotly_dark", title_font_size=18)
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.info("Sem desligamentos registrados por período.")

    st.divider()
    st.caption("🔗 Desenvolvido por Leandro Grande — versão futurista 2.0 • Powered by Streamlit & Plotly")

else:
    st.info("⬆️ Carregue o arquivo Excel com as abas `empresa`, `colaboradores` e `performance` para visualizar o dashboard.")
