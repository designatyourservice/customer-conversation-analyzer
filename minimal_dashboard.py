#!/usr/bin/env python3
"""
Dashboard Minimal para classificação de sessões - Sem cache
"""

import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Classificação de Sessões",
    page_icon="🤖",
    layout="wide"
)

def get_database_stats():
    """Obtém estatísticas básicas do banco"""
    db_path = "/Users/thomazkrause/workspace/python-apps/dog-food/talqui.db"
    
    if not os.path.exists(db_path):
        return {"error": f"Banco não encontrado: {db_path}"}
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Total de sessões
        cursor.execute("SELECT COUNT(DISTINCT sessionID) FROM talqui_unified WHERE sessionMessagesCount > 0")
        total_sessions = cursor.fetchone()[0]
        
        # Verificar se tabela de classificações existe
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='session_classifications'")
        has_classifications_table = cursor.fetchone()[0] > 0
        
        classified_count = 0
        if has_classifications_table:
            cursor.execute("SELECT COUNT(*) FROM session_classifications")
            classified_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_sessions": total_sessions,
            "classified_count": classified_count,
            "has_classifications_table": has_classifications_table,
            "progress_percent": (classified_count / total_sessions * 100) if total_sessions > 0 else 0
        }
        
    except Exception as e:
        return {"error": str(e)}

def get_classifications():
    """Obtém dados das classificações"""
    db_path = "/Users/thomazkrause/workspace/python-apps/dog-food/talqui.db"
    
    try:
        conn = sqlite3.connect(db_path)
        
        query = """
        SELECT 
            sessionID,
            category,
            subcategory,
            confidence,
            classified_at
        FROM session_classifications
        ORDER BY classified_at DESC
        LIMIT 100
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao carregar classificações: {e}")
        return pd.DataFrame()

def main():
    """Função principal"""
    
    st.title("🤖 Dashboard - Classificação de Sessões")
    st.markdown("Sistema de classificação automática usando DeepSeek AI")
    
    # Obter estatísticas
    stats = get_database_stats()
    
    if "error" in stats:
        st.error(f"Erro: {stats['error']}")
        st.stop()
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total de Sessões", f"{stats['total_sessions']:,}")
    
    with col2:
        st.metric("✅ Classificadas", f"{stats['classified_count']:,}")
    
    with col3:
        remaining = stats['total_sessions'] - stats['classified_count']
        st.metric("⏳ Restantes", f"{remaining:,}")
    
    with col4:
        st.metric("📈 Progresso", f"{stats['progress_percent']:.1f}%")
    
    # Verificar se há classificações
    if not stats['has_classifications_table'] or stats['classified_count'] == 0:
        st.info("📝 Nenhuma classificação encontrada ainda.")
        
        st.markdown("### 🚀 Para começar a classificar:")
        st.code("python3 session_classifier.py")
        
        if st.button("🔄 Verificar Novamente"):
            st.experimental_rerun()
        
        return
    
    # Mostrar dados das classificações
    st.subheader("📋 Últimas Classificações")
    
    df = get_classifications()
    
    if not df.empty:
        # Estatísticas rápidas
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Distribuição por Categoria:**")
            if 'category' in df.columns:
                category_counts = df['category'].value_counts()
                for category, count in category_counts.head(5).items():
                    st.write(f"• {category}: {count}")
        
        with col2:
            st.write("**Estatísticas:**")
            if 'confidence' in df.columns:
                avg_conf = df['confidence'].mean()
                min_conf = df['confidence'].min()
                max_conf = df['confidence'].max()
                
                st.write(f"• Confiança média: {avg_conf:.2f}")
                st.write(f"• Confiança mín/máx: {min_conf:.2f} / {max_conf:.2f}")
        
        # Tabela de dados
        st.dataframe(df, use_container_width=True, height=400)
        
        # Download
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"classificacoes_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
    
    # Estimativa de custos
    if remaining > 0:
        st.subheader("💰 Estimativa de Custos")
        
        avg_cost_per_session = 0.00009
        total_cost = remaining * avg_cost_per_session
        
        st.info(f"""
        **Sessões restantes:** {remaining:,}
        **Custo estimado:** ${total_cost:.4f} USD
        **Por sessão:** ${avg_cost_per_session:.6f} USD
        """)
    
    # Botões de ação
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Atualizar Dados", type="primary"):
            st.experimental_rerun()
    
    with col2:
        st.markdown("**Para executar classificações:**")
        st.code("python3 session_classifier.py")

if __name__ == "__main__":
    main()