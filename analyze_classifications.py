#!/usr/bin/env python3
"""
Script para análise das classificações realizadas
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import json

def analyze_classifications(db_path: str = "talqui.db"):
    """Gera análises das classificações realizadas"""
    
    conn = sqlite3.connect(db_path)
    
    print("📊 Análise das Classificações de Sessões")
    print("=" * 50)
    
    # 1. Estatísticas gerais
    query = """
    SELECT 
        COUNT(*) as total_classified,
        AVG(confidence) as avg_confidence,
        MIN(confidence) as min_confidence,
        MAX(confidence) as max_confidence
    FROM session_classifications
    """
    
    stats = pd.read_sql_query(query, conn).iloc[0]
    print(f"✅ Total classificado: {stats['total_classified']}")
    print(f"🎯 Confiança média: {stats['avg_confidence']:.2f}")
    print(f"📉 Confiança mínima: {stats['min_confidence']:.2f}")
    print(f"📈 Confiança máxima: {stats['max_confidence']:.2f}")
    
    # 2. Distribuição por categorias
    print("\n🏷️ Distribuição por Categoria:")
    category_dist = pd.read_sql_query("""
        SELECT 
            category, 
            COUNT(*) as count,
            AVG(confidence) as avg_confidence,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM session_classifications), 2) as percentage
        FROM session_classifications 
        GROUP BY category 
        ORDER BY count DESC
    """, conn)
    
    for _, row in category_dist.iterrows():
        print(f"  {row['category']}: {row['count']} ({row['percentage']}%) - Conf: {row['avg_confidence']:.2f}")
    
    # 3. Top subcategorias
    print("\n🏷️ Top Subcategorias:")
    subcat_dist = pd.read_sql_query("""
        SELECT 
            category,
            subcategory, 
            COUNT(*) as count
        FROM session_classifications 
        WHERE subcategory IS NOT NULL
        GROUP BY category, subcategory 
        ORDER BY count DESC
        LIMIT 10
    """, conn)
    
    for _, row in subcat_dist.iterrows():
        print(f"  {row['category']} - {row['subcategory']}: {row['count']}")
    
    # 4. Análise temporal
    print("\n⏰ Classificações por Hora:")
    temporal = pd.read_sql_query("""
        SELECT 
            strftime('%H', classified_at) as hour,
            COUNT(*) as count
        FROM session_classifications 
        GROUP BY strftime('%H', classified_at)
        ORDER BY hour
    """, conn)
    
    for _, row in temporal.iterrows():
        print(f"  {row['hour']}h: {row['count']} classificações")
    
    # 5. Análise por operador
    print("\n👥 Top Operadores (por sessões classificadas):")
    operator_stats = pd.read_sql_query("""
        SELECT 
            s.operator_info,
            sc.category,
            COUNT(*) as count
        FROM session_classifications sc
        JOIN talqui_unified s ON sc.sessionID = s.sessionID
        WHERE s.operator_info IS NOT NULL
        GROUP BY s.operator_info, sc.category
        ORDER BY count DESC
        LIMIT 15
    """, conn)
    
    for _, row in operator_stats.iterrows():
        print(f"  {row['operator_info']} - {row['category']}: {row['count']}")
    
    # 6. Correlação com duração de sessão
    print("\n⏱️ Análise por Duração de Sessão:")
    duration_analysis = pd.read_sql_query("""
        SELECT 
            sc.category,
            AVG(s.sessionDuration) as avg_duration,
            COUNT(*) as count
        FROM session_classifications sc
        JOIN talqui_unified s ON sc.sessionID = s.sessionID
        WHERE s.sessionDuration IS NOT NULL
        GROUP BY sc.category
        ORDER BY avg_duration DESC
    """, conn)
    
    for _, row in duration_analysis.iterrows():
        avg_minutes = row['avg_duration'] / 60 if row['avg_duration'] else 0
        print(f"  {row['category']}: {avg_minutes:.1f} min média ({row['count']} sessões)")
    
    # 7. Motivos de encerramento por categoria
    print("\n🔚 Motivos de Encerramento por Categoria:")
    closure_analysis = pd.read_sql_query("""
        SELECT 
            sc.category,
            s.closeMotive,
            COUNT(*) as count
        FROM session_classifications sc
        JOIN talqui_unified s ON sc.sessionID = s.sessionID
        WHERE s.closeMotive IS NOT NULL
        GROUP BY sc.category, s.closeMotive
        ORDER BY sc.category, count DESC
    """, conn)
    
    current_category = None
    for _, row in closure_analysis.iterrows():
        if row['category'] != current_category:
            print(f"\n  {row['category']}:")
            current_category = row['category']
        print(f"    {row['closeMotive']}: {row['count']}")
    
    # 8. Exemplos de classificações com baixa confiança
    print("\n⚠️ Classificações com Baixa Confiança (<0.8):")
    low_confidence = pd.read_sql_query("""
        SELECT 
            sc.sessionID,
            sc.category,
            sc.subcategory,
            sc.confidence,
            sc.reasoning,
            s.sessionDuration,
            s.sessionMessagesCount
        FROM session_classifications sc
        JOIN talqui_unified s ON sc.sessionID = s.sessionID
        WHERE sc.confidence < 0.8
        ORDER BY sc.confidence ASC
        LIMIT 5
    """, conn)
    
    for _, row in low_confidence.iterrows():
        print(f"  {row['sessionID'][:8]}... - {row['category']} ({row['confidence']:.2f})")
        print(f"    Razão: {row['reasoning'][:100]}...")
    
    conn.close()
    
    return {
        'total_classified': int(stats['total_classified']),
        'avg_confidence': float(stats['avg_confidence']),
        'category_distribution': category_dist.to_dict('records'),
        'operator_stats': operator_stats.to_dict('records')
    }

def export_analysis_report(db_path: str = "talqui.db"):
    """Exporta relatório completo para CSV"""
    
    conn = sqlite3.connect(db_path)
    
    # Relatório detalhado
    detailed_report = pd.read_sql_query("""
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
            s.closedAt,
            CASE 
                WHEN s.sessionDuration > 0 THEN s.sessionMessagesCount * 1.0 / (s.sessionDuration / 60.0)
                ELSE NULL 
            END as messages_per_minute
        FROM session_classifications sc
        JOIN talqui_unified s ON sc.sessionID = s.sessionID
        ORDER BY sc.classified_at DESC
    """, conn)
    
    filename = f"classification_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    detailed_report.to_csv(filename, index=False)
    print(f"\n📄 Relatório detalhado exportado: {filename}")
    
    conn.close()

if __name__ == "__main__":
    results = analyze_classifications()
    export_analysis_report()
    
    print(f"\n🎉 Análise concluída!")
    print(f"📊 {results['total_classified']} sessões analisadas com confiança média de {results['avg_confidence']:.2f}")