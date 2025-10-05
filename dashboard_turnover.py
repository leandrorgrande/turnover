import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import openai

# =========================
# CONFIG & ESTILO FUTURISTA
# =========================
st.set_page_config(page_title="Dashboard de Turnover • v3", layout="wide")

st.markdown("""
<style>
/* Fundo e tipografia */
html, body, [class*="css"]  {
  background-color: #0e1117 !important;
  color: #E6E6E6 !important;
  font-family: "Inter", system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, "Helvetica Neue", "Noto Sans", "Apple Color Emoji", "Segoe UI Emoji" !important;
}
/* Cards de métricas */
div[data-testid="stMetric"] {
  background: linear-gradient(135deg, #1a1f2b 0%, #151922 100%);
  border-radius: 18px;
  padding: 14px 16px;
  box-shadow: 0 0 18px rgba(0, 255, 204, 0.12);
  border: 1px solid rgba(0,255,204,0.12);
}
</style>
""", unsafe_allow_html=True)

st.title("🚀 Dashboard de Turnover — v3 (com Índice de Risco)")
st.caption("Visual futurista e interativo para análises de rotatividade, retenção, performance e **risco de turnover (TRI)**.")

# =========================
# UPLOAD
# =========================
uploaded_file = st.file_uploader("📂 Carregue seu Excel (.xlsx) com as abas: empresa, colaboradores, performance", type=["xlsx"])

if not uploaded_file:
    st.info("⬆️ Envie o arquivo para iniciar. Dica: use o `basededados_rh_ficticia_empresas.xlsx` que você já tem.")
    st.stop()

# =========================
# LEITURA & PREPARO BASE
# =========================
empresa = pd.read_excel(uploaded_file, sheet_name="empresa")
colab = pd.read_excel(uploaded_file, sheet_name="colaboradores")
perf = pd.read_excel(uploaded_file, sheet_name="performance")

# Tipos & datas
for c in ["data de admissão", "data de desligamento", "ultima promoção", "ultimo mérito"]:
    if c in colab.columns:
        colab[c] = pd.to_datetime(colab[c], errors="coerce")
if "data de encerramento do ciclo" in perf.columns:
    perf["data de encerramento do ciclo"] = pd.to_datetime(perf["data de encerramento do ciclo"], errors="coerce")

# Flags básicas
colab["ativo"] = colab["data de desligamento"].isna()
colab["ano_desligamento"] = colab["data de desligamento"].dt.year
colab["motivo_voluntario"] = colab["motivo de desligamento"].fillna("").str.contains("Pedido", case=False, na=False)

# =========================
# PERFORMANCE (última avaliação por matrícula)
# =========================
# Se houver várias avaliações por pessoa, mantemos a última por data de encerramento
if "data de encerramento do ciclo" in perf.columns:
    perf_sorted = perf.sort_values(["matricula", "data de encerramento do ciclo"])
    perf_last = perf_sorted.groupby("matricula", as_index=False).tail(1)
else:
    # fallback: qualquer linha (sem data)
    perf_last = perf.drop_duplicates(subset=["matricula"], keep="last")

# Merge – adiciona a última avaliação ao colaborador
colab = colab.merge(perf_last[["matricula", "avaliação"]], on="matricula", how="left")

# =========================
# FILTROS
# =========================
st.sidebar.header("🔎 Filtros")

# (Opcional) Empresa – não há vínculo direto no schema; mantemos apenas para contexto
empresa_sel = st.sidebar.selectbox("Empresa (contexto)", options=empresa["nome empresa"].tolist())

dept_opts = ["Todos"] + sorted(colab["departamento"].dropna().unique().tolist())
dept_sel = st.sidebar.selectbox("Departamento", options=dept_opts)

anos_opts = ["Todos"] + sorted(colab["ano_desligamento"].dropna().unique().tolist())
ano_sel = st.sidebar.selectbox("Ano de desligamento", options=anos_opts)

df = colab.copy()
if dept_sel != "Todos":
    df = df[df["departamento"] == dept_sel]
if ano_sel != "Todos":
    df = df[df["ano_desligamento"] == ano_sel]

# =========================
# KPIs E ANÁLISES TEMPORAIS DE TURNOVER
# =========================

st.markdown("## 📊 Visão Temporal de Turnover e Tenure")

# --- Preparar datas base
df["mes_desligamento"] = df["data de desligamento"].dt.to_period("M").astype(str)
df["mes_admissao"] = df["data de admissão"].dt.to_period("M").astype(str)
df["ano_mes"] = df["data de desligamento"].fillna(df["data de admissão"]).dt.to_period("M").astype(str)

