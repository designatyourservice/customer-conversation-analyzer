#!/usr/bin/env python3
"""
Script para analisar eficácia de agentes e detectar transbordos
Identifica se um agente conseguiu encerrar a conversa sozinho ou houve transbordo
"""

import sqlite3
import re
from datetime import datetime
from typing import List, Dict, Tuple, Optional

class AgentEffectivenessAnalyzer:
    def __init__(self, db_path: str = 'talqui.db'):
        self.db_path = db_path
        
        # Padrões para identificar agentes em mensagens
        self.agent_patterns = {
            'Isabella': [
                r'(?i)isabella',
                r'(?i)\*isabella\*',
                r'(?i)sou a isabella'
            ],
            'Alison': [
                r'(?i)alison',
                r'(?i)\*alison\*',
                r'(?i)sou o alison',
                r'(?i)alisson'
            ],
            'Thomaz': [
                r'(?i)thomaz',
                r'(?i)\*tom\*',
                r'(?i)sou o thomaz'
            ],
            'Achilles': [
                r'(?i)achilles',
                r'(?i)\*achilles\*',
                r'(?i)nome é achilles',
                r'(?i)achilles mello'
            ],
            'Gustavo': [
                r'(?i)gustavo',
                r'(?i)\*gustavo\*',
                r'(?i)sou o gustavo'
            ],
            'João': [
                r'(?i)joão miranda',
                r'(?i)\*joão miranda\*',
                r'(?i)meu nome é joão'
            ]
        }
        
        # Padrões que indicam transbordo/transferência
        self.handoff_patterns = [
            r'(?i)vou.*transfer',
            r'(?i)pass.*para',
            r'(?i)encaminh.*para',
            r'(?i)specialist.*vai.*atend',
            r'(?i)colega.*vai.*ajud',
            r'(?i)outro.*atendent',
            r'(?i)transfer.*para.*setor',
            r'(?i)direcion.*para'
        ]
    
    def identify_agent_from_message(self, message: str) -> Optional[str]:
        """Identifica qual agente está falando baseado no conteúdo da mensagem"""
        if not message:
            return None
        
        for agent_name, patterns in self.agent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message):
                    return agent_name
        
        return None
    
    def is_handoff_message(self, message: str) -> bool:
        """Verifica se a mensagem indica um transbordo/transferência"""
        if not message:
            return False
        
        for pattern in self.handoff_patterns:
            if re.search(pattern, message):
                return True
        
        return False
    
    def get_session_agent_sequence(self, session_id: str) -> List[Dict]:
        """
        Analisa a sequência de agentes em uma sessão
        Retorna lista ordenada de mensagens outbound com agente identificado
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT messageDirection, messageValue, operator_info, message_createdAt
            FROM talqui_unified 
            WHERE sessionID = ? AND messageDirection = 'outbound'
            ORDER BY message_createdAt ASC
        """, (session_id,))
        
        sequence = []
        for row in cursor.fetchall():
            direction, content, operator_info, created_at = row
            
            # Tentar identificar agente pelo conteúdo da mensagem
            agent_from_content = self.identify_agent_from_message(content or '')
            
            # Tentar identificar pelo operator_info
            agent_from_operator = None
            if operator_info:
                for agent_name in self.agent_patterns.keys():
                    if agent_name.lower() in operator_info.lower():
                        agent_from_operator = agent_name
                        break
            
            # Priorizar identificação por conteúdo (mais confiável para transbordo)
            identified_agent = agent_from_content or agent_from_operator
            
            sequence.append({
                'timestamp': created_at,
                'content': content,
                'operator_info': operator_info,
                'identified_agent': identified_agent,
                'is_handoff': self.is_handoff_message(content or '')
            })
        
        conn.close()
        return sequence
    
    def analyze_session_effectiveness(self, session_id: str) -> Dict:
        """
        Analisa a eficácia dos agentes em uma sessão específica
        Determina se houve transbordo e qual agente finalizou
        """
        sequence = self.get_session_agent_sequence(session_id)
        
        if not sequence:
            return {
                'session_id': session_id,
                'has_handoff': False,
                'agents_involved': [],
                'primary_agent': None,
                'final_agent': None,
                'handoff_count': 0,
                'effectiveness_score': 0.0,
                'analysis': 'Nenhuma mensagem outbound encontrada'
            }
        
        # Identificar agentes únicos na sequência
        agents_in_sequence = []
        handoff_points = []
        
        current_agent = None
        handoff_count = 0
        
        for i, msg in enumerate(sequence):
            if msg['identified_agent']:
                if current_agent and current_agent != msg['identified_agent']:
                    # Mudança de agente detectada
                    handoff_count += 1
                    handoff_points.append({
                        'from_agent': current_agent,
                        'to_agent': msg['identified_agent'],
                        'timestamp': msg['timestamp'],
                        'explicit_handoff': msg['is_handoff']
                    })
                
                if msg['identified_agent'] not in agents_in_sequence:
                    agents_in_sequence.append(msg['identified_agent'])
                
                current_agent = msg['identified_agent']
        
        # Determinar agente primário (primeiro a aparecer)
        primary_agent = agents_in_sequence[0] if agents_in_sequence else None
        
        # Determinar agente final (último a aparecer)
        final_agent = current_agent
        
        # Calcular score de eficácia
        # Score alto = agente único conseguiu finalizar
        # Score baixo = muitos transbordos
        if len(agents_in_sequence) == 1:
            effectiveness_score = 1.0  # Agente único, máxima eficácia
        elif len(agents_in_sequence) == 2:
            effectiveness_score = 0.7  # Um transbordo
        elif len(agents_in_sequence) == 3:
            effectiveness_score = 0.4  # Dois transbordos
        else:
            effectiveness_score = 0.2  # Múltiplos transbordos
        
        # Análise textual
        if handoff_count == 0:
            analysis = f"Atendimento completo por {primary_agent}"
        else:
            analysis = f"Transbordo: {' → '.join(agents_in_sequence)}"
        
        return {
            'session_id': session_id,
            'has_handoff': handoff_count > 0,
            'agents_involved': agents_in_sequence,
            'primary_agent': primary_agent,
            'final_agent': final_agent,
            'handoff_count': handoff_count,
            'handoff_points': handoff_points,
            'effectiveness_score': effectiveness_score,
            'analysis': analysis
        }
    
    def add_effectiveness_columns(self):
        """Adiciona colunas para análise de eficácia"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        columns_to_add = [
            ('has_handoff', 'INTEGER DEFAULT 0'),
            ('primary_agent', 'TEXT'),
            ('final_agent', 'TEXT'), 
            ('handoff_count', 'INTEGER DEFAULT 0'),
            ('effectiveness_score', 'REAL DEFAULT 1.0')
        ]
        
        for column_name, column_def in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE session_classifications ADD COLUMN {column_name} {column_def}")
                print(f"✅ Coluna '{column_name}' adicionada")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"⚠️  Coluna '{column_name}' já existe")
                else:
                    print(f"❌ Erro ao adicionar '{column_name}': {e}")
        
        conn.commit()
        conn.close()
    
    def process_all_sessions(self, batch_size: int = 100):
        """Processa todas as sessões para análise de eficácia"""
        
        print("🎯 INICIANDO ANÁLISE DE EFICÁCIA DOS AGENTES")
        print("=" * 50)
        
        # Backup
        self.create_backup()
        
        # Adicionar colunas
        self.add_effectiveness_columns()
        
        # Buscar todas as sessões
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT sessionID FROM session_classifications ORDER BY sessionID")
        all_sessions = [row[0] for row in cursor.fetchall()]
        total_sessions = len(all_sessions)
        
        print(f"📊 Total de sessões a analisar: {total_sessions:,}")
        
        # Contadores
        sessions_with_handoff = 0
        sessions_without_handoff = 0
        agent_effectiveness = {}
        
        # Processar em lotes
        for i in range(0, total_sessions, batch_size):
            batch = all_sessions[i:i + batch_size]
            batch_updates = []
            
            print(f"🔄 Processando lote {i//batch_size + 1}: sessões {i+1}-{min(i+batch_size, total_sessions)}")
            
            for session_id in batch:
                analysis = self.analyze_session_effectiveness(session_id)
                
                # Contar estatísticas
                if analysis['has_handoff']:
                    sessions_with_handoff += 1
                else:
                    sessions_without_handoff += 1
                
                # Coletar dados de eficácia por agente
                primary_agent = analysis['primary_agent']
                if primary_agent:
                    if primary_agent not in agent_effectiveness:
                        agent_effectiveness[primary_agent] = {
                            'total_sessions': 0,
                            'successful_closures': 0,
                            'handoffs': 0,
                            'effectiveness_scores': []
                        }
                    
                    agent_effectiveness[primary_agent]['total_sessions'] += 1
                    agent_effectiveness[primary_agent]['effectiveness_scores'].append(analysis['effectiveness_score'])
                    
                    if not analysis['has_handoff']:
                        agent_effectiveness[primary_agent]['successful_closures'] += 1
                    else:
                        agent_effectiveness[primary_agent]['handoffs'] += 1
                
                # Preparar update do banco
                batch_updates.append((
                    int(analysis['has_handoff']),
                    analysis['primary_agent'],
                    analysis['final_agent'],
                    analysis['handoff_count'],
                    analysis['effectiveness_score'],
                    session_id
                ))
            
            # Atualizar banco em lote
            cursor.executemany("""
                UPDATE session_classifications 
                SET has_handoff = ?, 
                    primary_agent = ?, 
                    final_agent = ?, 
                    handoff_count = ?,
                    effectiveness_score = ?
                WHERE sessionID = ?
            """, batch_updates)
            
            conn.commit()
            
            if (i // batch_size + 1) % 10 == 0:
                print(f"  ✅ Processados: {min(i+batch_size, total_sessions):,}/{total_sessions:,}")
        
        conn.close()
        
        # Relatório final
        print(f"\n🎉 ANÁLISE DE EFICÁCIA CONCLUÍDA!")
        print(f"✅ Sessões sem transbordo: {sessions_without_handoff:,} ({sessions_without_handoff/total_sessions*100:.1f}%)")
        print(f"🔄 Sessões com transbordo: {sessions_with_handoff:,} ({sessions_with_handoff/total_sessions*100:.1f}%)")
        
        # Calcular eficácia por agente
        print(f"\n📊 EFICÁCIA POR AGENTE:")
        for agent, data in sorted(agent_effectiveness.items(), 
                                key=lambda x: x[1]['total_sessions'], reverse=True):
            if data['total_sessions'] >= 10:  # Só mostrar agentes com volume significativo
                closure_rate = (data['successful_closures'] / data['total_sessions']) * 100
                avg_score = sum(data['effectiveness_scores']) / len(data['effectiveness_scores'])
                
                print(f"  {agent:15} | {data['total_sessions']:4d} sessões | "
                      f"{closure_rate:5.1f}% fechamento | Score: {avg_score:.3f}")
        
        return {
            'total_sessions': total_sessions,
            'sessions_with_handoff': sessions_with_handoff,
            'sessions_without_handoff': sessions_without_handoff,
            'agent_effectiveness': agent_effectiveness
        }
    
    def create_backup(self):
        """Cria backup antes de modificar dados"""
        conn = sqlite3.connect(self.db_path)
        backup_name = f"session_classifications_backup_effectiveness_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        conn.execute(f"CREATE TABLE {backup_name} AS SELECT * FROM session_classifications")
        conn.commit()
        conn.close()
        print(f"✅ Backup criado: {backup_name}")
        return backup_name
    
    def generate_detailed_effectiveness_report(self):
        """Gera relatório detalhado de eficácia"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print(f"\n📈 RELATÓRIO DETALHADO DE EFICÁCIA:")
        print("=" * 60)
        
        # Eficácia geral por agente
        cursor.execute("""
            SELECT 
                primary_agent,
                COUNT(*) as total_sessions,
                SUM(CASE WHEN has_handoff = 0 THEN 1 ELSE 0 END) as successful_closures,
                SUM(CASE WHEN has_handoff = 1 THEN 1 ELSE 0 END) as handoff_sessions,
                AVG(effectiveness_score) as avg_effectiveness,
                ROUND(SUM(CASE WHEN has_handoff = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as closure_rate
            FROM session_classifications 
            WHERE primary_agent IS NOT NULL
            GROUP BY primary_agent
            HAVING COUNT(*) >= 10
            ORDER BY closure_rate DESC
        """)
        
        print("🎯 RANKING DE EFICÁCIA (Taxa de Fechamento):")
        for row in cursor.fetchall():
            agent, total, closures, handoffs, avg_score, closure_rate = row
            status = "🏆" if closure_rate >= 85 else "✅" if closure_rate >= 70 else "⚠️"
            print(f"{status} {agent:12} | {total:3d} sessões | {closure_rate:5.1f}% fechamento | Score: {avg_score:.3f}")
        
        # Análise por categoria
        print(f"\n📋 EFICÁCIA POR CATEGORIA:")
        cursor.execute("""
            SELECT 
                category,
                primary_agent,
                COUNT(*) as sessions,
                ROUND(AVG(effectiveness_score), 3) as avg_score,
                ROUND(SUM(CASE WHEN has_handoff = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as closure_rate
            FROM session_classifications 
            WHERE primary_agent IS NOT NULL
            GROUP BY category, primary_agent
            HAVING COUNT(*) >= 5
            ORDER BY category, closure_rate DESC
        """)
        
        current_category = None
        for category, agent, sessions, avg_score, closure_rate in cursor.fetchall():
            if category != current_category:
                print(f"\n📂 {category}:")
                current_category = category
            
            status = "✅" if closure_rate >= 80 else "⚠️"
            print(f"  {status} {agent:12} | {sessions:2d} sessões | {closure_rate:5.1f}% | Score: {avg_score}")
        
        # Padrões de transbordo
        print(f"\n🔄 PADRÕES DE TRANSBORDO:")
        cursor.execute("""
            SELECT 
                primary_agent,
                final_agent,
                COUNT(*) as handoff_count
            FROM session_classifications 
            WHERE has_handoff = 1 AND primary_agent != final_agent
            GROUP BY primary_agent, final_agent
            HAVING COUNT(*) >= 3
            ORDER BY handoff_count DESC
        """)
        
        handoff_patterns = cursor.fetchall()
        if handoff_patterns:
            for from_agent, to_agent, count in handoff_patterns:
                print(f"  {from_agent:12} → {to_agent:12} | {count:2d} transbordos")
        else:
            print("  ✅ Poucos padrões de transbordo identificados")
        
        conn.close()
    
    def export_with_effectiveness(self, filename: str = 'FINAL_ALL_CLASSIFICATIONS_WITH_EFFECTIVENESS.csv'):
        """Exporta dados incluindo análise de eficácia"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT sessionID, category, subcategory, confidence, reasoning, 
                   classified_at, messages_analyzed, summary, agent,
                   has_handoff, primary_agent, final_agent, handoff_count, effectiveness_score
            FROM session_classifications 
            ORDER BY category, effectiveness_score DESC, agent
        """)
        
        import csv
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header expandido
            writer.writerow([
                'sessionID', 'category', 'subcategory', 'confidence', 'reasoning', 
                'classified_at', 'messages_analyzed', 'summary', 'agent',
                'has_handoff', 'primary_agent', 'final_agent', 'handoff_count', 'effectiveness_score'
            ])
            
            # Data
            for row in cursor.fetchall():
                writer.writerow(row)
        
        conn.close()
        
        print(f"📄 Arquivo exportado: {filename}")
        
        with open(filename, 'r') as f:
            total_lines = sum(1 for line in f) - 1
        
        print(f"📊 Total de registros: {total_lines:,}")
        return filename
    
    def run_complete_effectiveness_analysis(self):
        """Executa análise completa de eficácia"""
        print("🎯 ANALISADOR DE EFICÁCIA DE AGENTES - EXECUÇÃO COMPLETA")
        print("=" * 70)
        
        # Executar análise
        results = self.process_all_sessions(batch_size=100)
        
        # Gerar relatório detalhado
        self.generate_detailed_effectiveness_report()
        
        # Exportar dados
        csv_file = self.export_with_effectiveness()
        
        print(f"\n✅ ANÁLISE DE EFICÁCIA CONCLUÍDA!")
        print(f"📊 Taxa geral de fechamento: {results['sessions_without_handoff']/results['total_sessions']*100:.1f}%")
        print(f"📄 Arquivo final: {csv_file}")
        
        return results

