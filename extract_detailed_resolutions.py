#!/usr/bin/env python3
"""
Extração detalhada das mensagens de resolução técnica dos agentes Alison e João
"""

import sqlite3
import json
from datetime import datetime

def connect_db():
    """Conecta ao banco de dados SQLite"""
    return sqlite3.connect('talqui.db')

def get_detailed_resolutions():
    """Extrai exemplos detalhados de resoluções técnicas"""
    
    conn = connect_db()
    cursor = conn.cursor()
    
    # Query para buscar sessões com mensagens detalhadas
    query = """
    SELECT 
        sc.sessionID,
        sc.subcategory,
        sc.summary,
        sc.reasoning,
        sc.primary_agent,
        sc.confidence,
        tu.messageDirection,
        tu.messageValue,
        tu.message_createdAt,
        tu.operator_info
    FROM session_classifications sc
    JOIN talqui_unified tu ON sc.sessionID = tu.sessionID
    WHERE sc.category = 'SUPORTE_TECNICO'
        AND (sc.primary_agent = 'Alison' OR sc.primary_agent = 'João')
        AND sc.has_handoff = 0
        AND tu.messageValue IS NOT NULL
        AND tu.messageValue != ''
        AND LENGTH(tu.messageValue) > 20
    ORDER BY sc.subcategory, sc.sessionID, tu.message_createdAt
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    sessions_by_subcategory = {}
    current_session = None
    
    for row in results:
        session_id, subcategory, summary, reasoning, primary_agent, confidence, \
        msg_direction, msg_value, msg_created_at, operator_info = row
        
        if subcategory not in sessions_by_subcategory:
            sessions_by_subcategory[subcategory] = []
        
        # Encontrar ou criar sessão
        session = None
        for s in sessions_by_subcategory[subcategory]:
            if s['session_id'] == session_id:
                session = s
                break
        
        if session is None:
            session = {
                'session_id': session_id,
                'subcategory': subcategory,
                'summary': summary,
                'reasoning': reasoning,
                'primary_agent': primary_agent,
                'confidence': confidence,
                'messages': []
            }
            sessions_by_subcategory[subcategory].append(session)
        
        session['messages'].append({
            'direction': msg_direction,
            'text': msg_value,
            'created_at': msg_created_at,
            'operator': operator_info
        })
    
    conn.close()
    return sessions_by_subcategory

def analyze_resolution_techniques(sessions_data):
    """Analisa as técnicas de resolução utilizadas"""
    
    techniques = {
        'verificação_configurações': ['verificar', 'configuração', 'configurar', 'ajuste'],
        'reset_reconexão': ['resetar', 'reset', 'reconectar', 'desconectar', 'conectar novamente'],
        'orientação_passo_a_passo': ['primeiro', 'segundo', 'depois', 'em seguida', 'passo'],
        'investigação_logs': ['log', 'erro', 'investigar', 'verificar histórico'],
        'atualização_sistema': ['atualizar', 'versão', 'update', 'nova versão'],
        'configuração_permissões': ['permissão', 'acesso', 'autorização', 'admin'],
        'solução_api_integracao': ['api', 'token', 'webhook', 'integração'],
        'orientação_funcionalidade': ['funcionalidade', 'recurso', 'como usar', 'tutorial']
    }
    
    technique_usage = {}
    
    for subcategory, sessions in sessions_data.items():
        technique_usage[subcategory] = {technique: 0 for technique in techniques.keys()}
        
        for session in sessions:
            outbound_messages = [msg for msg in session['messages'] if msg['direction'] == 'OUTBOUND']
            
            for msg in outbound_messages:
                text_lower = msg['text'].lower()
                
                for technique, keywords in techniques.items():
                    if any(keyword in text_lower for keyword in keywords):
                        technique_usage[subcategory][technique] += 1
    
    return technique_usage

def generate_detailed_report():
    """Gera relatório detalhado com exemplos de resoluções"""
    
    print("Extraindo resoluções detalhadas...")
    sessions_data = get_detailed_resolutions()
    
    print("Analisando técnicas de resolução...")
    techniques = analyze_resolution_techniques(sessions_data)
    
    print("\n" + "="*100)
    print("ANÁLISE DETALHADA DAS RESOLUÇÕES TÉCNICAS - AGENTES ALISON E JOÃO")
    print("="*100)
    
    for subcategory, sessions in sessions_data.items():
        if not sessions:
            continue
            
        print(f"\n{'='*80}")
        print(f"SUBCATEGORIA: {subcategory.upper()}")
        print(f"{'='*80}")
        
        # Estatísticas gerais
        total_sessions = len(sessions)
        alison_sessions = len([s for s in sessions if s['primary_agent'] == 'Alison'])
        joao_sessions = len([s for s in sessions if s['primary_agent'] == 'João'])
        
        print(f"\n📊 ESTATÍSTICAS:")
        print(f"   • Total de sessões: {total_sessions}")
        print(f"   • Alison: {alison_sessions} sessões ({alison_sessions/total_sessions*100:.1f}%)")
        print(f"   • João: {joao_sessions} sessões ({joao_sessions/total_sessions*100:.1f}%)")
        
        # Técnicas mais utilizadas
        print(f"\n🛠️ TÉCNICAS DE RESOLUÇÃO MAIS UTILIZADAS:")
        subcategory_techniques = techniques.get(subcategory, {})
        sorted_techniques = sorted(subcategory_techniques.items(), key=lambda x: x[1], reverse=True)[:5]
        
        for technique, count in sorted_techniques:
            if count > 0:
                technique_name = technique.replace('_', ' ').title()
                print(f"   • {technique_name}: {count} ocorrências")
        
        # Exemplos detalhados (máximo 2 por subcategoria)
        print(f"\n📝 EXEMPLOS DETALHADOS DE RESOLUÇÃO:")
        
        example_count = 0
        for session in sessions[:2]:  # Pegar apenas 2 exemplos
            if example_count >= 2:
                break
                
            example_count += 1
            print(f"\n   {'='*60}")
            print(f"   EXEMPLO {example_count}")
            print(f"   {'='*60}")
            print(f"   Agente: {session['primary_agent']}")
            print(f"   Sessão ID: {session['session_id']}")
            print(f"   Confiança: {session['confidence']:.2f}")
            
            if session['summary']:
                print(f"   Resumo: {session['summary']}")
            
            # Separar mensagens por direção
            inbound = [msg for msg in session['messages'] if msg['direction'] == 'INBOUND']
            outbound = [msg for msg in session['messages'] if msg['direction'] == 'OUTBOUND']
            
            if inbound:
                print(f"\n   📥 PROBLEMA RELATADO PELO CLIENTE:")
                for i, msg in enumerate(inbound[:3], 1):  # Mostrar até 3 mensagens
                    print(f"      {i}. {msg['text'][:200]}{'...' if len(msg['text']) > 200 else ''}")
            
            if outbound:
                print(f"\n   📤 RESOLUÇÃO DO AGENTE:")
                for i, msg in enumerate(outbound[:5], 1):  # Mostrar até 5 mensagens
                    print(f"      {i}. {msg['text'][:200]}{'...' if len(msg['text']) > 200 else ''}")
    
    # Resumo geral por agente
    print(f"\n{'='*80}")
    print("RESUMO GERAL POR AGENTE")
    print(f"{'='*80}")
    
    alison_total = sum(len([s for s in sessions if s['primary_agent'] == 'Alison']) for sessions in sessions_data.values())
    joao_total = sum(len([s for s in sessions if s['primary_agent'] == 'João']) for sessions in sessions_data.values())
    
    print(f"\n👩‍💻 ALISON:")
    print(f"   • Total de sessões resolvidas: {alison_total}")
    print(f"   • Especialidades principais:")
    
    alison_by_category = {}
    for subcategory, sessions in sessions_data.items():
        alison_count = len([s for s in sessions if s['primary_agent'] == 'Alison'])
        if alison_count > 0:
            alison_by_category[subcategory] = alison_count
    
    sorted_alison = sorted(alison_by_category.items(), key=lambda x: x[1], reverse=True)[:3]
    for category, count in sorted_alison:
        print(f"     - {category}: {count} sessões")
    
    print(f"\n👨‍💻 JOÃO:")
    print(f"   • Total de sessões resolvidas: {joao_total}")
    print(f"   • Especialidades principais:")
    
    joao_by_category = {}
    for subcategory, sessions in sessions_data.items():
        joao_count = len([s for s in sessions if s['primary_agent'] == 'João'])
        if joao_count > 0:
            joao_by_category[subcategory] = joao_count
    
    sorted_joao = sorted(joao_by_category.items(), key=lambda x: x[1], reverse=True)[:3]
    for category, count in sorted_joao:
        print(f"     - {category}: {count} sessões")
    
    # Salvar dados detalhados em JSON
    output_data = {
        'generated_at': datetime.now().isoformat(),
        'sessions_by_subcategory': sessions_data,
        'techniques_analysis': techniques,
        'agent_summary': {
            'Alison': {
                'total_sessions': alison_total,
                'specialties': dict(sorted_alison)
            },
            'João': {
                'total_sessions': joao_total,
                'specialties': dict(sorted_joao)
            }
        }
    }
    
    with open('detailed_technical_resolutions.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Análise detalhada concluída!")
    print(f"📄 Dados detalhados salvos em: detailed_technical_resolutions.json")

def main():
    """Função principal"""
    try:
        generate_detailed_report()
    except Exception as e:
        print(f"❌ Erro na análise: {str(e)}")
        raise

if __name__ == "__main__":
    main()