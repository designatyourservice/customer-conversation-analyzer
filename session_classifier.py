#!/usr/bin/env python3
"""
Session Classifier using DeepSeek API
Classifica sessões de atendimento em categorias baseadas no conteúdo das mensagens
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import requests
from dotenv import load_dotenv
import pandas as pd

# Carregar variáveis de ambiente
load_dotenv()

class SessionClassifier:
    def __init__(self, db_path: str = "talqui.db"):
        self.db_path = db_path
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.base_url = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
        
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY não encontrada nas variáveis de ambiente")
        
        # Conectar ao banco SQLite
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
        # Criar tabela para armazenar classificações se não existir
        self.create_classification_table()
    
    def create_classification_table(self):
        """Cria tabela para armazenar classificações das sessões"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_classifications (
                sessionID TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                subcategory TEXT,
                confidence REAL,
                reasoning TEXT,
                classified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                messages_analyzed INTEGER,
                FOREIGN KEY (sessionID) REFERENCES talqui_unified(sessionID)
            )
        """)
        self.conn.commit()
    
    def get_session_messages(self, session_id: str) -> List[Dict]:
        """Extrai todas as mensagens de uma sessão específica"""
        cursor = self.conn.cursor()
        query = """
        SELECT 
            messageDirection,
            messageValue,
            messageKey,
            messageAutonomous,
            message_createdAt,
            operator_info
        FROM talqui_unified 
        WHERE sessionID = ? AND messageID IS NOT NULL
        ORDER BY message_createdAt ASC
        """
        
        cursor.execute(query, (session_id,))
        messages = []
        
        for row in cursor.fetchall():
            messages.append({
                'direction': row['messageDirection'],
                'content': row['messageValue'] or row['messageKey'] or '',
                'is_autonomous': bool(row['messageAutonomous']),
                'timestamp': row['message_createdAt'],
                'operator': row['operator_info']
            })
        
        return messages
    
    def get_sessions_to_classify(self, limit: int = 50) -> List[Dict]:
        """Obtém sessões que ainda não foram classificadas"""
        cursor = self.conn.cursor()
        query = """
        SELECT DISTINCT 
            s.sessionID,
            s.sessionKind,
            s.closeMotive,
            s.sessionDuration,
            s.sessionMessagesCount,
            s.operator_info,
            s.session_createdAt
        FROM talqui_unified s
        LEFT JOIN session_classifications sc ON s.sessionID = sc.sessionID
        WHERE sc.sessionID IS NULL 
          AND s.sessionMessagesCount > 0
        ORDER BY s.session_createdAt DESC
        LIMIT ?
        """
        
        cursor.execute(query, (limit,))
        sessions = []
        
        for row in cursor.fetchall():
            sessions.append({
                'sessionID': row['sessionID'],
                'sessionKind': row['sessionKind'],
                'closeMotive': row['closeMotive'],
                'duration': row['sessionDuration'],
                'messageCount': row['sessionMessagesCount'],
                'operator': row['operator_info'],
                'createdAt': row['session_createdAt']
            })
        
        return sessions
    
    def classify_session_with_deepseek(self, messages: List[Dict], session_info: Dict) -> Dict:
        """Classifica uma sessão usando a API do DeepSeek"""
        
        # Preparar contexto da sessão para o modelo
        conversation_text = self._format_conversation(messages)
        
        prompt = f"""
Você é um especialista em classificação de atendimento ao cliente. Analise a seguinte conversa e classifique-a em uma das categorias abaixo.

INFORMAÇÕES DA SESSÃO:
- Tipo: {session_info.get('sessionKind', 'N/A')}
- Duração: {session_info.get('duration', 0)} segundos
- Mensagens: {session_info.get('messageCount', 0)}
- Motivo de encerramento: {session_info.get('closeMotive', 'N/A')}
- Operador: {session_info.get('operator', 'N/A')}

CONVERSA:
{conversation_text}

CATEGORIAS DISPONÍVEIS:
1. COMERCIAL - Interesse em produtos, preços, planos, vendas
2. SUPORTE_TECNICO - Problemas técnicos, bugs, configurações
3. FINANCEIRO - Pagamentos, cobrança, faturas, reembolsos  
4. INFORMACAO - Dúvidas gerais, informações sobre serviços
5. RECLAMACAO - Insatisfação, problemas, críticas
6. CANCELAMENTO - Solicitação de cancelamento de serviços
7. OUTROS - Casos que não se encaixam nas categorias acima

