import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# =========================================================
# CONFIG + ESTILO
# =========================================================
st.set_page_config(page_title="Dashboard de Turnover • Single Page", layout="wide")

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
  border: 1px solid rgba(0,255,204,0.10);
}
.nav-btn {
  display:inline-block;margin:8px 12px;padding:10px 18px;border-radius:12px;text-decoration:none;
  background:linear-gradient(135deg,#00c9a7,#007cf0);color:white;font-weight:600;
  box-shadow:0 0 12px rgba(0,255,204,0.2);
}
.nav-btn.active{outline:2px solid #00ffd5;}
</style>
""", unsafe_allow_html=True)

st.title("🚀 Dashboard de People Analytics — Single Page")
st.caption("Uma única página com navegação simulada: Visão Geral, Headcount, Turnover e Risco (TRI).")

# =========================================================
# HELPERS
# =========================================================
DATE_COLS = ["data de admissão", "data de desligamento", "ultima promoção", "ultimo mérito"]

def to_datetime_safe(df: pd.DataFrame, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df

def ensure_core_fields(colab: pd.DataFrame) -> pd.DataFrame:
    # ativo
    if "data de desligamento" in colab.columns:
        colab["ativo"] = colab["data de desligamento"].isna()
    else:
        colab["ativo"] = True
    # tempo de casa (meses)
    now = pd.Timestamp.now()
    if "data de admissão" in colab.columns:
        colab["tempo_casa"] = (now - colab["data de admissão"]).dt.days / 30
    else:
        colab["tempo_casa"] = np.nan
    return colab

def merge_last_performance(colab: pd.DataFrame, perf: pd.DataFrame) -> pd.DataFrame:
    if perf is None or perf.empty:
        return colab
    perf_df = perf.copy()
    if "data de encerramento do ciclo" in perf_df.columns:
        perf_df["data de encerramento do ciclo"] = pd.to_datetime(perf_df["data de encerramento do ciclo"], errors="coerce")
        last = perf_df.sort_values(["matricula", "data de encerramento do ciclo"]).groupby("matricula", as_index=False).tail(1)
    else:
        last = perf_df.drop_duplicates(subset=["matricula"], keep="last")
    if "avaliação" in last.columns and "matricula" in colab.columns:
        colab = colab.merge(last[["matricula", "avaliação"]], on="matricula", how="left")
    return colab

def show_sheet_preview(name: str, df: pd.DataFrame, expected_cols: list[str] | None = None):
    st.markdown(f"#### 📄 Aba `{name}`")
    if df is None or df.empty:
        st.warning("⚠️ Não encontrada ou vazia.")
        return
    st.write(f"Linhas: **{len(df)}** • Colunas: **{len(df.columns)}**")
    if expected_cols:
        missing = [c for c in expected_cols if c not in df.columns]
        if missing:
            st.warning(f"⚠️ Colunas esperadas ausentes: {', '.join(missing)}")
    st.dataframe(df.head(5), use_container_width=True)

def col_like(df, name):
    """Retorna a coluna do df que bate com o nome (case/espacos ignorados)."""
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
    minv = s.min(skipna=True)
    maxv = s.max(skipna=True)
    rng = (maxv - minv)
    if pd.isna(maxv) or rng == 0:
        return s * 0
    return (s - minv) / rng

# =========================================================
# UPLOAD + LEITURA
# =========================================================
uploaded = st.file_uploader(
    "📂 Carregue o Excel (.xlsx) com as abas **empresa**, **colaboradores** e **performance**",
    type=["xlsx"]
)

with st.expander("📘 Modelo de referência das abas"):
    st.markdown("""
- **empresa** → `nome empresa`, `cnpj`, `unidade`, `cidade`, `uf`  
- **colaboradores** → `matricula`, `nome`, `departamento`, `cargo`, `matricula do gestor`, `tipo_contrato`, `genero`, `data de admissão`, `data de desligamento`, `motivo de desligamento`, `ultima promoção`, `ultimo mérito`  
- **performance** → `matricula`, `avaliação`, `data de encerramento do ciclo`
""")

if not uploaded:
    st.info("⬆️ Envie o arquivo para iniciar.")
    st.stop()

def safe_read(sheet):
    try:
        return pd.read_excel(uploaded, sheet_name=sheet)
    except ValueError:
        st.warning(f"⚠️ Aba **{sheet}** não encontrada.")
        return pd.DataFrame()
    except Exception as e:
        st.warning(f"⚠️ Erro ao ler aba {sheet}: {e}")
        return pd.DataFrame()

empresa = safe_read("empresa")
colab = safe_read("colaboradores")
perf = safe_read("performance")

# Validação: ignora extras e avisa faltantes (não quebra)
expected_cols = {
    "empresa": ["nome empresa", "cnpj", "unidade", "cidade", "uf"],
    "colaboradores": [
        "matricula", "nome", "departamento", "cargo", "matricula do gestor",
        "tipo_contrato", "genero", "data de admissão", "data de desligamento",
        "motivo de desligamento", "ultima promoção", "ultimo mérito"
    ],
    "performance": ["matricula", "avaliação", "data de encerramento do ciclo"]
}

def clean_and_warn(df, expected, name):
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

empresa = clean_and_warn(empresa, expected_cols["empresa"], "empresa")
colab = clean_and_warn(colab, expected_cols["colaboradores"], "colaboradores")
perf = clean_and_warn(perf, expected_cols["performance"], "performance")

# Conversões e flags
colab = to_datetime_safe(colab, DATE_COLS)
colab = ensure_core_fields(colab)
colab = merge_last_performance(colab, perf)
df = colab.copy()

# Guardar em sessão (se quiser reutilizar noutros pontos)
st.session_state["empresa"] = empresa
st.session_state["colab"] = colab
st.session_state["perf"] = perf
st.session_state["df"] = df

st.success("✅ Dados carregados e normalizados.")

# Prévia das abas
st.markdown("### 🔎 Prévia das abas carregadas")
pcol = st.columns(3)
with pcol[0]: show_sheet_preview("empresa", empresa, expected_cols["empresa"])
with pcol[1]: show_sheet_preview("colaboradores", colab, expected_cols["colaboradores"])
with pcol[2]: show_sheet_preview("performance", perf, expected_cols["performance"])

st.markdown("---")

# =========================================================
# NAVEGAÇÃO NO MESMO ARQUIVO (VIEW STATE)
# =========================================================
if "view" not in st.session_state:
    st.session_state["view"] = "overview"

c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("📍 Visão Geral", use_container_width=True):
        st.session_state["view"] = "overview"
with c2:
    if st.button("👥 Headcount", use_container_width=True):
        st.session_state["view"] = "headcount"
with c3:
    if st.button("🔄 Turnover", use_container_width=True):
        st.session_state["view"] = "turnover"
with c4:
    if st.button("🔮 Risco (TRI)", use_container_width=True):
        st.session_state["view"] = "risk"

st.markdown("---")

# =========================================================
# 🔧 FILTROS LATERAIS (SIDEBAR)
# =========================================================
with st.sidebar:
    st.header("🔎 Filtros Globais")

    # Filtro: Empresa
    empresas_disp = empresa["nome empresa"].dropna().unique().tolist() if not empresa.empty else []
    empresa_sel = st.selectbox("Empresa", empresas_disp, index=0 if empresas_disp else None)

    # Filtro: Período
    data_min = pd.to_datetime(df["data de admissão"], errors="coerce").min()
    data_max = pd.to_datetime(df["data de desligamento"], errors="coerce").max() if df["data de desligamento"].notna().any() else datetime.now()
    periodo = st.date_input(
        "Período de Análise",
        value=(data_min.date() if not pd.isna(data_min) else datetime(2023,1,1).date(),
               data_max.date() if not pd.isna(data_max) else datetime.now().date())
    )

    # Filtro: Departamento
    dept_col = col_like(df, "departamento")
    deptos = sorted(df[dept_col].dropna().unique().tolist()) if dept_col else []
    dept_sel = st.multiselect("Departamentos", deptos, default=deptos)

    # Filtro: Tipo de Contrato
    tipo_col = col_like(df, "tipo_contrato")
    tipos = sorted(df[tipo_col].dropna().unique().tolist()) if tipo_col else []
    tipo_sel = st.multiselect("Tipo de Contrato", tipos, default=tipos)

# Aplicação dos filtros ao dataframe
df_filt = df.copy()
if empresa_sel and "nome empresa" in empresa.columns:
    df_filt = df_filt.merge(empresa[empresa["nome empresa"] == empresa_sel], how="inner")
if dept_col and dept_sel:
    df_filt = df_filt[df_filt[dept_col].isin(dept_sel)]
if tipo_col and tipo_sel:
    df_filt = df_filt[df_filt[tipo_col].isin(tipo_sel)]
if "data de admissão" in df_filt.columns:
    df_filt = df_filt[df_filt["data de admissão"].between(pd.to_datetime(periodo[0]), pd.to_datetime(periodo[1]), inclusive="both")]

# =========================================================
# 📊 PAINEL DE QUALIDADE DE DADOS (RECOLHÍVEL)
# =========================================================
with st.expander("🧩 Análise de Qualidade e Estrutura dos Dados", expanded=False):
    st.markdown("Use esta seção apenas para verificar se os dados foram carregados corretamente e se as colunas estão padronizadas.")
    c1, c2, c3 = st.columns(3)
    with c1: show_sheet_preview("empresa", empresa, expected_cols["empresa"])
    with c2: show_sheet_preview("colaboradores", colab, expected_cols["colaboradores"])
    with c3: show_sheet_preview("performance", perf, expected_cols["performance"])
    st.caption("⚙️ Feche esta seção para focar apenas nos KPIs e análises.")
  
# =========================================================
# VIEWS (renderizadas abaixo conforme seleção)
# =========================================================
def view_overview(df):
    st.subheader("📍 Visão Geral — KPIs Consolidados")

    ativos = df[df["ativo"] == True]
    total_ativos = len(ativos)

    # Headcount KPIs
    tipo_col = col_like(ativos, "tipo_contrato")
    pct_clt = round((ativos[tipo_col].astype(str).str.upper().eq("CLT")).mean()*100,1) if tipo_col else 0
    gen_col = col_like(ativos, "genero")
    pct_fem = round((ativos[gen_col].astype(str).str.lower().eq("feminino")).mean()*100,1) if gen_col else 0
    cargo_col = col_like(ativos, "cargo")
    pct_lider = round(ativos[cargo_col].astype(str).str.lower().str.contains("coord|gerente|diretor", na=False).mean()*100,1) if cargo_col else 0

    # Turnover médio (total/vol/invol)
    adm_col = col_like(df, "data de admissão")
    desl_col = col_like(df, "data de desligamento")
    motivo_col = col_like(df, "motivo de desligamento")
    tott = totv = toti = 0
    if adm_col and desl_col:
        dft = df.copy()
        dft[adm_col] = pd.to_datetime(dft[adm_col], errors="coerce")
        dft[desl_col] = pd.to_datetime(dft[desl_col], errors="coerce")
        data_min = dft[adm_col].min()
        data_max = dft[desl_col].max() if dft[desl_col].notna().any() else datetime.now()
        meses = pd.date_range(data_min, data_max, freq="MS")
        vals = []
        for mes in meses:
            ativos_mes = dft[(dft[adm_col] <= mes) & ((dft[desl_col].isna()) | (dft[desl_col] > mes))]
            deslig_mes = dft[(dft[desl_col].notna()) & (dft[desl_col].dt.to_period("M")==mes.to_period("M"))]
            a = len(ativos_mes)
            d = len(deslig_mes)
            dv = deslig_mes[motivo_col].astype(str).str.contains("Pedido", case=False, na=False).sum() if motivo_col else 0
            di = d - dv
            vals.append((
                (d/a)*100 if a>0 else 0,
                (dv/a)*100 if a>0 else 0,
                (di/a)*100 if a>0 else 0,
            ))
        if vals:
            arr = np.array(vals)
            tott, totv, toti = round(arr[:,0].mean(),1), round(arr[:,1].mean(),1), round(arr[:,2].mean(),1)

    # Tenure
    tenure_total = tenure_vol = tenure_invol = tenure_ativos = 0
    try:
        if adm_col and desl_col:
            dfd = df[df["ativo"]==False].copy()
            dfd["tenure_meses"] = (dfd[desl_col] - dfd[adm_col]).dt.days/30
            tenure_total = safe_mean(dfd["tenure_meses"])
            if motivo_col:
                tenure_vol = safe_mean(dfd.loc[dfd[motivo_col].astype(str).str.contains("Pedido", case=False, na=False), "tenure_meses"])
                tenure_invol = safe_mean(dfd.loc[~dfd[motivo_col].astype(str).str.contains("Pedido", case=False, na=False), "tenure_meses"])
        tenure_ativos = safe_mean(df.loc[df["ativo"], "tempo_casa"])
    except Exception:
        pass

    # TRI
    risco_medio = 0
    risco_alto = 0
    try:
        now = pd.Timestamp.now()
        df["meses_desde_promocao"] = (now - pd.to_datetime(df.get("ultima promoção"), errors="coerce")).dt.days/30
        df["meses_desde_merito"]  = (now - pd.to_datetime(df.get("ultimo mérito"), errors="coerce")).dt.days/30
        if "tamanho_equipe" not in df.columns:
            df["tamanho_equipe"] = 0
        if "matricula do gestor" in df.columns:
            try:
                gsize = df.groupby("matricula do gestor")["matricula"].count().rename("tamanho_calc")
                df = df.merge(gsize, left_on="matricula do gestor", right_index=True, how="left")
                df["tamanho_equipe"] = df["tamanho_calc"].fillna(df["tamanho_equipe"])
                df.drop(columns=["tamanho_calc"], inplace=True, errors="ignore")
            except Exception:
                pass
        perf_map = {"excepcional":10,"acima do esperado":7,"dentro do esperado":4,"abaixo do esperado":1}
        if "avaliação" in df.columns:
            df["score_perf_raw"] = df["avaliação"].astype(str).str.lower().map(perf_map).fillna(4)
        else:
            df["score_perf_raw"] = 4
        df["score_perf_inv"]   = 1 - norm_0_1(df["score_perf_raw"])
        df["score_tempo_promo"]= norm_0_1(df["meses_desde_promocao"])
        df["score_tempo_casa"] = norm_0_1(df["tempo_casa"])
        df["score_merito"]     = norm_0_1(df["meses_desde_merito"])
        df["score_tamanho_eq"] = norm_0_1(df["tamanho_equipe"])
        df["risco_turnover"] = (
            0.30*df["score_perf_inv"] + 0.25*df["score_tempo_promo"] +
            0.15*df["score_tempo_casa"] + 0.15*df["score_tamanho_eq"] +
            0.15*df["score_merito"]
        )*100
        risco_medio = safe_mean(df["risco_turnover"])
        risco_alto  = round((df["risco_turnover"]>60).mean()*100,1)
    except Exception:
        pass

    # KPIs
    st.markdown("### 👥 Headcount")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Ativos", total_ativos)
    c2.metric("% CLT", f"{pct_clt}%")
    c3.metric("% Feminino", f"{pct_fem}%")
    c4.metric("% Liderança", f"{pct_lider}%")

    st.markdown("### 🔄 Turnover (médio)")
    c5,c6,c7 = st.columns(3)
    c5.metric("Total (%)", f"{tott}")
    c6.metric("Voluntário (%)", f"{totv}")
    c7.metric("Involuntário (%)", f"{toti}")

    st.markdown("### ⏳ Tenure (Tempo Médio)")
    c8,c9,c10,c11 = st.columns(4)
    c8.metric("Total (m)", f"{tenure_total}")
    c9.metric("Voluntário (m)", f"{tenure_vol}")
    c10.metric("Involuntário (m)", f"{tenure_invol}")
    c11.metric("Ativos (m)", f"{tenure_ativos}")

    st.markdown("### 🔮 Risco de Saída (TRI)")
    c12,c13 = st.columns(2)
    c12.metric("Risco Médio", f"{risco_medio}")
    c13.metric("% em Risco Alto", f"{risco_alto}%")

    st.divider()
    st.markdown(f"""
    📊 *Resumo executivo:* Headcount **{total_ativos}**, turnover médio **{tott}%** 
    ({totv}% voluntário / {toti}% involuntário). Tenure médio **{tenure_total}m**. 
    TRI médio **{risco_medio}** com **{risco_alto}%** em alto risco.
    """)

def view_headcount(df):
    st.subheader("👥 Headcount — Estrutura e Distribuição")
    ativos = df[df["ativo"]==True]
    total_ativos = len(ativos)
    dept_col = col_like(ativos, "departamento")
    cargo_col = col_like(ativos, "cargo")
    tipo_col  = col_like(ativos, "tipo_contrato")
    gen_col   = col_like(ativos, "genero")

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Ativos", total_ativos)
    if tipo_col:
        pct_clt = round((ativos[tipo_col].astype(str).str.upper().eq("CLT")).mean()*100,1)
        c2.metric("% CLT", f"{pct_clt}%")
    if gen_col:
        pct_fem = round((ativos[gen_col].astype(str).str.lower().eq("feminino")).mean()*100,1)
        c3.metric("% Feminino", f"{pct_fem}%")
    if cargo_col:
        pct_lider = round(ativos[cargo_col].astype(str).str.lower().str.contains("coord|gerente|diretor", na=False).mean()*100,1)
        c4.metric("% Liderança", f"{pct_lider}%")

    st.divider()
    if dept_col:
        dist = ativos.groupby(dept_col)["matricula"].count().reset_index().rename(columns={"matricula":"Headcount"})
        fig = px.bar(dist, x=dept_col, y="Headcount", color="Headcount", color_continuous_scale="Tealgrn")
        fig.update_layout(template="plotly_dark", title="Headcount por Departamento", xaxis_title="Departamento", yaxis_title="Qtd")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("🧩 Coluna 'departamento' não encontrada para gráfico.")

def view_turnover(df):
    st.subheader("🔄 Turnover — Mensal, Voluntário e Involuntário + Tenure")

    adm_col = col_like(df, "data de admissão")
    desl_col = col_like(df, "data de desligamento")
    motivo_col = col_like(df, "motivo de desligamento")

    if not (adm_col and desl_col):
        st.warning("⚠️ É necessário ter colunas de admissão e desligamento para esta análise.")
        return

    dft = df.copy()
    dft[adm_col] = pd.to_datetime(dft[adm_col], errors="coerce")
    dft[desl_col] = pd.to_datetime(dft[desl_col], errors="coerce")

    data_min = dft[adm_col].min()
    data_max = dft[desl_col].max() if dft[desl_col].notna().any() else datetime.now()
    meses = pd.date_range(data_min, data_max, freq="MS")

    rows = []
    for mes in meses:
        ativos_mes = dft[(dft[adm_col] <= mes) & ((dft[desl_col].isna()) | (dft[desl_col] > mes))]
        deslig_mes = dft[(dft[desl_col].notna()) & (dft[desl_col].dt.to_period("M")==mes.to_period("M"))]
        a = len(ativos_mes)
        d = len(deslig_mes)
        dv = deslig_mes[motivo_col].astype(str).str.contains("Pedido", case=False, na=False).sum() if motivo_col else 0
        di = d - dv
        rows.append({
            "Mês": mes.strftime("%Y-%m"),
            "Ativos": a,
            "Desligados": d,
            "Voluntários": dv,
            "Involuntários": di,
            "Turnover Total (%)": (d/a)*100 if a>0 else 0,
            "Turnover Voluntário (%)": (dv/a)*100 if a>0 else 0,
            "Turnover Involuntário (%)": (di/a)*100 if a>0 else 0
        })
    turn = pd.DataFrame(rows)

    # KPIs
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Ativos Médios", int(turn["Ativos"].mean()))
    c2.metric("Desligamentos Médios", int(turn["Desligados"].mean()))
    c3.metric("Turnover Médio (%)", round(turn["Turnover Total (%)"].mean(),1))
    c4.metric("Vol/Inv (%)", f"{round(turn['Turnover Voluntário (%)'].mean(),1)} / {round(turn['Turnover Involuntário (%)'].mean(),1)}")

    st.divider()

    # Gráfico 1: evolução do turnover (total/vol/invol)
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

    # Tenure médio
    dfd = dft[dft["ativo"]==False].copy()
    dfd["tenure_meses"] = (dfd[desl_col] - dfd[adm_col]).dt.days/30
    tenure_total = safe_mean(dfd["tenure_meses"])
    tenure_vol = safe_mean(dfd.loc[dfd[motivo_col].astype(str).str.contains("Pedido", case=False, na=False) if motivo_col else [], "tenure_meses"]) if motivo_col else 0
    tenure_invol = safe_mean(dfd.loc[~dfd[motivo_col].astype(str).str.contains("Pedido", case=False, na=False) if motivo_col else [], "tenure_meses"]) if motivo_col else 0

    st.markdown("### ⏳ Tenure até o desligamento")
    c5,c6,c7 = st.columns(3)
    c5.metric("Tenure Total (m)", f"{tenure_total}")
    c6.metric("Voluntário (m)", f"{tenure_vol}")
    c7.metric("Involuntário (m)", f"{tenure_invol}")

def view_risk(df):
    st.subheader("🔮 Risco de Turnover (TRI) — Índice Composto")

    now = pd.Timestamp.now()
    # Datas seguras
    df["meses_desde_promocao"] = (now - pd.to_datetime(df.get("ultima promoção"), errors="coerce")).dt.days/30 if "ultima promoção" in df.columns else 0
    df["meses_desde_merito"]  = (now - pd.to_datetime(df.get("ultimo mérito"), errors="coerce")).dt.days/30 if "ultimo mérito" in df.columns else 0
    if "tamanho_equipe" not in df.columns:
        df["tamanho_equipe"] = 0
    # Tamanho equipe se houver gestor
    if "matricula do gestor" in df.columns:
        try:
            gsize = df.groupby("matricula do gestor")["matricula"].count().rename("tamanho_calc")
            df = df.merge(gsize, left_on="matricula do gestor", right_index=True, how="left")
            df["tamanho_equipe"] = df["tamanho_calc"].fillna(df["tamanho_equipe"])
            df.drop(columns=["tamanho_calc"], inplace=True, errors="ignore")
        except Exception:
            st.warning("⚠️ Não foi possível calcular o tamanho das equipes; usando 0 como padrão.")

    # Performance
    perf_map = {"excepcional":10,"acima do esperado":7,"dentro do esperado":4,"abaixo do esperado":1}
    if "avaliação" in df.columns:
        df["score_perf_raw"] = df["avaliação"].astype(str).str.lower().map(perf_map).fillna(4)
    else:
        df["score_perf_raw"] = 4

    # Scores
    df["score_perf_inv"]   = 1 - norm_0_1(df["score_perf_raw"])
    df["score_tempo_promo"]= norm_0_1(df["meses_desde_promocao"])
    df["score_tempo_casa"] = norm_0_1(df.get("tempo_casa", 0))
    df["score_merito"]     = norm_0_1(df["meses_desde_merito"])
    df["score_tamanho_eq"] = norm_0_1(df["tamanho_equipe"])

    # TRI
    df["risco_turnover"] = (
        0.30*df["score_perf_inv"] + 0.25*df["score_tempo_promo"] +
        0.15*df["score_tempo_casa"] + 0.15*df["score_tamanho_eq"] +
        0.15*df["score_merito"]
    )*100
    df["risco_turnover"] = df["risco_turnover"].clip(0,100)

    avg_risk = safe_mean(df["risco_turnover"])
    pct_high = round((df["risco_turnover"] > 60).mean()*100, 1)

    c1,c2 = st.columns(2)
    c1.metric("⚠️ Risco Médio (TRI)", avg_risk)
    c2.metric("🚨 % Risco Alto", f"{pct_high}%")

    # Curva por tempo sem promoção
    bins = [0,3,6,12,24,np.inf]
    labels = ["0-3m","3-6m","6-12m","12-24m","+24m"]
    df["faixa_tempo_sem_promo"] = pd.cut(pd.to_numeric(df["meses_desde_promocao"], errors="coerce").fillna(0), bins=bins, labels=labels)
    risco_por_faixa = df.groupby("faixa_tempo_sem_promo")["risco_turnover"].mean().reset_index()

    fig = px.line(risco_por_faixa, x="faixa_tempo_sem_promo", y="risco_turnover", markers=True, color_discrete_sequence=["#00FFFF"])
    fig.update_layout(template="plotly_dark", title="📈 Risco Médio por Tempo sem Promoção", xaxis_title="Faixa", yaxis_title="Risco Médio (0-100)")
    st.plotly_chart(fig, use_container_width=True)

# Render da view selecionada
if st.session_state["view"] == "overview":
    view_overview(df.copy())
elif st.session_state["view"] == "headcount":
    view_headcount(df.copy())
elif st.session_state["view"] == "turnover":
    view_turnover(df.copy())
elif st.session_state["view"] == "risk":
    view_risk(df.copy())
else:
    view_overview(df.copy())
