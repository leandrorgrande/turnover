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
st.set_page_config(page_title="Dashboard de Turnover • v5", layout="wide")

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

st.title("🚀 Dashboard de People Analytics — Headcount, Turnover e Risco (v5)")
st.caption("Visual futurista interativo com análises de **headcount**, **rotatividade**, **tenure**, **performance** e **risco de turnover (TRI)** com apoio de IA.")

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

colab["ativo"] = colab["data de desligamento"].isna()
colab["ano_desligamento"] = colab["data de desligamento"].dt.year
colab["motivo_voluntario"] = colab["motivo de desligamento"].fillna("").str.contains("Pedido", case=False)

# Última performance
if "data de encerramento do ciclo" in perf.columns:
    perf_last = perf.sort_values(["matricula", "data de encerramento do ciclo"]).groupby("matricula", as_index=False).tail(1)
else:
    perf_last = perf.drop_duplicates(subset=["matricula"], keep="last")
colab = colab.merge(perf_last[["matricula", "avaliação"]], on="matricula", how="left")

# =========================
# FILTROS LATERAIS
# =========================
st.sidebar.header("🔎 Filtros")
empresa_sel = st.sidebar.selectbox("Empresa", empresa["nome empresa"].tolist())
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
# SEÇÃO 1 - HEADCOUNT E ESTRUTURA
# =========================
st.markdown("## 👥 Headcount e Estrutura Organizacional")

ativos = df[df["ativo"]]
total_ativos = len(ativos)
total_departamentos = ativos["departamento"].nunique()

# indicadores contratuais e diversidade
if "tipo_contrato" in ativos.columns:
    total_clt = (ativos["tipo_contrato"].str.upper() == "CLT").sum()
    total_pj = (ativos["tipo_contrato"].str.upper() == "PJ").sum()
else:
    total_clt = total_pj = 0

pct_clt = round((total_clt / total_ativos) * 100, 1) if total_ativos else 0
pct_pj = round((total_pj / total_ativos) * 100, 1) if total_ativos else 0

if "genero" in ativos.columns:
    genero_counts = ativos["genero"].value_counts(normalize=True) * 100
    pct_fem = round(genero_counts.get("Feminino", 0), 1)
    pct_masc = round(genero_counts.get("Masculino", 0), 1)
else:
    pct_fem = pct_masc = 0

if "cargo" in ativos.columns:
    cargos_lideranca = ativos["cargo"].str.lower().str.contains("coordenador|gerente|diretor", na=False)
    pct_lideranca = round((cargos_lideranca.sum() / total_ativos) * 100, 1)
else:
    pct_lideranca = 0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("👥 Ativos Totais", total_ativos)
col2.metric("🏢 Departamentos", total_departamentos)
col3.metric("📃 CLT (%)", f"{pct_clt}%")
col4.metric("🚺 Feminino (%)", f"{pct_fem}%")
col5.metric("🧭 Liderança (%)", f"{pct_lideranca}%")

st.divider()

# headcount por departamento
headcount_area = ativos.groupby("departamento")["matricula"].count().reset_index().rename(columns={"matricula": "Headcount"})
fig_area = px.bar(headcount_area, x="departamento", y="Headcount", color="Headcount", color_continuous_scale="tealgrn")
fig_area.update_layout(template="plotly_dark", title="Headcount por Departamento")
st.plotly_chart(fig_area, use_container_width=True)

# evolução mensal
meses_all = pd.date_range(df["data de admissão"].min(), datetime.now(), freq="MS")
hc_mensal = []
for mes in meses_all:
    ativos_mes = df[(df["data de admissão"] <= mes) & ((df["data de desligamento"].isna()) | (df["data de desligamento"] > mes))]
    hc_mensal.append({"Mês": mes.strftime("%Y-%m"), "Headcount": len(ativos_mes)})
hc_mensal = pd.DataFrame(hc_mensal)
fig_hc = px.line(hc_mensal, x="Mês", y="Headcount", markers=True, line_shape="spline", color_discrete_sequence=["#00FFFF"])
fig_hc.update_layout(template="plotly_dark", title="📈 Evolução Mensal do Headcount")
st.plotly_chart(fig_hc, use_container_width=True)

st.divider()

# =========================
# SEÇÃO 2 - TURNOVER E TENURE MÉDIO
# =========================
st.markdown("## 🔄 Turnover e Tempo de Casa")

df["mes_desligamento"] = df["data de desligamento"].dt.to_period("M").astype(str)
df["ano_mes"] = df["data de desligamento"].fillna(df["data de admissão"]).dt.to_period("M").astype(str)
meses = sorted(df["ano_mes"].dropna().unique().tolist())

turnover_mensal = (
    df.groupby("mes_desligamento")
    .agg(
        desligados=("matricula", "count"),
        voluntarios=("motivo_voluntario", lambda x: (x == True).sum()),
        involuntarios=("motivo_voluntario", lambda x: (x == False).sum())
    ).reset_index()
)

ativos_mensal = []
for mes in meses:
    mes_date = pd.Period(mes).to_timestamp()
    ativos_mes = df[(df["data de admissão"] <= mes_date) & ((df["data de desligamento"].isna()) | (df["data de desligamento"] > mes_date))]
    ativos_mensal.append({"mes": mes, "ativos": len(ativos_mes)})
ativos_mensal = pd.DataFrame(ativos_mensal)

turnover_mensal = turnover_mensal.merge(ativos_mensal, left_on="mes_desligamento", right_on="mes", how="left")
turnover_mensal["turnover_total_%"] = (turnover_mensal["desligados"] / turnover_mensal["ativos"]) * 100
turnover_mensal["turnover_vol_%"] = (turnover_mensal["voluntarios"] / turnover_mensal["ativos"]) * 100
turnover_mensal["turnover_invol_%"] = (turnover_mensal["involuntarios"] / turnover_mensal["ativos"]) * 100
turnover_mensal = turnover_mensal.fillna(0)

