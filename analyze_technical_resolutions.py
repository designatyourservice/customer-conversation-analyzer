#!/usr/bin/env python3
"""
Análise das resoluções técnicas dos agentes Alison e João
"""

import sqlite3
import json
import re
from collections import defaultdict
from datetime import datetime

def connect_db():
    """Conecta ao banco de dados SQLite"""
    return sqlite3.connect('talqui.db')

def extract_technical_resolutions():
    """Extrai as resoluções técnicas dos agentes especializados"""
    
    conn = connect_db()
    cursor = conn.cursor()
    
    # Query para buscar sessões técnicas resolvidas por Alison ou João
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
    ORDER BY sc.subcategory, sc.sessionID, tu.message_createdAt
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    # Organizar dados por subcategoria
    resolutions_by_subcategory = defaultdict(lambda: {
        'sessions': defaultdict(lambda: {
            'inbound_messages': [],
            'outbound_messages': [],
            'summary': '',
            'reasoning': '',
            'primary_agent': '',
            'confidence': 0
        }),
        'patterns': defaultdict(int),
        'solutions': defaultdict(int)
    })
    
    for row in results:
        session_id, subcategory, summary, reasoning, primary_agent, confidence, \
        msg_direction, msg_value, msg_created_at, operator_info = row
        
        session_data = resolutions_by_subcategory[subcategory]['sessions'][session_id]
        
        # Armazenar metadados da sessão
        if not session_data['summary']:
            session_data['summary'] = summary or ''
            session_data['reasoning'] = reasoning or ''
            session_data['primary_agent'] = primary_agent
            session_data['confidence'] = confidence
        
        # Categorizar mensagens
        if msg_direction == 'INBOUND':
            session_data['inbound_messages'].append({
                'text': msg_value,
                'created_at': msg_created_at,
                'operator': operator_info
            })
        elif msg_direction == 'OUTBOUND':
            session_data['outbound_messages'].append({
                'text': msg_value,
                'created_at': msg_created_at,
                'operator': operator_info
            })
    
    conn.close()
    return resolutions_by_subcategory

def extract_solution_patterns(messages):
    """Extrai padrões de soluções das mensagens de resolução"""
    patterns = []
    
    for msg in messages:
        text = msg['text'].lower()
        
        # Padrões comuns de soluções técnicas
        if 'acesso' in text and ('resetar' in text or 'reset' in text):
            patterns.append('reset_acesso')
        elif 'senha' in text and ('nova' in text or 'alterar' in text):
            patterns.append('alteracao_senha')
        elif 'integra' in text and ('config' in text or 'configur' in text):
            patterns.append('configuracao_integracao')
        elif 'whatsapp' in text and ('desconect' in text or 'reconect' in text):
            patterns.append('reconexao_whatsapp')
        elif 'chatbot' in text and ('desativ' in text or 'ativ' in text):
            patterns.append('configuracao_chatbot')
        elif 'api' in text and ('token' in text or 'chave' in text):
            patterns.append('configuracao_api')
        elif 'conta' in text and ('suspens' in text or 'bloq' in text):
            patterns.append('desbloqueio_conta')
        elif 'permiss' in text and ('admin' in text or 'acesso' in text):
            patterns.append('configuracao_permissoes')
        elif 'log' in text and ('erro' in text or 'falha' in text):
            patterns.append('analise_logs')
        elif 'funcionalidade' in text and ('ativ' in text or 'habilit' in text):
            patterns.append('habilitacao_funcionalidade')
    
    return patterns

