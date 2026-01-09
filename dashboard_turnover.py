import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Importar módulos utilitários
from utils import (
    load_and_prepare,
    validate_calculations,
    col_like,
    calculate_turnover,
    calculate_turnover_by_period,
    calculate_turnover_history,
    calculate_tenure,
    calculate_headcount,
    calculate_basic_kpis,
    calculate_contract_types,
    calculate_monthly_dismissals,
    safe_mean,
    norm_0_1
)
from utils.subscription import (
    get_user_subscription,
    set_user_subscription,
    SubscriptionLevel,
    show_subscription_info,
    has_feature
)
from utils.ai_features import (
    generate_ai_insights,
    generate_ai_presentation,
    generate_predictive_analysis
)

# =========================================================
# CONFIGURAÇÃO E ESTILO
# =========================================================
st.set_page_config(page_title="Dashboard Turnover • People Analytics", layout="wide")

st.markdown("""
<style>
html, body, [class*="css"] { background-color: #0e1117 !important; color: #E6E6E6 !important;
  font-family: "Inter", system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, "Helvetica Neue"; }
div[data-testid="stMetric"] { background: linear-gradient(135deg, #1a1f2b 0%, #151922 100%);
  border-radius: 18px; padding: 14px 16px; box-shadow: 0 0 18px rgba(0,255,204,0.12);
  border: 1px solid rgba(0,255,204,0.10); }
</style>
""", unsafe_allow_html=True)

st.title("🚀 Dashboard de People Analytics — Turnover")
st.caption("Plataforma para análise de indicadores de RH com suporte a múltiplas bases de dados e análises avançadas de IA.")

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

# =========================================================
# 🧩 UPLOAD, LEITURA E ANÁLISE DE QUALIDADE DOS DADOS
# =========================================================
# Mostrar informações de assinatura no sidebar
with st.sidebar:
    show_subscription_info()
    st.divider()

uploaded = st.file_uploader(
    "📂 Carregue o Excel (.xlsx) com abas 'empresa', 'colaboradores' e 'performance'",
    type=["xlsx"]
)
if not uploaded:
    st.info("⬆️ Envie o arquivo para começar a análise.")
    st.stop()

# Carregar dados usando módulo utilitário
empresa, colab, perf, expected_cols = load_and_prepare(uploaded)
df = colab.copy()