# --- Total por mês
meses = sorted(df["ano_mes"].dropna().unique().tolist())

# Contagem de desligamentos e ativos
turnover_mensal = (
    df.groupby("mes_desligamento")
    .agg(
        desligados=("matricula", "count"),
        voluntarios=("motivo_voluntario", lambda x: (x == True).sum()),
        involuntarios=("motivo_voluntario", lambda x: (x == False).sum()),
    )
    .reset_index()
)

# Calcular ativos estimados (colaboradores com admissão anterior e ainda sem desligamento naquele mês)
ativos_mensal = []
for mes in meses:
    mes_date = pd.Period(mes).to_timestamp()
    ativos = df[(df["data de admissão"] <= mes_date) & ((df["data de desligamento"].isna()) | (df["data de desligamento"] > mes_date))]
    ativos_mensal.append({"mes": mes, "ativos": len(ativos)})

ativos_mensal = pd.DataFrame(ativos_mensal)
turnover_mensal = turnover_mensal.merge(ativos_mensal, left_on="mes_desligamento", right_on="mes", how="left")

# --- Turnover %
turnover_mensal["turnover_total_%"] = (turnover_mensal["desligados"] / turnover_mensal["ativos"]) * 100
turnover_mensal["turnover_vol_%"] = (turnover_mensal["voluntarios"] / turnover_mensal["ativos"]) * 100
turnover_mensal["turnover_invol_%"] = (turnover_mensal["involuntarios"] / turnover_mensal["ativos"]) * 100
turnover_mensal = turnover_mensal.fillna(0)

# --- KPIs médios
turnover_medio_total = round(turnover_mensal["turnover_total_%"].mean(), 1)
turnover_medio_vol = round(turnover_mensal["turnover_vol_%"].mean(), 1)
turnover_medio_invol = round(turnover_mensal["turnover_invol_%"].mean(), 1)

# --- KPIs TENURE (tempo médio de casa)
df_desligados = df[~df["ativo"]].copy()
df_desligados["tenure_meses"] = (df_desligados["data de desligamento"] - df_desligados["data de admissão"]).dt.days / 30
tenure_total = round(df_desligados["tenure_meses"].mean(), 1)
tenure_vol = round(df_desligados.loc[df_desligados["motivo_voluntario"], "tenure_meses"].mean(), 1)
tenure_invol = round(df_desligados.loc[~df_desligados["motivo_voluntario"], "tenure_meses"].mean(), 1)
tenure_ativos = round(df.loc[df["ativo"], "tempo_casa"].mean(), 1)

# --- KPIs HEADER ORGANIZADOS EM BLOCOS
st.markdown("### 🧮 Indicadores de Turnover (Médias e Acumulados)")
colA, colB, colC = st.columns(3)
colA.metric("📉 Turnover Médio Total (%)", turnover_medio_total)
colB.metric("🤝 Voluntário (%)", turnover_medio_vol)
colC.metric("🏢 Involuntário (%)", turnover_medio_invol)

st.markdown("### ⏳ Tenure Médio (Tempo de Casa até Desligamento)")
colD, colE, colF, colG = st.columns(4)
colD.metric("⏱️ Total", f"{tenure_total} meses")
colE.metric("🫶 Voluntário", f"{tenure_vol} meses")
colF.metric("📋 Involuntário", f"{tenure_invol} meses")
colG.metric("👥 Ativos", f"{tenure_ativos} meses")

# --- GRÁFICO DE EVOLUÇÃO MENSAL
st.markdown("### 📆 Evolução Mensal do Turnover (%)")
fig_turnover_mensal = go.Figure()
fig_turnover_mensal.add_trace(go.Scatter(
    x=turnover_mensal["mes_desligamento"], y=turnover_mensal["turnover_total_%"],
    name="Total", line=dict(color="#00FFAA", width=3)
))
fig_turnover_mensal.add_trace(go.Scatter(
    x=turnover_mensal["mes_desligamento"], y=turnover_mensal["turnover_vol_%"],
    name="Voluntário", line=dict(color="#FFD700", width=2, dash="dash")
))
fig_turnover_mensal.add_trace(go.Scatter(
    x=turnover_mensal["mes_desligamento"], y=turnover_mensal["turnover_invol_%"],
    name="Involuntário", line=dict(color="#FF4500", width=2, dash="dot")
))
fig_turnover_mensal.update_layout(
    template="plotly_dark",
    title="📈 Turnover Mensal (Total, Voluntário e Involuntário)",
    xaxis_title="Mês",
    yaxis_title="Turnover (%)",
    hovermode="x unified"
)
st.plotly_chart(fig_turnover_mensal, use_container_width=True)

