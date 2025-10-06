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
# 🎛️ FILTROS AVANÇADOS (LAYOUT MODERNO)
# =========================================================
with st.sidebar:
    st.markdown("## 🎯 Filtros de Análise")
    st.caption("Os filtros abaixo são interdependentes — selecione uma ou mais opções para refinar as análises.")
    st.divider()

    df_filt = df.copy()

    # =======================
    # 1️⃣ Empresa / Departamento / Cargo
    # =======================
    empresa_col = col_like(df_filt, "empresa") or col_like(df_filt, "nome empresa")
    dept_col = col_like(df_filt, "departamento")
    cargo_col = col_like(df_filt, "cargo")

    col1, col2 = st.columns(2)
    with col1:
        empresas = sorted(df_filt[empresa_col].dropna().unique().tolist()) if empresa_col else []
        empresa_sel = st.selectbox("🏢 Empresa", ["Todas"] + empresas)

    with col2:
        if empresa_col and empresa_sel != "Todas":
            df_filt = df_filt[df_filt[empresa_col] == empresa_sel]
        deptos = sorted(df_filt[dept_col].dropna().unique().tolist()) if dept_col else []
        dept_sel = st.multiselect("🏬 Departamento", deptos, default=deptos)

    if dept_col and dept_sel:
        df_filt = df_filt[df_filt[dept_col].isin(dept_sel)]

    cargos = sorted(df_filt[cargo_col].dropna().unique().tolist()) if cargo_col else []
    cargo_sel = st.multiselect("👔 Cargo", cargos, default=cargos)
    if cargo_col and cargo_sel:
        df_filt = df_filt[df_filt[cargo_col].isin(cargo_sel)]

    st.divider()

    # =======================
    # 2️⃣ Contrato / Gestor / Gênero
    # =======================
    tipo_col = col_like(df_filt, "tipo_contrato")
    gestor_col = col_like(df_filt, "matricula do gestor") or col_like(df_filt, "gestor")
    genero_col = col_like(df_filt, "genero")

    col3, col4 = st.columns(2)
    with col3:
        tipos = sorted(df_filt[tipo_col].dropna().unique().tolist()) if tipo_col else []
        tipo_sel = st.multiselect("📑 Tipo Contrato", tipos, default=tipos)
    with col4:
        gestores = sorted(df_filt[gestor_col].dropna().unique().tolist()) if gestor_col else []
        gestor_sel = st.multiselect("👤 Gestor", gestores, default=gestores)

    if tipo_col and tipo_sel:
        df_filt = df_filt[df_filt[tipo_col].isin(tipo_sel)]
    if gestor_col and gestor_sel:
        df_filt = df_filt[df_filt[gestor_col].isin(gestor_sel)]

    if genero_col:
        generos = sorted(df_filt[genero_col].dropna().unique().tolist())
        genero_sel = st.multiselect("⚧ Gênero", generos, default=generos)
        df_filt = df_filt[df_filt[genero_col].isin(genero_sel)]

    st.divider()

    # =======================
    # 3️⃣ Ano / Mês / Intervalo de Datas
    # =======================
    adm_col = col_like(df_filt, "data de admissão")
    desl_col = col_like(df_filt, "data de desligamento")

    if adm_col:
        df_filt["ano_adm"] = pd.to_datetime(df_filt[adm_col], errors="coerce").dt.year
        df_filt["mes_adm"] = pd.to_datetime(df_filt[adm_col], errors="coerce").dt.month_name()
    if desl_col:
        df_filt["ano_desl"] = pd.to_datetime(df_filt[desl_col], errors="coerce").dt.year
        df_filt["mes_desl"] = pd.to_datetime(df_filt[desl_col], errors="coerce").dt.month_name()

    anos_disp = sorted(set(df_filt.get("ano_adm", [])).union(df_filt.get("ano_desl", [])))
    meses_disp = sorted(set(df_filt.get("mes_adm", [])).union(df_filt.get("mes_desl", [])))

    col5, col6 = st.columns(2)
    with col5:
        ano_sel = st.multiselect("📆 Ano", [a for a in anos_disp if not pd.isna(a)], default=anos_disp)
    with col6:
        mes_sel = st.multiselect("🗓️ Mês", [m for m in meses_disp if isinstance(m, str)], default=meses_disp)

    if ano_sel:
        df_filt = df_filt[
            (df_filt.get("ano_adm").isin(ano_sel)) | (df_filt.get("ano_desl").isin(ano_sel))
        ]
    if mes_sel:
        df_filt = df_filt[
            (df_filt.get("mes_adm").isin(mes_sel)) | (df_filt.get("mes_desl").isin(mes_sel))
        ]

    data_min = (
        pd.to_datetime(df_filt[adm_col], errors="coerce").min()
        if adm_col else datetime(2023, 1, 1)
    )
    data_max = (
        pd.to_datetime(df_filt[desl_col], errors="coerce").max()
        if desl_col else datetime.now()
    )

    periodo = st.date_input(
        "🧭 Intervalo",
        value=(
            data_min.date() if not pd.isna(data_min) else datetime(2023, 1, 1).date(),
            data_max.date() if not pd.isna(data_max) else datetime.now().date()
        )
    )
    if adm_col:
        dt_ini, dt_fim = map(pd.to_datetime, periodo)
        df_filt = df_filt[df_filt[adm_col].between(dt_ini, dt_fim, inclusive="both")]

    st.divider()

    # =======================
    # 4️⃣ Botões de ação
    # =======================
    col_apply, col_clear = st.columns(2)
    with col_apply:
        if st.button("✅ Aplicar Filtros"):
            st.session_state["df_filt"] = df_filt
            st.success(f"📊 {len(df_filt):,} registros após aplicar filtros.")
    with col_clear:
        if st.button("🧹 Limpar Filtros"):
            st.session_state.pop("df_filt", None)
            st.experimental_rerun()

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

    # Turnover médio (total/vol/invol)
    adm_c, desl_c, mot_c = col_like(dfv, "data de admissão"), col_like(dfv, "data de desligamento"), col_like(dfv, "motivo de desligamento")
    ttot = tvol = tinv = 0
    if adm_c and desl_c:
        dft = dfv.copy()
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
            ttot, tvol, tinv = round(arr[:,0].mean(),1), round(arr[:,1].mean(),1), round(arr[:,2].mean(),1)
    st.markdown("### 🔄 Turnover Médio")
    c5, c6, c7 = st.columns(3)
    c5.metric("Total (%)", ttot)
    c6.metric("Voluntário (%)", tvol)
    c7.metric("Involuntário (%)", tinv)

    # Tenure médio
    tenure_total = 0
    if adm_c and desl_c:
        dfd = dfv[dfv["ativo"] == False].copy()
        dfd["tenure_meses"] = (dfd[desl_c] - dfd[adm_c]).dt.days / 30
        tenure_total = safe_mean(dfd["tenure_meses"])
    st.markdown("### ⏳ Tenure (Tempo Médio)")
    st.metric("Tenure Médio (m)", tenure_total)