# Validação de dados
with st.expander("🧩 Análise de Qualidade e Validação dos Dados", expanded=False):
    st.markdown(
        "Visualize aqui como o arquivo foi carregado e validado. "
        "Essa etapa ocorre automaticamente antes de calcular os indicadores."
    )
    
    # Executar validação
    validation_report = validate_calculations(df)
    
    if validation_report["erros"]:
        st.error("❌ **Erros encontrados:**")
        for erro in validation_report["erros"]:
            st.error(f"- {erro}")
    
    if validation_report["avisos"]:
        st.warning("⚠️ **Avisos:**")
        for aviso in validation_report["avisos"]:
            st.warning(f"- {aviso}")
    
    if not validation_report["erros"] and not validation_report["avisos"]:
        st.success("✅ Dados validados com sucesso!")
    
    # Estatísticas
    if validation_report["estatisticas"]:
        st.markdown("### 📊 Estatísticas Básicas")
        stats = validation_report["estatisticas"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Registros", stats.get("total_registros", 0))
        if stats.get("ativos") is not None:
            c2.metric("Ativos", stats["ativos"])
        if stats.get("desligados") is not None:
            c3.metric("Desligados", stats["desligados"])
    
    st.divider()
    st.markdown("### Estrutura das Abas")
    c1, c2, c3 = st.columns(3)
    with c1: show_sheet_preview("empresa", empresa, expected_cols["empresa"])
    with c2: show_sheet_preview("colaboradores", colab, expected_cols["colaboradores"])
    with c3: show_sheet_preview("performance", perf, expected_cols["performance"])
    
    st.divider()
    st.caption("✅ Dados processados com sucesso. Feche esta seção para visualizar as análises abaixo.")



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

    # Armazenar filtros selecionados para usar nas views
    ano_filtro = int(ano_sel) if ano_sel != "Todos" else None
    mes_filtro = meses_inv[mes_sel] if mes_sel != "Todos" else None
    
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
    elif ano_sel != "Todos":
        # Só ano selecionado
        st.info(f"📅 Ano {ano_sel} — Média mensal do ano")
    elif mes_sel != "Todos":
        # Só mês selecionado
        st.info(f"📅 Mês: {mes_sel} — Média mensal de todos os anos")
    else:
        df_final["desligado_no_mes"] = False
        df_final["ativo"] = df_final["data de desligamento"].isna() if "data de desligamento" in df_final.columns else True
        st.info("📊 Período: Todos — Média mensal de todo o período histórico")

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
# NAVEGAÇÃO (PSEUDO-ABAS)
# =========================================================
if "view" not in st.session_state:
    st.session_state["view"] = "overview"

# Botões de navegação
num_cols = 5 if has_feature("Premium") else 4
cols = st.columns(num_cols)

if cols[0].button("📍 Visão Geral", use_container_width=True): 
    st.session_state["view"] = "overview"
if cols[1].button("👥 Headcount", use_container_width=True): 
    st.session_state["view"] = "headcount"
if cols[2].button("🔄 Turnover", use_container_width=True): 
    st.session_state["view"] = "turnover"
if has_feature("Premium"):
    if cols[3].button("🔮 Risco (TRI)", use_container_width=True): 
        st.session_state["view"] = "risk"
    if cols[4].button("🤖 IA & Apresentações", use_container_width=True): 
        st.session_state["view"] = "ai"
else:
    if cols[3].button("🔮 Risco (TRI) 🔒", use_container_width=True, disabled=True): 
        pass

st.markdown("---")

# =========================================================
# VIEWS
# =========================================================
def view_overview(dfv, ano_filtro=None, mes_filtro=None, df_total=None):
    """
    Visão geral com análise do período filtrado e comparação com total.
    
    Args:
        dfv: DataFrame filtrado
        ano_filtro: Ano selecionado (None = todos)
        mes_filtro: Mês selecionado (None = todos)
        df_total: DataFrame completo para comparação (None = usar dfv)
    """
    st.subheader("📍 Visão Geral — KPIs Consolidados")
    
    if df_total is None:
        df_total = dfv
    
    # Determinar período selecionado
    periodo_txt = "Todo o período"
    if ano_filtro is not None and mes_filtro is not None:
        meses_map = {
            1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
            7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
        }
        periodo_txt = f"{meses_map[mes_filtro]}/{ano_filtro}"
    elif ano_filtro is not None:
        periodo_txt = f"Ano {ano_filtro} (média mensal)"
    elif mes_filtro is not None:
        meses_map = {
            1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
            7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
        }
        periodo_txt = f"Mês {meses_map[mes_filtro]} (média de todos os anos)"
    
    st.markdown(f"**Período selecionado:** {periodo_txt}")
    
    # ============================================================
    # 1. HEADCOUNT ATUAL
    # ============================================================
    st.markdown("### 👥 Headcount Atual")
    basic_kpis = calculate_basic_kpis(dfv)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Ativos", basic_kpis["total_ativos"])
    c2.metric("Feminino", f"{basic_kpis['qtd_feminino']} ({basic_kpis['pct_feminino']}%)")
    c3.metric("Masculino", f"{basic_kpis['qtd_masculino']} ({basic_kpis['pct_masculino']}%)")
    c4.metric("Liderança", f"{basic_kpis['qtd_lideranca']} ({basic_kpis['pct_lideranca']}%)")

    st.divider()

    # ============================================================
    # 2. TIPOS DE CONTRATO (TODOS COM % E QUANTIDADE)
    # ============================================================
    st.markdown("### 📋 Tipos de Contrato")
    contract_types = calculate_contract_types(dfv)
    
    if not contract_types.empty:
        # Mostrar métricas principais
        cols = st.columns(min(len(contract_types), 4))
        for idx, row in contract_types.head(4).iterrows():
            with cols[idx]:
                st.metric(
                    row["Tipo"] if pd.notna(row["Tipo"]) else "N/A",
                    f"{int(row['Quantidade'])} ({row['Percentual (%)']}%)"
                )
        
        # Mostrar tabela completa
        with st.expander("📊 Ver todos os tipos de contrato"):
            st.dataframe(contract_types, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ Não há dados de tipo de contrato disponíveis.")
    
    st.divider()

    # ============================================================
    # 3. TURNOVER - PERÍODO SELECIONADO vs TOTAL
    # ============================================================
    st.markdown("### 🔄 Turnover")
    st.caption("Calculado com base no headcount do início de cada mês")
    
    # Calcular turnover do período selecionado
    # Se só mês selecionado, usar df_total para pegar todos os anos, senão usar dfv
    df_para_calculo = df_total if (mes_filtro is not None and ano_filtro is None) else dfv
    turnover_periodo = calculate_turnover_by_period(df_para_calculo, ano_filtro, mes_filtro)
    
    # Calcular turnover total (sem filtros) para comparação (sempre usar df_total)
    turnover_total_geral = calculate_turnover_by_period(df_total, None, None)
    
    # Mostrar período selecionado
    st.markdown(f"#### 📅 Período Selecionado: {periodo_txt}")
    
    meses_consid = turnover_periodo.get("meses_considerados", 0)
    if meses_consid > 0:
        st.caption(f"Meses considerados: {meses_consid}")
    
    c7, c8, c9, c10 = st.columns(4)
    ativos_per = turnover_periodo.get("ativos", 0) or 0
    deslig_per = turnover_periodo.get("desligados", 0) or 0
    vol_per = turnover_periodo.get("voluntarios", 0) or 0
    inv_per = turnover_periodo.get("involuntarios", 0) or 0
    
    c7.metric("Headcount Médio", int(ativos_per) if isinstance(ativos_per, (int, float)) else int(float(ativos_per)))
    c8.metric("Desligados/mês (média)", f"{deslig_per:.1f}" if isinstance(deslig_per, float) else int(deslig_per))
    c9.metric("Voluntários/mês (média)", f"{vol_per:.1f}" if isinstance(vol_per, float) else int(vol_per))
    c10.metric("Involuntários/mês (média)", f"{inv_per:.1f}" if isinstance(inv_per, float) else int(inv_per))
    
    c11, c12, c13 = st.columns(3)
    c11.metric("Turnover Total (%)", f"{turnover_periodo.get('turnover_total', 0.0):.1f}%")
    c12.metric("Turnover Voluntário (%)", f"{turnover_periodo.get('turnover_vol', 0.0):.1f}%")
    c13.metric("Turnover Involuntário (%)", f"{turnover_periodo.get('turnover_inv', 0.0):.1f}%")
    
    # Comparação com total (sempre mostrar, exceto quando não há filtro de período)
    # A comparação mostra o total vs o período selecionado
    if ano_filtro is not None or mes_filtro is not None:
        st.divider()
        st.markdown("#### 📊 Comparação: Total (Todo o Período Histórico)")
        
        # Calcular variação (diferença entre período selecionado e total)
        var_total = turnover_periodo.get('turnover_total', 0) - turnover_total_geral.get('turnover_total', 0)
        var_vol = turnover_periodo.get('turnover_vol', 0) - turnover_total_geral.get('turnover_vol', 0)
        var_inv = turnover_periodo.get('turnover_inv', 0) - turnover_total_geral.get('turnover_inv', 0)
        
        # Métricas do total com variação (delta mostra diferença do período selecionado)
        c14, c15, c16 = st.columns(3)
        var_total_val = var_total
        var_vol_val = var_vol
        var_inv_val = var_inv
        
        c14.metric(
            "Turnover Total (%)",
            f"{turnover_total_geral.get('turnover_total', 0.0):.1f}%",
            delta=f"{var_total_val:+.1f}%"
        )
        c15.metric(
            "Turnover Voluntário (%)",
            f"{turnover_total_geral.get('turnover_vol', 0.0):.1f}%",
            delta=f"{var_vol_val:+.1f}%"
        )
        c16.metric(
            "Turnover Involuntário (%)",
            f"{turnover_total_geral.get('turnover_inv', 0.0):.1f}%",
            delta=f"{var_inv_val:+.1f}%"
        )
        st.caption(f"*Valores mostram o total histórico. Delta mostra diferença em relação ao período selecionado ({periodo_txt}).*")
        
        ativos_total = turnover_total_geral.get("ativos", 0) or 0
        deslig_total = turnover_total_geral.get("desligados", 0) or 0
        vol_total = turnover_total_geral.get("voluntarios", 0) or 0
        inv_total = turnover_total_geral.get("involuntarios", 0) or 0
        
        c17, c18, c19, c20 = st.columns(4)
        var_ativos = ativos_per - ativos_total
        var_deslig = deslig_per - deslig_total
        var_vol_qtd = vol_per - vol_total
        var_inv_qtd = inv_per - inv_total
        
        c17.metric(
            "Headcount Médio (Total)",
            int(ativos_total),
            delta=f"{var_ativos:+.0f}"
        )
        c18.metric(
            "Desligados/mês (Total)",
            f"{deslig_total:.1f}",
            delta=f"{var_deslig:+.1f}"
        )
        c19.metric(
            "Voluntários/mês (Total)",
            f"{vol_total:.1f}",
            delta=f"{var_vol_qtd:+.1f}"
        )
        c20.metric(
            "Involuntários/mês (Total)",
            f"{inv_total:.1f}",
            delta=f"{var_inv_qtd:+.1f}"
        )
    
    # Aviso se não houver dados
    if ativos_per == 0 and deslig_per == 0:
        st.info("ℹ️ Não há dados históricos suficientes para calcular turnover no período selecionado.")

    st.divider()

    # ============================================================
    # 4. DESLIGAMENTOS MÉDIOS POR MÊS
    # ============================================================
    st.markdown("### 📊 Desligamentos por Mês")
    dismissals_data = calculate_monthly_dismissals(dfv)
    
    c21, c22, c23 = st.columns(3)
    c21.metric("Desligamentos Médios/mês", f"{dismissals_data['desligamentos_medio_mes']:.1f}")
    c22.metric("Total de Desligados", dismissals_data["total_desligados"])
    c23.metric("Meses com Dados", dismissals_data["meses_com_dados"])
    
    st.divider()

    # ============================================================
    # 5. TENURE MÉDIO
    # ============================================================
    st.markdown("### ⏳ Tenure (Tempo Médio até Desligamento)")
    tenure_data = calculate_tenure(dfv)
    
    c24, c25, c26 = st.columns(3)
    c24.metric("Tenure Médio Total (meses)", f"{tenure_data['tenure_total']:.1f}")
    c25.metric("Tenure Voluntário (meses)", f"{tenure_data['tenure_vol']:.1f}")
    c26.metric("Tenure Involuntário (meses)", f"{tenure_data['tenure_inv']:.1f}")
    
    st.divider()

    # ============================================================
    # 6. INSIGHTS DE IA (Premium)
    # ============================================================
    if has_feature("Premium"):
        st.markdown("### 🤖 Insights de IA (Premium)")
        
        with st.spinner("Gerando insights de IA..."):
            insights = generate_ai_insights(dfv)
        
        if insights["alertas"]:
            st.warning("🚨 **Alertas Críticos:**")
            for alerta in insights["alertas"]:
                st.warning(f"- {alerta}")
        
        if insights["recomendacoes"]:
            st.info("💡 **Recomendações:**")
            for rec in insights["recomendacoes"]:
                st.info(f"- {rec}")
    else:
        st.caption("💡 Upgrade para Premium para ver insights e recomendações de IA")




# =========================================================
# Headcount
# =========================================================

def view_headcount(dfv):
    st.subheader("👥 Headcount — Estrutura e Evolução")

    # Usar módulo de cálculo
    dist = calculate_headcount(dfv, "departamento")
    
    if dist.empty:
        st.info("Sem dados suficientes para calcular headcount.")
        return
    
    dept_col = "departamento"
    
    fig = px.bar(
        dist,
        x=dept_col,
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

    # Tabela com percentuais
    st.dataframe(dist, use_container_width=True)


# =========================================================
# TURNOVER
# =========================================================
def view_turnover(dfv, ano_filtro=None, mes_filtro=None, df_total=None):
    """
    View de turnover com análise do período filtrado e histórico.
    
    Args:
        dfv: DataFrame filtrado
        ano_filtro: Ano selecionado (None = todos)
        mes_filtro: Mês selecionado (None = todos)
        df_total: DataFrame completo para histórico
    """
    st.subheader("🔄 Turnover — Evolução, Indicadores e Tenure")

    adm_c = col_like(dfv, "data de admissão")
    desl_c = col_like(dfv, "data de desligamento")

    if not (adm_c and desl_c):
        st.warning("⚠️ Faltam colunas de admissão/desligamento para esta seção.")
        return
    
    if df_total is None:
        df_total = dfv

    # ============================================================
    # 🔹 Análise do Período Selecionado
    # ============================================================
    # Determinar período
    periodo_txt = "Todo o período"
    meses_map = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
        7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    
    if ano_filtro is not None and mes_filtro is not None:
        periodo_txt = f"{meses_map[mes_filtro]}/{ano_filtro}"
    elif ano_filtro is not None:
        periodo_txt = f"Ano {ano_filtro} (média mensal)"
    elif mes_filtro is not None:
        periodo_txt = f"Mês {meses_map[mes_filtro]} (média de todos os anos)"
    
    # Se só mês selecionado, usar df_total para pegar todos os anos
    df_para_calculo = df_total if (mes_filtro is not None and ano_filtro is None) else dfv
    turnover_data = calculate_turnover_by_period(df_para_calculo, ano_filtro, mes_filtro)
    
    st.markdown(f"### 📅 Indicadores do Período Selecionado: {periodo_txt}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Headcount Médio", turnover_data.get("ativos", 0))
    c2.metric("Desligados (média)", f"{turnover_data.get('desligados', 0):.1f}")
    c3.metric("Turnover Total (%)", f"{turnover_data.get('turnover_total', 0.0):.1f}%")
    c4.metric(
        "Vol / Inv (%)",
        f"{turnover_data.get('turnover_vol', 0.0):.1f} / {turnover_data.get('turnover_inv', 0.0):.1f}"
    )
    
    meses_consid = turnover_data.get("meses_considerados", 0)
    if meses_consid > 0:
        st.caption(f"Meses considerados: {meses_consid}")

    # ============================================================
    # 🔸 Construção do histórico completo (usando módulo)
    # ============================================================
    # Usar df_total para histórico completo se houver filtro
    turn = calculate_turnover_history(df_total if (ano_filtro is not None or mes_filtro is not None) else dfv)

    if turn.empty:
        st.warning("Sem dados suficientes para gerar histórico.")
        return

    # ============================================================
    # 🔹 KPIs Médios (histórico)
    # ============================================================
    st.markdown("### 📊 Indicadores Históricos (Média Geral)")
    st.caption("Baseado no headcount do início de cada mês")
    c1, c2, c3, c4 = st.columns(4)
    
    # Verificar qual coluna existe (pode ser "Headcount (início)" ou "Ativos")
    hc_col = "Headcount (início)" if "Headcount (início)" in turn.columns else "Ativos"
    c1.metric("Headcount Médio (início)", int(turn[hc_col].mean()))
    c2.metric("Desligamentos Médios", int(turn["Desligados"].mean()))
    c3.metric("Turnover Médio (%)", round(turn["Turnover Total (%)"].mean(), 1))
    c4.metric(
        "Vol / Inv (%)",
        f"{round(turn['Turnover Voluntário (%)'].mean(), 1)} / {round(turn['Turnover Involuntário (%)'].mean(), 1)}"
    )

    st.divider()

    # ============================================================
    # 📈 Gráfico 1: Evolução do Turnover
    # ============================================================
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=turn["Mês"], y=turn["Turnover Total (%)"],
        mode="lines+markers", name="Total",
        line=dict(color="#00FFFF", width=3)
    ))
    fig1.add_trace(go.Scatter(
        x=turn["Mês"], y=turn["Turnover Voluntário (%)"],
        mode="lines+markers", name="Voluntário",
        line=dict(color="#FFD700", dash="dash")
    ))
    fig1.add_trace(go.Scatter(
        x=turn["Mês"], y=turn["Turnover Involuntário (%)"],
        mode="lines+markers", name="Involuntário",
        line=dict(color="#FF4500", dash="dot")
    ))
    fig1.update_layout(
        template="plotly_dark",
        title="📆 Evolução Mensal do Turnover (%)",
        xaxis_title="Mês",
        yaxis_title="Turnover (%)",
        hovermode="x unified"
    )
    st.plotly_chart(fig1, use_container_width=True)

    # ============================================================
    # 📊 Gráfico 2: Headcount x Desligados
    # ============================================================
    fig2 = go.Figure()
    hc_col = "Headcount (início)" if "Headcount (início)" in turn.columns else "Ativos"
    fig2.add_trace(go.Bar(x=turn["Mês"], y=turn[hc_col], name="Headcount (início)", marker_color="rgba(0,255,204,0.4)"))
    fig2.add_trace(go.Bar(x=turn["Mês"], y=turn["Desligados"], name="Desligados", marker_color="rgba(255,80,80,0.7)"))
    fig2.update_layout(
        barmode="overlay",
        template="plotly_dark",
        title="📊 Headcount (início do mês) x Desligados por Mês",
        xaxis_title="Mês",
        yaxis_title="Quantidade"
    )
    st.plotly_chart(fig2, use_container_width=True)

    # ============================================================
    # ⏳ Tenure até o desligamento (usando módulo)
    # ============================================================
    tenure_data = calculate_tenure(dfv)

    st.markdown("### ⏳ Tempo Médio até o Desligamento (Tenure)")
    c5, c6, c7 = st.columns(3)
    c5.metric("Total (m)", f"{tenure_data['tenure_total']}")
    c6.metric("Voluntário (m)", f"{tenure_data['tenure_vol']}")
    c7.metric("Involuntário (m)", f"{tenure_data['tenure_inv']}")
    
    # ============================================================
    # Análise Preditiva (Premium)
    # ============================================================
    if has_feature("Premium"):
        st.divider()
        st.markdown("### 🔮 Análise Preditiva (Premium)")
        
        with st.spinner("Gerando análise preditiva..."):
            pred = generate_predictive_analysis(dfv)
        
        if "mensagem" in pred:
            st.info(pred["mensagem"])
        
        if "previsao_3_meses" in pred:
            st.markdown("**Previsão de Turnover para os próximos 3 meses:**")
            c8, c9, c10 = st.columns(3)
            for i, prev in enumerate(pred["previsao_3_meses"], 1):
                with [c8, c9, c10][i-1]:
                    st.metric(f"Mês {i}", f"{prev}%")
    else:
        st.caption("💡 Upgrade para Premium para ver análise preditiva de turnover")


# =========================================================
# RISK
# =========================================================

def view_risk(dfv):
    if not has_feature("Premium"):
        st.warning("🔒 Esta funcionalidade requer assinatura Premium.")
        st.info("💡 Entre em contato para fazer upgrade e acessar análises avançadas de IA, "
               "apresentações automáticas e relatórios personalizados.")
        return
    
    st.subheader("🔮 Risco de Turnover (TRI) — Modelo Interativo e Explicativo")

    # ============================================
    # CONFIGURAÇÃO DE VARIÁVEIS BASE
    # ============================================
    now = pd.Timestamp.now()
    dfv["meses_desde_promocao"] = (
        now - pd.to_datetime(dfv.get("ultima promoção"), errors="coerce")
    ).dt.days / 30 if "ultima promoção" in dfv.columns else 0
    dfv["meses_desde_merito"] = (
        now - pd.to_datetime(dfv.get("ultimo mérito"), errors="coerce")
    ).dt.days / 30 if "ultimo mérito" in dfv.columns else 0

    # Tamanho da equipe (auto cálculo)
    if "matricula do gestor" in dfv.columns:
        gsize = dfv.groupby("matricula do gestor")["matricula"].count().rename("tamanho_equipe_calc")
        dfv = dfv.merge(gsize, left_on="matricula do gestor", right_index=True, how="left")
        dfv["tamanho_equipe"] = dfv["tamanho_equipe_calc"].fillna(0)
    else:
        dfv["tamanho_equipe"] = 0

    # Performance
    perf_map = {"excepcional":10, "acima do esperado":7, "dentro do esperado":4, "abaixo do esperado":1}
    dfv["score_perf_raw"] = dfv.get("avaliação", "").astype(str).str.lower().map(perf_map).fillna(4)

    # Normalização
    dfv["score_perf_inv"] = 1 - norm_0_1(dfv["score_perf_raw"])
    dfv["score_tempo_promo"] = norm_0_1(dfv["meses_desde_promocao"])
    dfv["score_tempo_casa"] = norm_0_1(dfv.get("tempo_casa", 0))
    dfv["score_merito"] = norm_0_1(dfv["meses_desde_merito"])
    dfv["score_tamanho_eq"] = norm_0_1(dfv["tamanho_equipe"])

    # ============================================
    # CONTROLES INTERATIVOS DE PESO
    # ============================================
    st.markdown("### ⚙️ Ajuste dos Pesos das Variáveis")
    with st.expander("Personalizar pesos do modelo (soma 100%)", expanded=False):
        col1, col2, col3, col4, col5 = st.columns(5)
        w_perf = col1.slider("Performance", 0, 100, 30)
        w_promo = col2.slider("Tempo s/ Promoção", 0, 100, 25)
        w_casa = col3.slider("Tempo de Casa", 0, 100, 15)
        w_eq = col4.slider("Tam. Equipe", 0, 100, 15)
        w_merito = col5.slider("Tempo s/ Mérito", 0, 100, 15)

        total_w = w_perf + w_promo + w_casa + w_eq + w_merito
        if total_w != 100:
            st.warning(f"⚠️ A soma dos pesos é {total_w}%. Ajuste para totalizar 100%.")
        weights = {k: v/100 for k,v in {
            "perf": w_perf, "promo": w_promo, "casa": w_casa, "eq": w_eq, "merito": w_merito
        }.items()}

    # ============================================
    # CÁLCULO DO RISCO (TRI)
    # ============================================
    dfv["risco_turnover"] = (
        weights["perf"] * dfv["score_perf_inv"] +
        weights["promo"] * dfv["score_tempo_promo"] +
        weights["casa"] * dfv["score_tempo_casa"] +
        weights["eq"] * dfv["score_tamanho_eq"] +
        weights["merito"] * dfv["score_merito"]
    ) * 100
    dfv["risco_turnover"] = dfv["risco_turnover"].clip(0, 100)

    avg_risk = safe_mean(dfv["risco_turnover"])
    pct_high = round((dfv["risco_turnover"] > 60).mean() * 100, 1)

    c1, c2 = st.columns(2)
    c1.metric("⚠️ Risco Médio (TRI)", f"{avg_risk}%")
    c2.metric("🚨 % Risco Alto", f"{pct_high}%")

    st.divider()

    # ============================================
    # GRÁFICOS DE DISTRIBUIÇÃO
    # ============================================
    bins = [0, 20, 40, 60, 80, 100]
    labels = ["0–20", "20–40", "40–60", "60–80", "80–100"]
    dfv["faixa_risco"] = pd.cut(dfv["risco_turnover"], bins=bins, labels=labels, include_lowest=True)
    risco_dist = dfv["faixa_risco"].value_counts(normalize=True).sort_index() * 100

    fig_dist = px.bar(
        risco_dist, x=risco_dist.index, y=risco_dist.values,
        text=risco_dist.round(1).astype(str) + "%",
        color=risco_dist.values,
        color_continuous_scale="Tealgrn",
        title="📊 Distribuição do Risco de Turnover (%)"
    )
    fig_dist.update_traces(textposition="outside")
    fig_dist.update_layout(template="plotly_dark", showlegend=False)
    st.plotly_chart(fig_dist, use_container_width=True)

    # Risco médio por tempo sem promoção
    bins_promo = [0, 3, 6, 12, 24, np.inf]
    labels_promo = ["0–3m", "3–6m", "6–12m", "12–24m", "+24m"]
    dfv["faixa_tempo_sem_promo"] = pd.cut(dfv["meses_desde_promocao"], bins=bins_promo, labels=labels_promo)
    risco_por_faixa = dfv.groupby("faixa_tempo_sem_promo")["risco_turnover"].mean().reset_index()

    fig_risco = px.line(
        risco_por_faixa, x="faixa_tempo_sem_promo", y="risco_turnover",
        markers=True, color_discrete_sequence=["#00FFFF"],
        title="📈 Risco Médio por Tempo sem Promoção"
    )
    fig_risco.update_layout(template="plotly_dark")
    st.plotly_chart(fig_risco, use_container_width=True)

    # ============================================
    # ANÁLISE INDIVIDUAL / ANALÍTICO
    # ============================================
    st.markdown("### 🧾 Análise Individual de Risco")

    def explain_risk(row):
        motivos = []
        if row["score_perf_inv"] > 0.6: motivos.append("baixa performance")
        if row["score_tempo_promo"] > 0.6: motivos.append("muito tempo sem promoção")
        if row["score_tamanho_eq"] > 0.6: motivos.append("gestor com equipe grande")
        if row["score_merito"] > 0.6: motivos.append("sem mérito recente")
        if row["score_tempo_casa"] < 0.2: motivos.append("pouco tempo de casa (fase inicial)")
        if not motivos: return "Perfil estável"
        return ", ".join(motivos).capitalize()

    dfv["motivo_risco"] = dfv.apply(explain_risk, axis=1)

    cols_show = [
        c for c in ["nome", "departamento", "cargo", "avaliação", "risco_turnover", "motivo_risco"]
        if c in dfv.columns
    ]
    st.dataframe(
        dfv[cols_show].sort_values("risco_turnover", ascending=False).reset_index(drop=True),
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# IA & APRESENTAÇÕES (PREMIUM)
# =========================================================
def view_ai(dfv):
    st.subheader("🤖 Análises de IA e Apresentações Automáticas (Premium)")
    
    if not has_feature("Premium"):
        st.warning("🔒 Esta seção requer assinatura Premium.")
        st.info("💡 Entre em contato para fazer upgrade e acessar análises avançadas de IA, "
               "apresentações automáticas e relatórios personalizados.")
        return
    
    tab1, tab2, tab3 = st.tabs(["📊 Insights de IA", "📄 Apresentação Automática", "🔮 Análise Preditiva"])
    
    with tab1:
        st.markdown("### Insights Automáticos")
        with st.spinner("Gerando insights de IA..."):
            insights = generate_ai_insights(dfv)
        
        if insights["alertas"]:
            st.warning("🚨 **Alertas Críticos:**")
            for alerta in insights["alertas"]:
                st.warning(f"- {alerta}")
        
        if insights["tendencias"]:
            st.info("📈 **Tendências Identificadas:**")
            for tendencia in insights["tendencias"]:
                st.info(f"- {tendencia}")
        
        if insights["recomendacoes"]:
            st.success("💡 **Recomendações de Ação:**")
            for i, rec in enumerate(insights["recomendacoes"], 1):
                st.success(f"{i}. {rec}")
        
        if not insights["alertas"] and not insights["tendencias"] and not insights["recomendacoes"]:
            st.info("✅ Nenhum insight crítico identificado. Os indicadores estão dentro dos parâmetros normais.")
    
    with tab2:
        st.markdown("### Apresentação Automática")
        st.caption("Apresentação gerada automaticamente com os principais insights e recomendações.")
        
        with st.spinner("Gerando apresentação..."):
            presentation = generate_ai_presentation(dfv)
        
        st.markdown(presentation)
        
        st.download_button(
            label="📥 Baixar Apresentação (Markdown)",
            data=presentation,
            file_name="apresentacao_people_analytics.md",
            mime="text/markdown"
        )
    
    with tab3:
        st.markdown("### Análise Preditiva de Turnover")
        st.caption("Previsão baseada em padrões históricos identificados nos dados.")
        
        with st.spinner("Gerando análise preditiva..."):
            pred = generate_predictive_analysis(dfv)
        
        if "mensagem" in pred:
            st.info(pred["mensagem"])
        
        if "previsao_3_meses" in pred:
            st.markdown("#### Previsão para os Próximos 3 Meses")
            c1, c2, c3 = st.columns(3)
            for i, prev in enumerate(pred["previsao_3_meses"], 1):
                with [c1, c2, c3][i-1]:
                    st.metric(f"Mês {i}", f"{prev}%")
        
        if "tendencia" in pred:
            st.markdown(f"**Tendência Identificada:** {pred['tendencia'].upper()}")
            if "coeficiente_tendencia" in pred:
                st.caption(f"Coeficiente de tendência: {pred['coeficiente_tendencia']}")


# =========================================================
# RENDER DA VIEW SELECIONADA (usa df_filt)
# =========================================================
view = st.session_state["view"]
if view == "overview":
    view_overview(df_final.copy(), ano_filtro, mes_filtro, df.copy())
elif view == "headcount":
    view_headcount(df_final.copy())
elif view == "turnover":
    view_turnover(df_final.copy(), ano_filtro, mes_filtro, df.copy())
elif view == "risk":
    if has_feature("Premium"):
        view_risk(df_final.copy())
    else:
        st.warning("🔒 Análise de Risco (TRI) requer assinatura Premium.")
        st.info("💡 Entre em contato para fazer upgrade e acessar análises avançadas.")
elif view == "ai":
    view_ai(df_final.copy())
else:
    view_overview(df_final.copy(), ano_filtro, mes_filtro, df.copy())



