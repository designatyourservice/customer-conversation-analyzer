#!/usr/bin/env python3
"""
Classificação massiva otimizada - lotes maiores para todas as sessões
"""

from session_classifier import SessionClassifier
import time
from datetime import datetime

def run_massive_classification():
    """Executa classificação em lotes grandes até completar todas as sessões"""
    
    classifier = SessionClassifier()
    
    print("🚀 CLASSIFICAÇÃO MASSIVA INICIADA")
    print("=" * 60)
    
    total_processed = 0
    batch_num = 1
    start_time = datetime.now()
    
    # Loop até não haver mais sessões
    while True:
        print(f"\n📦 LOTE {batch_num} - {datetime.now().strftime('%H:%M:%S')}")
        
        # Classificar lote de 100 sessões
        batch_size = 100
        classified = 0
        errors = 0
        
        sessions = classifier.get_sessions_to_classify(batch_size)
        
        if not sessions:
            print("✅ Não há mais sessões para classificar!")
            break
        
        print(f"📋 Processando {len(sessions)} sessões...")
        
        for i, session in enumerate(sessions, 1):
            try:
                messages = classifier.get_session_messages(session['sessionID'])
                
                if messages:
                    classification = classifier.classify_session_with_deepseek(messages, session)
                    
                    if classification:
                        classifier.save_classification(
                            session['sessionID'], 
                            classification, 
                            len(messages)
                        )
                        classified += 1
                        
                        # Progresso a cada 10 sessões
                        if i % 10 == 0:
                            print(f"  ✅ {i}/{len(sessions)} - {classification['category'][:15]} (conf: {classification.get('confidence', 0):.2f})")
                    else:
                        errors += 1
                else:
                    errors += 1
                
                # Pausa mínima para não sobrecarregar API
                time.sleep(0.3)
                
            except Exception as e:
                errors += 1
                print(f"  ❌ Erro: {str(e)[:50]}...")
        
        total_processed += classified
        
        # Estatísticas do lote
        elapsed = datetime.now() - start_time
        rate = total_processed / elapsed.total_seconds() * 60
        
        print(f"\n📊 LOTE {batch_num} CONCLUÍDO:")
        print(f"  ✅ Classificadas: {classified}")
        print(f"  ❌ Erros: {errors}")
        print(f"  📈 Total processado: {total_processed}")
        print(f"  ⚡ Taxa: {rate:.1f} sessões/min")
        print(f"  ⏱️  Tempo decorrido: {elapsed}")
        
        # Backup a cada 500 classificações
        if total_processed % 500 == 0:
            try:
                classifier.export_classifications_to_csv(f"backup_{total_processed}_sessions.csv")
                print(f"💾 Backup salvo: backup_{total_processed}_sessions.csv")
            except:
                pass
        
        batch_num += 1
        
        # Pausa entre lotes
        print("⏸️  Pausando 2 segundos...")
        time.sleep(2)
    
    # Estatísticas finais
    elapsed = datetime.now() - start_time
    
    print(f"\n🎉 CLASSIFICAÇÃO MASSIVA CONCLUÍDA!")
    print("=" * 60)
    print(f"📊 Total classificado: {total_processed:,} sessões")
    print(f"⏱️  Tempo total: {elapsed}")
    print(f"⚡ Taxa média: {total_processed/elapsed.total_seconds()*60:.1f} sessões/min")
    
    # Custo estimado
    cost = total_processed * 0.00009
    print(f"💰 Custo estimado: ${cost:.4f} USD")
    
    # Obter estatísticas finais
    stats = classifier.get_classification_stats()
    print(f"\n📈 RESUMO FINAL:")
    print(f"  Total no banco: {stats['total_classified']:,}")
    
    if stats['categories']:
        print(f"  📊 Distribuição:")
        for category, count in sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True):
            percentage = count / stats['total_classified'] * 100
            print(f"    {category}: {count:,} ({percentage:.1f}%)")
    
    # Exportar resultado final
    classifier.export_classifications_to_csv("FINAL_ALL_CLASSIFICATIONS.csv")
    print(f"\n📄 Arquivo final: FINAL_ALL_CLASSIFICATIONS.csv")
    
    classifier.close()

if __name__ == "__main__":
    try:
        run_massive_classification()
    except KeyboardInterrupt:
        print("\n⏹️  Interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")