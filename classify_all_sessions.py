#!/usr/bin/env python3
"""
Script para classificar TODAS as sessões restantes em lotes otimizados
"""

from session_classifier import SessionClassifier
from cost_estimator import DeepSeekCostEstimator
import time
from datetime import datetime
import sys

def classify_all_sessions():
    """Classifica todas as sessões restantes com progresso detalhado"""
    
    print("🤖 Classificação em Massa - Todas as Sessões")
    print("=" * 60)
    
    # Inicializar classifier e estimador
    classifier = SessionClassifier()
    estimator = DeepSeekCostEstimator()
    
    # Obter estatísticas iniciais
    remaining_estimate = estimator.estimate_remaining_cost()
    
    if remaining_estimate.get('remaining_sessions', 0) == 0:
        print("✅ Todas as sessões já foram classificadas!")
        classifier.close()
        return
    
    total_remaining = remaining_estimate['remaining_sessions']
    estimated_cost = remaining_estimate['total_cost_usd']
    
    print(f"📊 Sessões para classificar: {total_remaining:,}")
    print(f"💰 Custo estimado: ${estimated_cost:.4f} USD")
    print(f"⏱️  Tempo estimado: ~{total_remaining * 2 / 60:.1f} minutos")
    print("\n🚀 Iniciando classificação em lotes de 20 sessões...")
    print("-" * 60)
    
    # Configuração dos lotes
    batch_size = 20
    total_processed = 0
    total_classified = 0
    total_errors = 0
    start_time = datetime.now()
    
    batch_num = 1
    
    while True:
        # Verificar se ainda há sessões para processar
        sessions_to_process = classifier.get_sessions_to_classify(batch_size)
        
        if not sessions_to_process:
            print("\n✅ Não há mais sessões para classificar!")
            break
        
        current_batch_size = len(sessions_to_process)
        
        print(f"\n📦 LOTE {batch_num} - {current_batch_size} sessões")
        print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
        
        batch_classified = 0
        batch_errors = 0
        
        for i, session in enumerate(sessions_to_process, 1):
            try:
                # Obter mensagens da sessão
                messages = classifier.get_session_messages(session['sessionID'])
                
                if not messages:
                    print(f"  ⚠️  {i:2d}/{current_batch_size} - Sem mensagens: {session['sessionID'][:8]}...")
                    continue
                
                # Classificar com DeepSeek
                classification = classifier.classify_session_with_deepseek(messages, session)
                
                if classification:
                    # Salvar classificação
                    classifier.save_classification(
                        session['sessionID'], 
                        classification, 
                        len(messages)
                    )
                    
                    batch_classified += 1
                    total_classified += 1
                    
                    # Mostrar progresso inline
                    confidence = classification.get('confidence', 0)
                    category = classification.get('category', 'N/A')[:15]
                    
                    print(f"  ✅ {i:2d}/{current_batch_size} - {category:<15} (conf: {confidence:.2f}) {session['sessionID'][:8]}...")
                else:
                    batch_errors += 1
                    total_errors += 1
                    print(f"  ❌ {i:2d}/{current_batch_size} - Falha na classificação: {session['sessionID'][:8]}...")
                
                # Pausa pequena entre chamadas da API
                time.sleep(0.5)
                
            except Exception as e:
                batch_errors += 1
                total_errors += 1
                print(f"  ❌ {i:2d}/{current_batch_size} - Erro: {str(e)[:50]}...")
        
        total_processed += current_batch_size
        
        # Estatísticas do lote
        elapsed = datetime.now() - start_time
        rate = total_classified / elapsed.total_seconds() * 60  # por minuto
        remaining_sessions = total_remaining - total_processed
        eta_minutes = remaining_sessions / rate if rate > 0 else 0
        
        print(f"📊 Lote {batch_num} finalizado:")
        print(f"  ✅ Classificadas: {batch_classified}")
        print(f"  ❌ Erros: {batch_errors}")
        print(f"  📈 Taxa: {rate:.1f} sessões/min")
        print(f"  ⏳ ETA: {eta_minutes:.0f} minutos")
        print(f"  🎯 Progresso: {total_processed}/{total_remaining} ({total_processed/total_remaining*100:.1f}%)")
        
        batch_num += 1
        
        # Pausa entre lotes para não sobrecarregar a API
        if remaining_sessions > 0:
            print("  ⏸️  Pausando 3 segundos entre lotes...")
            time.sleep(3)
        
        # Checkpoint a cada 10 lotes
        if batch_num % 10 == 1:
            print(f"\n🔄 CHECKPOINT - {total_classified} sessões classificadas até agora")
            
            # Backup dos resultados
            try:
                classifier.export_classifications_to_csv(f"backup_classifications_{int(time.time())}.csv")
                print("💾 Backup salvo com sucesso")
            except Exception as e:
                print(f"⚠️  Erro no backup: {e}")
    
    # Estatísticas finais
    elapsed = datetime.now() - start_time
    
    print("\n" + "=" * 60)
    print("🎉 CLASSIFICAÇÃO COMPLETA!")
    print("=" * 60)
    print(f"📊 Total processado: {total_processed:,} sessões")
    print(f"✅ Classificadas com sucesso: {total_classified:,}")
    print(f"❌ Erros: {total_errors}")
    print(f"🎯 Taxa de sucesso: {total_classified/(total_processed or 1)*100:.1f}%")
    print(f"⏱️  Tempo total: {elapsed}")
    print(f"⚡ Taxa média: {total_classified/elapsed.total_seconds()*60:.1f} sessões/min")
    
    # Custo real estimado
    real_cost = total_classified * 0.00009  # Custo médio por sessão
    print(f"💰 Custo estimado real: ${real_cost:.4f} USD")
    
    # Gerar relatório final
    try:
        stats = classifier.get_classification_stats()
        print(f"\n📈 Estatísticas finais:")
        print(f"  Total no banco: {stats['total_classified']:,} classificações")
        
        if stats['categories']:
            print(f"  📊 Distribuição:")
            for category, count in sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True):
                percentage = count / stats['total_classified'] * 100
                print(f"    {category}: {count} ({percentage:.1f}%)")
    except Exception as e:
        print(f"⚠️  Erro nas estatísticas finais: {e}")
    
    # Exportar resultado final
    try:
        classifier.export_classifications_to_csv("final_all_classifications.csv")
        print(f"\n📄 Relatório final exportado: final_all_classifications.csv")
    except Exception as e:
        print(f"❌ Erro na exportação: {e}")
    
    classifier.close()
    print(f"\n🏁 Processo finalizado às {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    try:
        classify_all_sessions()
    except KeyboardInterrupt:
        print("\n\n⏹️  Processo interrompido pelo usuário")
        print("💾 Dados já processados foram salvos no banco")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro crítico: {e}")
        sys.exit(1)