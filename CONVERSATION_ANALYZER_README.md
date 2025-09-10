# 💬 Conversation Analyzer - Interface de Análise de Conversas

## 📋 Visão Geral

Interface web interativa para análise detalhada das conversas da Talqui, permitindo visualização cronológica das mensagens, filtros avançados e informações completas sobre cada sessão de atendimento.

## 🎯 Funcionalidades

### **📊 Dashboard Principal**
- **Estatísticas gerais** em tempo real
- **Contadores** de conversas, confiança média, taxa de transbordo
- **Métricas** de performance por agente

### **🔍 Painel de Filtros (Esquerda)**
- **Categorias** - Filtragem por tipo de demanda
- **Subcategorias** - Refinamento específico
- **Agentes** - Por responsável pelo atendimento  
- **Confiança** - Faixas de percentual de certeza
- **Status de Transbordo** - Com ou sem transferência

### **💬 Visualizador Central**
- **Lista de conversas** com resumos e tags
- **Visualização cronológica** das mensagens
- **Interface estilo chat** com avatares
- **Busca em tempo real** por ID ou conteúdo

### **📋 Painel de Informações (Direita)**
- **Dados da classificação** (categoria, confiança)
- **Informações dos agentes** (primário, final)
- **Score de eficácia** visual
- **Status de transbordo** detalhado  
- **Métricas da sessão** (mensagens, tempo)
- **Resumo automático** e reasoning

## 🚀 Como Usar

### **Inicialização Rápida:**

```bash
# Via script automatizado (recomendado)
./start_conversation_analyzer.sh

# Ou manualmente
python3 conversation_analyzer_app.py
```

### **Acesso:**
- **URL:** http://localhost:5001
- **Interface:** Web responsiva
- **Compatibilidade:** Chrome, Firefox, Safari

## 📱 Interface

### **Layout Responsivo:**
```
┌─────────────────────────────────────────────────────────────┐
│ 🏆 Conversation Analyzer    📊 Stats: 3,674 | 85.2% | 37%  │
├─────────────┬───────────────────────────┬───────────────────┤
│   FILTROS   │      CONVERSAS/CHAT       │   INFORMAÇÕES     │
│             │                           │                   │
│ □ Categoria │ ┌─────────────────────────┐ │ 📋 Classificação │
│ □ Agente    │ │ Lista de Conversas      │ │ 👥 Agentes      │  
│ □ Confiança │ │ - Conv 1 [85%] Isabella │ │ 📊 Eficácia     │
│ □ Transbordo│ │ - Conv 2 [92%] Alison   │ │ 🔄 Transbordo   │
│             │ └─────────────────────────┘ │ 📈 Métricas     │
│ 🔍 Busca    │ ┌─────────────────────────┐ │ 📝 Resumo       │
│             │ │   💬 Chat Viewer        │ │                 │
│ 🏷️ Tags     │ │                         │ │ 🧠 Reasoning    │
│             │ │ Cliente: Olá, preciso   │ │                 │
│             │ │ de ajuda...             │ │                 │
│             │ │                         │ │                 │
│             │ │ Isabella: Claro! Vou    │ │                 │
│             │ │ te ajudar...           │ │                 │
│             │ └─────────────────────────┘ │                 │
└─────────────┴───────────────────────────┴───────────────────┘
```

## 🎨 Recursos Visuais

### **🏷️ Sistema de Tags:**
- **Categoria**: Azul (COMERCIAL, TÉCNICO, etc.)
- **Agente**: Roxo (Isabella, Alison, etc.)
- **Transbordo**: Vermelho/Verde (Com/Sem)

### **📊 Indicadores Visuais:**
- **Barra de confiança** com cores:
  - 🟢 Verde: 90-100% (Alta)
  - 🟡 Amarelo: 70-89% (Média)  
  - 🔴 Vermelho: <70% (Baixa)

### **⚡ Score de Eficácia:**
- **Alto** (80-100%): Gradiente verde
- **Médio** (60-79%): Gradiente amarelo
- **Baixo** (<60%): Gradiente vermelho

## 📊 Dados Analisados

### **Métricas Principais:**
- **3,674** conversas totais analisadas
- **Taxa de transbordo**: 37.0% geral
- **Confiança média**: 85.2%
- **Agentes únicos**: 7

