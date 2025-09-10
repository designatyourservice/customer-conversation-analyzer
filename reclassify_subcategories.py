#!/usr/bin/env python3
"""
Script para reclassificar subcategorias usando DeepSeek AI
Reduz subcategorias para máximo 10 por categoria principal
"""

import sqlite3
import json
import time
from datetime import datetime
from session_classifier import SessionClassifier

class SubcategoryReclassifier:
    def __init__(self):
        self.db_path = 'talqui.db'
        self.classifier = SessionClassifier()
        
    def analyze_current_subcategories(self):
        """Analisa subcategorias atuais e retorna top 10 por categoria"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        categories = ['COMERCIAL', 'SUPORTE_TECNICO', 'FINANCEIRO', 'INFORMACAO', 'RECLAMACAO', 'CANCELAMENTO', 'OUTROS']
        result = {}
        
        for category in categories:
            cursor.execute("""
                SELECT subcategory, COUNT(*) as count 
                FROM session_classifications 
                WHERE category = ? 
                GROUP BY subcategory 
                ORDER BY count DESC
                LIMIT 15
            """, (category,))
            
            subcats = cursor.fetchall()
            result[category] = {
                'top_10': [sub[0] for sub in subcats[:10]],
                'total_count': len(subcats),
                'sessions': sum(sub[1] for sub in subcats)
            }
            
            print(f"\n📊 {category} ({result[category]['total_count']} subcategorias):")
            for i, (subcat, count) in enumerate(subcats[:10], 1):
                print(f"  {i:2d}. {subcat[:60]}... ({count})")
                
        conn.close()
        return result
    
    def create_reclassification_prompt(self, category, original_subcategory, top_10_subcats):
        """Cria prompt para reclassificação usando DeepSeek"""
        
        top_10_list = "\n".join([f"- {sub}" for sub in top_10_subcats])
        
        prompt = f"""
Você é um especialista em classificação de atendimento ao cliente. 

TAREFA: Reclassificar a subcategoria abaixo para uma das TOP 10 subcategorias mais comuns da categoria {category}.

SUBCATEGORIA ORIGINAL: {original_subcategory}
CATEGORIA PRINCIPAL: {category}

TOP 10 SUBCATEGORIAS MAIS COMUNS EM {category}:
{top_10_list}

REGRAS:
1. Escolha a subcategoria das TOP 10 que melhor representa o significado da subcategoria original
2. Se nenhuma das TOP 10 for adequada, use "outros"
3. Mantenha o contexto e significado original
4. Responda APENAS com o nome da subcategoria escolhida (ou "outros")
5. NÃO adicione explicações ou comentários

