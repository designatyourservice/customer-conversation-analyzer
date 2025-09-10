#!/usr/bin/env python3
"""
Extrai exemplos específicos de mensagens de resolução técnica
"""

import sqlite3
from datetime import datetime

def connect_db():
    """Conecta ao banco de dados SQLite"""
    return sqlite3.connect('talqui.db')

def get_resolution_examples_by_subcategory(subcategory, limit=3):
    """Extrai exemplos de resolução para uma subcategoria específica"""
    
    conn = connect_db()
    cursor = conn.cursor()
    
    # Buscar sessões com mensagens substantivas
    query = """
    SELECT DISTINCT
        sc.sessionID,
        sc.subcategory,
        sc.summary,
        sc.primary_agent,
        sc.confidence
    FROM session_classifications sc
    JOIN talqui_unified tu ON sc.sessionID = tu.sessionID
    WHERE sc.category = 'SUPORTE_TECNICO'
        AND sc.subcategory = ?
        AND (sc.primary_agent = 'Alison' OR sc.primary_agent = 'João')
        AND sc.has_handoff = 0
        AND tu.messageDirection = 'OUTBOUND'
        AND LENGTH(tu.messageValue) > 50
    LIMIT ?
    """
    
    cursor.execute(query, (subcategory, limit))
    sessions = cursor.fetchall()
    
    examples = []
    
    for session_data in sessions:
        session_id, subcategory, summary, agent, confidence = session_data
        
        # Buscar todas as mensagens da sessão
        msg_query = """
        SELECT 
            messageDirection,
            messageValue,
            message_createdAt,
            operator_info
        FROM talqui_unified
        WHERE sessionID = ?
            AND messageValue IS NOT NULL 
            AND LENGTH(messageValue) > 10
        ORDER BY message_createdAt
        """
        
        cursor.execute(msg_query, (session_id,))
        messages = cursor.fetchall()
        
        if messages:
            examples.append({
                'session_id': session_id,
                'subcategory': subcategory,
                'summary': summary,
                'agent': agent,
                'confidence': confidence,
                'messages': [
                    {
                        'direction': msg[0],
                        'text': msg[1],
                        'created_at': msg[2],
                        'operator': msg[3]
                    }
                    for msg in messages
                ]
            })
    
    conn.close()
    return examples

def extract_all_subcategory_examples():
    """Extrai exemplos para todas as subcategorias"""
    
    subcategories = [
        'problemas de integração',
        'problemas de mensagens/whatsapp', 
        'problemas de configuração',
        'problemas de funcionamento/sistema',
        'problemas de acesso/login',
        'problemas com chatbot/automação'
    ]
    
    all_examples = {}
    
    for subcategory in subcategories:
        print(f"Extraindo exemplos para: {subcategory}")
        examples = get_resolution_examples_by_subcategory(subcategory, limit=2)
        if examples:
            all_examples[subcategory] = examples
    
    return all_examples

def print_detailed_examples():
    """Imprime exemplos detalhados de resoluções"""
    
    examples = extract_all_subcategory_examples()
    
    print("\n" + "="*100)
    print("EXEMPLOS DETALHADOS DE RESOLUÇÕES TÉCNICAS")
    print("="*100)
    
    for subcategory, subcategory_examples in examples.items():
        print(f"\n{'='*80}")
        print(f"SUBCATEGORIA: {subcategory.upper()}")
        print(f"{'='*80}")
        
        for i, example in enumerate(subcategory_examples, 1):
            print(f"\n{'─'*60}")
            print(f"EXEMPLO {i} - Agente: {example['agent']}")
            print(f"{'─'*60}")
            print(f"Sessão: {example['session_id']}")
            print(f"Confiança: {example['confidence']:.2f}")
            print(f"Resumo: {example['summary']}")
            
            # Separar mensagens por tipo
            inbound_msgs = [msg for msg in example['messages'] if msg['direction'] == 'INBOUND']
            outbound_msgs = [msg for msg in example['messages'] if msg['direction'] == 'OUTBOUND']
            
            print(f"\n📥 PROBLEMA REPORTADO PELO CLIENTE:")
            if inbound_msgs:
                for j, msg in enumerate(inbound_msgs[:3], 1):
                    print(f"   {j}. {msg['text']}")
            else:
                print("   (Nenhuma mensagem inbound encontrada)")
            
            print(f"\n📤 RESOLUÇÃO DO AGENTE {example['agent'].upper()}:")
            if outbound_msgs:
                for j, msg in enumerate(outbound_msgs[:5], 1):
                    print(f"   {j}. {msg['text']}")
            else:
                print("   (Nenhuma mensagem outbound encontrada)")
            
            print()

def main():
    """Função principal"""
    try:
        print_detailed_examples()
        print(f"\n✅ Extração de exemplos concluída!")
        
    except Exception as e:
        print(f"❌ Erro na extração: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()