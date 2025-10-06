import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# =========================================================
# CONFIGURAÇÃO GERAL E ESTILO
# =========================================================
st.set_page_config(page_title="Dashboard de Turnover • Main", layout="wide")

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
</style>
""", unsafe_allow_html=True)

st.title("🚀 Dashboard de People Analytics — Hub Principal")
st.caption("Carrega, valida e disponibiliza os dados-base para as páginas do dashboard.")

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
    # Flag de ativo
    if "data de desligamento" in colab.columns:
        colab["ativo"] = colab["data de desligamento"].isna()
    else:
        colab["ativo"] = True

    # Tempo de casa
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
    if "avaliação" in last.columns:
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

def nav_links():
    st.markdown("### 🧭 Acessar páginas de análise")
    cols = st.columns(3)

    if hasattr(st, "page_link"):
        with cols[0]:
            st.page_link("pages/1_Visão_Geral.py", label="📍 Visão Geral")
            st.page_link("pages/2_Headcount.py", label="👥 Headcount")
        with cols[1]:
            st.page_link("pages/3_Turnover.py", label="🔄 Turnover")
            st.page_link("pages/4_Risco_TRI.py", label="🔮 Risco (TRI)")
        with cols[2]:
            st.info("💡 As análises com IA estarão dentro das páginas.")
    else:
        st.write("⚠️ Sua versão do Streamlit é antiga — use o menu lateral para navegar entre as páginas.")

# =========================================================
# UPLOAD & LEITURA
# =========================================================
uploaded = st.file_uploader(
    "📂 Carregue o arquivo Excel (.xlsx) com as abas **empresa**, **colaboradores** e **performance**",
    type=["xlsx"]
)

with st.expander("📘 Estrutura esperada das abas (modelo de referência)"):
    st.markdown("""
- **empresa** → `nome empresa`, `cnpj`, `unidade`, `cidade`, `uf`  
- **colaboradores** → `matricula`, `nome`, `departamento`, `cargo`, `matricula do gestor`, `tipo_contrato`, `genero`, `data de admissão`, `data de desligamento`, `motivo de desligamento`, `ultima promoção`, `ultimo mérito`  
- **performance** → `matricula`, `avaliação`, `data de encerramento do ciclo`
""")

if not uploaded:
    st.info("⬆️ Envie o arquivo para iniciar.")
    st.stop()

def safe_read(sheet_name):
    try:
        df = pd.read_excel(uploaded, sheet_name=sheet_name)
        return df
    except ValueError:
        st.warning(f"⚠️ Aba **{sheet_name}** não encontrada.")
        return pd.DataFrame()
    except Exception as e:
        st.warning(f"⚠️ Erro ao ler aba {sheet_name}: {e}")
        return pd.DataFrame()

empresa = safe_read("empresa")
colab = safe_read("colaboradores")
perf = safe_read("performance")

# =========================================================
# VALIDAÇÃO E LIMPEZA DE CAMPOS
# =========================================================
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

# =========================================================
# CONVERSÕES E CAMPOS ESSENCIAIS
# =========================================================
colab = to_datetime_safe(colab, DATE_COLS)
colab = ensure_core_fields(colab)
colab = merge_last_performance(colab, perf)

# Guardar em sessão (para uso nas páginas)
st.session_state["empresa"] = empresa
st.session_state["colab"] = colab
st.session_state["perf"] = perf
st.session_state["df"] = colab.copy()

st.success("✅ Dados carregados e normalizados com sucesso!")

# =========================================================
# PRÉVIA / EXTRAÇÃO DOS DADOS
# =========================================================
st.markdown("### 🔎 Prévia das abas carregadas")
cols_prev = st.columns(3)
with cols_prev[0]:
    show_sheet_preview("empresa", empresa, expected_cols["empresa"])
with cols_prev[1]:
    show_sheet_preview("colaboradores", colab, expected_cols["colaboradores"])
with cols_prev[2]:
    show_sheet_preview("performance", perf, expected_cols["performance"])

# =========================================================
# VALIDAÇÕES RÁPIDAS
# =========================================================
with st.expander("🧪 Validações rápidas"):
    checks = [
        ("Aba empresa", not empresa.empty),
        ("Aba colaboradores", not colab.empty),
        ("Campo ativo criado", "ativo" in colab.columns),
        ("Campo tempo_casa criado", "tempo_casa" in colab.columns),
        ("Aba performance (opcional)", not perf.empty),
    ]
    ok = all(flag for _, flag in checks)
    for label, flag in checks:
        st.write(("✅ " if flag else "⚠️ ") + label)
    if not ok:
        st.warning("Alguns itens estão faltando — o dashboard funcionará parcialmente.")

st.markdown("---")
nav_links()