RESPOSTA:"""

        return prompt.strip()
    
    def reclassify_with_deepseek(self, category, original_subcategory, top_10_subcats):
        """Reclassifica usando DeepSeek API"""
        
        prompt = self.create_reclassification_prompt(category, original_subcategory, top_10_subcats)
        
        try:
            import requests
            import json
            import os
            
            # Configurar API
            api_key = os.getenv('DEEPSEEK_API_KEY', 'sk-3f7defc831b542b0a05b4c17ce49b8b1')
            base_url = 'https://api.deepseek.com/v1'
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'deepseek-chat',
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.1,
                'max_tokens': 100
            }
            
            response = requests.post(
                f'{base_url}/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                new_subcategory = result['choices'][0]['message']['content'].strip().lower()
                
                # Validar se a resposta está nas top 10 ou é "outros"
                valid_options = [opt.lower() for opt in top_10_subcats] + ['outros']
                
                for valid_opt in valid_options:
                    if valid_opt in new_subcategory or new_subcategory in valid_opt:
                        return valid_opt if valid_opt != 'outros' else 'outros'
                
                return 'outros'
            else:
                print(f"Erro API: {response.status_code}")
                return 'outros'
                    
        except Exception as e:
            print(f"Erro na API: {e}")
            return 'outros'
            
        return 'outros'
    
    def backup_current_data(self):
        """Faz backup dos dados atuais"""
        conn = sqlite3.connect(self.db_path)
        
        # Backup da tabela atual
        backup_name = f"session_classifications_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        conn.execute(f"""
            CREATE TABLE {backup_name} AS 
            SELECT * FROM session_classifications
        """)
        
        conn.commit()
        conn.close()
        print(f"✅ Backup criado: {backup_name}")
        return backup_name
    
    def add_summary_column(self):
        """Adiciona coluna summary e copia subcategory atual"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Adicionar coluna summary
            cursor.execute("ALTER TABLE session_classifications ADD COLUMN summary TEXT")
            
            # Copiar subcategory atual para summary
            cursor.execute("UPDATE session_classifications SET summary = subcategory")
            
            conn.commit()
            print("✅ Coluna 'summary' adicionada e populada")
            
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("⚠️  Coluna 'summary' já existe")
            else:
                raise e
                
        conn.close()
    
    def run_reclassification(self, limit=None, start_after=None):
        """Executa a reclassificação completa"""
        
        print("🚀 INICIANDO RECLASSIFICAÇÃO DE SUBCATEGORIAS")
        print("=" * 60)
        
        # Análise inicial
        top_subcats = self.analyze_current_subcategories()
        
        # Backup
        backup_name = self.backup_current_data()
        
        # Adicionar coluna summary
        self.add_summary_column()
        
        # Processar reclassificação
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Buscar registros únicos de subcategoria por categoria
        query = """
            SELECT DISTINCT category, subcategory
            FROM session_classifications 
            WHERE subcategory NOT IN (
                SELECT subcategory FROM session_classifications 
                WHERE category = ? 
                GROUP BY subcategory 
                ORDER BY COUNT(*) DESC 
                LIMIT 10
            )
        """
        
        total_processed = 0
        total_changed = 0
        
        for category in top_subcats.keys():
            print(f"\n🔄 Processando categoria: {category}")
            
            # Buscar subcategorias que não estão no top 10
            cursor.execute("""
                SELECT DISTINCT subcategory, COUNT(*) as count
                FROM session_classifications 
                WHERE category = ?
                GROUP BY subcategory
                ORDER BY count ASC
            """, (category,))
            
            all_subcats = cursor.fetchall()
            top_10_subcats = top_subcats[category]['top_10']
            
            # Identificar subcategorias para reclassificar (fora do top 10)
            subcats_to_reclassify = []
            for subcat, count in all_subcats:
                if subcat not in top_10_subcats:
                    subcats_to_reclassify.append((subcat, count))
            
            print(f"  📋 {len(subcats_to_reclassify)} subcategorias para reclassificar")
            
            # Processar cada subcategoria
            for original_subcat, count in subcats_to_reclassify:
                if limit and total_processed >= limit:
                    break
                    
                if start_after and original_subcat <= start_after:
                    continue
                
                print(f"  🔄 {original_subcat[:50]}... ({count} sessões)")
                
                # Reclassificar usando DeepSeek
                new_subcat = self.reclassify_with_deepseek(category, original_subcat, top_10_subcats)
                
                if new_subcat != original_subcat:
                    # Atualizar no banco
                    cursor.execute("""
                        UPDATE session_classifications 
                        SET subcategory = ? 
                        WHERE category = ? AND subcategory = ?
                    """, (new_subcat, category, original_subcat))
                    
                    total_changed += cursor.rowcount
                    print(f"    ✅ → {new_subcat} ({cursor.rowcount} registros)")
                else:
                    print(f"    ⚪ Mantido original")
                
                total_processed += 1
                time.sleep(0.5)  # Rate limiting
                
                if total_processed % 10 == 0:
                    conn.commit()  # Commit periódico
            
            if limit and total_processed >= limit:
                break
        
        conn.commit()
        conn.close()
        
        print(f"\n🎉 RECLASSIFICAÇÃO CONCLUÍDA!")
        print(f"📊 Processadas: {total_processed}")
        print(f"🔄 Alteradas: {total_changed}")
        print(f"💾 Backup: {backup_name}")
        
        # Análise final
        self.show_final_stats()
    
    def show_final_stats(self):
        """Mostra estatísticas finais após reclassificação"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print(f"\n📈 ESTATÍSTICAS FINAIS:")
        print("=" * 50)
        
        cursor.execute("""
            SELECT category, 
                   COUNT(DISTINCT subcategory) as subcats_count,
                   COUNT(*) as sessions_count
            FROM session_classifications 
            GROUP BY category 
            ORDER BY subcats_count DESC
        """)
        
        for category, subcats, sessions in cursor.fetchall():
            print(f"{category:15} | {subcats:3d} subcategorias | {sessions:4d} sessões")
        
        conn.close()

def main():
    print("🤖 RECLASSIFICADOR DE SUBCATEGORIAS")
    print("Usando DeepSeek AI para otimizar subcategorias")
    print()
    
    reclassifier = SubcategoryReclassifier()
    
    # Executar reclassificação
    # Para teste inicial, processa apenas 50 registros
    reclassifier.run_reclassification(limit=50)
    
    # Para execução completa, use:
    # reclassifier.run_reclassification()

if __name__ == "__main__":
    main()