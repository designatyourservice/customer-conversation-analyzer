#!/usr/bin/env python3
"""
Script para identificar o agente responsável por cada sessão
Analisa mensagens outbound para identificar quem atendeu cada sessão
"""

import sqlite3
import re
from datetime import datetime
from typing import Optional, Dict, List

class AgentIdentifier:
    def __init__(self, db_path: str = 'talqui.db'):
        self.db_path = db_path
        
        # Padrões para identificação de agentes
        self.agent_patterns = {
            'Isabella': [
                r'(?i)isabella',
                r'(?i)sou a isabella',
                r'(?i)eu sou a isabella'
            ],
            'Alison': [
                r'(?i)alison',
                r'(?i)sou o alison',
                r'(?i)\*alison\*',
                r'(?i)alisson'  # Variação encontrada
            ],
            'Thomaz': [
                r'(?i)thomaz',
                r'(?i)sou o thomaz',
                r'(?i)sou thomaz',
                r'(?i)\*tom\*'  # Assinatura abreviada
            ],
            'Achilles': [
                r'(?i)achilles',
                r'(?i)aquiles',
                r'(?i)meu nome é achilles',
                r'(?i)nome é achilles',
                r'(?i)\*achilles\*',
                r'(?i)achilles mello'
            ],
            'Gustavo': [
                r'(?i)gustavo',
                r'(?i)sou o gustavo',
                r'(?i)\*gustavo\*'
            ],
            'João': [
                r'(?i)joão miranda',
                r'(?i)joao miranda',
                r'(?i)meu nome é joão',
                r'(?i)sou o joão',
                r'(?i)\*joão miranda\*'
            ],
            'Ana': [
                r'(?i)sou a ana',
                r'(?i)meu nome é ana'
            ],
            'Paulo': [
                r'(?i)sou o paulo',
                r'(?i)meu nome é paulo'
            ],
            'Carlos': [
                r'(?i)sou o carlos',
                r'(?i)meu nome é carlos'
            ],
            'Rafael': [
                r'(?i)sou o rafael',
                r'(?i)meu nome é rafael'
            ],
            'Lucas': [
                r'(?i)sou o lucas',
                r'(?i)meu nome é lucas'
            ],
            'Gabriel': [
                r'(?i)sou o gabriel',
                r'(?i)meu nome é gabriel'
            ]
        }
    
    def identify_agent_from_message(self, message: str) -> Optional[str]:
        """Identifica agente baseado no conteúdo da mensagem"""
        if not message:
            return None
            
        # Verificar cada padrão de agente
        for agent_name, patterns in self.agent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message):
                    return agent_name
        
        return None
    
    def identify_agent_from_operator_info(self, operator_info: str) -> Optional[str]:
        """Identifica agente baseado no campo operator_info"""
        if not operator_info:
            return None
            
        # Verificar se operator_info contém nome do agente diretamente
        for agent_name in self.agent_patterns.keys():
            if agent_name.lower() in operator_info.lower():
                return agent_name
                
        return None
    
    def get_session_messages(self, session_id: str) -> List[Dict]:
        """Busca todas as mensagens de uma sessão"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT messageDirection, messageValue, operator_info, message_createdAt
            FROM talqui_unified 
            WHERE sessionID = ? 
            ORDER BY message_createdAt ASC
        """, (session_id,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'direction': row[0],
                'content': row[1],
                'operator_info': row[2],
                'created_at': row[3]
            })
        
        conn.close()
        return messages
    
    def identify_session_agent(self, session_id: str) -> Optional[str]:
        """Identifica o agente responsável por uma sessão específica"""
        messages = self.get_session_messages(session_id)
        
        if not messages:
            return None
        
        # Estratégia 1: Verificar operator_info primeiro
        for message in messages:
            if message['direction'] == 'outbound' and message['operator_info']:
                agent = self.identify_agent_from_operator_info(message['operator_info'])
                if agent:
                    return agent
        
        # Estratégia 2: Analisar conteúdo das mensagens outbound
        for message in messages:
            if message['direction'] == 'outbound' and message['content']:
                agent = self.identify_agent_from_message(message['content'])
                if agent:
                    return agent
        
        # Estratégia 3: Verificar se é mensagem automática/sistema
        outbound_messages = [m for m in messages if m['direction'] == 'outbound']
        if outbound_messages:
            # Se há mensagens outbound mas não identificamos agente, pode ser sistema
            first_outbound = outbound_messages[0]['content'] if outbound_messages[0]['content'] else ''
            
            # Padrões de mensagens automáticas
            auto_patterns = [
                r'lembrete.*pagamento',
                r'fatura.*vencimento',
                r'boleto.*cobrança',
                r'segunda.*via',
                r'atenção.*boleto'
            ]
            
            for pattern in auto_patterns:
                if re.search(pattern, first_outbound, re.IGNORECASE):
                    return 'Sistema'
        
        return None
    
    def add_agent_column(self):
        """Adiciona coluna agent na tabela session_classifications"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("ALTER TABLE session_classifications ADD COLUMN agent TEXT")
            conn.commit()
            print("✅ Coluna 'agent' adicionada à tabela session_classifications")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("⚠️  Coluna 'agent' já existe")
            else:
                raise e
        
        conn.close()
    
    def process_all_sessions(self, batch_size: int = 100):
        """Processa todas as sessões para identificar agentes"""
        
        print("🔍 INICIANDO IDENTIFICAÇÃO DE AGENTES POR SESSÃO")
        print("=" * 50)
        
        # Adicionar coluna se não existir
        self.add_agent_column()
        
        # Buscar todas as sessões classificadas
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT sessionID FROM session_classifications ORDER BY sessionID")
        all_sessions = [row[0] for row in cursor.fetchall()]
        total_sessions = len(all_sessions)
        
        print(f"📊 Total de sessões a processar: {total_sessions:,}")
        
        # Contadores
        identified_count = 0
        not_identified_count = 0
        agent_counts = {}
        
        # Processar em lotes
        for i in range(0, total_sessions, batch_size):
            batch = all_sessions[i:i + batch_size]
            batch_results = []
            
            print(f"🔄 Processando lote {i//batch_size + 1}: sessões {i+1}-{min(i+batch_size, total_sessions)}")
            
            for session_id in batch:
                agent = self.identify_session_agent(session_id)
                
                if agent:
                    identified_count += 1
                    agent_counts[agent] = agent_counts.get(agent, 0) + 1
                else:
                    agent = 'Não identificado'
                    not_identified_count += 1
                
                batch_results.append((agent, session_id))
            
            # Atualizar banco em lote
            cursor.executemany("""
                UPDATE session_classifications 
                SET agent = ? 
                WHERE sessionID = ?
            """, batch_results)
            
            conn.commit()
            
            if (i // batch_size + 1) % 10 == 0:
                print(f"  ✅ Processados: {min(i+batch_size, total_sessions):,}/{total_sessions:,}")
        
        conn.close()
        
        # Relatório final
        print(f"\n🎉 IDENTIFICAÇÃO CONCLUÍDA!")
        print(f"✅ Identificados: {identified_count:,} ({identified_count/total_sessions*100:.1f}%)")
        print(f"❌ Não identificados: {not_identified_count:,} ({not_identified_count/total_sessions*100:.1f}%)")
        
        print(f"\n📊 DISTRIBUIÇÃO POR AGENTE:")
        for agent, count in sorted(agent_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_sessions) * 100
            print(f"  {agent:15} | {count:4,} sessões ({percentage:5.1f}%)")
        
        return {
            'total_sessions': total_sessions,
            'identified': identified_count,
            'not_identified': not_identified_count,
            'agent_distribution': agent_counts
        }
    
    def export_with_agents(self, filename: str = 'FINAL_ALL_CLASSIFICATIONS_WITH_AGENTS.csv'):
        """Exporta CSV incluindo informação do agente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT sessionID, category, subcategory, confidence, reasoning, 
                   classified_at, messages_analyzed, summary, agent
            FROM session_classifications 
            ORDER BY category, subcategory, agent
        """)
        
        import csv
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow(['sessionID', 'category', 'subcategory', 'confidence', 
                           'reasoning', 'classified_at', 'messages_analyzed', 'summary', 'agent'])
            
            # Data
            for row in cursor.fetchall():
                writer.writerow(row)
        
        conn.close()
        
        print(f"📄 Arquivo exportado: {filename}")
        
        # Mostrar estatísticas do arquivo
        with open(filename, 'r') as f:
            total_lines = sum(1 for line in f) - 1
        
        print(f"📊 Total de registros exportados: {total_lines:,}")
        
        return filename
    
    def generate_agent_analysis_report(self):
        """Gera relatório de análise por agente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print(f"\n📈 ANÁLISE DETALHADA POR AGENTE:")
        print("=" * 60)
        
        # Análise por agente e categoria
        cursor.execute("""
            SELECT agent, category, COUNT(*) as sessions_count
            FROM session_classifications 
            WHERE agent IS NOT NULL
            GROUP BY agent, category
            ORDER BY agent, sessions_count DESC
        """)
        
        current_agent = None
        agent_totals = {}
        
        for agent, category, count in cursor.fetchall():
            if agent != current_agent:
                if current_agent:
                    print(f"  Total: {agent_totals[current_agent]:,} sessões\n")
                
                current_agent = agent
                agent_totals[agent] = 0
                print(f"👤 {agent.upper()}:")
            
            agent_totals[agent] += count
            percentage = (count / agent_totals.get(agent, 1)) * 100 if agent in agent_totals else 0
            print(f"  {category:15} | {count:4,} sessões")
        
        # Último agente
        if current_agent:
            print(f"  Total: {agent_totals[current_agent]:,} sessões")
        
        conn.close()

def main():
    """Função principal"""
    print("🤖 IDENTIFICADOR DE AGENTES POR SESSÃO")
    print("Analisando todas as sessões para identificar o agente responsável...")
    print()
    
    identifier = AgentIdentifier()
    
    # Executar identificação
    results = identifier.process_all_sessions(batch_size=100)
    
    # Gerar relatório detalhado
    identifier.generate_agent_analysis_report()
    
    # Exportar dados com agentes
    csv_file = identifier.export_with_agents()
    
    print(f"\n✅ PROCESSO CONCLUÍDO!")
    print(f"📄 Arquivo exportado: {csv_file}")
    
    return results

if __name__ == "__main__":
    main()