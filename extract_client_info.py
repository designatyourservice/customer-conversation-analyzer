#!/usr/bin/env python3
"""
Script para extrair informações de clientes (nome e empresa) das conversas
usando análise de LLM (Deepseek) com base nas mensagens recebidas.
"""

import sqlite3
import requests
import json
import time
from typing import Dict, List, Optional, Tuple
import re

class ClientInfoExtractor:
    def __init__(self, db_path: str = 'talqui.db'):
        self.db_path = db_path
        
    def get_all_sessions(self) -> List[str]:
        """Obtém todas as sessões que ainda não têm informações de cliente preenchidas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Buscar apenas sessões que não têm name e company preenchidos (limitando para teste)
        cursor.execute("""
            SELECT sessionID 
            FROM session_classifications 
            WHERE (name IS NULL OR name = '' OR name = 'Não informado') 
            AND (company IS NULL OR company = '' OR company = 'Não informado')
            ORDER BY classified_at DESC
            LIMIT 200
        """)
        
        sessions = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        print(f"Encontradas {len(sessions)} sessões para análise")
        return sessions
    
    def get_session_messages(self, session_id: str) -> List[Dict]:
        """Obtém todas as mensagens de uma sessão, focando nas inbound (cliente)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT messageDirection, messageValue, message_createdAt
            FROM talqui_unified 
            WHERE sessionID = ? 
            ORDER BY message_createdAt ASC
        """, (session_id,))
        
        messages = []
        for row in cursor.fetchall():
            # Focar apenas nas mensagens inbound (do cliente)
            if row[0] == 'inbound':
                messages.append({
                    'direction': row[0],
                    'content': row[1],
                    'timestamp': row[2]
                })
        
        conn.close()
        return messages
    
    def analyze_with_deepseek(self, client_messages: List[str]) -> Dict:
        """Análise usando Deepseek para extrair nome e empresa do cliente"""
        
        # Combinar mensagens do cliente
        combined_messages = "\n".join(client_messages[:10])  # Máximo 10 mensagens
        
        # Prompt otimizado para extração de informações do cliente
        prompt = f"""
Analise as mensagens abaixo que foram enviadas por um CLIENTE para um atendimento ao cliente. 
Extraia APENAS informações sobre o CLIENTE (não sobre os agentes de atendimento).

MENSAGENS DO CLIENTE:
{combined_messages}

Tarefa: Identifique o nome da pessoa (cliente) e o nome da empresa do cliente.

Regras importantes:
1. IGNORE qualquer menção a agentes, atendentes ou funcionários da empresa que está prestando o atendimento
2. Procure apenas por informações sobre o CLIENTE que está sendo atendido
3. Nomes de pessoas devem ser nomes próprios completos (ex: "João Silva", "Maria Santos")  
4. Nomes de empresas devem ser razões sociais ou nomes fantasia (ex: "TechCorp Ltda", "Padaria Central")
5. Se não tiver certeza suficiente (>80%), não extraia a informação

