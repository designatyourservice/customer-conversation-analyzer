# 🤖 Guia de Identificação de Agentes por Sessão

## 📋 Visão Geral
Este documento detalha o processo completo de identificação de agentes responsáveis por cada sessão de atendimento, incluindo regras de negócio, padrões de reconhecimento e scripts para execução automatizada após a classificação das sessões.

## 🎯 Objetivos da Identificação de Agentes
- **Identificar agente responsável** por cada sessão de atendimento
- **Analisar performance individual** dos agentes
- **Mapear especialização** por tipo de demanda
- **Gerar insights** de produtividade e distribuição de carga
- **Facilitar análises** de qualidade de atendimento

## 📊 Estrutura de Dados

### Tabela Principal: `session_classifications`
```sql
-- Estrutura após implementação da identificação
CREATE TABLE session_classifications (
    sessionID TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    subcategory TEXT NOT NULL,
    confidence REAL,
    reasoning TEXT,
    classified_at TIMESTAMP,
    messages_analyzed INTEGER,
    summary TEXT,
    agent TEXT  -- NOVA COLUNA ADICIONADA
);
```

### Tabela de Origem: `talqui_unified`
```sql
-- Campos relevantes para identificação
SELECT 
    sessionID,
    messageDirection,    -- 'inbound' ou 'outbound'
    messageValue,       -- Conteúdo da mensagem
    operator_info,      -- Informações do operador
    message_createdAt   -- Timestamp da mensagem
FROM talqui_unified;
```

## 👥 Agentes Identificados na Base

### 🏆 Agentes Principais (Por Volume)
1. **Isabella** - 2,389 sessões (65.0%)
2. **Alison** - 452 sessões (12.3%)
3. **Achilles** - 186 sessões (5.1%)
4. **Thomaz** - 56 sessões (1.5%)
5. **João** - 28 sessões (0.8%)
6. **Gustavo** - 17 sessões (0.5%)
7. **Sistema** - 2 sessões (0.1%)

### 📋 Perfis e Especializações

#### **👤 Isabella - Agente Generalista Principal**
- **Função**: Analista de Atendimento Principal
- **Volume**: 2,389 sessões (65.0% do total)
- **Especialização**: Generalista com foco em:
  - Suporte Técnico: 800 sessões (33.5%)
  - Outros: 479 sessões (20.1%)
  - Comercial: 468 sessões (19.6%)
  - Informação: 423 sessões (17.7%)
  - Financeiro: 181 sessões (7.6%)
- **Padrões de Apresentação**:
  - "Eu sou a Isabella, analista de atendimento da Talqui - Comercial"
  - "Bom dia! Eu sou a Isabella, analista de atendimento da Talqui"

#### **🔧 Alison - Especialista Técnico**
- **Função**: Especialista em Suporte Técnico
- **Volume**: 452 sessões (12.3% do total)
- **Especialização**: Técnico com apoio comercial:
  - Suporte Técnico: 166 sessões (36.8%)
  - Outros: 110 sessões (24.4%)
  - Comercial: 100 sessões (22.2%)
  - Financeiro: 44 sessões (9.8%)
- **Padrões de Apresentação**:
  - "Sou o Alison, do suporte da Talqui"
  - "Sou o Alison, do suporte ao cliente da Talqui"
- **Assinatura**: `*Alison*:`

#### **💼 Achilles - Especialista Comercial**
- **Função**: Especialista de Atendimento Comercial
- **Volume**: 186 sessões (5.1% do total)
- **Especialização**: Comercial focado:
  - Comercial: 106 sessões (58.9%)
  - Outros: 47 sessões (26.1%)
  - Suporte Técnico: 19 sessões (10.6%)
- **Padrões de Apresentação**:
  - "Meu nome é Achilles e sou do setor comercial da Talqui"
  - "Achilles Mello e sou o especialista de atendimento da Talqui"
- **Assinatura**: `*Achilles*:`

#### **🎯 Thomaz - Gerente Comercial**
- **Função**: Gerente de Relacionamento/Comercial
- **Volume**: 56 sessões (1.5% do total)
- **Especialização**: Estratégico:
  - Comercial: 24 sessões (45.3%)
  - Suporte Técnico: 13 sessões (24.5%)
  - Financeiro: 8 sessões (15.1%)
- **Padrões de Apresentação**:
  - "Sou o Thomaz, gerente comercial da Talqui"
  - "Thomaz, Gerente de Relacionamento com o cliente da Talqui"
