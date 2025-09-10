#!/usr/bin/env python3
"""
Script para reorganizar subcategorias de todas as categorias
Cria distribuições mais equilibradas e significativas
"""

import sqlite3
from datetime import datetime

class AllCategoriesReorganizer:
    def __init__(self):
        self.db_path = 'talqui.db'
        
        # Mapeamentos específicos por categoria
        self.mappings = {
            'COMERCIAL': {
                'consulta de preços/planos': [
                    'preço', 'plano', 'valor', 'custo', 'orçamento', 'proposta', 'cotação', 'tabela'
                ],
                'prospecção/contato inicial': [
                    'prospecção', 'contato inicial', 'primeiro contato', 'apresentação', 'inicial'
                ],
                'follow-up comercial': [
                    'follow-up', 'followup', 'acompanhamento', 'retorno', 'recontato'
                ],
                'demonstração/teste': [
                    'demonstração', 'demo', 'teste', 'trial', 'avaliação', 'experimentar'
                ],
                'interesse em produtos/serviços': [
                    'interesse', 'conhecer', 'informações sobre', 'saber mais', 'produto', 'serviço'
                ],
                'negociação/fechamento': [
                    'negociação', 'fechamento', 'contratação', 'assinatura', 'contrato', 'venda'
                ],
                'integração/implementação': [
                    'integração', 'implementação', 'instalação', 'setup', 'configuração comercial'
                ],
                'onboarding comercial': [
                    'onboarding', 'primeiros passos', 'ajuda inicial', 'orientação inicial'
                ]
            },
            'OUTROS': {
                'conversa incompleta/abandonada': [
                    'incompleta', 'abandonada', 'inconclusiva', 'indefinida', 'interrompida'
                ],
                'primeiro contato/boas-vindas': [
                    'primeiro contato', 'boas-vindas', 'boas vindas', 'bem-vindo', 'novo usuário'
                ],
                'redirecionamento/transferência': [
                    'redirecionamento', 'transferência', 'encaminhar', 'direcionar', 'novo canal'
                ],
                'teste/verificação sistema': [
                    'teste', 'verificação', 'test', 'check', 'validação'
                ],
                'contato não respondido': [
                    'não respondida', 'sem resposta', 'não atendida', 'sem retorno'
                ],
                'contato proativo': [
                    'proativo', 'ativo', 'iniciativa', 'contato empresa'
                ],
                'saudações/cortesia': [
                    'saudação', 'cortesia', 'obrigado', 'agradecimento', 'cumprimento'
                ],
                'conversa social/pessoal': [
                    'social', 'pessoal', 'conversa', 'papo', 'bate-papo'
                ]
            },
            'FINANCEIRO': {
                'lembrete de pagamento': [
                    'lembrete', 'aviso', 'notificação', 'alerta de pagamento'
                ],
                'envio de boleto/cobrança': [
                    'boleto', 'cobrança', 'fatura', 'envio', 'segunda via'
                ],
                'confirmação de pagamento': [
                    'confirmação', 'comprovante', 'pagamento efetuado', 'quitação'
                ],
                'dúvidas sobre fatura': [
                    'dúvida', 'esclarecimento', 'questionamento sobre fatura'
                ],
                'problemas de pagamento': [
                    'problema', 'erro', 'falha no pagamento', 'pagamento rejeitado'
                ],
                'negociação/parcelamento': [
                    'negociação', 'parcelamento', 'acordo', 'renegociação'
                ],
                'alteração dados cobrança': [
                    'alteração', 'mudança', 'atualização de dados', 'endereço cobrança'
                ],
                'solicitação de desconto': [
                    'desconto', 'promoção', 'redução', 'oferta especial'
                ]
            },
            'INFORMACAO': {
                'boas-vindas/primeiro contato': [
                    'boas-vindas', 'bem-vindo', 'primeiro contato', 'novo usuário'
                ],
                'dúvidas sobre criação de conta': [
                    'criação', 'conta', 'cadastro', 'registro', 'sign up'
                ],
                'dúvidas sobre funcionalidades': [
                    'funcionalidade', 'recurso', 'como usar', 'como funciona'
                ],
                'comunicação de novidades': [
                    'novidade', 'atualização', 'nova funcionalidade', 'lançamento'
                ],
                'onboarding/orientação': [
                    'onboarding', 'orientação', 'ajuda inicial', 'primeiros passos'
                ],
                'consulta sobre integrações': [
                    'integração', 'conectar', 'sincronizar', 'api'
                ],
                'informações gerais': [
                    'informação', 'esclarecimento', 'dúvida geral', 'explicação'
                ],
                'documentação/tutorial': [
                    'documentação', 'tutorial', 'manual', 'guia'
                ]
            },
            'RECLAMACAO': {
                'problema não resolvido': [
                    'não resolvido', 'não solucionado', 'persiste', 'continua'
                ],
                'demora no atendimento': [
                    'demora', 'lentidão', 'demorado', 'tempo de resposta'
                ],
                'falta de retorno/comunicação': [
                    'falta de retorno', 'sem retorno', 'não respondeu', 'comunicação'
                ],
                'problemas técnicos recorrentes': [
                    'recorrente', 'repetindo', 'sempre', 'toda vez'
                ],
                'insatisfação com serviço': [
                    'insatisfação', 'descontentamento', 'não atende', 'ruim'
                ],
                'cobrança indevida': [
                    'cobrança indevida', 'erro cobrança', 'cobrança errada'
                ],
                'suspensão/bloqueio indevido': [
                    'suspensão', 'bloqueio', 'indevida', 'sem motivo'
                ],
                'problemas de qualidade': [
                    'qualidade', 'funcionamento', 'performance', 'instabilidade'
                ]
            },
            'CANCELAMENTO': {
                'solicitação de cancelamento': [
                    'cancelamento', 'cancelar', 'encerrar', 'finalizar'
                ],
                'desativação de serviços': [
                    'desativação', 'desativar', 'parar', 'suspender'
                ],
                'exclusão de conta/dados': [
                    'exclusão', 'excluir', 'deletar', 'remover conta'
                ],
                'encerramento de parceria': [
                    'encerramento', 'fim', 'término', 'parceria'
                ],
                'desistência por preço': [
                    'preço', 'caro', 'valor', 'custo alto'
                ],
                'desinteresse no produto': [
                    'desinteresse', 'não precisa', 'não usa', 'não serve'
                ],
                'mudança de fornecedor': [
                    'mudança', 'outro fornecedor', 'concorrente', 'migração'
                ],
                'problemas técnicos graves': [
                    'problema grave', 'não funciona', 'instável', 'falha crítica'
                ]
            }
        }
    
    def classify_subcategory(self, category, original_summary):
        """Classifica baseado no mapeamento da categoria"""
        if category not in self.mappings:
            return 'outros'
            
        summary_lower = original_summary.lower()
        
        for new_subcat, keywords in self.mappings[category].items():
            for keyword in keywords:
                if keyword in summary_lower:
                    return new_subcat
        
        return 'outros'
    
    def reorganize_category(self, category):
        """Reorganiza uma categoria específica"""
        
        print(f"\n🔄 Reorganizando: {category}")
        print("-" * 40)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Buscar sessões da categoria
        cursor.execute("""
            SELECT sessionID, summary, subcategory
            FROM session_classifications 
            WHERE category = ?
        """, (category,))
        
        sessions = cursor.fetchall()
        
        if not sessions:
            print(f"⚠️  Nenhuma sessão encontrada para {category}")
            conn.close()
            return
        
        print(f"📊 Total de sessões: {len(sessions)}")
        
        # Contador para novas categorias
        new_categories = {}
        updated_count = 0
        
        # Processar cada sessão
        for session_id, summary, current_subcat in sessions:
            new_subcat = self.classify_subcategory(category, summary)
            
            # Contar distribuição
            if new_subcat not in new_categories:
                new_categories[new_subcat] = 0
            new_categories[new_subcat] += 1
            
            # Atualizar se mudou
            if new_subcat != current_subcat:
                cursor.execute("""
                    UPDATE session_classifications 
                    SET subcategory = ? 
                    WHERE sessionID = ? AND category = ?
                """, (new_subcat, session_id, category))
                updated_count += 1
        
        conn.commit()
        conn.close()
        
        # Mostrar distribuição
        total_sessions = sum(new_categories.values())
        print(f"📈 Nova distribuição ({len(new_categories)} subcategorias):")
        
        for subcat, count in sorted(new_categories.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_sessions) * 100
            print(f"  {subcat[:35]:35} | {count:3d} ({percentage:5.1f}%)")
        
        print(f"🔄 Sessões atualizadas: {updated_count}")
        
        return len(new_categories), updated_count
    
    def reorganize_all(self):
        """Reorganiza todas as categorias"""
        
        print("🔧 REORGANIZANDO TODAS AS CATEGORIAS")
        print("=" * 50)
        
        # Backup geral
        conn = sqlite3.connect(self.db_path)
        backup_name = f"session_classifications_backup_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        conn.execute(f"CREATE TABLE {backup_name} AS SELECT * FROM session_classifications")
        conn.close()
        print(f"✅ Backup criado: {backup_name}")
        
        categories_to_process = ['COMERCIAL', 'OUTROS', 'FINANCEIRO', 'INFORMACAO', 'RECLAMACAO', 'CANCELAMENTO']
        
        total_subcats = 0
        total_updated = 0
        
        for category in categories_to_process:
            subcats, updated = self.reorganize_category(category)
            total_subcats += subcats
            total_updated += updated
        
        print(f"\n🎉 REORGANIZAÇÃO COMPLETA!")
        print(f"📊 Total de subcategorias criadas: {total_subcats}")
        print(f"🔄 Total de sessões atualizadas: {total_updated:,}")
        print(f"💾 Backup: {backup_name}")
        
        # Exportar resultado final
        self.export_final_csv()
    
    def export_final_csv(self):
        """Exporta CSV final com todas as reorganizações"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT sessionID, category, subcategory, confidence, reasoning, 
                   classified_at, messages_analyzed, summary
            FROM session_classifications 
            ORDER BY category, subcategory
        """)
        
        import csv
        filename = "FINAL_ALL_CLASSIFICATIONS.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow(['sessionID', 'category', 'subcategory', 'confidence', 
                           'reasoning', 'classified_at', 'messages_analyzed', 'summary'])
            
            # Data
            for row in cursor.fetchall():
                writer.writerow(row)
        
        conn.close()
        
        print(f"\n📄 Arquivo final exportado: {filename}")
        
        # Mostrar estatísticas finais
        self.show_final_stats()
    
    def show_final_stats(self):
        """Mostra estatísticas finais de todas as categorias"""
        
        print(f"\n📈 ESTATÍSTICAS FINAIS DE TODAS AS CATEGORIAS:")
        print("=" * 60)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Por categoria
        cursor.execute("""
            SELECT category, 
                   COUNT(DISTINCT subcategory) as subcats_count,
                   COUNT(*) as sessions_count
            FROM session_classifications 
            GROUP BY category 
            ORDER BY sessions_count DESC
        """)
        
        for category, subcats, sessions in cursor.fetchall():
            print(f"{category:15} | {subcats:2d} subcategorias | {sessions:4d} sessões")
        
        # Total geral
        cursor.execute("SELECT COUNT(*) FROM session_classifications")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT subcategory) FROM session_classifications")
        total_subcats = cursor.fetchone()[0]
        
        print(f"\n📊 RESUMO GERAL:")
        print(f"Total de sessões: {total:,}")
        print(f"Total de subcategorias: {total_subcats}")
        print(f"Média por categoria: {total_subcats/7:.1f}")
        
        conn.close()

def main():
    reorganizer = AllCategoriesReorganizer()
    reorganizer.reorganize_all()

if __name__ == "__main__":
    main()