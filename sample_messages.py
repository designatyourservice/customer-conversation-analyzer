#!/usr/bin/env python3
"""
Extrai uma amostra de mensagens de resolução técnica
"""

import sqlite3

def get_sample_messages():
    """Extrai amostra de mensagens por subcategoria"""
    
    conn = sqlite3.connect('talqui.db')
    cursor = conn.cursor()
    
    # Buscar uma sessão específica para cada subcategoria
    query = """
    SELECT 
        sc.sessionID,
        sc.subcategory,
        sc.primary_agent,
        tu.messageDirection,
        tu.messageValue
    FROM session_classifications sc
    JOIN talqui_unified tu ON sc.sessionID = tu.sessionID
    WHERE sc.category = 'SUPORTE_TECNICO'
        AND sc.primary_agent IN ('Alison', 'João')
        AND sc.has_handoff = 0
        AND tu.messageValue IS NOT NULL
        AND LENGTH(TRIM(tu.messageValue)) > 20
    ORDER BY sc.subcategory, sc.sessionID, tu.message_createdAt
    LIMIT 500
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    # Organizar por subcategoria e sessão
    by_subcategory = {}
    
    for row in results:
        session_id, subcategory, agent, direction, message = row
        
        if subcategory not in by_subcategory:
            by_subcategory[subcategory] = {}
        
        if session_id not in by_subcategory[subcategory]:
            by_subcategory[subcategory][session_id] = {
                'agent': agent,
                'inbound': [],
                'outbound': []
            }
        
        if direction == 'INBOUND':
            by_subcategory[subcategory][session_id]['inbound'].append(message)
        else:
            by_subcategory[subcategory][session_id]['outbound'].append(message)
    
    conn.close()
    return by_subcategory

def print_sample_messages():
    """Imprime amostra de mensagens"""
    
    print("Extraindo amostra de mensagens...")
    data = get_sample_messages()
    
    print("\n" + "="*100)
    print("AMOSTRA DE MENSAGENS DE RESOLUÇÃO TÉCNICA")
    print("="*100)
    
    for subcategory, sessions in data.items():
        print(f"\n{'='*70}")
        print(f"SUBCATEGORIA: {subcategory.upper()}")
        print(f"{'='*70}")
        
        # Pegar até 2 sessões como exemplo
        session_count = 0
        for session_id, session_data in sessions.items():
            if session_count >= 2:
                break
            session_count += 1
            
            print(f"\n   EXEMPLO {session_count}")
            print(f"   Agente: {session_data['agent']}")
            print(f"   Sessão ID: {session_id[:20]}...")
            
            if session_data['inbound']:
                print(f"\n   📥 PROBLEMA DO CLIENTE:")
                for i, msg in enumerate(session_data['inbound'][:2], 1):
                    print(f"      {i}. {msg[:120]}{'...' if len(msg) > 120 else ''}")
            
            if session_data['outbound']:
                print(f"\n   📤 RESOLUÇÃO DO AGENTE:")
                for i, msg in enumerate(session_data['outbound'][:3], 1):
                    print(f"      {i}. {msg[:120]}{'...' if len(msg) > 120 else ''}")
            
            print()

if __name__ == "__main__":
    print_sample_messages()