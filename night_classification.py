#!/usr/bin/env python3
from session_classifier import SessionClassifier
import time
from datetime import datetime

def classify_remaining_sessions():
    """Classifica todas as sessões restantes"""
    
    classifier = SessionClassifier()
    
    print("🤖 CLASSIFICAÇÃO MASSIVA NOTURNA")
    print("=" * 50)
    
    start_time = datetime.now()
    total_processed = 0
    batch_num = 1
    
    while True:
        # Obter sessões para processar
        sessions = classifier.get_sessions_to_classify(100)  # Lotes de 100
        
        if not sessions:
            print("✅ Todas as sessões classificadas!")
            break
        
        print(f"\n📦 LOTE {batch_num} - {len(sessions)} sessões")
        print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
        
        batch_classified = 0
        
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
                        batch_classified += 1
                        
                        # Progresso a cada 25
                        if i % 25 == 0:
                            print(f"  ✅ {i}/{len(sessions)} - {classification['category'][:15]} (conf: {classification.get('confidence', 0):.2f})")
                
                # Pausa mínima
                time.sleep(0.15)
                
            except Exception as e:
                print(f"  ❌ Erro: {str(e)[:50]}...")
        
        total_processed += batch_classified
        elapsed = datetime.now() - start_time
        rate = total_processed / elapsed.total_seconds() * 60
        
        print(f"\n📊 Lote {batch_num}: {batch_classified} classificadas")
        print(f"  📈 Total: {total_processed} | Taxa: {rate:.1f}/min | Tempo: {elapsed}")
        
        # Backup a cada 500
        if total_processed % 500 == 0:
            try:
                classifier.export_classifications_to_csv(f"backup_night_{total_processed}.csv")
                print(f"💾 Backup: backup_night_{total_processed}.csv")
            except:
                pass
        
        batch_num += 1
        time.sleep(0.5)  # Pausa entre lotes
    
    # Relatório final
    final_stats = classifier.get_classification_stats()
    elapsed = datetime.now() - start_time
    
    print(f"\n🎉 CLASSIFICAÇÃO NOTURNA COMPLETA!")
    print("=" * 50)
    print(f"✅ Total processado: {total_processed:,} sessões")
    print(f"📊 Total no banco: {final_stats['total_classified']:,} sessões")
    print(f"⏱️  Tempo total: {elapsed}")
    print(f"⚡ Taxa média: {total_processed/elapsed.total_seconds()*60:.1f} sessões/min")
    print(f"💰 Custo total: ${total_processed * 0.00009:.4f} USD")
    
    # Distribuição final
    if final_stats['categories']:
        print(f"\n📈 DISTRIBUIÇÃO FINAL:")
        for category, count in sorted(final_stats['categories'].items(), key=lambda x: x[1], reverse=True):
            percentage = count / final_stats['total_classified'] * 100
            print(f"  {category:<18}: {count:4d} ({percentage:5.1f}%)")
    
    # Exportar resultado final
    classifier.export_classifications_to_csv("FINAL_COMPLETE_CLASSIFICATIONS.csv")
    print(f"\n📄 Arquivo final: FINAL_COMPLETE_CLASSIFICATIONS.csv")
    print(f"🕐 Finalizado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    classifier.close()

if __name__ == "__main__":
    try:
        classify_remaining_sessions()
    except Exception as e:
        print(f"❌ Erro: {e}")