def main():
    """Função principal"""
    print("🎯 ANALISADOR DE EFICÁCIA DE AGENTES")
    print("Detectando transbordos e calculando taxa de fechamento por agente...")
    print()
    
    analyzer = AgentEffectivenessAnalyzer()
    results = analyzer.run_complete_effectiveness_analysis()
    
    # Salvar relatório detalhado
    import json
    with open('agent_effectiveness_report.json', 'w', encoding='utf-8') as f:
        # Converter dados não serializáveis
        serializable_results = {
            'total_sessions': results['total_sessions'],
            'sessions_with_handoff': results['sessions_with_handoff'],
            'sessions_without_handoff': results['sessions_without_handoff'],
            'handoff_rate': results['sessions_with_handoff'] / results['total_sessions'],
            'agent_effectiveness': {
                agent: {
                    'total_sessions': data['total_sessions'],
                    'successful_closures': data['successful_closures'],
                    'handoffs': data['handoffs'],
                    'closure_rate': data['successful_closures'] / data['total_sessions'],
                    'avg_effectiveness_score': sum(data['effectiveness_scores']) / len(data['effectiveness_scores'])
                }
                for agent, data in results['agent_effectiveness'].items()
            },
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Relatório JSON salvo: agent_effectiveness_report.json")

if __name__ == "__main__":
    main()