- **Assinatura**: `*Tom*:`

#### **💰 Gustavo - Comercial Especializado**
- **Função**: Analista Comercial
- **Volume**: 17 sessões (0.5% do total)
- **Especialização**: 100% Comercial
- **Padrões de Apresentação**:
  - "Sou o Gustavo do time comercial"
- **Assinatura**: `*Gustavo*:`

#### **🛠️ João - Suporte Geral**
- **Função**: Analista de Suporte Geral
- **Volume**: 28 sessões (0.8% do total)
- **Especialização**: 
  - Outros: 11 sessões (44.0%)
  - Suporte Técnico: 8 sessões (32.0%)
- **Padrões de Apresentação**:
  - "Meu nome é João e vou dar continuidade ao seu atendimento"
- **Assinatura**: `*João Miranda*:`

## 🔍 Estratégias de Identificação

### Metodologia em Camadas (Prioridade Decrescente)

#### **Camada 1: Análise do Campo `operator_info`**
```python
# Verificar se operator_info contém nome do agente diretamente
if agent_name.lower() in operator_info.lower():
    return agent_name
```

#### **Camada 2: Análise de Conteúdo de Mensagens Outbound**
```python
# Padrões de regex para cada agente
agent_patterns = {
    'Isabella': [
        r'(?i)isabella',
        r'(?i)sou a isabella',
        r'(?i)eu sou a isabella'
    ],
    'Alison': [
        r'(?i)alison',
        r'(?i)sou o alison',
        r'(?i)\*alison\*',
        r'(?i)alisson'
    ],
    'Thomaz': [
        r'(?i)thomaz',
        r'(?i)sou o thomaz',
        r'(?i)\*tom\*'
    ],
    'Achilles': [
        r'(?i)achilles',
        r'(?i)meu nome é achilles',
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
        r'(?i)meu nome é joão',
        r'(?i)\*joão miranda\*'
    ]
}
```

#### **Camada 3: Detecção de Sistema Automático**
```python
# Padrões de mensagens automáticas
auto_patterns = [
    r'lembrete.*pagamento',
    r'fatura.*vencimento',
    r'boleto.*cobrança',
    r'segunda.*via',
    r'atenção.*boleto'
]
```

### Algoritmo de Identificação por Sessão

```python
def identify_session_agent(session_id):
    messages = get_session_messages(session_id)
    
    # Estratégia 1: Verificar operator_info
    for message in outbound_messages:
        if message['operator_info']:
            agent = identify_from_operator_info(message['operator_info'])
            if agent:
                return agent
    
    # Estratégia 2: Analisar conteúdo das mensagens
    for message in outbound_messages:
        if message['content']:
            agent = identify_from_content(message['content'])
            if agent:
                return agent
    
    # Estratégia 3: Verificar se é sistema automático
    if is_automatic_message(outbound_messages):
        return 'Sistema'
    
    return 'Não identificado'
```

## 📊 Taxas de Identificação por Categoria

| Categoria | Total | Identificados | Taxa de Identificação |
|-----------|-------|---------------|----------------------|
| **RECLAMACAO** | 28 | 28 | 100.0% |
| **CANCELAMENTO** | 19 | 19 | 100.0% |
| **SUPORTE_TECNICO** | 1,037 | 1,007 | 97.1% |
| **INFORMACAO** | 497 | 463 | 93.2% |
| **COMERCIAL** | 778 | 710 | 91.3% |
| **OUTROS** | 884 | 659 | 74.5% |
| **FINANCEIRO** | 431 | 244 | 56.6% |

### Análise das Taxas

**🎯 Excelente Identificação (>95%)**
- RECLAMACAO e CANCELAMENTO: 100% - Sempre tem agente humano
- SUPORTE_TECNICO: 97.1% - Agentes se identificam claramente

**✅ Boa Identificação (90-95%)**
- INFORMACAO: 93.2% - Maioria com apresentação formal
- COMERCIAL: 91.3% - Agentes comerciais se apresentam

**⚠️ Identificação Moderada (<90%)**
- OUTROS: 74.5% - Muitas mensagens automáticas/incompletas
- FINANCEIRO: 56.6% - Alto volume de mensagens automáticas (boletos, lembretes)

## 🛠️ Script de Automação Completo

### Script Principal: `identify_agents_by_session.py`

