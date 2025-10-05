import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import openai

# =========================
# CONFIGURAÇÃO GERAL E ESTILO FUTURISTA
# =========================
st.set_page_config(page_title="Dashboard de Turnover • v4", layout="wide")

st.markdown("""
<style>
html, body, [class*="css"]  {
  background-color: #0e1117 !important;
  color: #E6E6E6 !important;
  font-family: "Inter", system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, "Helvetica Neue", "Noto Sans", "Apple Color Emoji", "Segoe UI Emoji" !important;
}
div[data-testid="stMetric"] {
  background: linear-gradient(135deg, #1a1f2b 0%, #151922 100%);
  border-radius: 18px;
  padding: 14px 16px;
  box-shadow: 0 0 18px rgba(0, 255, 204, 0.12);
  border: 1px solid rgba(0,255,204,0.12);
}
</style>
""", unsafe_allow_html=True)

st.title("🚀 Dashboard de Turnover — v4 (com Risco e IA)")
st.caption("Visual futurista interativo com análises de rotatividade, retenção, performance e **risco de turnover (TRI)**.")

# =========================
# UPLOAD
# =========================
uploaded_file = st.file_uploader("📂 Carregue o arquivo Excel (.xlsx) com abas: empresa, colaboradores e performance", type=["xlsx"])

if not uploaded_file:
    st.info("⬆️ Envie o arquivo para iniciar a análise.")
    st.stop()

# =========================
# LEITURA E PREPARO DA BASE
# =========================
empresa = pd.read_excel(uploaded_file, sheet_name="empresa")
colab = pd.read_excel(uploaded_file, sheet_name="colaboradores")
perf = pd.read_excel(uploaded_file, sheet_name="performance")

# Conversões de data
for c in ["data de admissão", "data de desligamento", "ultima promoção", "ultimo mérito"]:
    if c in colab.columns:
        colab[c] = pd.to_datetime(colab[c], errors="coerce")

if "data de encerramento do ciclo" in perf.columns:
    perf["data de encerramento do ciclo"] = pd.to_datetime(perf["data de encerramento do ciclo"], errors="coerce")

# Flags e merge
colab["ativo"] = colab["data de desligamento"].isna()
colab["ano_desligamento"] = colab["data de desligamento"].dt.year
colab["motivo_voluntario"] = colab["motivo de desligamento"].fillna("").str.contains("Pedido", case=False)

# Última avaliação de performance
if "data de encerramento do ciclo" in perf.columns:
    perf_last = perf.sort_values(["matricula", "data de encerramento do ciclo"]).groupby("matricula", as_index=False).tail(1)
else:
    perf_last = perf.drop_duplicates(subset=["matricula"], keep="last")

colab = colab.merge(perf_last[["matricula", "avaliação"]], on="matricula", how="left")

# =========================
# FILTROS LATERAIS
# =========================
st.sidebar.header("🔎 Filtros")
empresa_sel = st.sidebar.selectbox("Empresa (contexto)", options=empresa["nome empresa"].tolist())
dept_opts = ["Todos"] + sorted(colab["departamento"].dropna().unique().tolist())
dept_sel = st.sidebar.selectbox("Departamento", dept_opts)
anos_opts = ["Todos"] + sorted(colab["ano_desligamento"].dropna().unique().tolist())
ano_sel = st.sidebar.selectbox("Ano de Desligamento", anos_opts)

df = colab.copy()
if dept_sel != "Todos":
    df = df[df["departamento"] == dept_sel]
if ano_sel != "Todos":
    df = df[df["ano_desligamento"] == ano_sel]

# =========================
# CÁLCULOS DO TRI (Turnover Risk Index)
# =========================
now = pd.Timestamp.now()
df["meses_desde_promocao"] = (now - df["ultima promoção"]).dt.days / 30
df["meses_desde_merito"] = (now - df["ultimo mérito"]).dt.days / 30
df["tempo_casa"] = (now - df["data de admissão"]).dt.days / 30

# Tamanho de equipe
gestor_size = df.groupby("matricula do gestor")["matricula"].count().rename("tamanho_equipe")
df = df.merge(gestor_size, left_on="matricula do gestor", right_index=True, how="left")

# Performance → score
perf_map = {"excepcional": 10, "acima do esperado": 7, "dentro do esperado": 4, "abaixo do esperado": 1}
df["score_perf_raw"] = df["avaliação"].str.lower().map(perf_map).fillna(4)

def norm_0_1(s):
    s = s.astype(float)
    maxv = s.max(skipna=True)
    return s / maxv if pd.notna(maxv) and maxv not in [0, np.inf] else s.fillna(0).mul(0)

