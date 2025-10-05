import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Dashboard de Turnover", layout="wide")

st.title("📊 Dashboard de Turnover - MVP")

st.markdown("""
Este dashboard permite analisar indicadores de **turnover**, **tempo de casa** e **performance** com base em um arquivo Excel.
Faça upload do arquivo com as abas `empresa`, `colaboradores` e `performance` para visualizar as métricas.
""")

# --- Upload do arquivo Excel
uploaded_file = st.file_uploader("📂 Carregue a base de dados RH (.xlsx)", type=["xlsx"])

if uploaded_file:
    # --- Ler as abas
    empresa = pd.read_excel(uploaded_file, sheet_name="empresa")
    colaboradores = pd.read_excel(uploaded_file, sheet_name="colaboradores")
    performance = pd.read_excel(uploaded_file, sheet_name="performance")

    # --- Limpeza e formatação
    colaboradores["data de admissão"] = pd.to_datetime(colaboradores["data de admissão"], errors="coerce")
    colaboradores["data de desligamento"] = pd.to_datetime(colaboradores["data de desligamento"], errors="coerce")
    colaboradores["ativo"] = colaboradores["data de desligamento"].isna()
    colaboradores["motivo_voluntario"] = colaboradores["motivo de desligamento"].str.contains("Pedido", na=False)

    # --- KPIs
    total_colabs = len(colaboradores)
    desligados = len(colaboradores[~colaboradores["ativo"]])
    ativos = len(colaboradores[colaboradores["ativo"]])
    turnover = round((desligados / total_colabs) * 100, 1) if total_colabs > 0 else 0

    voluntario = len(colaboradores[colaboradores["motivo_voluntario"]])
    involuntario = desligados - voluntario
    perc_voluntario = round(voluntario / desligados * 100, 1) if desligados > 0 else 0
    perc_involuntario = 100 - perc_voluntario

    tempo_medio_casa = round(
        colaboradores.loc[~colaboradores["ativo"], "data de desligamento"].sub(
            colaboradores["data de admissão"]
        ).dt.days.mean() / 30, 1
    ) if desligados > 0 else 0

    # --- Layout de KPIs
    st.subheader("📈 Indicadores Gerais")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Total de Colaboradores", total_colabs)
    col2.metric("📉 Turnover (%)", f"{turnover}%")
    col3.metric("📅 Tempo Médio de Casa", f"{tempo_medio_casa} meses")
    col4.metric("🏢 Colaboradores Ativos", ativos)

    st.divider()

    # --- Gráfico: Turnover Voluntário vs Involuntário
    st.subheader("📊 Distribuição do Turnover")
    turnover_tipo = pd.DataFrame({
        "Tipo": ["Voluntário", "Involuntário"],
        "Percentual": [perc_voluntario, perc_involuntario]
    }).set_index("Tipo")
    st.bar_chart(turnover_tipo)

    # --- Gráfico: Turnover por Departamento
    st.subheader("🏬 Turnover por Departamento")
    turnover_depto = (
        colaboradores.groupby("departamento")["ativo"]
        .apply(lambda x: 100 - x.mean() * 100)
        .sort_values(ascending=False)
    )
    st.bar_chart(turnover_depto)

    # --- Relação Performance x Turnover
    st.subheader("🎯 Relação entre Performance e Desligamentos")
    desligados_perf = colaboradores.merge(performance, on="matricula", how="left")
    perf_turnover = (
        desligados_perf.loc[~desligados_perf["ativo"], "avaliação"]
        .value_counts(normalize=True)
        .mul(100)
    )
    if not perf_turnover.empty:
        st.bar_chart(perf_turnover)
    else:
        st.info("Sem dados de avaliação de desligados disponíveis.")

    # --- Dados de empresa
    st.divider()
    st.subheader("🏢 Informações da Empresa")
    st.dataframe(empresa)

else:
    st.info("⬆️ Carregue um arquivo Excel com as abas: **empresa**, **colaboradores** e **performance** para iniciar o dashboard.")
