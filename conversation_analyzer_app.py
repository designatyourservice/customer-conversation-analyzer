#!/usr/bin/env python3
"""
App para análise de conversas - Talqui
Interface web para visualizar conversas com filtros e informações detalhadas
"""

from flask import Flask, render_template, jsonify, request
import sqlite3
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = 'conversation_analyzer_2025'

class ConversationAnalyzer:
    def __init__(self, db_path: str = 'talqui.db'):
        self.db_path = db_path
    
    def get_filters_data(self):
        """Retorna dados para os filtros laterais"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Categorias
        cursor.execute("""
            SELECT DISTINCT category, COUNT(*) as count 
            FROM session_classifications 
            GROUP BY category 
            ORDER BY count DESC
        """)
        categories = [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Subcategorias
        cursor.execute("""
            SELECT DISTINCT subcategory, COUNT(*) as count 
            FROM session_classifications 
            GROUP BY subcategory 
            ORDER BY count DESC
        """)
        subcategories = [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Agentes
        cursor.execute("""
            SELECT DISTINCT primary_agent, COUNT(*) as count 
            FROM session_classifications 
            WHERE primary_agent IS NOT NULL
            GROUP BY primary_agent 
            ORDER BY count DESC
        """)
        agents = [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Faixas de confiança
        confidence_ranges = [
            {'name': '90-100%', 'min': 0.9, 'max': 1.0},
            {'name': '80-89%', 'min': 0.8, 'max': 0.89},
            {'name': '70-79%', 'min': 0.7, 'max': 0.79},
            {'name': '60-69%', 'min': 0.6, 'max': 0.69},
            {'name': '<60%', 'min': 0.0, 'max': 0.59}
        ]
        
        # Status de transbordo
        cursor.execute("""
            SELECT 
                CASE WHEN has_handoff = 1 THEN 'Com Transbordo' ELSE 'Sem Transbordo' END as status,
                COUNT(*) as count
            FROM session_classifications 
            GROUP BY has_handoff
        """)
        handoff_status = [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Status RLHF
        cursor.execute("""
            SELECT 
                CASE WHEN rlhf = 1 THEN 'Validado' ELSE 'Não Validado' END as status,
                COUNT(*) as count
            FROM session_classifications 
            GROUP BY rlhf
        """)
        rlhf_status = [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'categories': categories,
            'subcategories': subcategories,
            'agents': agents,
            'confidence_ranges': confidence_ranges,
            'handoff_status': handoff_status,
            'rlhf_status': rlhf_status
        }
    
    def get_conversations_list(self, filters=None):
        """Retorna lista de conversas com filtros aplicados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Base query para contar total
        count_query = """
            SELECT COUNT(*)
            FROM session_classifications sc
            WHERE 1=1
        """
        
        # Base query para dados
        query = """
            SELECT 
                sc.sessionID,
                sc.category,
                sc.subcategory,
                sc.confidence,
                sc.summary,
                sc.primary_agent,
                sc.final_agent,
                sc.has_handoff,
                sc.handoff_count,
                sc.effectiveness_score,
                sc.classified_at,
                sc.messages_analyzed,
                sc.rlhf,
                sc.resolution,
                sc.template,
                sc.company,
                sc.name,
                sc.erp,
                sc.channel,
                sc.customerNumber
            FROM session_classifications sc
            WHERE 1=1
        """
        
        params = []
        
        # Aplicar filtros
        if filters:
            filter_conditions = ""
            
            if filters.get('category'):
                filter_conditions += " AND sc.category = ?"
                params.append(filters['category'])
            
            if filters.get('subcategory'):
                filter_conditions += " AND sc.subcategory = ?"
                params.append(filters['subcategory'])
            
            if filters.get('agent'):
                filter_conditions += " AND sc.primary_agent = ?"
                params.append(filters['agent'])
            
            if filters.get('confidence_min') and filters.get('confidence_max'):
                filter_conditions += " AND sc.confidence BETWEEN ? AND ?"
                params.append(filters['confidence_min'])
                params.append(filters['confidence_max'])
            
            if filters.get('has_handoff') is not None:
                filter_conditions += " AND sc.has_handoff = ?"
                params.append(int(filters['has_handoff']))
            
            if filters.get('rlhf') is not None:
                filter_conditions += " AND sc.rlhf = ?"
                params.append(int(filters['rlhf']))
            
            count_query += filter_conditions
            query += filter_conditions
        
        # Obter count total
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        # Obter dados limitados
        query += " ORDER BY sc.classified_at DESC LIMIT 50"
        cursor.execute(query, params)
        
        conversations = []
        for row in cursor.fetchall():
            conversations.append({
                'sessionID': row[0],
                'category': row[1],
                'subcategory': row[2],
                'confidence': row[3],
                'summary': row[4],
                'primary_agent': row[5],
                'final_agent': row[6],
                'has_handoff': bool(row[7]),
                'handoff_count': row[8],
                'effectiveness_score': row[9],
                'classified_at': row[10],
                'messages_analyzed': row[11],
                'rlhf': bool(row[12]),
                'resolution': bool(row[13]),
                'template': bool(row[14]),
                'company': row[15] or '',
                'name': row[16] or '',
                'erp': row[17] or '',
                'channel': row[18] or '',
                'customerNumber': row[19] or ''
            })
        
        conn.close()
        return {
            'conversations': conversations,
            'total_count': total_count
        }
    
    def get_conversation_messages(self, session_id):
        """Retorna todas as mensagens de uma conversa"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Buscar mensagens
        cursor.execute("""
            SELECT 
                messageDirection,
                messageValue,
                operator_info,
                message_createdAt,
                contactID
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
                'timestamp': row[3],
                'contact_id': row[4]
            })
        
        # Buscar informações da sessão
        cursor.execute("""
            SELECT 
                category,
                subcategory,
                confidence,
                reasoning,
                summary,
                primary_agent,
                final_agent,
                has_handoff,
                handoff_count,
                effectiveness_score,
                classified_at,
                messages_analyzed,
                rlhf,
                resolution,
                template,
                company,
                name,
                erp,
                channel,
                customerNumber
            FROM session_classifications
            WHERE sessionID = ?
        """, (session_id,))
        
        session_info = None
        row = cursor.fetchone()
        if row:
            session_info = {
                'category': row[0],
                'subcategory': row[1],
                'confidence': row[2],
                'reasoning': row[3],
                'summary': row[4],
                'primary_agent': row[5],
                'final_agent': row[6],
                'has_handoff': bool(row[7]),
                'handoff_count': row[8],
                'effectiveness_score': row[9],
                'classified_at': row[10],
                'messages_analyzed': row[11],
                'rlhf': bool(row[12]),
                'resolution': bool(row[13]),
                'template': bool(row[14]),
                'company': row[15] or '',
                'name': row[16] or '',
                'erp': row[17] or '',
                'channel': row[18] or '',
                'customerNumber': row[19] or ''
            }
        
        conn.close()
        
        return {
            'messages': messages,
            'session_info': session_info
        }

