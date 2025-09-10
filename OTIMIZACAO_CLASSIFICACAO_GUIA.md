# 🤖 Guia de Otimização de Classificação de Sessões

## 📋 Visão Geral
Este documento detalha o processo completo de otimização das classificações de sessões de atendimento, incluindo regras de negócio, procedimentos e scripts para execução automatizada após a classificação inicial pelo DeepSeek.

## 🎯 Objetivos da Otimização
- **Reduzir subcategorias** para máximo 10 por categoria principal
- **Consolidar subcategorias similares** com baixo volume (< 50 sessões)
- **Manter rastreabilidade** dos dados originais
- **Criar distribuições equilibradas** e significativas
- **Facilitar análise** e geração de insights

## 📊 Estrutura de Dados

### Tabela Principal: `session_classifications`
```sql
CREATE TABLE session_classifications (
    sessionID TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    subcategory TEXT NOT NULL,
    confidence REAL,
    reasoning TEXT,
    classified_at TIMESTAMP,
    messages_analyzed INTEGER,
    summary TEXT  -- Subcategoria original para rastreabilidade
);
```

### Categorias Principais (7)
1. **COMERCIAL** - Interesse em produtos, preços, planos, vendas
2. **SUPORTE_TECNICO** - Problemas técnicos, bugs, configurações
3. **FINANCEIRO** - Pagamentos, cobrança, faturas, reembolsos
4. **INFORMACAO** - Dúvidas gerais, informações sobre serviços
5. **RECLAMACAO** - Insatisfação, problemas, críticas
6. **CANCELAMENTO** - Solicitação de cancelamento de serviços
7. **OUTROS** - Casos que não se encaixam nas categorias acima

## 🔄 Processo de Otimização (Passo a Passo)

### Fase 1: Análise Inicial
1. **Backup dos dados originais**
2. **Criação da coluna `summary`** para preservar subcategorias originais
3. **Análise de distribuição** atual por categoria
4. **Identificação de candidatos** para consolidação

### Fase 2: Reorganização por Categoria

#### SUPORTE_TECNICO (Target: 10 subcategorias)
**Mapeamento de palavras-chave:**
```python
suporte_mapping = {
    'problemas de acesso/login': [
        'acesso', 'login', 'entrar', 'conta', 'senha', 'bloqueio', 'liberação'
    ],
    'problemas de integração': [
        'integração', 'api', 'webhook', 'conexão', 'sgp', 'ixc', 'ifood', 'marketplace'
    ],
    'problemas de mensagens/whatsapp': [
        'mensagem', 'whatsapp', 'envio', 'recebimento', 'entrega', 'disparo'
    ],
    'problemas de configuração': [
        'configuração', 'configurar', 'setup', 'atalho', 'personalização', 'ajuste'
    ],
    'problemas de funcionamento/sistema': [
        'funcionamento', 'sistema', 'plataforma', 'erro', 'bug', 'falha', 'travou'
    ],
    'problemas com chatbot/automação': [
        'chatbot', 'bot', 'robô', 'automação', 'fluxo', 'resposta automática'
    ],
    'migração/mudanças técnicas': [
        'migração', 'migrar', 'mudança', 'transferência', 'host', 'ip', 'servidor'
    ],
    'problemas de cobrança/boletos': [
        'boleto', 'cobrança', 'fatura', 'pagamento', 'financeiro'
    ],
    'suporte técnico geral': [
        'suporte', 'ajuda', 'orientação', 'dúvida técnica', 'esclarecimento'
    ]
}
```

#### COMERCIAL (Target: 7-9 subcategorias)
**Mapeamento de palavras-chave:**
```python
comercial_mapping = {
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
}
```

#### FINANCEIRO (Target: 4-7 subcategorias)
**Mapeamento de palavras-chave:**
```python
financeiro_mapping = {
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
    ]
}
```

#### INFORMACAO (Target: 7-8 subcategorias)
**Mapeamento de palavras-chave:**
```python
informacao_mapping = {
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
    ]
}
```

#### OUTROS (Target: 7-9 subcategorias)
**Mapeamento de palavras-chave:**
```python
outros_mapping = {
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
}
```

#### RECLAMACAO (Target: 4-7 subcategorias)
**Mapeamento de palavras-chave:**
```python
reclamacao_mapping = {
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
    ]
}
```