# =========================
# CÁLCULO DO TRI (Turnover Risk Index)
# =========================
now = pd.Timestamp.now()

# Tempos (meses)
df["meses_desde_promocao"] = (now - df["ultima promoção"]).dt.days.div(30).replace([np.inf, -np.inf], np.nan)
df["meses_desde_merito"] = (now - df["ultimo mérito"]).dt.days.div(30).replace([np.inf, -np.inf], np.nan)
df["tempo_casa"] = (now - df["data de admissão"]).dt.days.div(30).replace([np.inf, -np.inf], np.nan)

# Tamanho de equipe do gestor
gestor_size = df.groupby("matricula do gestor")["matricula"].count().rename("tamanho_equipe")
df = df.merge(gestor_size, left_on="matricula do gestor", right_index=True, how="left")

# Score de performance (quanto MENOR a avaliação, MAIOR o risco)
perf_map = {
    "excepcional": 10,
    "acima do esperado": 7,
    "dentro do esperado": 4,
    "abaixo do esperado": 1
}
df["avaliação_norm"] = df["avaliação"].str.lower().str.strip()
# normaliza para chaves do map
df["avaliação_norm"] = df["avaliação_norm"].replace({
    "excepcional": "excepcional",
    "acima do esperado": "acima do esperado",
    "dentro do esperado": "dentro do esperado",
    "abaixo do esperado": "abaixo do esperado"
})
df["score_perf_raw"] = df["avaliação_norm"].map(perf_map)
df["score_perf_raw"] = df["score_perf_raw"].fillna(4)  # neutro quando sem avaliação

# Normalizações robustas (evita divisão por zero)
def norm_0_1(s):
    s = s.astype(float)
    maxv = s.max(skipna=True)
    return s / maxv if pd.notna(maxv) and maxv not in [0, np.inf] else s.fillna(0).mul(0)

df["score_tempo_promo"]   = norm_0_1(df["meses_desde_promocao"].fillna(0))
df["score_tempo_casa"]    = norm_0_1(df["tempo_casa"].fillna(0))
df["score_merito"]        = norm_0_1(df["meses_desde_merito"].fillna(0))
df["score_tamanho_eq"]    = norm_0_1(df["tamanho_equipe"].fillna(0))

# Inverter performance (quanto pior, maior risco). 10 (excelente) → 0 risco; 1 (ruim) → alto risco
df["score_perf_inv"] = 1 - norm_0_1(df["score_perf_raw"])

# Pesos
W_PERF, W_PROMO, W_TEMPO, W_EQUIPE, W_MERITO = 0.30, 0.25, 0.15, 0.15, 0.15

# TRI 0-100
df["risco_turnover"] = (
    W_PERF  * df["score_perf_inv"] +
    W_PROMO * df["score_tempo_promo"] +
    W_TEMPO * df["score_tempo_casa"] +
    W_EQUIPE* df["score_tamanho_eq"] +
    W_MERITO* df["score_merito"]
) * 100

df["risco_turnover"] = df["risco_turnover"].clip(lower=0, upper=100)

df["risco_categoria"] = pd.cut(
    df["risco_turnover"],
    bins=[-0.001, 30, 60, 100],
    labels=["Baixo", "Médio", "Alto"]
)

# KPIs de risco
avg_risk = round(df["risco_turnover"].mean(), 1) if len(df) else 0.0
pct_high = round((df["risco_categoria"] == "Alto").mean() * 100, 1) if len(df) else 0.0

# =========================
# LAYOUT: KPIs
# =========================
st.markdown("### 📈 Indicadores de Pessoas")
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("👥 Total", total_colabs)
k2.metric("🏢 Ativos", ativos)
k3.metric("📉 Turnover (%)", f"{turnover}%")
k4.metric("🫶 Voluntário (%)", f"{perc_vol}%")
k5.metric("⏳ Tempo médio de casa", f"{tempo_medio_casa} m")
k6.metric("⚠️ Risco médio (TRI)", f"{avg_risk}")

st.markdown("### 🔥 Indicadores de Risco")
r1, r2 = st.columns(2)
r1.metric("🚨 % em Risco Alto", f"{pct_high}%")
r2.metric("🧠 Avaliações faltantes (impacto no TRI)", int(df["avaliação"].isna().sum()))

st.divider()

# =========================
# VISUALIZAÇÕES CLÁSSICAS
# =========================
c1, c2 = st.columns([1,1])

