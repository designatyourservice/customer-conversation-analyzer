#!/usr/bin/env python3
"""
Dashboard Streamlit para visualização e controle da classificação de sessões
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
from datetime import datetime, timedelta
import time
import subprocess
import sys
import os

# Importar módulos locais
from session_classifier import SessionClassifier
from cost_estimator import DeepSeekCostEstimator
from analyze_classifications import analyze_classifications

# Configuração da página
st.set_page_config(
    page_title="Dashboard - Classificação de Sessões",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border: 1px solid #e1e5eb;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
        color: white;
    }
    .status-success { background-color: #28a745; }
    .status-warning { background-color: #ffc107; color: #000; }
    .status-danger { background-color: #dc3545; }
    .status-info { background-color: #17a2b8; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)  # Cache por 1 minuto
def load_data():
    """Carrega dados do banco SQLite"""
    try:
        db_path = "/Users/thomazkrause/workspace/python-apps/dog-food/talqui.db"
        conn = sqlite3.connect(db_path)
        
        # Dados das classificações
        classifications_query = """
        SELECT 
            sc.*,
            s.operator_info,
            s.sessionKind,
            s.sessionDuration,
            s.sessionMessagesCount,
            s.closeMotive,
            s.session_createdAt,
            s.queuedAt,
            s.manualAt,
            s.closedAt
        FROM session_classifications sc
        JOIN talqui_unified s ON sc.sessionID = s.sessionID
        ORDER BY sc.classified_at DESC
        """
        
        classifications_df = pd.read_sql_query(classifications_query, conn)
        
        # Estatísticas gerais
        stats_query = """
        SELECT 
            COUNT(DISTINCT sessionID) as total_sessions,
            COUNT(DISTINCT CASE WHEN sessionMessagesCount > 0 THEN sessionID END) as sessions_with_messages,
            COUNT(DISTINCT operatorID) as unique_operators,
            AVG(sessionDuration) as avg_duration,
            COUNT(DISTINCT messageID) as total_messages
        FROM talqui_unified
        """
        
        general_stats = pd.read_sql_query(stats_query, conn).iloc[0]
        
        # Progresso de classificação
        classified_count = len(classifications_df)
        total_classifiable = general_stats['sessions_with_messages']
        progress_percent = (classified_count / total_classifiable * 100) if total_classifiable > 0 else 0
        
        conn.close()
        
        return {
            'classifications': classifications_df,
            'general_stats': general_stats,
            'progress': {
                'classified': classified_count,
                'total': total_classifiable,
                'percent': progress_percent,
                'remaining': total_classifiable - classified_count
            }
        }
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

def create_category_chart(df):
    """Cria gráfico de distribuição por categoria"""
    if df.empty:
        return None
    
    category_counts = df['category'].value_counts()
    
    fig = px.pie(
        values=category_counts.values,
        names=category_counts.index,
        title="Distribuição por Categoria",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Quantidade: %{value}<br>Percentual: %{percent}<extra></extra>'
    )
    
    return fig

def create_confidence_histogram(df):
    """Cria histograma de confiança das classificações"""
    if df.empty:
        return None
    
    fig = px.histogram(
        df,
        x='confidence',
        nbins=20,
        title="Distribuição de Confiança das Classificações",
        labels={'confidence': 'Confiança', 'count': 'Quantidade'},
        color_discrete_sequence=['#1f77b4']
    )
    
    fig.update_layout(
        xaxis_title="Nível de Confiança",
        yaxis_title="Quantidade de Classificações"
    )
    
    return fig

def create_timeline_chart(df):
    """Cria gráfico temporal das classificações"""
    if df.empty:
        return None
    
    df['classified_date'] = pd.to_datetime(df['classified_at']).dt.date
    daily_counts = df.groupby(['classified_date', 'category']).size().reset_index(name='count')
    
    fig = px.bar(
        daily_counts,
        x='classified_date',
        y='count',
        color='category',
        title="Classificações por Data e Categoria",
        labels={'classified_date': 'Data', 'count': 'Quantidade'}
    )
    
    return fig

def create_operator_performance_chart(df):
    """Cria gráfico de performance por operador"""
    if df.empty:
        return None
    
    operator_stats = df.groupby(['operator_info', 'category']).size().reset_index(name='count')
    top_operators = operator_stats.groupby('operator_info')['count'].sum().nlargest(10).index
    filtered_stats = operator_stats[operator_stats['operator_info'].isin(top_operators)]
    
    fig = px.bar(
        filtered_stats,
        x='operator_info',
        y='count',
        color='category',
        title="Top 10 Operadores por Categoria de Atendimento",
        labels={'operator_info': 'Operador', 'count': 'Quantidade'}
    )
    
    fig.update_layout(xaxis={'tickangle': 45})
    return fig

def run_classification_batch(num_sessions):
    """Executa classificação em lote"""
    try:
        classifier = SessionClassifier()
        
        # Criar container para log em tempo real
        log_container = st.empty()
        progress_bar = st.progress(0)
        
        # Simular processo de classificação
        sessions = classifier.get_sessions_to_classify(num_sessions)
        total_sessions = len(sessions)
        
        if total_sessions == 0:
            st.warning("Nenhuma sessão encontrada para classificação!")
            return False
        
        classified = 0
        for i, session in enumerate(sessions):
            try:
                # Simular processamento
                messages = classifier.get_session_messages(session['sessionID'])
                if messages:
                    classification = classifier.classify_session_with_deepseek(messages, session)
                    if classification:
                        classifier.save_classification(session['sessionID'], classification, len(messages))
                        classified += 1
                
                # Atualizar progresso
                progress = (i + 1) / total_sessions
                progress_bar.progress(progress)
                log_container.text(f"Processando: {i+1}/{total_sessions} - Classificadas: {classified}")
                
                # Pausa pequena para não sobrecarregar
                time.sleep(0.5)
                
            except Exception as e:
                st.error(f"Erro ao processar sessão {session['sessionID']}: {e}")
        
        classifier.close()
        st.success(f"✅ Classificação concluída! {classified}/{total_sessions} sessões processadas.")
        return True
        
    except Exception as e:
        st.error(f"Erro durante classificação: {e}")
        return False

def main():
    """Função principal do dashboard"""
    
    # Header
    st.title("🤖 Dashboard - Classificação de Sessões")
    st.markdown("**Sistema de classificação automática usando DeepSeek AI**")
    
    # Sidebar
    st.sidebar.title("⚙️ Controles")
    
    # Carregar dados
    with st.spinner("Carregando dados..."):
        data = load_data()
    
    if not data:
        st.error("Falha ao carregar dados do banco.")
        return
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📊 Total de Sessões",
            f"{data['general_stats']['total_sessions']:,}",
            delta=None
        )
    
    with col2:
        st.metric(
            "✅ Classificadas", 
            f"{data['progress']['classified']:,}",
            delta=f"{data['progress']['percent']:.1f}%"
        )
    
    with col3:
        st.metric(
            "⏳ Restantes",
            f"{data['progress']['remaining']:,}",
            delta=None
        )
    
    with col4:
        if data['classifications'].empty:
            avg_confidence = 0
        else:
            avg_confidence = data['classifications']['confidence'].mean()
        
        st.metric(
            "🎯 Confiança Média",
            f"{avg_confidence:.1%}" if avg_confidence > 0 else "N/A",
            delta=None
        )
    
    # Estimativa de custos
    st.sidebar.subheader("💰 Estimativa de Custos")
    
    try:
        cost_estimator = DeepSeekCostEstimator()
        remaining_cost = cost_estimator.estimate_remaining_cost()
        
        if remaining_cost.get('remaining_sessions', 0) > 0:
            st.sidebar.info(f"""
            **Sessões restantes:** {remaining_cost['remaining_sessions']:,}
            
            **Custo estimado:** ${remaining_cost['total_cost_usd']:.4f}
            
            **Por sessão:** ${remaining_cost['cost_per_session']:.6f}
            """)
            
            # Calculadora de custo personalizada
            st.sidebar.subheader("🧮 Calculadora de Custo")
            custom_volume = st.sidebar.number_input(
                "Número de sessões:", 
                min_value=1, 
                max_value=remaining_cost['remaining_sessions'],
                value=min(100, remaining_cost['remaining_sessions'])
            )
            
            if st.sidebar.button("💸 Calcular Custo"):
                custom_estimate = cost_estimator.estimate_cost_for_sessions(custom_volume)
                if 'error' not in custom_estimate:
                    st.sidebar.success(f"""
                    **{custom_volume} sessões:**
                    - Custo: ${custom_estimate['total_cost_usd']:.4f}
                    - Tokens: {custom_estimate['total_input_tokens'] + custom_estimate['total_output_tokens']:,}
                    """)
        else:
            st.sidebar.success("✅ Todas as sessões já foram classificadas!")
            
    except Exception as e:
        st.sidebar.error(f"Erro na estimativa: {e}")
    
    # Controles de classificação
    st.sidebar.subheader("🔄 Executar Classificação")
    
    if data['progress']['remaining'] > 0:
        batch_size = st.sidebar.selectbox(
            "Tamanho do lote:",
            [5, 10, 25, 50, 100],
            index=1
        )
        
        max_batch = min(batch_size, data['progress']['remaining'])
        
        if st.sidebar.button(f"🚀 Classificar {max_batch} sessões", type="primary"):
            with st.spinner(f"Executando classificação de {max_batch} sessões..."):
                success = run_classification_batch(max_batch)
                if success:
                    st.experimental_rerun()
    else:
        st.sidebar.info("✅ Não há sessões para classificar")
    
    # Refresh button
    if st.sidebar.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.experimental_rerun()
    
    # Abas principais
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Visão Geral", "📊 Análise Detalhada", "🔍 Explorar Dados", "⚙️ Configurações"])
    
    with tab1:
        st.subheader("📈 Visão Geral das Classificações")
        
        if not data['classifications'].empty:
            # Gráficos principais
            col1, col2 = st.columns(2)
            
            with col1:
                category_chart = create_category_chart(data['classifications'])
                if category_chart:
                    st.plotly_chart(category_chart, use_container_width=True)
            
            with col2:
                confidence_chart = create_confidence_histogram(data['classifications'])
                if confidence_chart:
                    st.plotly_chart(confidence_chart, use_container_width=True)
            
            # Timeline
            timeline_chart = create_timeline_chart(data['classifications'])
            if timeline_chart:
                st.plotly_chart(timeline_chart, use_container_width=True)
                
        else:
            st.info("📝 Nenhuma classificação encontrada. Execute algumas classificações para ver os gráficos.")
    
    with tab2:
        st.subheader("📊 Análise Detalhada")
        
        if not data['classifications'].empty:
            # Performance por operador
            operator_chart = create_operator_performance_chart(data['classifications'])
            if operator_chart:
                st.plotly_chart(operator_chart, use_container_width=True)
            
            # Estatísticas por categoria
            st.subheader("📋 Estatísticas por Categoria")
            
            category_stats = data['classifications'].groupby('category').agg({
                'confidence': ['mean', 'min', 'max', 'count'],
                'sessionDuration': 'mean',
                'sessionMessagesCount': 'mean'
            }).round(3)
            
            category_stats.columns = ['Conf. Média', 'Conf. Mín', 'Conf. Máx', 'Quantidade', 'Duração Média', 'Msgs Média']
            st.dataframe(category_stats, use_container_width=True)
            
            # Top subcategorias
            st.subheader("🏷️ Top Subcategorias")
            subcategory_stats = data['classifications'].groupby(['category', 'subcategory']).size().reset_index(name='count')
            subcategory_stats = subcategory_stats.sort_values('count', ascending=False).head(15)
            
            fig_sub = px.bar(
                subcategory_stats,
                x='count',
                y='subcategory',
                color='category',
                orientation='h',
                title="Top 15 Subcategorias",
                labels={'count': 'Quantidade', 'subcategory': 'Subcategoria'}
            )
            st.plotly_chart(fig_sub, use_container_width=True)
            
        else:
            st.info("📝 Execute algumas classificações para ver análises detalhadas.")
    
    with tab3:
        st.subheader("🔍 Explorar Dados")
        
        if not data['classifications'].empty:
            # Filtros
            col1, col2, col3 = st.columns(3)
            
            with col1:
                category_filter = st.multiselect(
                    "Filtrar por Categoria:",
                    options=data['classifications']['category'].unique(),
                    default=[]
                )
            
            with col2:
                confidence_range = st.slider(
                    "Faixa de Confiança:",
                    min_value=0.0,
                    max_value=1.0,
                    value=(0.0, 1.0),
                    step=0.05
                )
            
            with col3:
                operator_filter = st.multiselect(
                    "Filtrar por Operador:",
                    options=data['classifications']['operator_info'].dropna().unique(),
                    default=[]
                )
            
            # Aplicar filtros
            filtered_df = data['classifications'].copy()
            
            if category_filter:
                filtered_df = filtered_df[filtered_df['category'].isin(category_filter)]
            
            filtered_df = filtered_df[
                (filtered_df['confidence'] >= confidence_range[0]) &
                (filtered_df['confidence'] <= confidence_range[1])
            ]
            
            if operator_filter:
                filtered_df = filtered_df[filtered_df['operator_info'].isin(operator_filter)]
            
            # Mostrar dados filtrados
            st.subheader(f"📋 Dados Filtrados ({len(filtered_df)} registros)")
            
            if not filtered_df.empty:
                # Colunas a exibir
                display_cols = [
                    'sessionID', 'category', 'subcategory', 'confidence', 
                    'operator_info', 'sessionDuration', 'sessionMessagesCount',
                    'classified_at'
                ]
                
                available_cols = [col for col in display_cols if col in filtered_df.columns]
                st.dataframe(filtered_df[available_cols], use_container_width=True)
                
                # Botão de download
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"classificacoes_filtradas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("Nenhum registro encontrado com os filtros aplicados.")
        else:
            st.info("📝 Nenhum dado disponível para exploração.")
    
    with tab4:
        st.subheader("⚙️ Configurações e Informações")
        
        # Informações do sistema
        st.write("**📋 Informações do Sistema:**")
        st.code(f"""