```python
#!/usr/bin/env python3
"""
Script completo para identificação de agentes por sessão
Analisa todas as sessões e identifica o agente responsável
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
                r'(?i)alisson'
            ],
            'Thomaz': [
                r'(?i)thomaz',
                r'(?i)sou o thomaz',
                r'(?i)sou thomaz',
                r'(?i)\*tom\*'
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
        
        # Padrões de mensagens automáticas
        self.auto_patterns = [
            r'(?i)lembrete.*pagamento',
            r'(?i)fatura.*vencimento',
            r'(?i)boleto.*cobrança',
            r'(?i)segunda.*via',
            r'(?i)atenção.*boleto',
            r'(?i)sua fatura.*disponível',
            r'(?i)vencimento.*hoje',
            r'(?i)cobrança.*automática'
        ]
    
    def identify_agent_from_message(self, message: str) -> Optional[str]:
        """Identifica agente baseado no conteúdo da mensagem"""
        if not message:
            return None
        
        for agent_name, patterns in self.agent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message):
                    return agent_name
        
        return None
    
    def identify_agent_from_operator_info(self, operator_info: str) -> Optional[str]:
        """Identifica agente baseado no campo operator_info"""
        if not operator_info:
            return None
        
        for agent_name in self.agent_patterns.keys():
            if agent_name.lower() in operator_info.lower():
                return agent_name
        
        return None
    
    def is_automatic_message(self, messages: List[Dict]) -> bool:
        """Verifica se é mensagem automática do sistema"""
        if not messages:
            return False
        
        outbound_messages = [m for m in messages if m['direction'] == 'outbound']
        if not outbound_messages:
            return False
        
        first_content = outbound_messages[0]['content'] or ''
        
        for pattern in self.auto_patterns:
            if re.search(pattern, first_content):
                return True
        
        return False
    
    def get_session_messages(self, session_id: str) -> List[Dict]:
        """Busca todas as mensagens de uma sessão ordenadas por timestamp"""
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
    
    def identify_session_agent(self, session_id: str) -> str:
        """
        Identifica o agente responsável por uma sessão específica
        Retorna o nome do agente ou 'Não identificado'
        """
        messages = self.get_session_messages(session_id)
        
        if not messages:
            return 'Não identificado'
        
        outbound_messages = [m for m in messages if m['direction'] == 'outbound']
        
        if not outbound_messages:
            return 'Não identificado'
        
        # Estratégia 1: Verificar operator_info primeiro (mais confiável)
        for message in outbound_messages:
            if message['operator_info']:
                agent = self.identify_agent_from_operator_info(message['operator_info'])
                if agent:
                    return agent
        
        # Estratégia 2: Analisar conteúdo das mensagens outbound
        for message in outbound_messages:
            if message['content']:
                agent = self.identify_agent_from_message(message['content'])
                if agent:
                    return agent
        
        # Estratégia 3: Verificar se é mensagem automática/sistema
        if self.is_automatic_message(messages):
            return 'Sistema'
        
        return 'Não identificado'
    
    def add_agent_column(self):
        """Adiciona coluna agent na tabela session_classifications se não existir"""
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
        """
        Processa todas as sessões para identificar agentes
        Processa em lotes para otimizar performance
        """
        
        print("🔍 INICIANDO IDENTIFICAÇÃO DE AGENTES POR SESSÃO")
        print("=" * 50)
        
        # Backup antes de modificar
        self.create_backup()
        
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
        
        # Processar em lotes para otimizar performance
        for i in range(0, total_sessions, batch_size):
            batch = all_sessions[i:i + batch_size]
            batch_results = []
            
            print(f"🔄 Processando lote {i//batch_size + 1}: sessões {i+1}-{min(i+batch_size, total_sessions)}")
            
            for session_id in batch:
                agent = self.identify_session_agent(session_id)
                
                if agent and agent != 'Não identificado':
                    identified_count += 1
                    agent_counts[agent] = agent_counts.get(agent, 0) + 1
                else:
                    not_identified_count += 1
                
                batch_results.append((agent or 'Não identificado', session_id))
            
            # Atualizar banco em lote (mais eficiente)
            cursor.executemany("""
                UPDATE session_classifications 
                SET agent = ? 
                WHERE sessionID = ?
            """, batch_results)
            
            conn.commit()
            
            # Log de progresso a cada 10 lotes
            if (i // batch_size + 1) % 10 == 0:
                print(f"  ✅ Processados: {min(i+batch_size, total_sessions):,}/{total_sessions:,}")
        
        conn.close()
        
        # Relatório final
        print(f"\n🎉 IDENTIFICAÇÃO CONCLUÍDA!")
        print(f"✅ Identificados: {identified_count:,} ({identified_count/total_sessions*100:.1f}%)")
        print(f"❌ Não identificados: {not_identified_count:,} ({not_identified_count/total_sessions*100:.1f}%)")
        
        if agent_counts:
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
    
    def create_backup(self):
        """Cria backup da tabela antes de modificar"""
        conn = sqlite3.connect(self.db_path)
        backup_name = f"session_classifications_backup_agents_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        conn.execute(f"CREATE TABLE {backup_name} AS SELECT * FROM session_classifications")
        conn.commit()
        conn.close()
        print(f"✅ Backup criado: {backup_name}")
        return backup_name
    
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
            
            # Header com nova coluna
            writer.writerow(['sessionID', 'category', 'subcategory', 'confidence', 
                           'reasoning', 'classified_at', 'messages_analyzed', 'summary', 'agent'])
            
            # Data
            for row in cursor.fetchall():
                writer.writerow(row)
        
        conn.close()
        
        print(f"📄 Arquivo exportado: {filename}")
        
        # Estatísticas do arquivo
        with open(filename, 'r') as f:
            total_lines = sum(1 for line in f) - 1
        
        print(f"📊 Total de registros exportados: {total_lines:,}")
        
        return filename
    
    def generate_detailed_report(self):
        """Gera relatório detalhado de análise por agente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print(f"\n📈 ANÁLISE DETALHADA POR AGENTE:")
        print("=" * 60)
        
        # Análise de especialização por agente
        cursor.execute("""
            SELECT 
                agent,
                category,
                COUNT(*) as sessions_count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY agent), 1) as pct_within_agent
            FROM session_classifications 
            WHERE agent IS NOT NULL AND agent != 'Não identificado'
            GROUP BY agent, category
            HAVING COUNT(*) >= 3
            ORDER BY agent, sessions_count DESC
        """)
        
        current_agent = None
        agent_totals = {}
        
        for agent, category, count, percentage in cursor.fetchall():
            if agent != current_agent:
                if current_agent and current_agent in agent_totals:
                    print(f"  Total: {agent_totals[current_agent]:,} sessões\n")
                
                current_agent = agent
                print(f"👤 {agent.upper()}:")
            
            print(f"  {category:15} | {count:4,} sessões ({percentage:4.1f}%)")
            agent_totals[current_agent] = agent_totals.get(current_agent, 0) + count
        
        # Último agente
        if current_agent and current_agent in agent_totals:
            print(f"  Total: {agent_totals[current_agent]:,} sessões")
        
        # Taxa de identificação por categoria
        print(f"\n💯 TAXA DE IDENTIFICAÇÃO POR CATEGORIA:")
        print("-" * 50)
        
        cursor.execute("""
            SELECT 
                category,
                COUNT(*) as total,
                SUM(CASE WHEN agent != 'Não identificado' THEN 1 ELSE 0 END) as identified,
                ROUND(SUM(CASE WHEN agent != 'Não identificado' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as rate
            FROM session_classifications
            GROUP BY category
            ORDER BY rate DESC
        """)
        
        for category, total, identified, rate in cursor.fetchall():
            status = "✅" if rate >= 90 else "⚠️" if rate >= 70 else "❌"
            print(f"{status} {category:15} | {identified:3,}/{total:3,} ({rate:5.1f}%)")
        
        conn.close()
    
    def run_complete_identification(self):
        """Executa identificação completa com relatórios"""
        print("🤖 IDENTIFICADOR DE AGENTES - EXECUÇÃO COMPLETA")
        print("=" * 60)
        
        # Executar identificação
        results = self.process_all_sessions(batch_size=100)
        
        # Gerar relatório detalhado
        self.generate_detailed_report()
        
        # Exportar dados
        csv_file = self.export_with_agents()
        
        print(f"\n✅ PROCESSO CONCLUÍDO!")
        print(f"📊 Taxa de identificação: {results['identified']/results['total_sessions']*100:.1f}%")
        print(f"📄 Arquivo final: {csv_file}")
        
        return results

def main():
    """Função principal para execução do script"""
    identifier = AgentIdentifier()
    results = identifier.run_complete_identification()
    
    # Salvar relatório em JSON
    import json
    with open('agent_identification_report.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Relatório JSON salvo: agent_identification_report.json")

if __name__ == "__main__":
    main()
```