Responda APENAS em formato JSON:
{{
    "name": "nome completo da pessoa cliente ou null",
    "company": "nome da empresa do cliente ou null",  
    "confidence_name": 0.0-1.0,
    "confidence_company": 0.0-1.0,
    "reasoning": "breve explicação do que foi encontrado"
}}
"""
        
        try:
            # Simulando chamada para Deepseek - substitua pela API real
            # Por enquanto, vou usar uma análise baseada em padrões
            result = self.analyze_with_patterns(combined_messages)
            return result
            
        except Exception as e:
            print(f"Erro na análise: {e}")
            return {
                "name": None,
                "company": None, 
                "confidence_name": 0.0,
                "confidence_company": 0.0,
                "reasoning": f"Erro na análise: {str(e)}"
            }
    
    def analyze_with_patterns(self, text: str) -> Dict:
        """Análise baseada em padrões regex enquanto não temos acesso ao Deepseek"""
        
        # Filtrar mensagens de assistentes virtuais (não são de clientes reais)
        if '👩🏽‍💻' in text or 'assistente virtual' in text.lower():
            return {
                "name": None,
                "company": None,
                "confidence_name": 0.0,
                "confidence_company": 0.0,
                "reasoning": "Mensagem de assistente virtual ignorada"
            }
        
        # Padrões para identificar nomes de pessoas (ordem por prioridade)
        name_patterns = [
            r'(?:meu nome é|me chamo|sou (?:a|o))\s+([A-ZÀ-Ÿ][a-zà-ÿ]+(?:\s+[A-ZÀ-Ÿ][a-zà-ÿ]+)*)',  # Nome com contexto explícito
            r'^([A-ZÀ-Ÿ][a-zà-ÿ]{4,})$',  # Nome sozinho em linha própria (mín 5 chars)
        ]
        
        # Padrões para identificar empresas (ordem por prioridade)
        company_patterns = [
            r'(?:empresa|companhia|firma)\s+([A-Z][A-Za-z\s\-]{4,})',
            r'(?:da empresa)\s+([A-Z][A-Za-z\s\-]{4,})',
            r'\*([A-Z][A-Z\-]{3,})\*',  # Nomes em asteriscos como *SGPFLOW*
            r'([A-Z][A-Za-z\s\-]+(?:Ltda|LTDA|S\.A\.|SA|ME|EPP|Corp|Inc))',
            r'^([A-Z][a-z]+(?:[A-Z][a-z]*){2,})$',  # Palavras compostas em linha própria
        ]
        
        name_found = None
        company_found = None
        name_confidence = 0.0
        company_confidence = 0.0
        
        # Buscar nome da pessoa primeiro
        used_text_for_name = None
        for i, pattern in enumerate(name_patterns):
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                potential_name = matches[0].strip()
                # Verificar se não é uma palavra comum/genérica
                common_words = ['bom', 'boa', 'dia', 'tarde', 'noite', 'ok', 'sim', 'não', 'obrigada', 'obrigado', 
                               'mas', 'uma', 'sou', 'dias', 'pouco', 'breve', 'boleto', 'antes', 'gostaria',
                               'enorme', 'estou', 'configurar', 'precisando', 'ordem', 'gerente', 'supervisora',
                               'empresa', 'companhia', 'firma']
                if potential_name.lower() not in common_words and len(potential_name) >= 4:
                    name_found = potential_name.title()
                    used_text_for_name = potential_name.lower()
                    # Confiança baseada no tipo de padrão
                    if i == 0:  # Padrão "meu nome é..."
                        name_confidence = 0.95
                    else:  # Nome sozinho
                        name_confidence = 0.85
                    break
        
        # Buscar nome da empresa (evitando texto já usado para nome)
        for i, pattern in enumerate(company_patterns):
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                potential_company = matches[0].strip()
                # Verificar se não é o mesmo texto usado para nome
                if used_text_for_name and potential_company.lower() == used_text_for_name:
                    continue
                    
                # Verificar se não é uma palavra muito genérica
                invalid_companies = ['assistente', 'virtual', 'startup', 'mensagem', 'dor', 'nome', 'meu']
                if (len(potential_company) >= 4 and 
                    potential_company.lower() not in invalid_companies and
                    not any(word in potential_company.lower() for word in invalid_companies)):
                    # Limpar e formatar
                    potential_company = potential_company.replace('*', '').strip()
                    company_found = potential_company
                    # Confiança baseada no tipo de padrão
                    if i < 2:  # Padrões com contexto explícito de empresa
                        company_confidence = 0.90
                    elif i == 2:  # Padrão com asteriscos
                        company_confidence = 0.85
                    else:
                        company_confidence = 0.75
                    break
        
        return {
            "name": name_found,
            "company": company_found,
            "confidence_name": name_confidence,
            "confidence_company": company_confidence,
            "reasoning": f"Análise por padrões. Nome: {'encontrado' if name_found else 'não encontrado'}, Empresa: {'encontrada' if company_found else 'não encontrada'}"
        }
    
    def update_client_info(self, session_id: str, name: str, company: str) -> bool:
        """Atualiza as informações do cliente no banco de dados"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE session_classifications 
                SET name = ?, company = ?
                WHERE sessionID = ?
            """, (name or '', company or '', session_id))
            
            updated = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return updated
        except Exception as e:
            print(f"Erro ao atualizar sessão {session_id}: {e}")
            return False
    
    def process_all_sessions(self):
        """Processa todas as sessões para extrair informações de clientes"""
        sessions = self.get_all_sessions()
        
        processed = 0
        updated = 0
        
        print("Iniciando análise de sessões...")
        
        for i, session_id in enumerate(sessions):
            print(f"\nProcessando sessão {i+1}/{len(sessions)}: {session_id[:8]}...")
            
            # Obter mensagens do cliente
            messages = self.get_session_messages(session_id)
            
            if not messages:
                print("  - Nenhuma mensagem do cliente encontrada")
                continue
            
            # Extrair conteúdo das mensagens
            client_messages = [msg['content'] for msg in messages if msg['content'].strip()]
            
            if not client_messages:
                print("  - Mensagens vazias")
                continue
            
            # Analisar com IA
            result = self.analyze_with_deepseek(client_messages)
            
            # Verificar confiança e atualizar se necessário
            should_update_name = (result['confidence_name'] > 0.8 and result['name'])
            should_update_company = (result['confidence_company'] > 0.8 and result['company'])
            
            if should_update_name or should_update_company:
                name = result['name'] if should_update_name else None
                company = result['company'] if should_update_company else None
                
                if self.update_client_info(session_id, name, company):
                    updated += 1
                    print(f"  ✅ Atualizado - Nome: {name}, Empresa: {company}")
                    print(f"     Confiança - Nome: {result['confidence_name']:.1%}, Empresa: {result['confidence_company']:.1%}")
                else:
                    print(f"  ❌ Erro na atualização")
            else:
                print(f"  - Confiança baixa - Nome: {result['confidence_name']:.1%}, Empresa: {result['confidence_company']:.1%}")
            
            processed += 1
            
            # Pequena pausa para não sobrecarregar
            time.sleep(0.1)
        
        print(f"\n{'='*50}")
        print(f"Análise concluída!")
        print(f"Sessões processadas: {processed}")
        print(f"Sessões atualizadas: {updated}")
        print(f"{'='*50}")

def main():
    print("🔍 EXTRAÇÃO DE INFORMAÇÕES DE CLIENTES")
    print("="*50)
    
    extractor = ClientInfoExtractor()
    extractor.process_all_sessions()

if __name__ == "__main__":
    main()