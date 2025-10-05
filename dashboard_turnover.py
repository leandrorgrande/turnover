import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import openai

# =========================
# CONFIGURAÇÃO GERAL
# =========================
st.set_page_config(page_title="Dashboard de People Analytics • v6", layout="wide")

st.markdown("""
<style>
html, body, [class*="css"] {
  background-color: #0e1117 !important;
  color: #E6E6E6 !important;
  font-family: "Inter", system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, "Helvetica Neue";
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

st.title("🚀 Dashboard de People Analytics — v6")
st.caption("Headcount • Turnover • Risco de Turnover (TRI) • Insights com IA")

# =========================
# UPLOAD
# =========================
uploaded_file = st.file_uploader("📂 Carregue o arquivo Excel (.xlsx)", type=["xlsx"])
if not uploaded_file:
    st.info("⬆️ Envie o arquivo com abas: empresa, colaboradores e performance.")
    st.stop()

empresa = pd.read_excel(uploaded_file, sheet_name="empresa")
colab = pd.read_excel(uploaded_file, sheet_name="colaboradores")
perf = pd.read_excel(uploaded_file, sheet_name="performance")

# =========================
# PREPARAÇÃO DE DADOS
# =========================
for c in ["data de admissão", "data de desligamento", "ultima promoção", "ultimo mérito"]:
    if c in colab.columns:
        colab[c] = pd.to_datetime(colab[c], errors="coerce")

colab["ativo"] = colab["data de desligamento"].isna()
colab["ano_desligamento"] = colab["data de desligamento"].dt.year
colab["motivo_voluntario"] = colab["motivo de desligamento"].fillna("").str.contains("Pedido", case=False)

# performance - última avaliação
if "data de encerramento do ciclo" in perf.columns:
    perf["data de encerramento do ciclo"] = pd.to_datetime(perf["data de encerramento do ciclo"], errors="coerce")
    perf_last = perf.sort_values(["matricula", "data de encerramento do ciclo"]).groupby("matricula", as_index=False).tail(1)
else:
    perf_last = perf.drop_duplicates(subset=["matricula"], keep="last")
colab = colab.merge(perf_last[["matricula", "avaliação"]], on="matricula", how="left")

# criar tempo de casa
now = pd.Timestamp.now()
colab["tempo_casa"] = (now - colab["data de admissão"]).dt.days / 30

# =========================
# FILTROS
# =========================
st.sidebar.header("🔎 Filtros")
empresa_sel = st.sidebar.selectbox("Empresa", empresa["nome empresa"].tolist())
dept_opts = ["Todos"] + sorted(colab["departamento"].dropna().unique().tolist())
dept_sel = st.sidebar.selectbox("Departamento", dept_opts)

df = colab.copy()
if dept_sel != "Todos":
    df = df[df["departamento"] == dept_sel]

# =========================
# ABAS
# =========================
tab_headcount, tab_turnover, tab_risco, tab_ia = st.tabs(["👥 Headcount", "🔄 Turnover", "🔮 Risco (TRI)", "🤖 Insights com IA"])

# =========================
# 1️⃣ HEADCOUNT
# =========================
with tab_headcount:
    st.subheader("📊 Headcount e Estrutura Organizacional")
    ativos = df[df["ativo"]]

    total_ativos = len(ativos)
    total_departamentos = ativos["departamento"].nunique()

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
    else:
        pct_fem = 0

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
    headcount_area = ativos.groupby("departamento")["matricula"].count().reset_index()
    fig_area = px.bar(headcount_area, x="departamento", y="matricula", color="matricula", color_continuous_scale="Tealgrn")
    fig_area.update_layout(template="plotly_dark", title="Headcount por Departamento")
    st.plotly_chart(fig_area, use_container_width=True)

# =========================
# 2️⃣ TURNOVER
# =========================
with tab_turnover:
    st.subheader("🔄 Turnover e Tenure Médio")
    df["mes_desligamento"] = df["data de desligamento"].dt.to_period("M").astype(str)
    df_desligados = df[~df["ativo"]].copy()
    df_desligados["tenure_meses"] = (df_desligados["data de desligamento"] - df_desligados["data de admissão"]).dt.days / 30

    tenure_total = round(df_desligados["tenure_meses"].mean(), 1)
    tenure_vol = round(df_desligados.loc[df_desligados["motivo_voluntario"], "tenure_meses"].mean(), 1)
    tenure_invol = round(df_desligados.loc[~df_desligados["motivo_voluntario"], "tenure_meses"].mean(), 1)
    tenure_ativos = round(df.loc[df["ativo"], "tempo_casa"].mean(), 1)

    colA, colB, colC, colD = st.columns(4)
    colA.metric("⏱️ Tenure Total", f"{tenure_total}m")
    colB.metric("🤝 Voluntário", f"{tenure_vol}m")
    colC.metric("🏢 Involuntário", f"{tenure_invol}m")
    colD.metric("👥 Ativos", f"{tenure_ativos}m")

# =========================
# 3️⃣ RISCO (TRI)
# =========================
with tab_risco:
    st.subheader("🔮 Risco de Turnover (TRI)")
    now = pd.Timestamp.now()
    df["meses_desde_promocao"] = (now - df["ultima promoção"]).dt.days / 30
    df["meses_desde_merito"] = (now - df["ultimo mérito"]).dt.days / 30

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

    df["risco_turnover"] = (
        0.30 * df["score_perf_inv"] +
        0.25 * df["score_tempo_promo"] +
        0.15 * df["score_tempo_casa"] +
        0.15 * df["score_tamanho_eq"] +
        0.15 * df["score_merito"]
    ) * 100
    df["risco_turnover"] = df["risco_turnover"].clip(0, 100)

    avg_risk = round(df["risco_turnover"].mean(), 1)
    pct_high = round((df["risco_turnover"] > 60).mean() * 100, 1)

    colR1, colR2 = st.columns(2)
    colR1.metric("⚠️ Risco Médio (TRI)", avg_risk)
    colR2.metric("🚨 % Risco Alto", f"{pct_high}%")

    bins = [0, 3, 6, 12, 24, np.inf]
    labels = ["0-3m", "3-6m", "6-12m", "12-24m", "+24m"]
    df["faixa_tempo_sem_promo"] = pd.cut(df["meses_desde_promocao"].fillna(0), bins=bins, labels=labels)

    risco_por_faixa = df.groupby("faixa_tempo_sem_promo")["risco_turnover"].mean().reset_index()
    fig_risco = px.line(risco_por_faixa, x="faixa_tempo_sem_promo", y="risco_turnover", markers=True, color_discrete_sequence=["#00FFFF"])
    fig_risco.update_layout(template="plotly_dark", title="📈 Risco Médio por Tempo sem Promoção")
    st.plotly_chart(fig_risco, use_container_width=True)

# =========================
# 4️⃣ INSIGHTS COM IA
# =========================
with tab_ia:
    st.subheader("🤖 Insights Analíticos com GPT-4")
    st.markdown("Gere uma análise qualitativa dos resultados atuais.")
    if st.button("Gerar Análise com IA"):
        with st.spinner("Gerando insights..."):
            try:
                openai.api_key = st.secrets["OPENAI_API_KEY"]
                prompt = f"""
                Gere uma análise de People Analytics considerando:
                - Headcount: {len(df[df['ativo']])}
                - Turnover médio e tenure: {round(df['tempo_casa'].mean(),1)}m
                - Risco médio TRI: {avg_risk}, {pct_high}% alto.
                Crie 3 a 4 frases com contexto, causas e recomendações práticas.
                """
                resp = openai.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[{"role": "system", "content": "Você é um analista de People Analytics."},
                              {"role": "user", "content": prompt}],
                    temperature=0.6
                )
                st.success(resp.choices[0].message.content)
            except Exception as e:
                st.error(f"Erro: {e}")
    else:
        st.info("Clique para gerar análise com IA.")

st.caption("• Versão 6.0 • Dashboard modular com abas e IA sob demanda.")