## 📊 Métricas de Qualidade

### KPIs de Identificação
- **Taxa Global de Identificação**: Target > 80%
- **Taxa por Categoria**: Todas > 70%
- **Distribuição Equilibrada**: Nenhum agente > 70% das sessões
- **Precisão**: < 5% de identificações incorretas (validação manual)

### Validações de Qualidade

#### Script de Validação: `validate_agent_identification.py`

```python
#!/usr/bin/env python3
"""
Script para validar a qualidade da identificação de agentes
"""

import sqlite3
from collections import defaultdict

def validate_identification_quality(db_path='talqui.db'):
    """Valida a qualidade da identificação realizada"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("📊 VALIDAÇÃO DA IDENTIFICAÇÃO DE AGENTES")
    print("=" * 50)
    
    # Verificar taxa de identificação global
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN agent != 'Não identificado' THEN 1 ELSE 0 END) as identified
        FROM session_classifications
    """)
    
    total, identified = cursor.fetchone()
    identification_rate = (identified / total) * 100
    
    status = "✅" if identification_rate >= 80 else "⚠️" if identification_rate >= 70 else "❌"
    print(f"{status} Taxa Global: {identified:,}/{total:,} ({identification_rate:.1f}%)")
    
    # Verificar distribuição por agente
    cursor.execute("""
        SELECT agent, COUNT(*) as count,
               ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM session_classifications), 1) as percentage
        FROM session_classifications 
        GROUP BY agent 
        ORDER BY count DESC
    """)
    
    print(f"\n📈 DISTRIBUIÇÃO POR AGENTE:")
    concentration_warning = False
    
    for agent, count, percentage in cursor.fetchall():
        status = "⚠️" if percentage > 70 else "✅"
        print(f"{status} {agent:15} | {count:4,} sessões ({percentage:5.1f}%)")
        
        if percentage > 70 and agent != 'Não identificado':
            concentration_warning = True
    
    # Verificar casos suspeitos (agentes com poucas sessões mas alta variedade)
    cursor.execute("""
        SELECT agent, COUNT(*) as sessions, COUNT(DISTINCT category) as categories
        FROM session_classifications 
        WHERE agent != 'Não identificado'
        GROUP BY agent
        HAVING COUNT(*) < 20 AND COUNT(DISTINCT category) >= 5
    """)
    
    suspicious_cases = cursor.fetchall()
    if suspicious_cases:
        print(f"\n🔍 CASOS PARA REVISÃO MANUAL:")
        for agent, sessions, categories in suspicious_cases:
            print(f"⚠️  {agent}: {sessions} sessões, {categories} categorias diferentes")
    
    conn.close()
    
    # Recomendações
    print(f"\n💡 RECOMENDAÇÕES:")
    if identification_rate < 80:
        print("🔄 Ajustar padrões de identificação para melhorar taxa global")
    
    if concentration_warning:
        print("🔄 Revisar distribuição - possível super-concentração em um agente")
    
    if not suspicious_cases and identification_rate >= 80:
        print("✅ Identificação está com boa qualidade!")

if __name__ == "__main__":
    validate_identification_quality()
```

