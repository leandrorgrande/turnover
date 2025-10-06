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
# 🎛️ PAINEL DE FILTROS (LAYOUT MELHORADO)
# =========================================================
st.markdown("""
<style>
.filter-card {
    background: linear-gradient(135deg, #1a1f2b, #151922);
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 10px;
    box-shadow: 0 0 14px rgba(0,255,204,0.12);
    border: 1px solid rgba(0,255,204,0.12);
}
.filter-label {
    color: #00FFC8;
    font-weight: 600;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

with st.container():
    st.markdown("### 🎛️ Filtros Globais")

    c1, c2, c3 = st.columns(3)
    c4, c5, c6 = st.columns(3)

    # --- EMPRESA ---
    empresa_col = col_like(df, "empresa") or col_like(df, "nome empresa")
    empresas = sorted(df[empresa_col].dropna().unique().tolist()) if empresa_col else []
    with c1:
        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
        st.markdown('<div class="filter-label">🏢 Empresa</div>', unsafe_allow_html=True)
        empresa_sel = st.selectbox("", ["Todas"] + empresas)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- DEPARTAMENTO ---
    dept_col = col_like(df, "departamento")
    deptos = sorted(df[dept_col].dropna().unique().tolist()) if dept_col else []
    with c2:
        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
        st.markdown('<div class="filter-label">🏬 Departamento</div>', unsafe_allow_html=True)
        dept_sel = st.multiselect("", deptos, default=deptos)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- CARGO ---
    cargo_col = col_like(df, "cargo")
    cargos = sorted(df[cargo_col].dropna().unique().tolist()) if cargo_col else []
    with c3:
        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
        st.markdown('<div class="filter-label">👔 Cargo</div>', unsafe_allow_html=True)
        cargo_sel = st.multiselect("", cargos, default=cargos)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- TIPO CONTRATO ---
    tipo_col = col_like(df, "tipo_contrato")
    tipos = sorted(df[tipo_col].dropna().unique().tolist()) if tipo_col else []
    with c4:
        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
        st.markdown('<div class="filter-label">📑 Tipo de Contrato</div>', unsafe_allow_html=True)
        tipo_sel = st.multiselect("", tipos, default=tipos)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- ANO ---
    adm_col = col_like(df, "data de admissão")
    desl_col = col_like(df, "data de desligamento")

    anos_disp = sorted(
        pd.unique(
            df[adm_col].dropna().dt.year.tolist() +
            (df[desl_col].dropna().dt.year.tolist() if desl_col else [])
        )
    ) if adm_col else []
    with c5:
        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
        st.markdown('<div class="filter-label">📆 Ano de Referência</div>', unsafe_allow_html=True)
        ano_sel = st.multiselect("", anos_disp, default=anos_disp)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- MÊS ---
    meses = [
        "Janeiro","Fevereiro","Março","Abril","Maio","Junho",
        "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"
    ]
    with c6:
        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
        st.markdown('<div class="filter-label">🗓️ Mês</div>', unsafe_allow_html=True)
        mes_sel = st.multiselect("", meses, default=meses)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- BOTÃO DE APLICAÇÃO ---
    st.markdown("<br>", unsafe_allow_html=True)
    apply = st.button("🚀 Aplicar Filtros", type="primary")

# =========================================================
# APLICAÇÃO DOS FILTROS AO DATAFRAME
# =========================================================
if apply:
    df_filt = df.copy()

    if empresa_sel != "Todas" and empresa_col:
        df_filt = df_filt[df_filt[empresa_col] == empresa_sel]
    if dept_col and dept_sel:
        df_filt = df_filt[df_filt[dept_col].isin(dept_sel)]
    if cargo_col and cargo_sel:
        df_filt = df_filt[df_filt[cargo_col].isin(cargo_sel)]
    if tipo_col and tipo_sel:
        df_filt = df_filt[df_filt[tipo_col].isin(tipo_sel)]

    if adm_col:
        df_filt["ano_adm"] = pd.to_datetime(df_filt[adm_col], errors="coerce").dt.year
        df_filt["mes_adm"] = pd.to_datetime(df_filt[adm_col], errors="coerce").dt.month_name()
        if ano_sel:
            df_filt = df_filt[df_filt["ano_adm"].isin(ano_sel)]
        if mes_sel:
            df_filt = df_filt[df_filt["mes_adm"].isin(mes_sel)]

    st.success(f"📊 {len(df_filt):,} registros após aplicar filtros.")
else:
    df_filt = df.copy()

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
