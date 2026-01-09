# 🚀 Dashboard de People Analytics - Turnover

Plataforma completa para análise de indicadores de RH com suporte a múltiplas bases de dados, validação automática de cálculos e funcionalidades avançadas de IA.

## 📋 Funcionalidades

### ✅ Plano Básico (Gratuito)

- **Visão Geral**: KPIs consolidados (Ativos, % CLT, % Feminino, % Liderança)
- **Headcount**: Estrutura e evolução por departamento
- **Turnover**: Indicadores básicos, evolução mensal e tenure
- **Validação de Dados**: Verificação automática de qualidade e consistência dos dados

### ⭐ Plano Premium (Pago)

- **Todas as funcionalidades do Plano Básico**
- **Risco de Turnover (TRI)**: Modelo interativo de análise de risco
- **Análises de IA**: Insights automáticos e recomendações
- **Apresentações Automáticas**: Geração de apresentações em Markdown
- **Análise Preditiva**: Previsão de turnover para os próximos 3 meses
- **Relatórios Personalizados**: Exportação avançada de dados

## 🛠️ Instalação

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd turnover
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Execute o dashboard:
```bash
streamlit run dashboard_turnover.py
```

## 📊 Estrutura de Dados

O dashboard espera um arquivo Excel (.xlsx) com as seguintes abas:

### Aba "empresa"
- `nome empresa`
- `cnpj`
- `unidade`
- `cidade`
- `uf`

### Aba "colaboradores"
- `matricula`
- `nome`
- `departamento`
- `cargo`
- `matricula do gestor`
- `tipo_contrato`
- `genero`
- `data de admissão`
- `data de desligamento`
- `motivo de desligamento`
- `ultima promoção`
- `ultimo mérito`

### Aba "performance"
- `matricula`
- `avaliação`
- `data de encerramento do ciclo`

## 🔍 Validação de Dados

O sistema inclui validação automática que verifica:
- ✅ Presença de colunas essenciais
- ✅ Consistência de datas (admissão vs desligamento)
- ✅ Valores nulos e dados faltantes
- ✅ Datas futuras inválidas

## 📈 Cálculos de KPIs

Todos os cálculos são validados e documentados:

- **Turnover**: `(Desligados no período / Ativos no período) * 100`
- **Turnover Voluntário**: Baseado em motivo de desligamento contendo "Pedido"
- **Turnover Involuntário**: Total - Voluntário
- **Tenure**: Tempo médio até desligamento (em meses)
- **Headcount**: Distribuição de colaboradores ativos por departamento

## 🤖 Funcionalidades de IA (Premium)

### Insights Automáticos
- Identificação de tendências de aumento de turnover
- Alertas sobre departamentos críticos
- Análise de tenure e recomendações

### Análise Preditiva
- Previsão de turnover para próximos 3 meses
- Identificação de tendências (crescente/decrescente/estável)
- Baseado em regressão linear simples sobre histórico

### Apresentações Automáticas
- Geração de apresentação em Markdown
- Inclui resumo executivo, alertas, tendências e recomendações
- Download disponível

## 🏗️ Arquitetura

```
turnover/
├── dashboard_turnover.py    # Dashboard principal
├── utils/
│   ├── __init__.py          # Exports dos módulos
│   ├── data_loader.py        # Carregamento e validação de dados
│   ├── kpi_helpers.py        # Cálculos de KPIs
│   ├── subscription.py       # Sistema de níveis (Básico/Premium)
│   └── ai_features.py        # Funcionalidades de IA
└── requirements.txt          # Dependências
```

## 🔐 Sistema de Níveis

O sistema suporta dois níveis de acesso:

- **Básico**: Acesso gratuito a indicadores básicos
- **Premium**: Acesso pago a funcionalidades avançadas

Por padrão, todos os usuários começam com acesso Básico. Para implementar verificação real de assinatura, edite `utils/subscription.py`.

## 🐛 Correções Implementadas

- ✅ Correção de bugs nos cálculos de turnover
- ✅ Validação de variáveis antes de uso
- ✅ Remoção de código duplicado
- ✅ Modularização para melhor manutenção
- ✅ Validação automática de dados

## 📝 Notas

- Os cálculos são revisados e validados automaticamente
- O sistema suporta múltiplas bases de dados (uma por upload)
- Funcionalidades Premium são claramente marcadas
- Todos os KPIs são calculados usando módulos centralizados para garantir consistência

## 🤝 Contribuindo

Para contribuir com melhorias:
1. Revise os cálculos em `utils/kpi_helpers.py`
2. Adicione novas funcionalidades seguindo a estrutura modular
3. Mantenha a separação entre funcionalidades Básicas e Premium

## 📄 Licença

[Adicione informações de licença aqui]
