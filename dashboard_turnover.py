import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# =========================================================
# CONFIGURAÇÃO E ESTILO
# =========================================================
st.set_page_config(page_title="Dashboard Turnover • Single Page", layout="wide")

st.markdown("""
<style>
html, body, [class*="css"] { background-color: #0e1117 !important; color: #E6E6E6 !important;
  font-family: "Inter", system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, "Helvetica Neue"; }
div[data-testid="stMetric"] { background: linear-gradient(135deg, #1a1f2b 0%, #151922 100%);
  border-radius: 18px; padding: 14px 16px; box-shadow: 0 0 18px rgba(0,255,204,0.12);
  border: 1px solid rgba(0,255,204,0.10); }
</style>
""", unsafe_allow_html=True)

st.title("🚀 Dashboard de People Analytics — Turnover (Single Page)")
st.caption("Filtros globais à esquerda, painel de qualidade recolhível e navegação por seções na mesma página.")

# =========================================================
# HELPERS
# =========================================================
DATE_COLS = ["data de admissão", "data de desligamento", "ultima promoção", "ultimo mérito"]

def col_like(df, name):
    for c in df.columns:
        if c.lower().strip() == name.lower().strip():
            return c
    return None

def safe_mean(series):
    try:
        return round(pd.to_numeric(series, errors="coerce").dropna().mean(), 1)
    except Exception:
        return 0

def norm_0_1(s: pd.Series):
    s = pd.to_numeric(s, errors="coerce").fillna(0).astype(float)
    if s.empty:
        return s
    minv, maxv = s.min(), s.max()
    rng = maxv - minv
    if rng == 0 or pd.isna(rng):
        return s * 0
    return (s - minv) / rng

@st.cache_data(show_spinner=False)
def load_excel(file):
    try:
        return pd.read_excel(file, sheet_name=None)
    except Exception as e:
        st.error(f"Erro ao carregar arquivo: {e}")
        return {}