#### CANCELAMENTO (Target: 3-6 subcategorias)
**Mapeamento de palavras-chave:**
```python
cancelamento_mapping = {
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
    ]
}
```

### Fase 3: Unificações Específicas

#### Regras de Unificação por Categoria

**COMERCIAL:**
- `follow-up comercial` + `negociação/fechamento` → `follow-up/negociação`
- `integração/implementação` + `onboarding comercial` → `integração/onboarding`

**FINANCEIRO:**
- `lembrete de pagamento de fatura em atraso` + `lembrete de pagamento de fatura pendente` + `lembrete de pagamento de fatura próxima do vencimento` → `lembrete de pagamento`
- `confirmação de pagamento` + `problemas de pagamento` + `dúvidas sobre fatura` → `questões de pagamento`
- `alteração dados cobrança` → mover para `outros` (volume muito baixo)

**INFORMACAO:**
- `comunicação de atualização de funcionalidades do sistema` + `comunicação de novidades e atualizações de produto` + `comunicação de novidades e atualizações do sistema` → `comunicação de novidades`
- `onboarding/orientação` + `informações gerais` → `orientações gerais`

**OUTROS:**
- `contato não respondido` + `contato proativo` → `contatos proativos/não respondidos`
- `conversa social/pessoal` + `saudações/cortesia` → `interações sociais`

**RECLAMACAO:**
- `problema não resolvido` + `falta de retorno/comunicação` + `problemas de qualidade` → `problemas de atendimento`
- `suspensão/bloqueio indevido` + `insatisfação com serviço` → `problemas de serviço`

**CANCELAMENTO:**
- `exclusão de conta/dados` + `encerramento de parceria` + `desativação de serviços` + `desinteresse no produto` → `encerramentos diversos`

**SUPORTE_TECNICO:**
- `suporte técnico geral` + `migração/mudanças técnicas` + `problemas de cobrança/boletos` → `suporte técnico diverso`

### Fase 4: Critérios de Consolidação

#### Regras Gerais
1. **Threshold de Volume**: Subcategorias com < 50 sessões são candidatas para consolidação
2. **Similaridade Semântica**: Agrupar subcategorias com significado similar
3. **Relevância de Negócio**: Manter subcategorias estratégicas mesmo com baixo volume
4. **Limite por Categoria**: Máximo 10 subcategorias por categoria principal

#### Processo de Decisão
```python
def deve_consolidar(subcategoria, count, total_categoria):
    percentage = (count / total_categoria) * 100
    
    # Regras de consolidação
    if count < 5:  # Muito baixo volume
        return True
    elif count < 20 and percentage < 2:  # Baixo volume e baixa representatividade
        return True
    elif count < 50 and percentage < 5 and similar_exists():  # Volume médio mas similar existe
        return True
    else:
        return False
```

## 🛠️ Scripts de Automação

### Script Principal: `optimize_classifications.py`

