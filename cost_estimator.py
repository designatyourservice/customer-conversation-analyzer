#!/usr/bin/env python3
"""
Estimador de custos para classificação de sessões usando DeepSeek API
"""

import tiktoken
from typing import Dict, List
import sqlite3
from datetime import datetime

class DeepSeekCostEstimator:
    """Estimador de custos para a API DeepSeek"""
    
    # Preços DeepSeek API (por 1M tokens) - atualizar conforme tabela oficial
    PRICING = {
        'deepseek-chat': {
            'input': 0.14,   # USD per 1M input tokens
            'output': 0.28   # USD per 1M output tokens
        }
    }
    
    def __init__(self, db_path: str = "talqui.db"):
        self.db_path = db_path
        self.encoder = tiktoken.get_encoding("cl100k_base")  # Encoding similar ao GPT
        
    def estimate_tokens_per_session(self, session_messages: List[Dict]) -> Dict[str, int]:
        """Estima tokens para uma sessão específica"""
        
        # Construir prompt base
        base_prompt = """
Você é um especialista em classificação de atendimento ao cliente. Analise a seguinte conversa e classifique-a em uma das categorias abaixo.

INFORMAÇÕES DA SESSÃO:
- Tipo: transactional
- Duração: 15000 segundos
- Mensagens: 10
- Motivo de encerramento: INACTIVITY
- Operador: Alison

CONVERSA:
"""
        
        categories_info = """
CATEGORIAS DISPONÍVEIS:
1. COMERCIAL - Interesse em produtos, preços, planos, vendas
2. SUPORTE_TECNICO - Problemas técnicos, bugs, configurações
3. FINANCEIRO - Pagamentos, cobrança, faturas, reembolsos  
4. INFORMACAO - Dúvidas gerais, informações sobre serviços
5. RECLAMACAO - Insatisfação, problemas, críticas
6. CANCELAMENTO - Solicitação de cancelamento de serviços
7. OUTROS - Casos que não se encaixam nas categorias acima

Responda APENAS com um JSON no seguinte formato:
{
    "category": "CATEGORIA_PRINCIPAL",
    "subcategory": "descrição mais específica",
    "confidence": 0.95,
    "reasoning": "breve explicação da classificação"
}
"""
        
        # Formatar mensagens da sessão
        conversation_text = ""
        for msg in session_messages[:20]:  # Limitar a 20 mensagens
            direction = "CLIENTE" if msg.get('direction') == 'inbound' else "ATENDENTE"
            content = (msg.get('content', '') or '')[:500]  # Limitar tamanho
            if content.strip():
                conversation_text += f"{direction}: {content}\n"
        
        # Prompt completo
        full_prompt = base_prompt + conversation_text + "\n" + categories_info
        
        # Estimar tokens
        input_tokens = len(self.encoder.encode(full_prompt))
        
        # Resposta típica (JSON estruturado)
        expected_output = '{"category": "SUPORTE_TECNICO", "subcategory": "configuração de sistema", "confidence": 0.92, "reasoning": "Cliente reportou problemas de configuração e recebeu suporte técnico"}'
        output_tokens = len(self.encoder.encode(expected_output))
        
        return {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens
        }
    
    def get_sample_sessions(self, sample_size: int = 10) -> List[Dict]:
        """Obtém amostra de sessões para estimativa"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Buscar sessões com diferentes tamanhos de mensagens
        query = """
        SELECT DISTINCT 
            sessionID, 
            sessionMessagesCount,
            sessionDuration,
            sessionKind,
            closeMotive,
            operator_info
        FROM talqui_unified 
        WHERE sessionMessagesCount > 0
        ORDER BY RANDOM()
        LIMIT ?
        """
        
        cursor.execute(query, (sample_size,))
        sessions = []
        
        for row in cursor.fetchall():
            # Buscar mensagens da sessão
            msg_query = """
            SELECT messageDirection, messageValue, messageKey
            FROM talqui_unified 
            WHERE sessionID = ? AND messageID IS NOT NULL
            ORDER BY message_createdAt ASC
            """
            cursor.execute(msg_query, (row[0],))
            messages = []
            
            for msg_row in cursor.fetchall():
                messages.append({
                    'direction': msg_row[0],
                    'content': msg_row[1] or msg_row[2] or ''
                })
            
            sessions.append({
                'sessionID': row[0],
                'messageCount': row[1],
                'duration': row[2],
                'kind': row[3],
                'closeMotive': row[4],
                'operator': row[5],
                'messages': messages
            })
        
        conn.close()
        return sessions
    
    def estimate_cost_for_sessions(self, num_sessions: int) -> Dict:
        """Estima custo total para classificar N sessões"""
        
        # Obter amostra para estimativa
        sample_sessions = self.get_sample_sessions(min(20, num_sessions))
        
        if not sample_sessions:
            return {
                'error': 'Nenhuma sessão encontrada para estimativa'
            }
        
        # Calcular tokens médios por sessão
        total_input_tokens = 0
        total_output_tokens = 0
        valid_samples = 0
        
        for session in sample_sessions:
            if session['messages']:
                tokens = self.estimate_tokens_per_session(session['messages'])
                total_input_tokens += tokens['input_tokens']
                total_output_tokens += tokens['output_tokens']
                valid_samples += 1
        
        if valid_samples == 0:
            return {
                'error': 'Nenhuma sessão válida para estimativa'
            }
        
        # Médias por sessão
        avg_input_tokens = total_input_tokens / valid_samples
        avg_output_tokens = total_output_tokens / valid_samples
        
        # Estimativa total
        total_input_tokens_est = avg_input_tokens * num_sessions
        total_output_tokens_est = avg_output_tokens * num_sessions
        
        # Calcular custos
        input_cost = (total_input_tokens_est / 1_000_000) * self.PRICING['deepseek-chat']['input']
        output_cost = (total_output_tokens_est / 1_000_000) * self.PRICING['deepseek-chat']['output']
        total_cost = input_cost + output_cost
        
        return {
            'num_sessions': num_sessions,
            'sample_size': valid_samples,
            'avg_input_tokens': int(avg_input_tokens),
            'avg_output_tokens': int(avg_output_tokens),
            'total_input_tokens': int(total_input_tokens_est),
            'total_output_tokens': int(total_output_tokens_est),
            'input_cost_usd': round(input_cost, 4),
            'output_cost_usd': round(output_cost, 4),
            'total_cost_usd': round(total_cost, 4),
            'cost_per_session': round(total_cost / num_sessions, 6),
            'pricing_model': 'deepseek-chat',
            'estimated_at': datetime.now().isoformat()
        }
    
    def get_remaining_sessions_count(self) -> int:
        """Retorna quantas sessões ainda precisam ser classificadas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total de sessões com mensagens
        cursor.execute("""
            SELECT COUNT(DISTINCT sessionID) 
            FROM talqui_unified 
            WHERE sessionMessagesCount > 0
        """)
        total_sessions = cursor.fetchone()[0]
        
        # Verificar se tabela existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='session_classifications'")
        if not cursor.fetchone():
            conn.close()
            return total_sessions
        
        # Sessões já classificadas
        cursor.execute("SELECT COUNT(*) FROM session_classifications")
        classified_sessions = cursor.fetchone()[0]
        
        conn.close()
        
        remaining = total_sessions - classified_sessions
        return max(0, remaining)
    
    def estimate_remaining_cost(self) -> Dict:
        """Estima custo para classificar sessões restantes"""
        remaining = self.get_remaining_sessions_count()
        
        if remaining == 0:
            return {
                'remaining_sessions': 0,
                'total_cost_usd': 0.0,
                'message': 'Todas as sessões já foram classificadas!'
            }
        
        return self.estimate_cost_for_sessions(remaining)