## 📋 Checklist de Execução

### Pré-requisitos
- [ ] Sessões já classificadas em categorias
- [ ] Banco de dados `talqui.db` atualizado  
- [ ] Scripts de identificação preparados
- [ ] Backup do ambiente realizado

### Execução
- [ ] Executar `python3 identify_agents_by_session.py`
- [ ] Verificar logs de processamento
- [ ] Executar `python3 validate_agent_identification.py`
- [ ] Analisar taxas de identificação por categoria
- [ ] Validar amostra manual de identificações

### Pós-execução
- [ ] Atualizar dashboards com dados de agentes
- [ ] Comunicar stakeholders sobre nova funcionalidade
- [ ] Arquivar backups antigos
- [ ] Documentar ajustes manuais necessários

## 🔧 Troubleshooting

### Problemas Comuns

#### Taxa de Identificação Baixa (< 70%)
```python
# Adicionar novos padrões de identificação
new_patterns = {
    'AgenteName': [
        r'(?i)novo_padrao_1',
        r'(?i)novo_padrao_2'
    ]
}

# Verificar mensagens não identificadas
cursor.execute("""
    SELECT tu.messageValue 
    FROM talqui_unified tu
    JOIN session_classifications sc ON tu.sessionID = sc.sessionID
    WHERE sc.agent = 'Não identificado' 
    AND tu.messageDirection = 'outbound'
    AND tu.messageValue IS NOT NULL
    LIMIT 20
""")
```