with c1:
    st.subheader("📊 Distribuição do Turnover")
    tipo_df = pd.DataFrame({
        "Tipo": ["Voluntário", "Involuntário"],
        "Percentual": [perc_vol, perc_invol]
    })
    fig_tipo = px.pie(
        tipo_df, values="Percentual", names="Tipo",
        color_discrete_sequence=["#00F5D4", "#9B5DE5"], hole=0.45
    )
    fig_tipo.update_layout(template="plotly_dark", margin=dict(l=0,r=0,t=30,b=0))
    st.plotly_chart(fig_tipo, use_container_width=True)

with c2:
    st.subheader("🏬 Turnover por Departamento (%)")
    depto_turn = (
        df.groupby("departamento")["ativo"]
        .apply(lambda x: 100 - x.mean() * 100)
        .reset_index(name="Turnover (%)")
        .sort_values("Turnover (%)", ascending=False)
    )
    if not depto_turn.empty:
        fig_depto = px.bar(
            depto_turn, x="departamento", y="Turnover (%)",
            color="Turnover (%)", color_continuous_scale="plasma"
        )
        fig_depto.update_layout(template="plotly_dark", xaxis_title=None, yaxis_title="%",
                                margin=dict(l=10,r=10,t=30,b=10))
        st.plotly_chart(fig_depto, use_container_width=True)
    else:
        st.info("Sem dados suficientes para calcular por departamento.")

st.subheader("⏳ Evolução Mensal de Desligamentos")
df["mes_desligamento"] = df["data de desligamento"].dt.to_period("M").astype(str)
turnover_tempo = df.loc[~df["ativo"]].groupby("mes_desligamento").size().reset_index(name="Desligamentos")
if not turnover_tempo.empty:
    fig_time = px.line(
        turnover_tempo, x="mes_desligamento", y="Desligamentos",
        markers=True, line_shape="spline", color_discrete_sequence=["#00FFAA"]
    )
    fig_time.update_layout(template="plotly_dark", margin=dict(l=10,r=10,t=30,b=10))
    st.plotly_chart(fig_time, use_container_width=True)
else:
    st.info("Sem desligamentos com data para exibir a série temporal.")

st.divider()

# =========================
# VISUALIZAÇÕES DE RISCO (TRI)
# =========================
st.header("🔮 Risco de Turnover (TRI)")

c3, c4 = st.columns([1,1])

with c3:
    st.subheader("🧭 Dispersão: Tempo desde Promoção × Risco")
    fig_risco = px.scatter(
        df,
        x="meses_desde_promocao", y="risco_turnover",
        color="avaliação",
        hover_data=["matricula", "departamento", "tamanho_equipe", "tempo_casa"],
        color_discrete_sequence=px.colors.sequential.Viridis,
        labels={"meses_desde_promocao": "Meses desde a última promoção", "risco_turnover": "TRI (0-100)"},
    )
    fig_risco.update_layout(template="plotly_dark", margin=dict(l=10,r=10,t=30,b=10))
    st.plotly_chart(fig_risco, use_container_width=True)

with c4:
    st.subheader("🌡️ Mapa de Calor: Risco Médio por Departamento & Gestor")
    heat = (
        df.groupby(["departamento", "matricula do gestor"])["risco_turnover"]
        .mean()
        .reset_index()
        .rename(columns={"risco_turnover": "Risco médio"})
    )
    if not heat.empty:
        fig_heat = px.density_heatmap(
            heat, x="matricula do gestor", y="departamento", z="Risco médio",
            color_continuous_scale="inferno"
        )
        fig_heat.update_layout(template="plotly_dark", margin=dict(l=10,r=10,t=30,b=10))
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("Sem dados suficientes para o heatmap de risco.")

st.subheader("🏆 Top 15 Colaboradores com Maior Risco")
top_risk = (
    df.loc[df["ativo"]]
    .sort_values("risco_turnover", ascending=False)
    .head(15)[["matricula", "departamento", "tamanho_equipe", "tempo_casa",
               "meses_desde_promocao", "meses_desde_merito", "avaliação", "risco_turnover", "risco_categoria"]]
)
st.dataframe(top_risk, use_container_width=True, hide_index=True)



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


# =========================
# EXPORT
# =========================
st.download_button(
    "💾 Baixar CSV com TRI (todas as colunas)",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="colaboradores_com_TRI.csv",
    mime="text/csv"
)

st.caption("• Versão 3.0 • TRI baseado em fatores de performance, carreira e estrutura. Ajuste os pesos conforme histórico real.")