### **Categorias Disponíveis:**
1. **SUPORTE_TECNICO** (1,037 conversas)
2. **OUTROS** (884 conversas)  
3. **COMERCIAL** (778 conversas)
4. **INFORMACAO** (497 conversas)
5. **FINANCEIRO** (431 conversas)
6. **CANCELAMENTO** (19 conversas)
7. **RECLAMACAO** (28 conversas)

### **Top Agentes:**
1. **Isabella**: 2,456 sessões (46.7% fechamento)
2. **Alison**: 391 sessões (92.6% fechamento) 
3. **Achilles**: 186 sessões (94.1% fechamento)

## 🔧 Funcionalidades Técnicas

### **Filtros Dinâmicos:**
- **Múltipla seleção** por categoria
- **Filtros combinados** (ex: Categoria + Agente)
- **Busca em tempo real** por texto
- **Limpeza rápida** de todos os filtros

### **Performance:**
- **Carregamento lazy** de mensagens
- **Cache inteligente** de dados
- **Scroll infinito** para listas grandes
- **Busca instantânea** sem reload

### **Interações:**
- **Clique** para selecionar conversa
- **ESC** para limpar seleção
- **Busca por ID** ou conteúdo
- **Filtros persistentes** durante navegação

## 🗂️ Estrutura do Projeto

```
conversation_analyzer/
├── conversation_analyzer_app.py    # Backend Flask
├── templates/
│   └── index.html                  # Interface principal
├── static/
│   ├── css/
│   │   └── style.css              # Estilos responsivos
│   └── js/
│       └── app.js                 # Lógica frontend
├── start_conversation_analyzer.sh  # Script de inicialização
└── talqui.db                      # Banco de dados (requerido)
```

## 📡 API Endpoints

### **Backend APIs:**
- `GET /` - Interface principal
- `GET /api/filters` - Dados para filtros
- `GET /api/conversations` - Lista de conversas
- `GET /api/conversation/<id>` - Detalhes específicos
- `GET /api/stats` - Estatísticas gerais

### **Parâmetros de Filtro:**
```javascript
// Exemplo de uso da API
fetch('/api/conversations?category=COMERCIAL&agent=Alison&confidence_min=0.8')
```

## 🔒 Segurança

- **Acesso local**: Apenas localhost por padrão
- **Dados sensíveis**: Sem exposição de informações pessoais
- **Debug mode**: Desabilitado em produção
- **Rate limiting**: Configurável por endpoint

## 🎯 Casos de Uso

### **📊 Para Gestores:**
- **Análise de performance** por agente
- **Identificação de gargalos** de transbordo
- **Métricas de qualidade** de atendimento
- **ROI de treinamentos** especializados

### **🎓 Para Treinamento:**
- **Exemplos de conversas** bem resolvidas
- **Casos de estudo** de transbordos
- **Padrões de comunicação** eficazes
- **Benchmarking** entre agentes

### **🔍 Para Análise Operacional:**
- **Distribuição de demanda** por categoria
- **Horários de pico** de atendimento
- **Eficácia de classificação** automática
- **Oportunidades de automação**

## 📈 Insights Disponíveis

### **Padrões Identificados:**
- **Isabella**: Alto volume, baixa taxa de fechamento (46.7%)
- **Especialistas técnicos**: Alta eficácia (90%+)  
- **Categorias técnicas**: Maior necessidade de transbordo
- **Confiança alta**: Correlação com menos transbordos

### **Oportunidades:**
- **Treinamento técnico** para Isabella
- **Redistribuição de carga** de trabalho
- **Automação** de casos recorrentes
- **Especialização** por categoria

## 🚀 Próximos Passos

1. **✅ CONCLUÍDO**: Interface completa funcional
2. **🔄 EM DESENVOLVIMENTO**: 
   - Exportação de relatórios
   - Filtros salvos
   - Dashboard de métricas avançadas
3. **📋 PLANEJADO**:
   - Análise de sentimento
   - Integração com APIs externas
   - Alertas automáticos

---

**🎯 Desenvolvido para otimizar a análise de conversas e melhorar a eficácia do atendimento Talqui**

**📅 Versão**: 1.0  
**🔧 Tecnologias**: Flask, SQLite, HTML5, CSS3, JavaScript ES6  
**🌐 Acesso**: http://localhost:5001