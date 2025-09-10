# 🤖 Sistema de Classificação de Sessões - Talqui

Sistema completo para classificação automática de sessões de atendimento usando **DeepSeek AI**, com dashboard interativo e análise de custos.

## 📋 Visão Geral

Este sistema analisa conversas de atendimento ao cliente e as classifica automaticamente em categorias usando inteligência artificial, oferecendo insights valiosos sobre o tipo de demandas recebidas.

### 🎯 Categorias de Classificação
- **COMERCIAL** - Interesse em produtos, preços, planos, vendas
- **SUPORTE_TECNICO** - Problemas técnicos, bugs, configurações  
- **FINANCEIRO** - Pagamentos, cobrança, faturas, reembolsos
- **INFORMACAO** - Dúvidas gerais, informações sobre serviços
- **RECLAMACAO** - Insatisfação, problemas, críticas
- **CANCELAMENTO** - Solicitação de cancelamento de serviços
- **OUTROS** - Casos que não se encaixam nas categorias acima

## 📁 Estrutura do Projeto

```
dog-food/
├── 📊 Dados
│   ├── talqui-messages.csv          # Mensagens das conversas
│   ├── talqui-operator.csv          # Dados dos operadores
│   ├── talqui-sessions-plugin.csv   # Sessões com plugin
│   └── talqui.db                    # Banco SQLite unificado
├── 🔧 Scripts Principais
│   ├── session_classifier.py        # Classificador principal
│   ├── cost_estimator.py           # Estimador de custos
│   ├── dashboard.py                 # Dashboard Streamlit
│   ├── run_batch_classification.py  # Execução em lotes
│   └── analyze_classifications.py   # Análise dos resultados
├── 🗄️ Configuração
│   ├── create_talqui_database.sql   # Script de criação do banco
│   ├── requirements.txt             # Dependências Python
│   ├── .env                        # Configurações da API
│   └── README.md                   # Este arquivo
└── 📈 Relatórios (gerados)
    ├── session_classifications.csv
    └── classification_report_*.csv
```

## 🚀 Configuração Inicial

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar API DeepSeek
Arquivo `.env` já configurado com a chave da API.

### 3. Criar Banco de Dados
```bash
sqlite3 talqui.db < create_talqui_database.sql
```

## 💻 Como Usar

### 🎨 Dashboard Interativo (Recomendado)
```bash
streamlit run dashboard.py
```

Acesse: `http://localhost:8501`

**Funcionalidades do Dashboard:**
- 📊 Visualizações interativas das classificações
- 💰 Estimativa de custos em tempo real
- 🔄 Execução de classificações via interface
- 📈 Métricas e estatísticas detalhadas
- 🔍 Exploração e filtragem de dados
- 📥 Download de relatórios

### 🤖 Classificação via Linha de Comando

#### Classificar sessões individuais:
```bash
python3 session_classifier.py
```

#### Processar em lotes:
```bash
python3 run_batch_classification.py
```

#### Análise dos resultados:
```bash
python3 analyze_classifications.py
```

#### Estimativa de custos:
```bash
python3 cost_estimator.py
```

## 💰 Análise de Custos

O sistema inclui um estimador de custos que calcula o preço para classificar sessões usando a API DeepSeek:

### Preços DeepSeek (por 1M tokens):
- **Input**: $0.14 USD
- **Output**: $0.28 USD

### Estimativas Típicas:
- **Por sessão**: ~$0.00009 USD
- **1.000 sessões**: ~$0.09 USD  
- **10.000 sessões**: ~$0.90 USD

## 📊 Resultados Esperados

### Métricas de Performance:
- **Confiança média**: 90-95%
- **Velocidade**: ~2-3 sessões/segundo
- **Precisão**: Alta (baseada em contexto completo da conversa)

### Distribuição Típica por Categoria:
- **SUPORTE_TECNICO**: 35-40%
- **COMERCIAL**: 20-25%
- **INFORMACAO**: 15-20%
- **FINANCEIRO**: 10-15%
- **OUTROS**: 5-10%

## 🗄️ Estrutura do Banco de Dados

### Tabela Principal: `talqui_unified`
Join session-centric entre mensagens e sessões com 67.870+ registros

### Tabela de Classificações: `session_classifications`
```sql
- sessionID (PK)
- category 
- subcategory
- confidence (0.0-1.0)
- reasoning
- classified_at
- messages_analyzed
```

### Views Disponíveis:
- `session_summary` - Resumo por sessão
- `operator_metrics` - Métricas por operador  
- `message_analysis` - Análise de mensagens

## 🔧 Configurações Avançadas

### Personalizar Categorias:
Edite o prompt em `session_classifier.py` linha ~95

### Ajustar Batch Size:
```python
# Em run_batch_classification.py
run_classification_batches(total_sessions=100, batch_size=10)
```

### Configurar Timeouts:
```python
# Em session_classifier.py
timeout=30  # segundos para API
```

## 🛠️ Troubleshooting

### Erro de Conexão API:
- Verifique se a chave DeepSeek está correta no `.env`
- Teste conectividade: `python3 -c "from session_classifier import SessionClassifier; c=SessionClassifier()"`

### Problema no SQLite:
- Recriar banco: `rm talqui.db && sqlite3 talqui.db < create_talqui_database.sql`

### Dashboard não carrega:
- Verificar se Streamlit está instalado: `pip install streamlit`
- Porta ocupada: `streamlit run dashboard.py --server.port 8502`

## 📈 Análises Disponíveis

### 1. Distribuição por Categoria
Gráfico de pizza mostrando proporção de cada tipo de atendimento

### 2. Confiança das Classificações  
Histograma com distribuição dos níveis de confiança

### 3. Timeline de Classificações
Evolução temporal das classificações por categoria

### 4. Performance por Operador
Ranking dos operadores por volume e tipo de atendimento

### 5. Análise de Duração
Correlação entre tipo de atendimento e tempo de sessão

## 🚀 Próximos Passos

### Melhorias Sugeridas:
1. **🔄 Auto-classificação**: Executar classificações automaticamente
2. **📧 Alertas**: Notificações para categorias específicas  
3. **🎯 Fine-tuning**: Treinar modelo customizado
4. **📊 Dashboard tempo real**: Updates automáticos
5. **🔗 Integração**: API para outros sistemas

### Expansões Possíveis:
- **Sentiment analysis** nas mensagens
- **Detecção de urgência** nas solicitações
- **Clustering** de tópicos similares
- **Predição de NPS** baseada na conversa

---

## 📞 Suporte

Para questões técnicas ou melhorias, consulte:
- Logs do sistema em tempo de execução
- Função de debug no dashboard (aba Configurações)
- Verificação de integridade do banco

---

**🤖 Desenvolvido com Python, Streamlit e DeepSeek AI**