def view_headcount(dfv):
    st.subheader("👥 Headcount — Estrutura")
    dept_c = col_like(dfv, "departamento")
    if dept_c:
        dist = dfv[dfv["ativo"]].groupby(dept_c)["matricula"].count().reset_index().rename(columns={"matricula": "Headcount"})
        fig = px.bar(dist, x=dept_c, y="Headcount", color="Headcount", color_continuous_scale="Tealgrn")
        fig.update_layout(template="plotly_dark", title="Headcount por Departamento", xaxis_title="Departamento", yaxis_title="Qtd")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem coluna 'departamento' para detalhar headcount.")

def view_turnover(dfv):
    st.subheader("🔄 Turnover — Evolução Mensal e Tenure")
    adm_c, desl_c, mot_c = col_like(dfv, "data de admissão"), col_like(dfv, "data de desligamento"), col_like(dfv, "motivo de desligamento")
    if not (adm_c and desl_c):
        st.warning("⚠️ Faltam colunas de admissão/desligamento para esta seção.")
        return
    dft = dfv.copy()
    dft[adm_c] = pd.to_datetime(dft[adm_c], errors="coerce")
    dft[desl_c] = pd.to_datetime(dft[desl_c], errors="coerce")
    dmin = dft[adm_c].min()
    dmax = dft[desl_c].max() if dft[desl_c].notna().any() else datetime.now()
    meses = pd.date_range(dmin, dmax, freq="MS")

    rows = []
    for mes in meses:
        ativos_mes = dft[(dft[adm_c] <= mes) & ((dft[desl_c].isna()) | (dft[desl_c] > mes))]
        deslig_mes = dft[(dft[desl_c].notna()) & (dft[desl_c].dt.to_period("M") == mes.to_period("M"))]
        a, d = len(ativos_mes), len(deslig_mes)
        dv = deslig_mes[mot_c].astype(str).str.contains("Pedido", case=False, na=False).sum() if mot_c else 0
        di = d - dv
        rows.append({
            "Mês": mes.strftime("%Y-%m"),
            "Ativos": a, "Desligados": d, "Voluntários": dv, "Involuntários": di,
            "Turnover Total (%)": (d/a)*100 if a>0 else 0,
            "Turnover Voluntário (%)": (dv/a)*100 if a>0 else 0,
            "Turnover Involuntário (%)": (di/a)*100 if a>0 else 0
        })
    turn = pd.DataFrame(rows)

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ativos Médios", int(turn["Ativos"].mean()) if not turn.empty else 0)
    c2.metric("Desligamentos Médios", int(turn["Desligados"].mean()) if not turn.empty else 0)
    c3.metric("Turnover Médio (%)", round(turn["Turnover Total (%)"].mean(),1) if not turn.empty else 0)
    c4.metric("Vol/Inv (%)",
              f"{round(turn['Turnover Voluntário (%)'].mean(),1) if not turn.empty else 0} / " +
              f"{round(turn['Turnover Involuntário (%)'].mean(),1) if not turn.empty else 0}")

    st.divider()

    # Gráfico 1: Evolução turnover
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=turn["Mês"], y=turn["Turnover Total (%)"], mode="lines+markers", name="Total", line=dict(color="#00FFFF", width=3)))
    fig1.add_trace(go.Scatter(x=turn["Mês"], y=turn["Turnover Voluntário (%)"], mode="lines+markers", name="Voluntário", line=dict(color="#FFD700", dash="dash")))
    fig1.add_trace(go.Scatter(x=turn["Mês"], y=turn["Turnover Involuntário (%)"], mode="lines+markers", name="Involuntário", line=dict(color="#FF4500", dash="dot")))
    fig1.update_layout(template="plotly_dark", title="📆 Evolução Mensal do Turnover (%)", xaxis_title="Mês", yaxis_title="Turnover (%)", hovermode="x unified")
    st.plotly_chart(fig1, use_container_width=True)

    # Gráfico 2: Ativos x Desligados
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=turn["Mês"], y=turn["Ativos"], name="Ativos", marker_color="rgba(0,255,204,0.4)"))
    fig2.add_trace(go.Bar(x=turn["Mês"], y=turn["Desligados"], name="Desligados", marker_color="rgba(255,80,80,0.7)"))
    fig2.update_layout(barmode="overlay", template="plotly_dark", title="📊 Ativos x Desligados por Mês", xaxis_title="Mês", yaxis_title="Quantidade")
    st.plotly_chart(fig2, use_container_width=True)

    # Tenure
    dfd = dft[dft["ativo"] == False].copy()
    dfd["tenure_meses"] = (dfd[desl_c] - dfd[adm_c]).dt.days / 30
    tenure_total = safe_mean(dfd["tenure_meses"])
    tenure_vol = safe_mean(dfd.loc[dfd[mot_c].astype(str).str.contains("Pedido", case=False, na=False) if mot_c else [], "tenure_meses"]) if mot_c else 0
    tenure_invol = safe_mean(dfd.loc[~dfd[mot_c].astype(str).str.contains("Pedido", case=False, na=False) if mot_c else [], "tenure_meses"]) if mot_c else 0

    st.markdown("### ⏳ Tenure até o desligamento")
    c5, c6, c7 = st.columns(3)
    c5.metric("Tenure Total (m)", f"{tenure_total}")
    c6.metric("Voluntário (m)", f"{tenure_vol}")
    c7.metric("Involuntário (m)", f"{tenure_invol}")