def analyze_resolutions():
    """Analisa as resoluções técnicas e gera relatório"""
    
    print("Extraindo resoluções técnicas dos agentes Alison e João...")
    resolutions = extract_technical_resolutions()
    
    report = {
        'generated_at': datetime.now().isoformat(),
        'agents': ['Alison', 'João'],
        'subcategories': {}
    }
    
    # Analisar cada subcategoria
    for subcategory, data in resolutions.items():
        print(f"\nAnalisando subcategoria: {subcategory}")
        
        subcategory_analysis = {
            'total_sessions': len(data['sessions']),
            'agents_distribution': defaultdict(int),
            'common_problems': [],
            'resolution_patterns': defaultdict(int),
            'sample_resolutions': []
        }
        
        # Analisar cada sessão
        for session_id, session in data['sessions'].items():
            agent = session['primary_agent']
            subcategory_analysis['agents_distribution'][agent] += 1
            
            # Extrair padrões de solução das mensagens outbound
            patterns = extract_solution_patterns(session['outbound_messages'])
            for pattern in patterns:
                subcategory_analysis['resolution_patterns'][pattern] += 1
            
            # Coletar exemplos de resoluções (máximo 3 por subcategoria)
            if len(subcategory_analysis['sample_resolutions']) < 3:
                outbound_texts = [msg['text'] for msg in session['outbound_messages']]
                inbound_texts = [msg['text'] for msg in session['inbound_messages']]
                
                subcategory_analysis['sample_resolutions'].append({
                    'session_id': session_id,
                    'agent': agent,
                    'problem_context': inbound_texts[:2] if inbound_texts else [],
                    'resolution_messages': outbound_texts[:3] if outbound_texts else [],
                    'summary': session['summary'],
                    'confidence': session['confidence']
                })
        
        # Identificar problemas comuns baseado nas mensagens inbound
        problem_keywords = defaultdict(int)
        for session in data['sessions'].values():
            for msg in session['inbound_messages']:
                text = msg['text'].lower()
                # Extrair palavras-chave de problemas
                keywords = ['não consigo', 'erro', 'problema', 'falha', 'bug', 
                          'não funciona', 'travou', 'lento', 'indisponível']
                for keyword in keywords:
                    if keyword in text:
                        problem_keywords[keyword] += 1
        
        # Converter para dict ordenado pelos mais comuns
        sorted_problems = sorted(problem_keywords.items(), key=lambda x: x[1], reverse=True)[:5]
        subcategory_analysis['common_problems'] = dict(sorted_problems)
        subcategory_analysis['resolution_patterns'] = dict(subcategory_analysis['resolution_patterns'])
        subcategory_analysis['agents_distribution'] = dict(subcategory_analysis['agents_distribution'])
        
        report['subcategories'][subcategory] = subcategory_analysis
    
    return report

def generate_knowledge_base_report(report):
    """Gera relatório formatado da base de conhecimento"""
    
    print("\n" + "="*80)
    print("BASE DE CONHECIMENTO - RESOLUÇÕES TÉCNICAS")
    print("Agentes: Alison e João")
    print("="*80)
    
    total_sessions = sum(sub['total_sessions'] for sub in report['subcategories'].values())
    print(f"\nTotal de sessões analisadas: {total_sessions}")
    print(f"Gerado em: {report['generated_at']}")
    
    for subcategory, data in report['subcategories'].items():
        print(f"\n{'='*60}")
        print(f"SUBCATEGORIA: {subcategory.upper()}")
        print(f"{'='*60}")
        
        print(f"\n📊 ESTATÍSTICAS:")
        print(f"   • Total de sessões: {data['total_sessions']}")
        print(f"   • Distribuição por agente:")
        for agent, count in data['agents_distribution'].items():
            percentage = (count / data['total_sessions']) * 100
            print(f"     - {agent}: {count} sessões ({percentage:.1f}%)")
        
        print(f"\n🔍 PROBLEMAS MAIS COMUNS:")
        for problem, count in data['common_problems'].items():
            print(f"   • '{problem}': {count} ocorrências")
        
        print(f"\n🛠️ PADRÕES DE RESOLUÇÃO:")
        for pattern, count in data['resolution_patterns'].items():
            pattern_name = pattern.replace('_', ' ').title()
            print(f"   • {pattern_name}: {count} ocorrências")
        
        print(f"\n📝 EXEMPLOS DE RESOLUÇÕES:")
        for i, example in enumerate(data['sample_resolutions'], 1):
            print(f"\n   EXEMPLO {i} - Agente: {example['agent']}")
            print(f"   Sessão: {example['session_id']}")
            print(f"   Confiança: {example['confidence']:.2f}")
            
            if example['problem_context']:
                print(f"   📥 CONTEXTO DO PROBLEMA:")
                for ctx in example['problem_context']:
                    print(f"      - {ctx[:100]}...")
            
            if example['resolution_messages']:
                print(f"   📤 MENSAGENS DE RESOLUÇÃO:")
                for res in example['resolution_messages']:
                    print(f"      - {res[:100]}...")
            
            if example['summary']:
                print(f"   📋 RESUMO: {example['summary'][:150]}...")

def main():
    """Função principal"""
    try:
        # Analisar resoluções técnicas
        report = analyze_resolutions()
        
        # Gerar relatório formatado
        generate_knowledge_base_report(report)
        
        # Salvar relatório em JSON para análise posterior
        with open('technical_resolutions_knowledge_base.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Análise concluída!")
        print(f"📄 Relatório detalhado salvo em: technical_resolutions_knowledge_base.json")
        
    except Exception as e:
        print(f"❌ Erro na análise: {str(e)}")
        raise

if __name__ == "__main__":
    main()