df["score_perf_inv"] = 1 - norm_0_1(df["score_perf_raw"])
df["score_tempo_promo"] = norm_0_1(df["meses_desde_promocao"].fillna(0))
df["score_tempo_casa"] = norm_0_1(df["tempo_casa"].fillna(0))
df["score_merito"] = norm_0_1(df["meses_desde_merito"].fillna(0))
df["score_tamanho_eq"] = norm_0_1(df["tamanho_equipe"].fillna(0))

W_PERF, W_PROMO, W_TEMPO, W_EQUIPE, W_MERITO = 0.30, 0.25, 0.15, 0.15, 0.15
df["risco_turnover"] = (
    W_PERF * df["score_perf_inv"] +
    W_PROMO * df["score_tempo_promo"] +
    W_TEMPO * df["score_tempo_casa"] +
    W_EQUIPE * df["score_tamanho_eq"] +
    W_MERITO * df["score_merito"]
) * 100

df["risco_turnover"] = df["risco_turnover"].clip(0, 100)
df["risco_categoria"] = pd.cut(df["risco_turnover"], bins=[-0.001, 30, 60, 100], labels=["Baixo", "Médio", "Alto"])

# =========================
# KPIs DE CABEÇALHO
# =========================
avg_risk = round(df["risco_turnover"].mean(), 1)
pct_high = round((df["risco_categoria"] == "Alto").mean() * 100, 1)
tempo_alto = round(df["meses_desde_promocao"].mean(), 1)
tamanho_medio_eq = round(df["tamanho_equipe"].mean(), 1)
nota_media_perf = round(df["score_perf_raw"].mean(), 1)

st.markdown("### 📈 Indicadores Gerais")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("⚠️ Risco Médio (TRI)", avg_risk)
k2.metric("🚨 % em Risco Alto", f"{pct_high}%")
k3.metric("📅 Meses desde última promoção (médio)", tempo_alto)
k4.metric("👥 Tamanho médio da equipe", tamanho_medio_eq)
k5.metric("⭐ Nota média de performance", nota_media_perf)

st.divider()

# =========================
# CURVA DE RISCO POR TEMPO SEM PROMOÇÃO
# =========================
bins = [0, 3, 6, 12, 24, np.inf]
labels = ["0-3m", "3-6m", "6-12m", "12-24m", "+24m"]
df["faixa_tempo_sem_promo"] = pd.cut(df["meses_desde_promocao"].fillna(0), bins=bins, labels=labels)

risco_por_faixa = (
    df.groupby("faixa_tempo_sem_promo")["risco_turnover"]
    .mean()
    .reset_index()
    .rename(columns={"risco_turnover": "Risco Médio"})
)

fig_risco_tempo = go.Figure()
fig_risco_tempo.add_trace(go.Scatter(
    x=risco_por_faixa["faixa_tempo_sem_promo"],
    y=risco_por_faixa["Risco Médio"],
    mode="lines+markers",
    line=dict(color="#00FFFF", width=3),
    marker=dict(size=8),
    name="Risco Médio"
))
fig_risco_tempo.update_layout(
    template="plotly_dark",
    title="📈 Risco de Turnover por Tempo sem Promoção",
    xaxis_title="Faixa de Tempo sem Promoção",
    yaxis_title="Risco Médio (0-100)",
    hovermode="x unified"
)
st.plotly_chart(fig_risco_tempo, use_container_width=True)

# =========================
# ANÁLISE QUALITATIVA COM BOTÃO
# =========================
st.markdown("## 💡 Insights Analíticos (IA)")
st.markdown("Clique no botão abaixo para gerar um resumo interpretativo sobre o risco de turnover com base nos filtros atuais.")

if st.button("🤖 Gerar Análise com IA"):
    with st.spinner("🔎 Gerando análise com GPT-4..."):
        try:
            openai.api_key = st.secrets["OPENAI_API_KEY"]

            prompt = f"""
            Analise os dados de risco de turnover:
            - risco médio total: {avg_risk}
            - {pct_high}% dos colaboradores estão em risco alto
            - tempo médio desde última promoção: {tempo_alto} meses
            - tamanho médio da equipe: {tamanho_medio_eq}
            - nota média de performance: {nota_media_perf}
            - faixa de maior risco: {risco_por_faixa.loc[risco_por_faixa['Risco Médio'].idxmax(), 'faixa_tempo_sem_promo']}

            Gere uma análise de People Analytics (2–4 frases) explicando:
            1. Quais grupos estão em maior risco.
            2. Como tempo sem promoção e sobrecarga impactam.
            3. Sugira uma ação gerencial.
            """

            response = openai.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "Você é um analista sênior de People Analytics especializado em retenção de talentos."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6
            )
            texto_analise = response.choices[0].message.content
            st.success(texto_analise)

        except Exception as e:
            st.error(f"Erro ao gerar análise: {e}")
else:
    st.info("Aperte **Gerar Análise com IA** para ver um resumo contextual baseado nos resultados atuais.")

st.caption("• Versão 4.0 • Inclui TRI, curva temporal e análise IA sob demanda.")