Responda APENAS com um JSON no seguinte formato:
{{
    "category": "CATEGORIA_PRINCIPAL",
    "subcategory": "descrição mais específica",
    "confidence": 0.95,
    "reasoning": "breve explicação da classificação"
}}
"""

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'deepseek-chat',
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.1,
            'max_tokens': 500
        }
        
        try:
            response = requests.post(
                f'{self.base_url}/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"Erro na API DeepSeek: {response.status_code} - {response.text}")
                return None
            
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            # Tentar extrair JSON da resposta
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            
            try:
                classification = json.loads(content)
                return classification
            except json.JSONDecodeError:
                print(f"Erro ao decodificar JSON: {content}")
                return None
                
        except Exception as e:
            print(f"Erro na chamada da API: {e}")
            return None
    
    def _format_conversation(self, messages: List[Dict]) -> str:
        """Formata as mensagens em texto legível para análise"""
        conversation = []
        
        for msg in messages:
            direction = "CLIENTE" if msg['direction'] == 'inbound' else "ATENDENTE"
            autonomous = " (AUTOMÁTICO)" if msg.get('is_autonomous') else ""
            content = msg['content'][:500]  # Limitar tamanho
            
            if content.strip():
                conversation.append(f"{direction}{autonomous}: {content}")
        
        return "\n".join(conversation[:20])  # Limitar a 20 mensagens
    
    def save_classification(self, session_id: str, classification: Dict, messages_count: int):
        """Salva a classificação no banco de dados"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO session_classifications 
            (sessionID, category, subcategory, confidence, reasoning, messages_analyzed)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            classification.get('category'),
            classification.get('subcategory'),
            classification.get('confidence'),
            classification.get('reasoning'),
            messages_count
        ))
        self.conn.commit()
    
    def classify_sessions(self, batch_size: int = 10):
        """Classifica um lote de sessões"""
        sessions = self.get_sessions_to_classify(batch_size)
        print(f"Encontradas {len(sessions)} sessões para classificar")
        
        classified = 0
        errors = 0
        
        for session in sessions:
            try:
                print(f"\nClassificando sessão {session['sessionID']}...")
                
                # Obter mensagens da sessão
                messages = self.get_session_messages(session['sessionID'])
                
                if not messages:
                    print("Sessão sem mensagens válidas, pulando...")
                    continue
                
                # Classificar com DeepSeek
                classification = self.classify_session_with_deepseek(messages, session)
                
                if classification:
                    # Salvar classificação
                    self.save_classification(
                        session['sessionID'], 
                        classification, 
                        len(messages)
                    )
                    
                    print(f"✅ Classificada como: {classification['category']} "
                          f"(confiança: {classification.get('confidence', 'N/A')})")
                    classified += 1
                else:
                    print("❌ Falha na classificação")
                    errors += 1
                    
            except Exception as e:
                print(f"❌ Erro ao processar sessão {session['sessionID']}: {e}")
                errors += 1
        
        print(f"\n📊 Resumo: {classified} classificadas, {errors} erros")
    
    def get_classification_stats(self) -> Dict:
        """Obtém estatísticas das classificações"""
        cursor = self.conn.cursor()
        
        # Total de classificações por categoria
        cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM session_classifications 
            GROUP BY category 
            ORDER BY count DESC
        """)
        
        categories = dict(cursor.fetchall())
        
        # Estatísticas gerais
        cursor.execute("SELECT COUNT(*) FROM session_classifications")
        total_classified = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT sessionID) FROM talqui_unified WHERE sessionMessagesCount > 0")
        total_sessions = cursor.fetchone()[0]
        
        return {
            'total_classified': total_classified,
            'total_sessions': total_sessions,
            'progress_percent': (total_classified / total_sessions * 100) if total_sessions > 0 else 0,
            'categories': categories
        }
    
    def export_classifications_to_csv(self, filename: str = "session_classifications.csv"):
        """Exporta classificações para CSV"""
        query = """
        SELECT 
            sc.*,
            s.sessionKind,
            s.closeMotive,
            s.sessionDuration,
            s.operator_info,
            s.session_createdAt
        FROM session_classifications sc
        JOIN talqui_unified s ON sc.sessionID = s.sessionID
        GROUP BY sc.sessionID
        ORDER BY sc.classified_at DESC
        """
        
        df = pd.read_sql_query(query, self.conn)
        df.to_csv(filename, index=False)
        print(f"Classificações exportadas para {filename}")
    
    def close(self):
        """Fecha conexão com o banco"""
        self.conn.close()


def main():
    """Função principal"""
    print("🤖 Classificador de Sessões - DeepSeek AI")
    print("=" * 50)
    
    try:
        classifier = SessionClassifier()
        
        # Mostrar estatísticas atuais
        stats = classifier.get_classification_stats()
        print(f"📈 Progresso: {stats['total_classified']}/{stats['total_sessions']} "
              f"({stats['progress_percent']:.1f}%)")
        
        if stats['categories']:
            print("\n📊 Distribuição por categoria:")
            for category, count in stats['categories'].items():
                print(f"  {category}: {count}")
        
        # Classificar sessões
        print("\n🔄 Iniciando classificação...")
        classifier.classify_sessions(batch_size=5)  # Começar com lote pequeno
        
        # Estatísticas finais
        stats = classifier.get_classification_stats()
        print(f"\n✅ Total classificado: {stats['total_classified']} sessões")
        
        # Exportar resultados
        classifier.export_classifications_to_csv()
        
        classifier.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")


if __name__ == "__main__":
    main()