def view_risk(dfv):
    st.subheader("🔮 Risco de Turnover (TRI) — Índice Composto")

    now = pd.Timestamp.now()
    dfv["meses_desde_promocao"] = (now - pd.to_datetime(dfv.get("ultima promoção"), errors="coerce")).dt.days / 30 if "ultima promoção" in dfv.columns else 0
    dfv["meses_desde_merito"]  = (now - pd.to_datetime(dfv.get("ultimo mérito"), errors="coerce")).dt.days / 30 if "ultimo mérito" in dfv.columns else 0

    # tamanho de equipe
    if "tamanho_equipe" not in dfv.columns:
        dfv["tamanho_equipe"] = 0
    if "matricula do gestor" in dfv.columns:
        try:
            gsize = dfv.groupby("matricula do gestor")["matricula"].count().rename("tamanho_calc")
            dfv = dfv.merge(gsize, left_on="matricula do gestor", right_index=True, how="left")
            dfv["tamanho_equipe"] = dfv["tamanho_calc"].fillna(dfv["tamanho_equipe"])
            dfv.drop(columns=["tamanho_calc"], inplace=True, errors="ignore")
        except Exception:
            st.warning("⚠️ Não foi possível calcular tamanho das equipes. Usando 0 como padrão.")

    # performance
    perf_map = {"excepcional":10, "acima do esperado":7, "dentro do esperado":4, "abaixo do esperado":1}
    if "avaliação" in dfv.columns:
        dfv["score_perf_raw"] = dfv["avaliação"].astype(str).str.lower().map(perf_map).fillna(4)
    else:
        dfv["score_perf_raw"] = 4

    # scores normalizados
    dfv["score_perf_inv"]   = 1 - norm_0_1(dfv["score_perf_raw"])
    dfv["score_tempo_promo"]= norm_0_1(dfv["meses_desde_promocao"])
    dfv["score_tempo_casa"] = norm_0_1(dfv.get("tempo_casa", 0))
    dfv["score_merito"]     = norm_0_1(dfv["meses_desde_merito"])
    dfv["score_tamanho_eq"] = norm_0_1(dfv["tamanho_equipe"])

    # TRI
    dfv["risco_turnover"] = (
        0.30*dfv["score_perf_inv"] + 0.25*dfv["score_tempo_promo"] +
        0.15*dfv["score_tempo_casa"] + 0.15*dfv["score_tamanho_eq"] +
        0.15*dfv["score_merito"]
    ) * 100
    dfv["risco_turnover"] = dfv["risco_turnover"].clip(0, 100)

    avg_risk = safe_mean(dfv["risco_turnover"])
    pct_high = round((dfv["risco_turnover"] > 60).mean() * 100, 1)

    c1, c2 = st.columns(2)
    c1.metric("⚠️ Risco Médio (TRI)", avg_risk)
    c2.metric("🚨 % Risco Alto", f"{pct_high}%")

    # Curva risco x tempo sem promoção
    bins = [0, 3, 6, 12, 24, np.inf]
    labels = ["0-3m", "3-6m", "6-12m", "12-24m", "+24m"]
    dfv["faixa_tempo_sem_promo"] = pd.cut(pd.to_numeric(dfv["meses_desde_promocao"], errors="coerce").fillna(0), bins=bins, labels=labels)

    risco_por_faixa = dfv.groupby("faixa_tempo_sem_promo")["risco_turnover"].mean().reset_index().rename(columns={"risco_turnover":"Risco Médio"})
    fig = px.line(risco_por_faixa, x="faixa_tempo_sem_promo", y="Risco Médio", markers=True, color_discrete_sequence=["#00FFFF"])
    fig.update_layout(template="plotly_dark", title="📈 Risco Médio por Tempo sem Promoção", xaxis_title="Faixa", yaxis_title="Risco (0-100)")
    st.plotly_chart(fig, use_container_width=True)

# =========================================================
# RENDER DA VIEW SELECIONADA (usa df_filt)
# =========================================================
view = st.session_state["view"]
if view == "overview":
    view_overview(df_filt.copy())
elif view == "headcount":
    view_headcount(df_filt.copy())
elif view == "turnover":
    view_turnover(df_filt.copy())
elif view == "risk":
    view_risk(df_filt.copy())
else:
    view_overview(df_filt.copy())