```python
#!/usr/bin/env python3
"""
Script completo para otimização de classificações
Executa todas as fases do processo de otimização
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Tuple

class ClassificationOptimizer:
    def __init__(self, db_path: str = 'talqui.db'):
        self.db_path = db_path
        self.mappings = {
            # [Incluir todos os mapeamentos definidos acima]
        }
        
    def create_backup(self) -> str:
        """Cria backup da tabela atual"""
        conn = sqlite3.connect(self.db_path)
        backup_name = f"session_classifications_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        conn.execute(f"CREATE TABLE {backup_name} AS SELECT * FROM session_classifications")
        conn.commit()
        conn.close()
        return backup_name
    
    def add_summary_column(self):
        """Adiciona coluna summary se não existir"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("ALTER TABLE session_classifications ADD COLUMN summary TEXT")
            conn.execute("UPDATE session_classifications SET summary = subcategory WHERE summary IS NULL")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Coluna já existe
        conn.close()
    
    def classify_subcategory(self, category: str, original_summary: str) -> str:
        """Classifica baseado no mapeamento da categoria"""
        if category not in self.mappings:
            return 'outros'
            
        summary_lower = original_summary.lower()
        
        for new_subcat, keywords in self.mappings[category].items():
            for keyword in keywords:
                if keyword in summary_lower:
                    return new_subcat
        
        return 'outros'
    
    def reorganize_category(self, category: str) -> Tuple[int, int]:
        """Reorganiza uma categoria específica"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Buscar sessões da categoria
        cursor.execute("""
            SELECT sessionID, summary, subcategory
            FROM session_classifications 
            WHERE category = ?
        """, (category,))
        
        sessions = cursor.fetchall()
        updated_count = 0
        
        for session_id, summary, current_subcat in sessions:
            new_subcat = self.classify_subcategory(category, summary)
            
            if new_subcat != current_subcat:
                cursor.execute("""
                    UPDATE session_classifications 
                    SET subcategory = ? 
                    WHERE sessionID = ? AND category = ?
                """, (new_subcat, session_id, category))
                updated_count += 1
        
        conn.commit()
        
        # Contar subcategorias finais
        cursor.execute("""
            SELECT COUNT(DISTINCT subcategory) 
            FROM session_classifications 
            WHERE category = ?
        """, (category,))
        
        final_count = cursor.fetchone()[0]
        conn.close()
        
        return final_count, updated_count
    
    def apply_specific_unifications(self):
        """Aplica unificações específicas conforme regras definidas"""
        unifications = {
            'COMERCIAL': [
                (['follow-up comercial', 'negociação/fechamento'], 'follow-up/negociação'),
                (['integração/implementação', 'onboarding comercial'], 'integração/onboarding')
            ],
            'FINANCEIRO': [
                (['confirmação de pagamento', 'problemas de pagamento', 'dúvidas sobre fatura'], 'questões de pagamento'),
                (['alteração dados cobrança'], 'outros')
            ],
            'INFORMACAO': [
                (['onboarding/orientação', 'informações gerais'], 'orientações gerais')
            ],
            'OUTROS': [
                (['contato não respondido', 'contato proativo'], 'contatos proativos/não respondidos'),
                (['conversa social/pessoal', 'saudações/cortesia'], 'interações sociais')
            ],
            'RECLAMACAO': [
                (['problema não resolvido', 'falta de retorno/comunicação', 'problemas de qualidade'], 'problemas de atendimento'),
                (['suspensão/bloqueio indevido', 'insatisfação com serviço'], 'problemas de serviço')
            ],
            'CANCELAMENTO': [
                (['exclusão de conta/dados', 'encerramento de parceria', 'desativação de serviços', 'desinteresse no produto'], 'encerramentos diversos')
            ],
            'SUPORTE_TECNICO': [
                (['suporte técnico geral', 'migração/mudanças técnicas', 'problemas de cobrança/boletos'], 'suporte técnico diverso')
            ]
        }
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        total_updated = 0
        
        for category, category_unifications in unifications.items():
            for old_subcats, new_subcat in category_unifications:
                placeholders = ','.join(['?' for _ in old_subcats])
                cursor.execute(f"""
                    UPDATE session_classifications 
                    SET subcategory = ? 
                    WHERE category = ? AND subcategory IN ({placeholders})
                """, [new_subcat, category] + old_subcats)
                
                total_updated += cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return total_updated
    
    def export_final_csv(self, filename: str = 'FINAL_ALL_CLASSIFICATIONS.csv'):
        """Exporta resultado final para CSV"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT sessionID, category, subcategory, confidence, reasoning, 
                   classified_at, messages_analyzed, summary
            FROM session_classifications 
            ORDER BY category, subcategory
        """)
        
        import csv
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow(['sessionID', 'category', 'subcategory', 'confidence', 
                           'reasoning', 'classified_at', 'messages_analyzed', 'summary'])
            
            # Data
            for row in cursor.fetchall():
                writer.writerow(row)
        
        conn.close()
        return filename
    
    def generate_report(self) -> Dict:
        """Gera relatório final da otimização"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Estatísticas por categoria
        cursor.execute("""
            SELECT category, 
                   COUNT(DISTINCT subcategory) as subcats_count,
                   COUNT(*) as sessions_count
            FROM session_classifications 
            GROUP BY category 
            ORDER BY sessions_count DESC
        """)
        
        category_stats = []
        for row in cursor.fetchall():
            category_stats.append({
                'category': row[0],
                'subcategories': row[1],
                'sessions': row[2]
            })
        
        # Totais gerais
        cursor.execute("SELECT COUNT(*) FROM session_classifications")
        total_sessions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT subcategory) FROM session_classifications")
        total_subcats = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_sessions': total_sessions,
            'total_subcategories': total_subcats,
            'categories': category_stats,
            'timestamp': datetime.now().isoformat()
        }
    
    def run_full_optimization(self) -> Dict:
        """Executa otimização completa"""
        print("🚀 INICIANDO OTIMIZAÇÃO COMPLETA DE CLASSIFICAÇÕES")
        print("=" * 60)
        
        # Fase 1: Preparação
        backup_name = self.create_backup()
        print(f"✅ Backup criado: {backup_name}")
        
        self.add_summary_column()
        print("✅ Coluna summary adicionada/verificada")
        
        # Fase 2: Reorganização por categoria
        categories = ['COMERCIAL', 'SUPORTE_TECNICO', 'FINANCEIRO', 'INFORMACAO', 
                     'RECLAMACAO', 'CANCELAMENTO', 'OUTROS']
        
        total_reorganized = 0
        for category in categories:
            subcats, updated = self.reorganize_category(category)
            total_reorganized += updated
            print(f"✅ {category}: {subcats} subcategorias, {updated} sessões reorganizadas")
        
        # Fase 3: Unificações específicas
        unification_updates = self.apply_specific_unifications()
        print(f"✅ Unificações específicas: {unification_updates} sessões atualizadas")
        
        # Fase 4: Exportação e relatório
        csv_file = self.export_final_csv()
        print(f"✅ CSV exportado: {csv_file}")
        
        report = self.generate_report()
        
        print(f"\n🎉 OTIMIZAÇÃO CONCLUÍDA!")
        print(f"📊 Total de sessões: {report['total_sessions']:,}")
        print(f"📊 Total de subcategorias: {report['total_subcategories']}")
        print(f"📊 Sessões reorganizadas: {total_reorganized:,}")
        print(f"📊 Sessões unificadas: {unification_updates:,}")
        print(f"💾 Backup: {backup_name}")
        
        return report

def main():
    """Função principal para execução do script"""
    optimizer = ClassificationOptimizer()
    report = optimizer.run_full_optimization()
    
    # Salvar relatório
    with open('optimization_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Relatório salvo: optimization_report.json")

if __name__ == "__main__":
    main()
```