#### Agente Incorretamente Identificado
```python
# Refinar padrões específicos
agent_patterns['AgenteName'] = [
    r'(?i)sou o agentename\b',  # Usar word boundary
    r'(?i)meu nome é agentename\b'
]

# Evitar falsos positivos
exclude_patterns = [
    r'(?i)não sou o agentename',
    r'(?i)agentename não está'
]
```

#### Performance Lenta
```python
# Otimizar com índices
cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_session_direction 
    ON talqui_unified(sessionID, messageDirection)
""")

cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_message_content 
    ON talqui_unified(messageValue)
""")

# Processar em lotes menores
results = identifier.process_all_sessions(batch_size=50)
```

### Logs e Debugging

#### Habilitar Debug Detalhado
```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent_identification.log'),
        logging.StreamHandler()
    ]
)

# Log de cada identificação
def identify_session_agent(self, session_id):
    logging.debug(f"Processing session: {session_id}")
    agent = self.identify_session_agent_internal(session_id)
    logging.debug(f"Session {session_id} -> Agent: {agent}")
    return agent
```

#### Verificar Integridade dos Dados
```sql
-- Verificar se há sessões sem mensagens
SELECT COUNT(*) 
FROM session_classifications sc
LEFT JOIN talqui_unified tu ON sc.sessionID = tu.sessionID
WHERE tu.sessionID IS NULL;

-- Verificar sessões com apenas mensagens inbound
SELECT COUNT(*) 
FROM session_classifications sc
WHERE sc.sessionID NOT IN (
    SELECT DISTINCT sessionID 
    FROM talqui_unified 
    WHERE messageDirection = 'outbound'
);

-- Verificar distribuição de agent = NULL
SELECT COUNT(*) 
FROM session_classifications 
WHERE agent IS NULL;
```

## 📝 Análises Disponíveis Pós-Identificação

### 1. Performance por Agente
```sql
SELECT 
    agent,
    category,
    COUNT(*) as sessions,
    AVG(confidence) as avg_confidence,
    COUNT(DISTINCT DATE(classified_at)) as active_days
FROM session_classifications 
WHERE agent != 'Não identificado'
GROUP BY agent, category
ORDER BY agent, sessions DESC;
```

### 2. Distribuição de Carga de Trabalho
```sql
SELECT 
    agent,
    COUNT(*) as total_sessions,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM session_classifications), 2) as workload_percentage
FROM session_classifications
GROUP BY agent
ORDER BY total_sessions DESC;
```

### 3. Especialização por Agente
```sql
SELECT 
    agent,
    category,
    COUNT(*) as sessions,
    RANK() OVER (PARTITION BY agent ORDER BY COUNT(*) DESC) as category_rank
FROM session_classifications
WHERE agent != 'Não identificado'
GROUP BY agent, category;
```

### 4. Análise Temporal
```sql
SELECT 
    agent,
    DATE(classified_at) as date,
    COUNT(*) as daily_sessions
FROM session_classifications
WHERE agent != 'Não identificado'
GROUP BY agent, DATE(classified_at)
ORDER BY date DESC, daily_sessions DESC;
```

## 📊 Dashboards Recomendados

### KPIs Principais
- **Taxa de Identificação Global**
- **Distribuição de Sessões por Agente** 
- **Especialização por Categoria**
- **Performance Temporal**

### Visualizações Sugeridas
1. **Gráfico de Pizza**: Distribuição de sessões por agente
2. **Heatmap**: Agente x Categoria (intensidade = volume)
3. **Linha do Tempo**: Sessões por agente ao longo do tempo
4. **Barras Horizontais**: Top categorias por agente
5. **Gauge**: Taxa de identificação global

## 🔄 Manutenção e Evolução

### Manutenção Contínua
- **Revisão mensal**: Verificar novos padrões de apresentação
- **Atualização de agentes**: Incluir novos membros da equipe
- **Refinamento de padrões**: Melhorar precisão baseado em feedback
- **Limpeza de dados**: Revisar identificações duvidosas

### Evolução do Sistema
- **Machine Learning**: Implementar classificação automática de agentes
- **Análise de Sentimento**: Correlacionar satisfação com agente
- **Predição de Demanda**: Antecipar necessidades de cada agente
- **Gamificação**: Métricas de performance para agentes

---

**📅 Última atualização**: Setembro 2025  
**👤 Responsável**: Sistema de Identificação de Agentes  
**🔄 Versão**: 1.0