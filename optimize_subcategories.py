#!/usr/bin/env python3
"""
Script otimizado para reduzir subcategorias para máximo 10 por categoria
Processa sem usar API externa para ser mais rápido
"""

import sqlite3
from datetime import datetime
from collections import Counter

class SubcategoryOptimizer:
    def __init__(self):
        self.db_path = 'talqui.db'
        
    def analyze_and_optimize(self):
        """Analisa e otimiza subcategorias automaticamente"""
        
        print("🚀 OTIMIZADOR DE SUBCATEGORIAS")
        print("=" * 50)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Backup
        backup_name = f"session_classifications_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        cursor.execute(f"CREATE TABLE {backup_name} AS SELECT * FROM session_classifications")
        print(f"✅ Backup criado: {backup_name}")
        
        # Adicionar coluna summary se não existir
        try:
            cursor.execute("ALTER TABLE session_classifications ADD COLUMN summary TEXT")
            cursor.execute("UPDATE session_classifications SET summary = subcategory WHERE summary IS NULL")
            print("✅ Coluna 'summary' criada e populada")
        except sqlite3.OperationalError:
            print("⚠️  Coluna 'summary' já existe")
        
        categories = ['COMERCIAL', 'SUPORTE_TECNICO', 'FINANCEIRO', 'INFORMACAO', 'RECLAMACAO', 'CANCELAMENTO', 'OUTROS']
        
        total_optimized = 0
        
        for category in categories:
            print(f"\n🔄 Processando: {category}")
            
            # Buscar todas as subcategorias da categoria
            cursor.execute("""
                SELECT subcategory, COUNT(*) as count 
                FROM session_classifications 
                WHERE category = ? 
                GROUP BY subcategory 
                ORDER BY count DESC
            """, (category,))
            
            subcats = cursor.fetchall()
            
            if len(subcats) <= 10:
                print(f"  ✅ Já otimizada ({len(subcats)} subcategorias)")
                continue
                
            # Top 9 subcategorias (reservamos 1 spot para "outros")
            top_9 = [sub[0] for sub in subcats[:9]]
            
            print(f"  📊 {len(subcats)} → 10 subcategorias")
            print(f"  🏆 Top 9 mantidas:")
            
            for i, (subcat, count) in enumerate(subcats[:9], 1):
                print(f"    {i}. {subcat[:50]}... ({count})")
            
            # Reclassificar todas as outras para "outros"
            others_count = 0
            for subcat, count in subcats[9:]:
                cursor.execute("""
                    UPDATE session_classifications 
                    SET subcategory = 'outros' 
                    WHERE category = ? AND subcategory = ?
                """, (category, subcat))
                
                others_count += count
                total_optimized += count
            
            print(f"  🔄 {len(subcats) - 9} subcategorias → 'outros' ({others_count} sessões)")
        
        conn.commit()
        conn.close()
        
        print(f"\n🎉 OTIMIZAÇÃO CONCLUÍDA!")
        print(f"📊 Total de sessões reclassificadas: {total_optimized:,}")
        print(f"💾 Backup salvo: {backup_name}")
        
        # Mostrar estatísticas finais
        self.show_final_stats()
    
    def show_final_stats(self):
        """Mostra estatísticas finais"""
        
        print(f"\n📈 ESTATÍSTICAS FINAIS:")
        print("=" * 50)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT category, 
                   COUNT(DISTINCT subcategory) as subcats_count,
                   COUNT(*) as sessions_count
            FROM session_classifications 
            GROUP BY category 
            ORDER BY subcats_count DESC
        """)
        
        for category, subcats, sessions in cursor.fetchall():
            status = "✅" if subcats <= 10 else "⚠️"
            print(f"{status} {category:15} | {subcats:2d} subcategorias | {sessions:4d} sessões")
        
        # Mostrar distribuição de "outros"
        print(f"\n📋 DISTRIBUIÇÃO DE 'OUTROS':")
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM session_classifications 
            WHERE subcategory = 'outros'
            GROUP BY category 
            ORDER BY count DESC
        """)
        
        for category, count in cursor.fetchall():
            cursor.execute("SELECT COUNT(*) FROM session_classifications WHERE category = ?", (category,))
            total = cursor.fetchone()[0]
            percentage = (count / total) * 100
            print(f"  {category:15} | {count:3d} sessões ({percentage:4.1f}%)")
        
        conn.close()

def main():
    optimizer = SubcategoryOptimizer()
    optimizer.analyze_and_optimize()

if __name__ == "__main__":
    main()