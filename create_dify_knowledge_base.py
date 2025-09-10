#!/usr/bin/env python3
"""
Script para criar base de conhecimento técnico para Dify
Extrai resoluções de Alison e João para treinar Isabella
"""

import sqlite3
import json
import re
from collections import defaultdict

class DifyKnowledgeBaseCreator:
    def __init__(self, db_path: str = 'talqui.db'):
        self.db_path = db_path
        self.knowledge_base = []
        
    def clean_message(self, message: str) -> str:
        """Limpa mensagem removendo assinaturas e formatações"""
        if not message:
            return ""
        
        # Remover assinaturas
        message = re.sub(r'\*[^*]+\*:', '', message)
        message = re.sub(r'\*[^*]+\*', '', message)
        
        # Remover quebras de linha excessivas
        message = re.sub(r'\n+', ' ', message)
        
        # Remover espaços extras
        message = re.sub(r'\s+', ' ', message)
        
        return message.strip()
    
    def chunk_text(self, text: str, max_chars: int = 900) -> list:
        """Divide texto em chunks adequados para Dify"""
        if len(text) <= max_chars:
            return [text]
        
        chunks = []
        sentences = text.split('. ')
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) <= max_chars:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def extract_problem_and_solution(self, session_id: str, subcategory: str, agent: str):
        """Extrai problema e solução de uma sessão"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Buscar mensagens da sessão
        cursor.execute("""
            SELECT messageDirection, messageValue, message_createdAt
            FROM talqui_unified 
            WHERE sessionID = ? AND messageValue IS NOT NULL
            ORDER BY message_createdAt ASC
        """, (session_id,))
        
        messages = cursor.fetchall()
        
        inbound_msgs = []
        outbound_msgs = []
        
        for direction, content, timestamp in messages:
            clean_content = self.clean_message(content)
            if len(clean_content) > 20:  # Filtrar mensagens muito curtas
                if direction == 'inbound':
                    inbound_msgs.append(clean_content)
                else:
                    outbound_msgs.append(clean_content)
        
        conn.close()
        
        # Combinar mensagens para formar problema e solução
        problem = " ".join(inbound_msgs[:3])  # Primeiras 3 mensagens do cliente
        solution = " ".join(outbound_msgs[:5])  # Primeiras 5 respostas do agente
        
        return {
            'subcategory': subcategory,
            'agent': agent,
            'problem': problem,
            'solution': solution
        }
    
    def create_qa_pairs(self):
        """Cria pares de pergunta e resposta por subcategoria"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Buscar sessões resolvidas por Alison e João
        cursor.execute("""
            SELECT sessionID, subcategory, primary_agent, summary
            FROM session_classifications 
            WHERE primary_agent IN ('Alison', 'João') 
            AND has_handoff = 0 
            AND category = 'SUPORTE_TECNICO'
            AND subcategory != 'outros'
            ORDER BY subcategory, sessionID
        """)
        
        sessions = cursor.fetchall()
        
        qa_by_category = defaultdict(list)
        
        for session_id, subcategory, agent, summary in sessions:
            data = self.extract_problem_and_solution(session_id, subcategory, agent)
            
            if data['problem'] and data['solution']:
                qa_by_category[subcategory].append(data)
        
        conn.close()
        return qa_by_category
    
    def generate_dify_chunks(self, qa_data):
        """Gera chunks formatados para Dify"""
        
        # Templates por categoria
        templates = {
            'problemas de integração': {
                'questions': [
                    "Como resolver problemas de conexão do WhatsApp Business?",
                    "O que fazer quando o QR Code não conecta?",
                    "Como reconectar o WhatsApp na plataforma?",
                    "Problemas de integração com WhatsApp, como resolver?",
                    "WhatsApp Business não conecta, qual a solução?"
                ],
                'context': "Problemas de integração e conexão com WhatsApp Business"
            },
            'problemas de configuração': {
                'questions': [
                    "Como configurar o tempo de inatividade da sessão?",
                    "Como alterar configurações visuais da interface?",
                    "Como configurar promessa de pagamento via chat?",
                    "Problemas de configuração no sistema, como resolver?",
                    "Como fazer configurações avançadas na plataforma?"
                ],
                'context': "Configurações e personalizações do sistema"
            },
            'problemas de mensagens/whatsapp': {
                'questions': [
                    "Mensagens duplicadas no WhatsApp, como resolver?",
                    "Problemas de entrega de mensagens, qual a solução?",
                    "Como resolver problemas com imagens no WhatsApp?",
                    "Mensagens de localização não funcionam, como corrigir?",
                    "Disparo de faturas com erro, como resolver?"
                ],
                'context': "Problemas específicos com mensagens no WhatsApp"
            },
            'problemas de funcionamento/sistema': {
                'questions': [
                    "Sistema com problemas de formatação de texto?",
                    "Como resolver problemas de funcionamento do chatbot?",
                    "Verificação de funcionamento da localização?",
                    "Sistema apresentando erros, como diagnosticar?",
                    "Problemas gerais de funcionamento, como resolver?"
                ],
                'context': "Problemas gerais de funcionamento do sistema"
            },
            'problemas de acesso/login': {
                'questions': [
                    "Não consigo acessar a plataforma, como resolver?",
                    "Problemas com login no Meta Business?",
                    "Como configurar conta do Facebook para acesso?",
                    "Erro de acesso após configuração, o que fazer?",
                    "Problemas de autenticação, como resolver?"
                ],
                'context': "Problemas de acesso e autenticação"
            },
            'problemas com chatbot/automação': {
                'questions': [
                    "Chatbot ficou offline, como reativar?",
                    "Como otimizar fluxo de atendimento automático?",
                    "Problemas técnicos com chatbot, como resolver?",
                    "Conectividade do chatbot com problema, o que fazer?",
                    "Automação não funciona, como corrigir?"
                ],
                'context': "Problemas com chatbot e automação"
            }
        }
        
        chunks = []
        
        for subcategory, data_list in qa_data.items():
            if subcategory not in templates:
                continue
                
            template = templates[subcategory]
            
            # Extrair soluções reais dos especialistas
            solutions = []
            for data in data_list[:3]:  # Top 3 soluções
                if data['solution'] and len(data['solution']) > 50:
                    solutions.append(data['solution'][:800])  # Limitar tamanho
            
            # Criar múltiplos chunks por categoria
            for i, question in enumerate(template['questions']):
                solution_text = solutions[i % len(solutions)] if solutions else "Encaminhar para suporte técnico especializado."
                
                # Criar chunk com pergunta e resposta
                chunk_content = f"""PERGUNTA: {question}

CONTEXTO: {template['context']}

RESOLUÇÃO:
{solution_text}

ESPECIALISTA: Baseado nas resoluções de {', '.join(set([d['agent'] for d in data_list]))}"""
                
                # Dividir em chunks se necessário
                chunk_parts = self.chunk_text(chunk_content, 950)
                
                for j, chunk_part in enumerate(chunk_parts):
                    chunks.append({
                        'id': f"{subcategory.replace(' ', '_')}_{i+1}_{j+1}",
                        'category': subcategory,
                        'question': question,
                        'content': chunk_part,
                        'tokens': len(chunk_part.split()),
                        'chars': len(chunk_part)
                    })
        
        return chunks
    
    def create_knowledge_base(self):
        """Cria a base de conhecimento completa"""
        print("🔍 Extraindo resoluções técnicas dos especialistas...")
        qa_data = self.create_qa_pairs()
        
        print("📝 Gerando chunks para Dify...")
        chunks = self.generate_dify_chunks(qa_data)
        
        print(f"✅ {len(chunks)} chunks criados")
        
        # Estatísticas
        total_chars = sum(chunk['chars'] for chunk in chunks)
        total_tokens = sum(chunk['tokens'] for chunk in chunks)
        
        print(f"📊 Total: {total_chars:,} caracteres, ~{total_tokens:,} tokens")
        
        return {
            'metadata': {
                'created_at': '2025-09-06',
                'purpose': 'Base de conhecimento técnico para treinamento de Isabella',
                'source': 'Resoluções dos especialistas Alison e João',
                'total_chunks': len(chunks),
                'total_chars': total_chars,
                'total_tokens': total_tokens
            },
            'chunks': chunks
        }
    
    def export_to_dify_format(self, filename='DIFY_TECHNICAL_KNOWLEDGE_BASE.json'):
        """Exporta no formato adequado para Dify"""
        knowledge_base = self.create_knowledge_base()
        
        # Formato específico para Dify
        dify_format = {
            'version': '1.0',
            'type': 'technical_support',
            'language': 'pt-BR',
            'chunks': []
        }
        
        for chunk in knowledge_base['chunks']:
            dify_format['chunks'].append({
                'content': chunk['content'],
                'metadata': {
                    'category': chunk['category'],
                    'question': chunk['question'],
                    'id': chunk['id']
                }
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(dify_format, f, ensure_ascii=False, indent=2)
        
        print(f"📄 Base de conhecimento salva: {filename}")
        
        # Criar também versão markdown para visualização
        md_filename = filename.replace('.json', '.md')
        with open(md_filename, 'w', encoding='utf-8') as f:
            f.write("# Base de Conhecimento Técnico para Isabella\n\n")
            f.write("## Resoluções baseadas na expertise de Alison e João\n\n")
            
            current_category = None
            for chunk in knowledge_base['chunks']:
                if chunk['category'] != current_category:
                    current_category = chunk['category']
                    f.write(f"\n## 🔧 {current_category.title()}\n\n")
                
                f.write(f"### {chunk['question']}\n\n")
                f.write(f"{chunk['content']}\n\n")
                f.write("---\n\n")
        
        print(f"📄 Versão markdown salva: {md_filename}")
        
        return filename, knowledge_base['metadata']

def main():
    creator = DifyKnowledgeBaseCreator()
    filename, metadata = creator.export_to_dify_format()
    
    print("\n✅ BASE DE CONHECIMENTO CRIADA PARA DIFY!")
    print(f"📄 Arquivo: {filename}")
    print(f"📊 Chunks: {metadata['total_chunks']}")
    print(f"📝 Caracteres: {metadata['total_chars']:,}")
    print(f"🎯 Tokens estimados: {metadata['total_tokens']:,}")

if __name__ == "__main__":
    main()