### Script de Verificação: `verify_optimization.py`

```python
#!/usr/bin/env python3
"""
Script para verificar a qualidade da otimização
"""

import sqlite3
from collections import defaultdict

def verify_optimization(db_path: str = 'talqui.db'):
    """Verifica a qualidade da otimização realizada"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("📊 VERIFICAÇÃO DA OTIMIZAÇÃO")
    print("=" * 40)
    
    # Verificar número de subcategorias por categoria
    cursor.execute("""
        SELECT category, COUNT(DISTINCT subcategory) as subcats
        FROM session_classifications 
        GROUP BY category 
        ORDER BY subcats DESC
    """)
    
    print("\n🎯 SUBCATEGORIAS POR CATEGORIA:")
    categories_over_limit = []
    
    for category, subcats in cursor.fetchall():
        status = "✅" if subcats <= 10 else "⚠️"
        print(f"{status} {category}: {subcats} subcategorias")
        
        if subcats > 10:
            categories_over_limit.append(category)
    
    # Verificar distribuição de "outros"
    print("\n📈 DISTRIBUIÇÃO DE 'OUTROS':")
    cursor.execute("""
        SELECT category, 
               COUNT(*) as outros_count,
               (SELECT COUNT(*) FROM session_classifications sc2 WHERE sc2.category = sc.category) as total_count
        FROM session_classifications sc
        WHERE subcategory = 'outros'
        GROUP BY category
    """)
    
    for category, outros_count, total_count in cursor.fetchall():
        percentage = (outros_count / total_count) * 100
        status = "⚠️" if percentage > 50 else "✅"
        print(f"{status} {category}: {outros_count}/{total_count} ({percentage:.1f}%)")
    
    # Verificar subcategorias com muito baixo volume
    print("\n🔍 SUBCATEGORIAS COM BAIXO VOLUME (<5 sessões):")
    cursor.execute("""
        SELECT category, subcategory, COUNT(*) as count
        FROM session_classifications 
        GROUP BY category, subcategory 
        HAVING COUNT(*) < 5
        ORDER BY count ASC
    """)
    
    low_volume = cursor.fetchall()
    if low_volume:
        for category, subcategory, count in low_volume:
            print(f"⚠️  {category}: {subcategory} ({count} sessões)")
    else:
        print("✅ Nenhuma subcategoria com volume muito baixo")
    
    conn.close()
    
    # Recomendações
    print("\n💡 RECOMENDAÇÕES:")
    if categories_over_limit:
        print(f"🔄 Considere consolidar mais subcategorias em: {', '.join(categories_over_limit)}")
    
    if len(low_volume) > 5:
        print("🔄 Considere mover subcategorias de baixo volume para 'outros'")
    
    if not categories_over_limit and len(low_volume) <= 5:
        print("✅ Otimização está bem balanceada!")

if __name__ == "__main__":
    verify_optimization()
```