def to_datetime_safe(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df

def ensure_core_fields(colab):
    # flag ativo
    if "data de desligamento" in colab.columns:
        colab["ativo"] = colab["data de desligamento"].isna()
    else:
        colab["ativo"] = True
    # tempo de casa (meses)
    if "data de admissão" in colab.columns:
        now = pd.Timestamp.now()
        colab["tempo_casa"] = (now - colab["data de admissão"]).dt.days / 30
    else:
        colab["tempo_casa"] = np.nan
    return colab

def merge_last_performance(colab, perf):
    if perf is None or perf.empty:
        return colab
    p = perf.copy()
    if "data de encerramento do ciclo" in p.columns:
        p["data de encerramento do ciclo"] = pd.to_datetime(p["data de encerramento do ciclo"], errors="coerce")
        last = p.sort_values(["matricula", "data de encerramento do ciclo"]).groupby("matricula", as_index=False).tail(1)
    else:
        last = p.drop_duplicates(subset=["matricula"], keep="last")
    if "avaliação" in last.columns and "matricula" in colab.columns:
        colab = colab.merge(last[["matricula", "avaliação"]], on="matricula", how="left")
    return colab

def show_sheet_preview(name, df, expected_cols=None):
    st.markdown(f"#### 📄 Aba `{name}`")
    if df.empty:
        st.warning("⚠️ Aba vazia ou não encontrada.")
        return
    st.write(f"Linhas: **{len(df)}** | Colunas: **{len(df.columns)}**")
    if expected_cols:
        missing = [c for c in expected_cols if c not in df.columns]
        if missing:
            st.warning(f"⚠️ Colunas ausentes: {', '.join(missing)}")
    st.dataframe(df.head(5), use_container_width=True)

def clean_and_warn(df, expected, name):
    """Ignora colunas extras (avisa) e alerta para faltantes. Não quebra o app."""
    if df.empty:
        return df
    current = set(df.columns)
    expected_set = set(expected)
    extras = current - expected_set
    missing = expected_set - current
    if extras:
        st.info(f"ℹ️ A aba **{name}** contém colunas extras ignoradas: {', '.join(sorted(extras))}")
        df = df[[c for c in df.columns if c in expected_set]]
    if missing:
        st.warning(f"⚠️ A aba **{name}** está faltando colunas: {', '.join(sorted(missing))}")
    return df

# =========================================================
# 🧩 UPLOAD, LEITURA E ANÁLISE DE QUALIDADE DOS DADOS
# =========================================================
uploaded = st.file_uploader(
    "📂 Carregue o Excel (.xlsx) com abas 'empresa', 'colaboradores' e 'performance'",
    type=["xlsx"]
)
if not uploaded:
    st.info("⬆️ Envie o arquivo para começar a análise.")
    st.stop()

with st.expander("🧩 Análise de Qualidade e Estrutura dos Dados", expanded=False):

    st.markdown(
        "Visualize aqui como o arquivo foi carregado e validado. "
        "Essa etapa ocorre automaticamente antes de calcular os indicadores."
    )

    @st.cache_data(show_spinner=True)
    def load_and_prepare(file):
        """Carrega e trata os dados de forma cacheada e segura."""
        sheets = load_excel(file)

        empresa = sheets.get("empresa", pd.DataFrame())
        colab = sheets.get("colaboradores", pd.DataFrame())
        perf = sheets.get("performance", pd.DataFrame())

        expected_cols = {
            "empresa": ["nome empresa", "cnpj", "unidade", "cidade", "uf"],
            "colaboradores": [
                "matricula", "nome", "departamento", "cargo", "matricula do gestor",
                "tipo_contrato", "genero", "data de admissão", "data de desligamento",
                "motivo de desligamento", "ultima promoção", "ultimo mérito"
            ],
            "performance": ["matricula", "avaliação", "data de encerramento do ciclo"]
        }

        # Limpeza e alertas
        empresa = clean_and_warn(empresa, expected_cols["empresa"], "empresa")
        colab = clean_and_warn(colab, expected_cols["colaboradores"], "colaboradores")
        perf = clean_and_warn(perf, expected_cols["performance"], "performance")

        # Conversão e merges
        colab = to_datetime_safe(colab, DATE_COLS)
        colab = ensure_core_fields(colab)
        colab = merge_last_performance(colab, perf)

        return empresa, colab, perf, expected_cols

    # --- Executa a carga real ---
    empresa, colab, perf, expected_cols = load_and_prepare(uploaded)
    df = colab.copy()



# =========================================================
# 🎛️ FILTROS LATERAIS (COM COMPETÊNCIA FUNCIONAL)
# =========================================================
with st.sidebar:
    st.header("🔎 Filtros Inteligentes")
    st.caption("Os filtros se adaptam automaticamente ao conteúdo da base.")

    df_filt = df.copy()

    def get_unique(df, col):
        if not col or col not in df.columns:
            return []
        vals = sorted([v for v in df[col].dropna().unique().tolist() if str(v).strip() != ""])
        return vals

    # Empresa
    emp_col = col_like(df_filt, "empresa") or col_like(df_filt, "nome empresa")
    emp_opts = get_unique(df_filt, emp_col)
    emp_sel = st.selectbox("🏢 Empresa", ["Todas"] + emp_opts)
    if emp_sel != "Todas" and emp_col:
        df_filt = df_filt[df_filt[emp_col] == emp_sel]

    # Departamento
    dept_col = col_like(df_filt, "departamento")
    dept_opts = get_unique(df_filt, dept_col)
    dept_sel = st.multiselect("🏬 Departamento", dept_opts, default=dept_opts)
    if dept_sel and dept_col:
        df_filt = df_filt[df_filt[dept_col].isin(dept_sel)]

    # Cargo
    cargo_col = col_like(df_filt, "cargo")
    cargo_opts = get_unique(df_filt, cargo_col)
    cargo_sel = st.multiselect("👔 Cargo", cargo_opts, default=cargo_opts)
    if cargo_sel and cargo_col:
        df_filt = df_filt[df_filt[cargo_col].isin(cargo_sel)]

    # Gestor
    gestor_col = col_like(df_filt, "matricula do gestor") or col_like(df_filt, "gestor")
    gestor_opts = get_unique(df_filt, gestor_col)
    gestor_sel = st.multiselect("👤 Gestor", gestor_opts, default=gestor_opts)
    if gestor_sel and gestor_col:
        df_filt = df_filt[df_filt[gestor_col].isin(gestor_sel)]

    # Tipo contrato
    tipo_col = col_like(df_filt, "tipo_contrato")
    tipo_opts = get_unique(df_filt, tipo_col)
    tipo_sel = st.multiselect("📑 Tipo Contrato", tipo_opts, default=tipo_opts)
    if tipo_sel and tipo_col:
        df_filt = df_filt[df_filt[tipo_col].isin(tipo_sel)]

    # ========================================================
    # 🧭 FILTRO DE COMPETÊNCIA
    # ========================================================
    st.divider()
    st.markdown("### 🧭 Competência de Referência")

    adm_col = col_like(df_filt, "data de admissão")
    desl_col = col_like(df_filt, "data de desligamento")

    meses_map = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
        7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    meses_inv = {v: k for k, v in meses_map.items()}

    anos = sorted(set(
        pd.to_datetime(df_filt[adm_col], errors="coerce").dt.year.dropna().astype(int).tolist() +
        pd.to_datetime(df_filt[desl_col], errors="coerce").dt.year.dropna().astype(int).tolist()
    ))

    ano_sel = st.selectbox("📆 Ano de Competência", ["Todos"] + anos)
    mes_sel = st.selectbox("🗓️ Mês de Competência", ["Todos"] + list(meses_map.values()))

    # Cria df_final e status ativo/desligado com base no filtro
    df_final = df_filt.copy()
    if ano_sel != "Todos" and mes_sel != "Todos":
        mes_num = meses_inv[mes_sel]
        inicio = pd.Timestamp(int(ano_sel), mes_num, 1)
        fim = inicio + pd.offsets.MonthEnd(1)

        adm_dates = pd.to_datetime(df_final[adm_col], errors="coerce")
        desl_dates = pd.to_datetime(df_final[desl_col], errors="coerce")

        df_final["ativo"] = (adm_dates <= fim) & ((desl_dates.isna()) | (desl_dates > fim))
        df_final["desligado_no_mes"] = (desl_dates >= inicio) & (desl_dates <= fim)

        ativos = df_final["ativo"].sum()
        deslig = df_final["desligado_no_mes"].sum()

        st.info(f"📅 {mes_sel}/{ano_sel} — 👥 Ativos: {ativos} | 🏁 Desligados: {deslig}")
    else:
        df_final["desligado_no_mes"] = False
        df_final["ativo"] = df_final["data de desligamento"].isna()
        st.caption("📊 Nenhuma competência aplicada — mostrando totais gerais.")

    # ========================================================
    # 🔍 BUSCA POR NOME
    # ========================================================
    nome_col = col_like(df_final, "nome")
    busca = st.text_input("🔍 Buscar colaborador")
    if busca and nome_col:
        df_final = df_final[df_final[nome_col].str.contains(busca, case=False, na=False)]

    st.divider()
    st.success(f"✅ {len(df_final):,} registros após aplicar filtros.")





# =========================================================
# 🧩 ANÁLISE DE QUALIDADE E ESTRUTURA DOS DADOS
# =========================================================
with st.expander("🧩 Análise de Qualidade e Estrutura dos Dados", expanded=False):

    st.markdown("Visualize aqui como o arquivo foi carregado e validado. "
                "Essa etapa ocorre automaticamente antes de calcular os indicadores.")

    @st.cache_data(show_spinner=True)
    def load_and_prepare(file):
        """Carrega e trata os dados de forma cacheada e segura."""
        sheets = load_excel(file)

        empresa = sheets.get("empresa", pd.DataFrame())
        colab = sheets.get("colaboradores", pd.DataFrame())
        perf = sheets.get("performance", pd.DataFrame())

        expected_cols = {
            "empresa": ["nome empresa", "cnpj", "unidade", "cidade", "uf"],
            "colaboradores": [
                "matricula", "nome", "departamento", "cargo", "matricula do gestor",
                "tipo_contrato", "genero", "data de admissão", "data de desligamento",
                "motivo de desligamento", "ultima promoção", "ultimo mérito"
            ],
            "performance": ["matricula", "avaliação", "data de encerramento do ciclo"]
        }

        # Limpeza e alertas
        empresa = clean_and_warn(empresa, expected_cols["empresa"], "empresa")
        colab = clean_and_warn(colab, expected_cols["colaboradores"], "colaboradores")
        perf = clean_and_warn(perf, expected_cols["performance"], "performance")

        # Conversão e merges
        colab = to_datetime_safe(colab, DATE_COLS)
        colab = ensure_core_fields(colab)
        colab = merge_last_performance(colab, perf)

        return empresa, colab, perf, expected_cols

    # --- Executa a carga real ---
    empresa, colab, perf, expected_cols = load_and_prepare(uploaded)
    df = colab.copy()

    # --- Exibe resultados e estrutura ---
    st.markdown("### Estrutura das Abas")
    c1, c2, c3 = st.columns(3)
    with c1: show_sheet_preview("empresa", empresa, expected_cols["empresa"])
    with c2: show_sheet_preview("colaboradores", colab, expected_cols["colaboradores"])
    with c3: show_sheet_preview("performance", perf, expected_cols["performance"])

    st.divider()
    st.caption("✅ Dados processados com sucesso. Feche esta seção para visualizar as análises abaixo.")

# =========================================================
# NAVEGAÇÃO (PSEUDO-ABAS)
# =========================================================
if "view" not in st.session_state:
    st.session_state["view"] = "overview"
c1, c2, c3, c4 = st.columns(4)
if c1.button("📍 Visão Geral", use_container_width=True): st.session_state["view"] = "overview"
if c2.button("👥 Headcount", use_container_width=True): st.session_state["view"] = "headcount"
if c3.button("🔄 Turnover", use_container_width=True): st.session_state["view"] = "turnover"
if c4.button("🔮 Risco (TRI)", use_container_width=True): st.session_state["view"] = "risk"

st.markdown("---")

# =========================================================
# VIEWS
# =========================================================
def view_overview(dfv):
    st.subheader("📍 Visão Geral — KPIs Consolidados")

    # -------------------------------
    # KPI BÁSICOS
    # -------------------------------
    ativos = dfv[dfv["ativo"] == True]
    total_ativos = len(ativos)

    tipo_c = col_like(ativos, "tipo_contrato")
    pct_clt = round((ativos[tipo_c].astype(str).str.upper().eq("CLT")).mean()*100,1) if tipo_c else 0

    gen_c = col_like(ativos, "genero")
    pct_fem = round((ativos[gen_c].astype(str).str.lower().eq("feminino")).mean()*100,1) if gen_c else 0

    cargo_c = col_like(ativos, "cargo")
    pct_lider = round(ativos[cargo_c].astype(str).str.lower().str.contains("coord|gerente|diretor", na=False).mean()*100,1) if cargo_c else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ativos", total_ativos)
    c2.metric("% CLT", f"{pct_clt}%")
    c3.metric("% Feminino", f"{pct_fem}%")
    c4.metric("% Liderança", f"{pct_lider}%")

    # -------------------------------
    # TURNOVER
    # -------------------------------
    adm_c = col_like(dfv, "data de admissão")
    desl_c = col_like(dfv, "data de desligamento")
    mot_c = col_like(dfv, "motivo de desligamento")

    turnover_total = turnover_vol = turnover_inv = 0.0

    if "desligado_no_mes" in dfv.columns and "ativo" in dfv.columns:
        # Se veio da competência
        ativos_mes = dfv[dfv["ativo"] == True]
        deslig_mes = dfv[dfv["desligado_no_mes"] == True]

        a = len(ativos_mes)
        d = len(deslig_mes)

        if a > 0:
            dv = deslig_mes[mot_c].astype(str).str.contains("Pedido", case=False, na=False).sum() if mot_c else 0
            di = d - dv
            turnover_total = round((d / a) * 100, 1)
            turnover_vol = round((dv / a) * 100, 1)
            turnover_inv = round((di / a) * 100, 1)
    else:
        # Caso sem competência (histórico médio)
        dft = dfv.copy()
        if adm_c and desl_c:
            dft[adm_c] = pd.to_datetime(dft[adm_c], errors="coerce")
            dft[desl_c] = pd.to_datetime(dft[desl_c], errors="coerce")
            dmin = dft[adm_c].min()
            dmax = dft[desl_c].max() if dft[desl_c].notna().any() else datetime.now()
            meses = pd.date_range(dmin, dmax, freq="MS")
            vals = []
            for mes in meses:
                ativos_mes = dft[(dft[adm_c] <= mes) & ((dft[desl_c].isna()) | (dft[desl_c] > mes))]
                deslig_mes = dft[(dft[desl_c].notna()) & (dft[desl_c].dt.to_period("M") == mes.to_period("M"))]
                a, d = len(ativos_mes), len(deslig_mes)
                dv = deslig_mes[mot_c].astype(str).str.contains("Pedido", case=False, na=False).sum() if mot_c else 0
                di = d - dv
                vals.append([(d/a)*100 if a>0 else 0, (dv/a)*100 if a>0 else 0, (di/a)*100 if a>0 else 0])
            if vals:
                arr = np.array(vals)
                turnover_total, turnover_vol, turnover_inv = round(arr[:,0].mean(),1), round(arr[:,1].mean(),1), round(arr[:,2].mean(),1)

    st.markdown("### 🔄 Turnover Médio")
    c5, c6, c7 = st.columns(3)
    c5.metric("Total (%)", turnover_total)
    c6.metric("Voluntário (%)", turnover_vol)
    c7.metric("Involuntário (%)", turnover_inv)

    # -------------------------------
    # TENURE MÉDIO
    # -------------------------------
    tenure_total = 0
    if adm_c and desl_c:
        dfd = dfv[dfv["ativo"] == False].copy()
        dfd["tenure_meses"] = (dfd[desl_c] - dfd[adm_c]).dt.days / 30
        tenure_total = safe_mean(dfd["tenure_meses"])

    st.markdown("### ⏳ Tenure (Tempo Médio)")
    st.metric("Tenure Médio (m)", tenure_total)
  

# =========================================================
# RENDER DA VIEW SELECIONADA (usa df_filt)
# =========================================================
view = st.session_state["view"]
if view == "overview":
    view_overview(df_final.copy())
elif view == "headcount":
    view_headcount(df_final.copy())
elif view == "turnover":
    view_turnover(df_final.copy())
elif view == "risk":
    view_risk(df_final.copy())
else:
    view_overview(df_final.copy())

def view_headcount(dfv):
    st.subheader("👥 Headcount — Estrutura e Evolução")

    dept_c = col_like(dfv, "departamento")
    if not dept_c:
        st.info("Sem coluna 'departamento' para detalhar headcount.")
        return

    # Caso tenha competência, usa apenas os ativos
    if "ativo" in dfv.columns:
        base = dfv[dfv["ativo"] == True]
    else:
        base = dfv[dfv["data de desligamento"].isna()]

    if base.empty:
        st.warning("Nenhum colaborador ativo para o filtro selecionado.")
        return

    dist = base.groupby(dept_c)["matricula"].count().reset_index().rename(columns={"matricula": "Headcount"})
    fig = px.bar(
        dist,
        x=dept_c,
        y="Headcount",
        color="Headcount",
        color_continuous_scale="Tealgrn"
    )
    fig.update_layout(
        template="plotly_dark",
        title="Headcount por Departamento (Ativos no Período)",
        xaxis_title="Departamento",
        yaxis_title="Qtd"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Adicional: % por departamento
    dist["%"] = (dist["Headcount"] / dist["Headcount"].sum()) * 100
    st.dataframe(dist.sort_values("Headcount", ascending=False).reset_index(drop=True), use_container_width=True)