# Instância global do analisador
analyzer = ConversationAnalyzer()

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/api/filters')
def get_filters():
    """API para obter dados dos filtros"""
    try:
        filters_data = analyzer.get_filters_data()
        return jsonify({'success': True, 'data': filters_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/conversations')
def get_conversations():
    """API para obter lista de conversas"""
    try:
        # Obter filtros da query string
        filters = {}
        
        if request.args.get('category'):
            filters['category'] = request.args.get('category')
        
        if request.args.get('subcategory'):
            filters['subcategory'] = request.args.get('subcategory')
        
        if request.args.get('agent'):
            filters['agent'] = request.args.get('agent')
        
        if request.args.get('confidence_min') and request.args.get('confidence_max'):
            filters['confidence_min'] = float(request.args.get('confidence_min'))
            filters['confidence_max'] = float(request.args.get('confidence_max'))
        
        if request.args.get('has_handoff'):
            filters['has_handoff'] = request.args.get('has_handoff') == 'true'
        
        if request.args.get('rlhf'):
            filters['rlhf'] = request.args.get('rlhf') == 'true'
        
        result = analyzer.get_conversations_list(filters if filters else None)
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/conversation/<session_id>')
def get_conversation(session_id):
    """API para obter detalhes de uma conversa específica"""
    try:
        conversation_data = analyzer.get_conversation_messages(session_id)
        return jsonify({'success': True, 'data': conversation_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/conversation/<session_id>/update', methods=['PUT'])
def update_conversation(session_id):
    """API para atualizar informações de uma conversa"""
    try:
        data = request.get_json()
        
        if not data or 'category' not in data or 'subcategory' not in data:
            return jsonify({'success': False, 'error': 'Dados inválidos'})
        
        conn = sqlite3.connect(analyzer.db_path)
        cursor = conn.cursor()
        
        # Preparar campos para atualização
        update_fields = ['category = ?', 'subcategory = ?', 'rlhf = 1', 'classified_at = CURRENT_TIMESTAMP']
        update_values = [data['category'], data['subcategory']]
        
        # Verificar se has_handoff foi fornecido
        if 'has_handoff' in data:
            update_fields.append('has_handoff = ?')
            update_values.append(1 if data['has_handoff'] else 0)
        
        # Verificar se resolution foi fornecido
        if 'resolution' in data:
            update_fields.append('resolution = ?')
            update_values.append(1 if data['resolution'] else 0)
        
        # Verificar se template foi fornecido
        if 'template' in data:
            update_fields.append('template = ?')
            update_values.append(1 if data['template'] else 0)
        
        # Verificar se rlhf foi fornecido (edição manual do RLHF)
        if 'rlhf' in data:
            # Para edição manual do RLHF, não atualizar classified_at automaticamente
            # Remove o classified_at automático se só RLHF está sendo editado
            if len(update_fields) == 3:  # Apenas category, subcategory e rlhf = 1
                update_fields = ['category = ?', 'subcategory = ?', 'rlhf = ?']
                update_values = [data['category'], data['subcategory'], 1 if data['rlhf'] else 0]
            else:
                update_fields.append('rlhf = ?')
                update_values.append(1 if data['rlhf'] else 0)
        
        # Verificar se company foi fornecido
        if 'company' in data:
            update_fields.append('company = ?')
            update_values.append(data['company'] or '')
        
        # Verificar se name foi fornecido
        if 'name' in data:
            update_fields.append('name = ?')
            update_values.append(data['name'] or '')
        
        # Verificar se erp foi fornecido
        if 'erp' in data:
            update_fields.append('erp = ?')
            update_values.append(data['erp'] or '')
        
        # Verificar se channel foi fornecido
        if 'channel' in data:
            update_fields.append('channel = ?')
            update_values.append(data['channel'] or '')
        
        # Verificar se customerNumber foi fornecido
        if 'customerNumber' in data:
            update_fields.append('customerNumber = ?')
            update_values.append(data['customerNumber'] or '')
        
        # Montar query dinâmica
        query = f"""
            UPDATE session_classifications 
            SET {', '.join(update_fields)}
            WHERE sessionID = ?
        """
        update_values.append(session_id)
        
        # Atualizar conversa
        cursor.execute(query, update_values)
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'Sessão não encontrada'})
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Conversa atualizada com sucesso'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stats')
def get_stats():
    """API para estatísticas gerais"""
    try:
        conn = sqlite3.connect(analyzer.db_path)
        cursor = conn.cursor()
        
        # Estatísticas gerais
        cursor.execute("SELECT COUNT(*) FROM session_classifications")
        total_conversations = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(confidence) FROM session_classifications WHERE confidence IS NOT NULL")
        avg_confidence = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM session_classifications WHERE has_handoff = 1")
        with_handoff = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT primary_agent) FROM session_classifications WHERE primary_agent IS NOT NULL")
        unique_agents = cursor.fetchone()[0]
        
        conn.close()
        
        stats = {
            'total_conversations': total_conversations,
            'avg_confidence': round(avg_confidence, 3) if avg_confidence else 0,
            'handoff_rate': round((with_handoff / total_conversations) * 100, 1) if total_conversations > 0 else 0,
            'unique_agents': unique_agents
        }
        
        return jsonify({'success': True, 'data': stats})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    print("🚀 CONVERSATION ANALYZER APP")
    print("=" * 40)
    print("📊 Interface para análise de conversas")
    print(f"🌐 Porta: {port}")
    print("=" * 40)
    
    app.run(debug=debug, host='0.0.0.0', port=port)