## 📋 Checklist de Execução

### Pré-requisitos
- [ ] Todas as sessões classificadas pelo DeepSeek
- [ ] Banco de dados `talqui.db` atualizado
- [ ] Scripts de otimização prontos
- [ ] Backup do ambiente realizado

### Execução
- [ ] Executar `python3 optimize_classifications.py`
- [ ] Verificar logs de execução
- [ ] Executar `python3 verify_optimization.py`
- [ ] Analisar relatório gerado
- [ ] Validar arquivo CSV final

### Pós-execução
- [ ] Atualizar dashboard com novas classificações
- [ ] Comunicar stakeholders sobre nova estrutura
- [ ] Arquivar backups antigos se necessário
- [ ] Documentar quaisquer ajustes manuais

## 📊 Métricas de Sucesso

### KPIs de Otimização
- **Redução de subcategorias**: Target > 20%
- **Distribuição equilibrada**: Nenhuma categoria com > 70% em "outros"
- **Volume mínimo**: Subcategorias principais com > 20 sessões
- **Cobertura**: < 5 subcategorias com volume < 5 sessões

### Qualidade dos Dados
- **Rastreabilidade**: 100% dos dados originais preservados em `summary`
- **Consistência**: Nenhuma subcategoria vazia
- **Integridade**: Total de sessões inalterado após otimização

## 🔧 Troubleshooting

### Problemas Comuns

#### Erro: "Column already exists"
```sql
-- Verificar se coluna summary já existe
PRAGMA table_info(session_classifications);

-- Se necessário, pular criação da coluna
```

#### Performance lenta na reorganização
```python
# Adicionar índices para melhor performance
CREATE INDEX idx_category_summary ON session_classifications(category, summary);
CREATE INDEX idx_subcategory ON session_classifications(subcategory);
```

#### Distribuição desequilibrada após otimização
- Revisar mapeamentos de palavras-chave
- Ajustar thresholds de consolidação
- Executar análise manual das subcategorias "outros"

### Logs e Debugging

#### Habilitar logs detalhados
```python
import logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
```

#### Verificar integridade dos dados
```sql
-- Verificar se há sessões sem classificação
SELECT COUNT(*) FROM session_classifications WHERE category IS NULL;

-- Verificar se summary foi populado
SELECT COUNT(*) FROM session_classifications WHERE summary IS NULL;

-- Verificar distribuição geral
SELECT category, COUNT(*) FROM session_classifications GROUP BY category;
```

## 📝 Notas Finais

### Manutenção Contínua
- **Revisão mensal**: Analisar novas subcategorias emergentes
- **Ajustes de mapeamento**: Atualizar palavras-chave conforme necessário
- **Feedback dos usuários**: Incorporar sugestões da equipe de análise

### Evolução do Sistema
- **Machine Learning**: Considerar automatizar mapeamentos com ML
- **Análise semântica**: Implementar similaridade de texto mais sofisticada  
- **Dashboard dinâmico**: Permitir ajustes de classificação via interface

### Documentação
- Manter este guia atualizado com mudanças no processo
- Documentar todas as exceções e casos especiais
- Registrar decisões de negócio para futuras referências

---

**📅 Última atualização**: Setembro 2025  
**👤 Responsável**: Sistema de Classificação Talqui  
**🔄 Versão**: 1.0  