Database: talqui.db
Total de sessões: {data['general_stats']['total_sessions']:,}
Sessões com mensagens: {data['general_stats']['sessions_with_messages']:,}
Operadores únicos: {data['general_stats']['unique_operators']}
Duração média: {data['general_stats']['avg_duration']/60:.1f} minutos
Total de mensagens: {data['general_stats']['total_messages']:,}
        """)
        
        # Configurações da API
        st.write("**🔧 Configurações da API:**")
        
        if os.path.exists('.env'):
            st.success("✅ Arquivo .env encontrado")
            
            # Verificar conexão com DeepSeek
            if st.button("🔗 Testar Conexão DeepSeek"):
                try:
                    classifier = SessionClassifier()
                    st.success("✅ Conexão com DeepSeek estabelecida com sucesso!")
                    classifier.close()
                except Exception as e:
                    st.error(f"❌ Erro na conexão: {e}")
        else:
            st.error("❌ Arquivo .env não encontrado")
        
        # Logs e debug
        st.write("**🐛 Debug e Logs:**")
        
        if st.button("🔍 Verificar Integridade do Banco"):
            try:
                conn = sqlite3.connect("talqui.db")
                cursor = conn.cursor()
                
                # Verificar tabelas
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                st.write(f"Tabelas encontradas: {[table[0] for table in tables]}")
                
                # Verificar índices
                cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
                indexes = cursor.fetchall()
                st.write(f"Índices encontrados: {[idx[0] for idx in indexes if idx[0] is not None]}")
                
                conn.close()
                st.success("✅ Integridade do banco verificada")
                
            except Exception as e:
                st.error(f"❌ Erro na verificação: {e}")
    
    # Footer
    st.markdown("---")
    st.markdown("**🤖 Dashboard desenvolvido com Streamlit | Classificação powered by DeepSeek AI**")

if __name__ == "__main__":
    main()