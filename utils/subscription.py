"""
Sistema de níveis de acesso (Básico vs Premium).
Controla quais funcionalidades estão disponíveis para cada usuário.
"""
import streamlit as st
from typing import Dict, List, Callable
from enum import Enum


class SubscriptionLevel(Enum):
    """Níveis de assinatura disponíveis."""
    BASIC = "basic"
    PREMIUM = "premium"


# Definição de funcionalidades por nível
FEATURES = {
    SubscriptionLevel.BASIC: [
        "Visão Geral - KPIs Básicos",
        "Headcount por Departamento",
        "Turnover - Indicadores Básicos",
        "Gráficos de Evolução",
        "Validação de Dados"
    ],
    SubscriptionLevel.PREMIUM: [
        "Todas as funcionalidades Básicas",
        "Risco de Turnover (TRI) - Modelo Avançado",
        "Análises de IA",
        "Apresentações Automáticas",
        "Relatórios Personalizados",
        "Exportação Avançada",
        "Análise Preditiva",
        "Recomendações de IA"
    ]
}


def get_user_subscription() -> SubscriptionLevel:
    """
    Obtém o nível de assinatura do usuário.
    Por enquanto, retorna sempre BASIC. 
    Em produção, isso viria de um banco de dados ou sistema de autenticação.
    """
    if "subscription_level" not in st.session_state:
        st.session_state["subscription_level"] = SubscriptionLevel.BASIC
    
    # TODO: Implementar verificação real de assinatura
    # Por enquanto, permite alternar manualmente para testes
    return st.session_state["subscription_level"]


def set_user_subscription(level: SubscriptionLevel):
    """Define o nível de assinatura do usuário."""
    st.session_state["subscription_level"] = level


def has_feature(feature_name: str) -> bool:
    """
    Verifica se o usuário tem acesso a uma funcionalidade.
    
    Args:
        feature_name: Nome da funcionalidade a verificar ou "Premium" para verificar nível
    
    Returns:
        True se o usuário tem acesso, False caso contrário
    """
    level = get_user_subscription()
    
    # Se pedir verificação de Premium, retorna se é premium
    if feature_name == "Premium":
        return level == SubscriptionLevel.PREMIUM
    
    # Premium tem acesso a tudo
    if level == SubscriptionLevel.PREMIUM:
        return True
    
    # Básico tem acesso apenas às funcionalidades básicas
    basic_features = FEATURES[SubscriptionLevel.BASIC]
    return feature_name in basic_features


def require_premium(func: Callable) -> Callable:
    """
    Decorator para exigir assinatura premium.
    Mostra mensagem de upgrade se o usuário não tiver acesso.
    """
    def wrapper(*args, **kwargs):
        if not has_feature("Premium"):
            st.warning("🔒 Esta funcionalidade requer assinatura Premium.")
            st.info("💡 Entre em contato para fazer upgrade e acessar análises avançadas de IA, "
                   "apresentações automáticas e relatórios personalizados.")
            return None
        return func(*args, **kwargs)
    return wrapper


def show_subscription_info():
    """Mostra informações sobre o plano atual do usuário."""
    level = get_user_subscription()
    
    if level == SubscriptionLevel.BASIC:
        st.sidebar.info("📊 **Plano Básico Ativo**\n\n"
                       "Você tem acesso a indicadores básicos de turnover e headcount.")
        
        with st.sidebar.expander("🔓 Upgrade para Premium"):
            st.markdown("""
            **Funcionalidades Premium:**
            - ✅ Análise de Risco de Turnover (TRI)
            - ✅ Análises e recomendações de IA
            - ✅ Apresentações automáticas
            - ✅ Relatórios personalizados
            - ✅ Exportação avançada
            - ✅ Análise preditiva
            
            Entre em contato para fazer upgrade!
            """)
    else:
        st.sidebar.success("⭐ **Plano Premium Ativo**\n\n"
                          "Você tem acesso a todas as funcionalidades avançadas!")


def get_available_features() -> List[str]:
    """Retorna lista de funcionalidades disponíveis para o usuário atual."""
    level = get_user_subscription()
    return FEATURES[level].copy()
