#!/usr/bin/env python3
"""
Classificar até atingir 10% do total (367 sessões)
"""

from session_classifier import SessionClassifier
import time
from datetime import datetime

def classify_to_10_percent():
    """Classifica até atingir 10% do total de sessões"""
    
    classifier = SessionClassifier()
    
    # Meta: 10% de 3674 = 367 sessões
    target = 367
    current_stats = classifier.get_classification_stats()
    current_count = current_stats['total_classified']
    
    remaining_needed = target - current_count
    
    print("🎯 CLASSIFICAÇÃO ATÉ 10%")
    print("=" * 50)
    print(f"📊 Meta: 367 sessões (10% de 3.674)")
    print(f"✅ Já classificadas: {current_count}")
    print(f"🎯 Faltam: {remaining_needed}")
    print(f"💰 Custo estimado: ${remaining_needed * 0.00009:.4f} USD")
    
    if remaining_needed <= 0:
        print("🎉 Meta já atingida!")
        classifier.close()
        return
    
    print(f"\n🚀 Iniciando classificação de {remaining_needed} sessões...")
    print("-" * 50)
    
    start_time = datetime.now()
    processed_in_session = 0
    batch_num = 1
    
    while processed_in_session < remaining_needed:
        # Verificar progresso atual
        current_stats = classifier.get_classification_stats()
        current_total = current_stats['total_classified']
        
        if current_total >= target:
            print(f"\n🎉 META ATINGIDA! {current_total} sessões classificadas")
            break
        
        # Determinar tamanho do lote
        remaining_in_target = target - current_total
        batch_size = min(25, remaining_in_target)
        
        print(f"\n📦 LOTE {batch_num} - {batch_size} sessões")
        print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
        
        # Obter sessões para classificar
        sessions = classifier.get_sessions_to_classify(batch_size)
        
        if not sessions:
            print("❌ Nenhuma sessão disponível para classificação")
            break
        
        batch_classified = 0
        batch_errors = 0
        
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
                        processed_in_session += 1
                        
                        # Mostrar progresso
                        category = classification['category'][:12]
                        conf = classification.get('confidence', 0)
                        total_now = current_total + batch_classified
                        progress_pct = (total_now / target) * 100
                        
                        print(f"  ✅ {i:2d}/{len(sessions)} - {category:<12} ({conf:.2f}) - Total: {total_now:3d} ({progress_pct:5.1f}%)")
                        
                        # Verificar se atingimos a meta
                        if total_now >= target:
                            print(f"\n🎉 META DE 10% ATINGIDA! {total_now} sessões")
                            break
                    else:
                        batch_errors += 1
                else:
                    batch_errors += 1
                
                # Pausa entre chamadas
                time.sleep(0.4)
                
            except Exception as e:
                batch_errors += 1
                print(f"  ❌ {i:2d}/{len(sessions)} - Erro: {str(e)[:30]}...")
        
        # Estatísticas do lote
        elapsed = datetime.now() - start_time
        rate = processed_in_session / elapsed.total_seconds() * 60
        
        print(f"\n📊 Lote {batch_num}:")
        print(f"  ✅ Classificadas: {batch_classified}")
        print(f"  ❌ Erros: {batch_errors}")
        print(f"  📈 Taxa: {rate:.1f}/min")
        print(f"  ⏱️  Tempo: {elapsed}")
        
        batch_num += 1
        
        # Verificar se atingimos a meta
        current_stats = classifier.get_classification_stats()
        if current_stats['total_classified'] >= target:
            break
        
        # Pausa entre lotes
        print("  ⏸️  Pausa de 2 segundos...")
        time.sleep(2)
    
    # Estatísticas finais
    final_stats = classifier.get_classification_stats()
    elapsed = datetime.now() - start_time
    
    print(f"\n🏁 CLASSIFICAÇÃO FINALIZADA!")
    print("=" * 50)
    print(f"🎯 Meta: {target} sessões (10%)")
    print(f"✅ Atingido: {final_stats['total_classified']} sessões")
    print(f"📊 Progresso: {final_stats['progress_percent']:.2f}%")
    print(f"⏱️  Tempo total: {elapsed}")
    print(f"⚡ Taxa média: {processed_in_session/elapsed.total_seconds()*60:.1f} sessões/min")
    print(f"💰 Custo desta sessão: ${processed_in_session * 0.00009:.4f} USD")
    
    # Distribuição atualizada
    if final_stats['categories']:
        print(f"\n📈 DISTRIBUIÇÃO FINAL:")
        total_final = final_stats['total_classified']
        for category, count in sorted(final_stats['categories'].items(), key=lambda x: x[1], reverse=True):
            percentage = count / total_final * 100
            print(f"  {category:<18}: {count:3d} ({percentage:5.1f}%)")
    
    # Exportar milestone
    classifier.export_classifications_to_csv("milestone_10_percent.csv")
    print(f"\n📄 Relatório de 10% salvo: milestone_10_percent.csv")
    
    classifier.close()

if __name__ == "__main__":
    try:
        classify_to_10_percent()
    except KeyboardInterrupt:
        print("\n⏹️  Interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")