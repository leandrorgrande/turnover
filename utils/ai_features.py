"""
Funcionalidades de IA para análises avançadas (Premium).
Inclui análises, recomendações e apresentações automáticas.
"""
import pandas as pd
import streamlit as st
from typing import Dict, List, Optional
from utils.subscription import require_premium, SubscriptionLevel
from utils.data_loader import col_like
from utils.kpi_helpers import calculate_turnover_history, calculate_turnover


@require_premium
def generate_ai_insights(df: pd.DataFrame) -> Dict[str, any]:
    """
    Gera insights automáticos usando análise de padrões.
    Funcionalidade Premium.
    """
    insights = {
        "alertas": [],
        "tendencias": [],
        "recomendacoes": []
    }
    
    # Análise de turnover
    turnover_data = calculate_turnover_history(df)
    
    if not turnover_data.empty:
        # Verificar tendência de aumento
        if len(turnover_data) >= 3:
            ultimos_3 = turnover_data["Turnover Total (%)"].tail(3).values
            if ultimos_3[-1] > ultimos_3[0] * 1.2:  # Aumento de 20%
                insights["alertas"].append(
                    "⚠️ Turnover aumentou significativamente nos últimos meses. "
                    "Recomenda-se investigar causas raiz."
                )
                insights["recomendacoes"].append(
                    "Realizar pesquisa de clima organizacional e entrevistas de desligamento."
                )
        
        # Verificar se turnover está acima de benchmarks
        turnover_medio = turnover_data["Turnover Total (%)"].mean()
        if turnover_medio > 5.0:
            insights["alertas"].append(
                f"⚠️ Turnover médio ({turnover_medio:.1f}%) está acima do benchmark de mercado (3-5%)."
            )
    
    # Análise de departamentos críticos
    dept_col = col_like(df, "departamento")
    if dept_col:
        dept_turnover = {}
        for dept in df[dept_col].dropna().unique():
            df_dept = df[df[dept_col] == dept]
            turnover_dept = calculate_turnover(df_dept)
            dept_turnover[dept] = turnover_dept.get("turnover_total", 0)
        
        if dept_turnover:
            max_dept = max(dept_turnover.items(), key=lambda x: x[1])
            if max_dept[1] > 8.0:
                insights["alertas"].append(
                    f"🚨 Departamento '{max_dept[0]}' apresenta turnover crítico ({max_dept[1]:.1f}%)."
                )
                insights["recomendacoes"].append(
                    f"Priorizar ações de retenção no departamento {max_dept[0]}."
                )
    
    # Análise de tenure
    adm_col = col_like(df, "data de admissão")
    desl_col = col_like(df, "data de desligamento")
    
    if adm_col and desl_col:
        df_deslig = df[df["ativo"] == False].copy() if "ativo" in df.columns else df.copy()
        if not df_deslig.empty:
            df_deslig[adm_col] = pd.to_datetime(df_deslig[adm_col], errors="coerce")
            df_deslig[desl_col] = pd.to_datetime(df_deslig[desl_col], errors="coerce")
            df_deslig["tenure"] = (df_deslig[desl_col] - df_deslig[adm_col]).dt.days / 30
            
            tenure_medio = df_deslig["tenure"].mean()
            if tenure_medio < 12:
                insights["alertas"].append(
                    f"⚠️ Tenure médio baixo ({tenure_medio:.1f} meses). "
                    "Colaboradores estão saindo muito cedo."
                )
                insights["recomendacoes"].append(
                    "Melhorar processo de onboarding e engajamento nos primeiros meses."
                )
    
    return insights


@require_premium
def generate_ai_presentation(df: pd.DataFrame) -> str:
    """
    Gera apresentação automática em texto com os principais insights.
    Funcionalidade Premium.
    """
    insights = generate_ai_insights(df)
    turnover_data = calculate_turnover_history(df)
    
    presentation = "# 📊 Apresentação Automática de People Analytics\n\n"
    
    # Resumo executivo
    presentation += "## Resumo Executivo\n\n"
    
    if not turnover_data.empty:
        turnover_medio = turnover_data["Turnover Total (%)"].mean()
        presentation += f"- **Turnover Médio**: {turnover_medio:.1f}%\n"
        presentation += f"- **Período Analisado**: {turnover_data['Mês'].min()} a {turnover_data['Mês'].max()}\n"
    
    ativos = df[df["ativo"] == True] if "ativo" in df.columns else df
    presentation += f"- **Total de Colaboradores Ativos**: {len(ativos):,}\n\n"
    
    # Alertas
    if insights["alertas"]:
        presentation += "## 🚨 Alertas Críticos\n\n"
        for alerta in insights["alertas"]:
            presentation += f"- {alerta}\n"
        presentation += "\n"
    
    # Tendências
    if insights["tendencias"]:
        presentation += "## 📈 Tendências Identificadas\n\n"
        for tendencia in insights["tendencias"]:
            presentation += f"- {tendencia}\n"
        presentation += "\n"
    
    # Recomendações
    if insights["recomendacoes"]:
        presentation += "## 💡 Recomendações de Ação\n\n"
        for i, rec in enumerate(insights["recomendacoes"], 1):
            presentation += f"{i}. {rec}\n"
        presentation += "\n"
    
    presentation += "---\n\n"
    presentation += "*Apresentação gerada automaticamente pela plataforma de People Analytics.*"
    
    return presentation


@require_premium
def generate_predictive_analysis(df: pd.DataFrame) -> Dict[str, any]:
    """
    Gera análise preditiva de turnover baseada em padrões históricos.
    Funcionalidade Premium.
    """
    turnover_data = calculate_turnover_history(df)
    
    if turnover_data.empty or len(turnover_data) < 3:
        return {
            "mensagem": "Dados insuficientes para análise preditiva. "
                       "Necessário histórico de pelo menos 3 meses."
        }
    
    # Análise de tendência simples (regressão linear básica)
    turnover_values = turnover_data["Turnover Total (%)"].values
    meses = list(range(len(turnover_values)))
    
    # Calcular tendência
    n = len(meses)
    x_mean = sum(meses) / n
    y_mean = sum(turnover_values) / n
    
    numerator = sum((meses[i] - x_mean) * (turnover_values[i] - y_mean) for i in range(n))
    denominator = sum((meses[i] - x_mean) ** 2 for i in range(n))
    
    if denominator == 0:
        slope = 0
    else:
        slope = numerator / denominator
    
    intercept = y_mean - slope * x_mean
    
    # Previsão para próximos 3 meses
    proximos_meses = [n, n+1, n+2]
    previsoes = [slope * mes + intercept for mes in proximos_meses]
    
    return {
        "tendencia": "crescente" if slope > 0.1 else "decrescente" if slope < -0.1 else "estável",
        "previsao_3_meses": [max(0, round(p, 1)) for p in previsoes],
        "coeficiente_tendencia": round(slope, 3),
        "mensagem": f"Tendência {('crescente' if slope > 0.1 else 'decrescente' if slope < -0.1 else 'estável')} "
                   f"identificada. Previsão de turnover para os próximos 3 meses: "
                   f"{', '.join([f'{p:.1f}%' for p in previsoes])}"
    }