def main():
    """Teste do estimador de custos"""
    estimator = DeepSeekCostEstimator()
    
    print("💰 Estimador de Custos DeepSeek")
    print("=" * 40)
    
    # Estimar para diferentes volumes
    test_volumes = [10, 50, 100, 500, 1000]
    
    for volume in test_volumes:
        cost_est = estimator.estimate_cost_for_sessions(volume)
        if 'error' in cost_est:
            print(f"❌ Erro: {cost_est['error']}")
            continue
            
        print(f"\n📊 {volume} sessões:")
        print(f"  💵 Custo total: ${cost_est['total_cost_usd']:.4f}")
        print(f"  📈 Por sessão: ${cost_est['cost_per_session']:.6f}")
        print(f"  🔤 Tokens médios: {cost_est['avg_input_tokens']} + {cost_est['avg_output_tokens']}")
    
    # Estimar restantes
    print("\n" + "="*40)
    remaining_est = estimator.estimate_remaining_cost()
    
    if 'error' in remaining_est:
        print(f"❌ {remaining_est['error']}")
    elif remaining_est.get('remaining_sessions', 0) == 0:
        print(f"✅ {remaining_est.get('message', 'Todas as sessões classificadas!')}")
    else:
        print(f"📋 Sessões restantes: {remaining_est['remaining_sessions']}")
        print(f"💰 Custo estimado: ${remaining_est['total_cost_usd']:.4f}")
        print(f"🔤 Total tokens: {remaining_est['total_input_tokens'] + remaining_est['total_output_tokens']:,}")

if __name__ == "__main__":
    main()