# KPIs médios
turnover_medio_total = round(turnover_mensal["turnover_total_%"].mean(), 1)
turnover_medio_vol = round(turnover_mensal["turnover_vol_%"].mean(), 1)
turnover_medio_invol = round(turnover_mensal["turnover_invol_%"].mean(), 1)

# Tenure médio
df_desligados = df[~df["ativo"]].copy()
df_desligados["tenure_meses"] = (df_desligados["data de desligamento"] - df_desligados["data de admissão"]).dt.days / 30
tenure_total = round(df_desligados["tenure_meses"].mean(), 1)
tenure_vol = round(df_desligados.loc[df_desligados["motivo_voluntario"], "tenure_meses"].mean(), 1)
tenure_invol = round(df_desligados.loc[~df_desligados["motivo_voluntario"], "tenure_meses"].mean(), 1)
tenure_ativos = round(df.loc[df["ativo"], "tempo_casa"].mean(), 1)

colT1, colT2, colT3 = st.columns(3)
colT1.metric("📉 Turnover Médio Total (%)", turnover_medio_total)
colT2.metric("🫶 Voluntário (%)", turnover_medio_vol)
colT3.metric("📋 Involuntário (%)", turnover_medio_invol)

colTT1, colTT2, colTT3, colTT4 = st.columns(4)
colTT1.metric("⏱️ Tenure Total", f"{tenure_total}m")
colTT2.metric("🤝 Tenure Voluntário", f"{tenure_vol}m")
colTT3.metric("🏢 Tenure Involuntário", f"{tenure_invol}m")
colTT4.metric("👥 Tenure Ativos", f"{tenure_ativos}m")

fig_turnover_mensal = go.Figure()
fig_turnover_mensal.add_trace(go.Scatter(x=turnover_mensal["mes_desligamento"], y=turnover_mensal["turnover_total_%"], name="Total", line=dict(color="#00FFAA", width=3)))
fig_turnover_mensal.add_trace(go.Scatter(x=turnover_mensal["mes_desligamento"], y=turnover_mensal["turnover_vol_%"], name="Voluntário", line=dict(color="#FFD700", dash="dash")))
fig_turnover_mensal.add_trace(go.Scatter(x=turnover_mensal["mes_desligamento"], y=turnover_mensal["turnover_invol_%"], name="Involuntário", line=dict(color="#FF4500", dash="dot")))
fig_turnover_mensal.update_layout(template="plotly_dark", title="📆 Evolução Mensal do Turnover (%)", xaxis_title="Mês", yaxis_title="Turnover (%)")
st.plotly_chart(fig_turnover_mensal, use_container_width=True)

st.divider()

# =========================
# SEÇÃO 3 - RISCO DE TURNOVER (TRI)
# =========================
st.markdown("## 🔮 Risco de Turnover (TRI)")

now = pd.Timestamp.now()
df["meses_desde_promocao"] = (now - df["ultima promoção"]).dt.days / 30
df["meses_desde_merito"] = (now - df["ultimo mérito"]).dt.days / 30
df["tempo_casa"] = (now - df["data de admissão"]).dt.days / 30

gestor_size = df.groupby("matricula do gestor")["matricula"].count().rename("tamanho_equipe")
df = df.merge(gestor_size, left_on="matricula do gestor", right_index=True, how="left")

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

avg_risk = round(df["risco_turnover"].mean(), 1)
pct_high = round((df["risco_categoria"] == "Alto").mean() * 100, 1)
tempo_alto = round(df["meses_desde_promocao"].mean(), 1)
tamanho_medio_eq = round(df["tamanho_equipe"].mean(), 1)
nota_media_perf = round(df["score_perf_raw"].mean(), 1)

colR1, colR2, colR3, colR4, colR5 = st.columns(5)
colR1.metric("⚠️ Risco Médio (TRI)", avg_risk)
colR2.metric("🚨 % em Risco Alto", f"{pct_high}%")
colR3.metric("📅 Meses desde última promoção", tempo_alto)
colR4.metric("👥 Tamanho médio da equipe", tamanho_medio_eq)
colR5.metric("⭐ Nota média de performance", nota_media_perf)

# Curva por tempo sem promoção
bins = [0, 3, 6, 12, 24, np.inf]
labels = ["0-3m", "3-6m", "6-12m", "12-24m", "+24m"]
df["faixa_tempo_sem_promo"] = pd.cut(df["meses_desde_promocao"].fillna(0), bins=bins, labels=labels)
risco_por_faixa = df.groupby("faixa_tempo_sem_promo")["risco_turnover"].mean().reset_index().rename(columns={"risco_turnover": "Risco Médio"})
fig_risco_tempo = px.line(risco_por_faixa, x="faixa_tempo_sem_promo", y="Risco Médio", markers=True, color_discrete_sequence=["#00FFFF"])
fig_risco_tempo.update_layout(template="plotly_dark", title="📈 Risco de Turnover por Tempo sem Promoção")
st.plotly_chart(fig_risco_tempo, use_container_width=True)

# =========================
# ANÁLISE QUALITATIVA COM BOTÃO
# =========================
st.markdown("## 💡 Insights Analíticos (IA)")
st.markdown("Clique no botão abaixo para gerar um resumo interpretativo sobre os resultados atuais.")
if st.button("🤖 Gerar Análise com IA"):
    with st.spinner("🔎 Gerando análise com GPT-4..."):
        try:
            openai.api_key = st.secrets["OPENAI_API_KEY"]
            prompt = f"""
            Analise os dados de headcount, turnover e risco:
            - Headcount atual: {total_ativos}
            - Turn
