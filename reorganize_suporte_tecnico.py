#!/usr/bin/env python3
"""
Script para reorganizar subcategorias de SUPORTE_TECNICO
Cria 10 subcategorias principais baseadas nos padrões mais comuns
"""

import sqlite3
import re
from datetime import datetime

class SuporteReorganizer:
    def __init__(self):
        self.db_path = 'talqui.db'
        
        # Mapeamento de palavras-chave para novas subcategorias
        self.category_mapping = {
            'problemas de acesso/login': [
                'acesso', 'login', 'entrar', 'conta', 'senha', 'bloqueio', 'liberação'
            ],
            'problemas de integração': [
                'integração', 'api', 'webhook', 'conexão', 'sgp', 'ixc', 'ifood', 'marketplace'
            ],
            'problemas de mensagens/whatsapp': [
                'mensagem', 'whatsapp', 'envio', 'recebimento', 'entrega', 'disparo'
            ],
            'problemas de configuração': [
                'configuração', 'configurar', 'setup', 'atalho', 'personalização', 'ajuste'
            ],
            'problemas de funcionamento/sistema': [
                'funcionamento', 'sistema', 'plataforma', 'erro', 'bug', 'falha', 'travou'
            ],
            'problemas com chatbot/automação': [
                'chatbot', 'bot', 'robô', 'automação', 'fluxo', 'resposta automática'
            ],
            'migração/mudanças técnicas': [
                'migração', 'migrar', 'mudança', 'transferência', 'host', 'ip', 'servidor'
            ],
            'problemas de cobrança/boletos': [
                'boleto', 'cobrança', 'fatura', 'pagamento', 'financeiro'
            ],
            'suporte técnico geral': [
                'suporte', 'ajuda', 'orientação', 'dúvida técnica', 'esclarecimento'
            ]
        }
    
    def classify_subcategory(self, original_summary):
        """Classifica a subcategoria original em uma das 9 categorias principais"""
        summary_lower = original_summary.lower()
        
        for new_category, keywords in self.category_mapping.items():
            for keyword in keywords:
                if keyword in summary_lower:
                    return new_category
        
        return 'outros'
    
    def reorganize_suporte_tecnico(self):
        """Reorganiza todas as subcategorias de SUPORTE_TECNICO"""
        
        print("🔧 REORGANIZANDO SUPORTE_TÉCNICO")
        print("=" * 50)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Backup
        backup_name = f"session_classifications_backup_suporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        cursor.execute(f"CREATE TABLE {backup_name} AS SELECT * FROM session_classifications")
        print(f"✅ Backup criado: {backup_name}")
        
        # Buscar todas as sessões de SUPORTE_TECNICO
        cursor.execute("""
            SELECT sessionID, summary, subcategory
            FROM session_classifications 
            WHERE category = 'SUPORTE_TECNICO'
        """)
        
        sessions = cursor.fetchall()
        print(f"📊 Total de sessões a reorganizar: {len(sessions)}")
        
        # Contador para novas categorias
        new_categories = {}
        updated_count = 0
        
        # Processar cada sessão
        for session_id, summary, current_subcat in sessions:
            new_subcat = self.classify_subcategory(summary)
            
            # Contar distribuição
            if new_subcat not in new_categories:
                new_categories[new_subcat] = 0
            new_categories[new_subcat] += 1
            
            # Atualizar se mudou
            if new_subcat != current_subcat:
                cursor.execute("""
                    UPDATE session_classifications 
                    SET subcategory = ? 
                    WHERE sessionID = ? AND category = 'SUPORTE_TECNICO'
                """, (new_subcat, session_id))
                updated_count += 1
        
        conn.commit()
        
        print(f"\n📈 NOVA DISTRIBUIÇÃO DE SUPORTE_TÉCNICO:")
        print("-" * 50)
        
        total_sessions = sum(new_categories.values())
        for category, count in sorted(new_categories.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_sessions) * 100
            print(f"{category:35} | {count:3d} ({percentage:5.1f}%)")
        
        print(f"\n🎉 REORGANIZAÇÃO CONCLUÍDA!")
        print(f"📊 Sessões atualizadas: {updated_count:,}")
        print(f"📊 Total de subcategorias: {len(new_categories)}")
        print(f"💾 Backup: {backup_name}")
        
        conn.close()
        
        # Exportar dados atualizados
        self.export_updated_data()
    
    def export_updated_data(self):
        """Exporta dados atualizados para CSV"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Exportar dados completos atualizados
        cursor.execute("""
            SELECT sessionID, category, subcategory, confidence, reasoning, 
                   classified_at, messages_analyzed, summary
            FROM session_classifications 
            ORDER BY category, subcategory
        """)
        
        import csv
        filename = f"FINAL_ALL_CLASSIFICATIONS_SUPORTE_REORGANIZED.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow(['sessionID', 'category', 'subcategory', 'confidence', 
                           'reasoning', 'classified_at', 'messages_analyzed', 'summary'])
            
            # Data
            for row in cursor.fetchall():
                writer.writerow(row)
        
        conn.close()
        
        print(f"📄 Arquivo exportado: {filename}")
        
        # Estatísticas do arquivo
        with open(filename, 'r') as f:
            total_lines = sum(1 for line in f) - 1  # -1 for header
        
        print(f"📊 Total de registros exportados: {total_lines:,}")

def main():
    reorganizer = SuporteReorganizer()
    reorganizer.reorganize_suporte_tecnico()

if __name__ == "__main__":
    main()