#!/usr/bin/env python3
"""
Dashboard Streamlit Simplificado para classificação de sessões
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime
import os

# Configuração da página
st.set_page_config(
    page_title="Dashboard - Classificação de Sessões",
    page_icon="🤖",
    layout="wide"
)

def load_data():
    """Carrega dados do banco SQLite"""
    db_path = "/Users/thomazkrause/workspace/python-apps/dog-food/talqui.db"
    
    if not os.path.exists(db_path):
        st.error(f"Banco de dados não encontrado: {db_path}")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Verificar se tabela de classificações existe
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='session_classifications';")
        if not cursor.fetchone():
            st.warning("Tabela de classificações não encontrada. Execute algumas classificações primeiro.")
            conn.close()
            return {'classifications': pd.DataFrame(), 'has_data': False}
        
        # Carregar classificações
        classifications_query = """
        SELECT 
            sc.*,
            s.operator_info,
            s.sessionDuration,
            s.sessionMessagesCount,
            s.closeMotive
        FROM session_classifications sc
        LEFT JOIN (
            SELECT DISTINCT sessionID, operator_info, sessionDuration, sessionMessagesCount, closeMotive
            FROM talqui_unified
        ) s ON sc.sessionID = s.sessionID
        ORDER BY sc.classified_at DESC
        """
        
        classifications_df = pd.read_sql_query(classifications_query, conn)
        
        # Estatísticas gerais
        cursor.execute("SELECT COUNT(DISTINCT sessionID) FROM talqui_unified WHERE sessionMessagesCount > 0")
        total_sessions = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'classifications': classifications_df,
            'total_sessions': total_sessions,
            'has_data': len(classifications_df) > 0
        }
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

def main():
    """Função principal do dashboard"""
    
    # Header
    st.title("🤖 Dashboard - Classificação de Sessões")
    st.markdown("**Sistema de classificação automática usando DeepSeek AI**")
    
    # Carregar dados
    with st.spinner("Carregando dados..."):
        data = load_data()
    
    if not data:
        st.stop()
    
    # Verificar se há dados
    if not data['has_data']:
        st.info("📝 Nenhuma classificação encontrada ainda.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📊 Total de Sessões", data.get('total_sessions', 0))
        with col2:
            st.metric("✅ Classificadas", 0)
            
        st.markdown("### 🚀 Para começar:")
        st.code("python3 session_classifier.py")
        st.markdown("Ou execute classificações via linha de comando e recarregue esta página.")
        
        if st.button("🔄 Recarregar"):
            st.experimental_rerun()
        
        return
    
    # Dados disponíveis
    df = data['classifications']
    total_sessions = data['total_sessions']
    classified_count = len(df)
    progress_percent = (classified_count / total_sessions * 100) if total_sessions > 0 else 0
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total de Sessões", f"{total_sessions:,}")
    
    with col2:
        st.metric("✅ Classificadas", f"{classified_count:,}", delta=f"{progress_percent:.1f}%")
    
    with col3:
        st.metric("⏳ Restantes", f"{total_sessions - classified_count:,}")
    
    with col4:
        avg_confidence = df['confidence'].mean() if 'confidence' in df.columns else 0
        st.metric("🎯 Confiança Média", f"{avg_confidence:.1%}" if avg_confidence > 0 else "N/A")
    
    # Abas
    tab1, tab2, tab3 = st.tabs(["📈 Visão Geral", "🔍 Dados Detalhados", "💰 Custos"])
    
    with tab1:
        st.subheader("📈 Distribuição por Categoria")
        
        if 'category' in df.columns:
            # Gráfico de categoria
            category_counts = df['category'].value_counts()
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                fig = px.pie(
                    values=category_counts.values,
                    names=category_counts.index,
                    title="Classificações por Categoria"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.write("**Resumo:**")
                for category, count in category_counts.items():
                    percentage = (count / len(df)) * 100
                    st.write(f"• **{category}**: {count} ({percentage:.1f}%)")
        
        # Confiança das classificações
        if 'confidence' in df.columns:
            st.subheader("🎯 Distribuição de Confiança")
            
            fig_conf = px.histogram(
                df,
                x='confidence',
                nbins=20,
                title="Níveis de Confiança das Classificações"
            )
            st.plotly_chart(fig_conf, use_container_width=True)
    
    with tab2:
        st.subheader("🔍 Dados Detalhados")
        
        # Filtros simples
        if 'category' in df.columns:
            categories = st.multiselect(
                "Filtrar por Categoria:",
                options=df['category'].unique(),
                default=[]
            )
            
            if categories:
                df_filtered = df[df['category'].isin(categories)]
            else:
                df_filtered = df
        else:
            df_filtered = df
        
        # Mostrar dados
        st.dataframe(df_filtered, use_container_width=True)
        
        # Download
        if not df_filtered.empty:
            csv = df_filtered.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"classificacoes_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
    
    with tab3:
        st.subheader("💰 Estimativa de Custos")
        
        remaining = total_sessions - classified_count
        
        if remaining > 0:
            # Estimativa simples baseada em médias
            avg_cost_per_session = 0.00009  # Baseado nos testes
            
            st.info(f"""
            **Sessões restantes para classificar:** {remaining:,}
            
            **Estimativa de custo:** ${remaining * avg_cost_per_session:.4f} USD
            
            **Custo por sessão:** ${avg_cost_per_session:.6f} USD
            """)
            
            # Calculadora
            st.subheader("🧮 Calculadora de Custo")
            custom_volume = st.number_input(
                "Quantidade de sessões:",
                min_value=1,
                max_value=remaining,
                value=min(100, remaining)
            )
            
            estimated_cost = custom_volume * avg_cost_per_session
            st.success(f"**Custo estimado para {custom_volume} sessões:** ${estimated_cost:.4f} USD")
            
        else:
            st.success("✅ Todas as sessões foram classificadas!")
    
    # Botão de refresh
    if st.button("🔄 Atualizar Dados"):
        st.experimental_rerun()
    
    # Instruções
    st.markdown("---")
    st.markdown("### 🚀 Para executar mais classificações:")
    st.code("python3 session_classifier.py")
    st.markdown("Ou use os scripts em lote para processar várias sessões de uma vez.")

if __name__ == "__main__":
    main()