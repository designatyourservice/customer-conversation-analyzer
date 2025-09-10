#!/usr/bin/env python3
"""
Classificar até atingir 25% do total (918 sessões)
Meta atual: 367 -> 918 sessões (mais 551 necessárias)
"""

from session_classifier import SessionClassifier
import time
from datetime import datetime

def classify_to_25_percent():
    """Classifica até atingir 25% do total de sessões"""
    
    classifier = SessionClassifier()
    
    # Meta: 25% de 3674 = 918 sessões (arredondado)
    target = 918
    current_stats = classifier.get_classification_stats()
    current_count = current_stats['total_classified']
    
    remaining_needed = target - current_count
    
    print("🎯 CLASSIFICAÇÃO ATÉ 25%")
    print("=" * 60)
    print(f"📊 Meta: {target} sessões (25% de 3.674)")
    print(f"✅ Já classificadas: {current_count}")
    print(f"🎯 Faltam: {remaining_needed}")
    print(f"💰 Custo estimado: ${remaining_needed * 0.00009:.4f} USD")
    print(f"⏱️  Tempo estimado: ~{remaining_needed / 6.3:.0f} minutos")
    
    if remaining_needed <= 0:
        print("🎉 Meta já atingida!")
        classifier.close()
        return
    
    print(f"\n🚀 Iniciando classificação de {remaining_needed} sessões...")
    print("📦 Processando em lotes de 50 para maior eficiência")
    print("-" * 60)
    
    start_time = datetime.now()
    processed_in_session = 0
    batch_num = 1
    total_errors = 0
    
    while processed_in_session < remaining_needed:
        # Verificar progresso atual
        current_stats = classifier.get_classification_stats()
        current_total = current_stats['total_classified']
        
        if current_total >= target:
            print(f"\n🎉 META DE 25% ATINGIDA! {current_total} sessões")
            break
        
        # Determinar tamanho do lote (maior para eficiência)
        remaining_in_target = target - current_total
        batch_size = min(50, remaining_in_target)  # Lotes de 50
        
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
                        
                        # Mostrar progresso a cada 10 sessões
                        if i % 10 == 0:
                            category = classification['category'][:12]
                            conf = classification.get('confidence', 0)
                            total_now = current_total + batch_classified
                            progress_pct = (total_now / target) * 100
                            
                            print(f"  ✅ {i:2d}/{len(sessions)} - {category:<12} ({conf:.2f}) - Total: {total_now:3d} ({progress_pct:5.1f}%)")
                        
                        # Verificar se atingimos a meta
                        if current_total + batch_classified >= target:
                            print(f"\n🎉 META DE 25% ATINGIDA! {current_total + batch_classified} sessões")
                            break
                    else:
                        batch_errors += 1
                        total_errors += 1
                else:
                    batch_errors += 1
                    total_errors += 1
                
                # Pausa reduzida para maior velocidade
                time.sleep(0.2)
                
            except Exception as e:
                batch_errors += 1
                total_errors += 1
                if batch_errors <= 3:  # Mostrar apenas primeiros erros
                    print(f"  ❌ {i:2d}/{len(sessions)} - Erro: {str(e)[:40]}...")
        
        # Estatísticas do lote
        elapsed = datetime.now() - start_time
        rate = processed_in_session / elapsed.total_seconds() * 60 if elapsed.total_seconds() > 0 else 0
        remaining_sessions = target - (current_total + batch_classified)
        eta_minutes = remaining_sessions / rate if rate > 0 else 0
        
        print(f"\n📊 Lote {batch_num} finalizado:")
        print(f"  ✅ Classificadas: {batch_classified}")
        print(f"  ❌ Erros: {batch_errors}")
        print(f"  📈 Taxa atual: {rate:.1f}/min")
        print(f"  ⏳ ETA: {eta_minutes:.0f} min")
        print(f"  🎯 Progresso: {current_total + batch_classified}/{target} ({((current_total + batch_classified)/target*100):.1f}%)")
        
        batch_num += 1
        
        # Verificar se atingimos a meta
        if current_total + batch_classified >= target:
            break
        
        # Pausa reduzida entre lotes
        print("  ⏸️  Pausa de 1 segundo...")
        time.sleep(1)
        
        # Checkpoint a cada 200 sessões
        if processed_in_session % 200 == 0 and processed_in_session > 0:
            print(f"\n🔄 CHECKPOINT - {processed_in_session} sessões processadas nesta rodada")
            try:
                classifier.export_classifications_to_csv(f"checkpoint_{current_total + batch_classified}_sessions.csv")
                print("💾 Checkpoint salvo")
            except:
                pass
    
    # Estatísticas finais
    final_stats = classifier.get_classification_stats()
    elapsed = datetime.now() - start_time
    
    print(f"\n🏁 CLASSIFICAÇÃO DE 25% FINALIZADA!")
    print("=" * 60)
    print(f"🎯 Meta: {target} sessões (25%)")
    print(f"✅ Atingido: {final_stats['total_classified']} sessões")
    print(f"📊 Progresso: {(final_stats['total_classified']/3674*100):.2f}%")
    print(f"⏱️  Tempo total: {elapsed}")
    print(f"⚡ Taxa média: {processed_in_session/elapsed.total_seconds()*60:.1f} sessões/min")
    print(f"💰 Custo desta rodada: ${processed_in_session * 0.00009:.4f} USD")
    print(f"📈 Taxa de sucesso: {((processed_in_session-total_errors)/processed_in_session*100):.1f}%")
    
    # Distribuição atualizada
    if final_stats['categories']:
        print(f"\n📈 DISTRIBUIÇÃO FINAL (25%):")
        total_final = final_stats['total_classified']
        for category, count in sorted(final_stats['categories'].items(), key=lambda x: x[1], reverse=True):
            percentage = count / total_final * 100
            print(f"  {category:<18}: {count:3d} ({percentage:5.1f}%)")
    
    # Exportar milestone de 25%
    classifier.export_classifications_to_csv("milestone_25_percent.csv")
    print(f"\n📄 Relatório de 25% salvo: milestone_25_percent.csv")
    
    # Estimativa para 100%
    remaining_for_100 = 3674 - final_stats['total_classified']
    cost_for_100 = remaining_for_100 * 0.00009
    time_for_100 = remaining_for_100 / (processed_in_session/elapsed.total_seconds()) if processed_in_session > 0 else 0
    
    print(f"\n🔮 PROJEÇÃO PARA 100%:")
    print(f"  📋 Restantes: {remaining_for_100:,} sessões")
    print(f"  💰 Custo estimado: ${cost_for_100:.4f} USD")
    print(f"  ⏱️  Tempo estimado: {time_for_100/60:.1f} horas")
    
    classifier.close()

if __name__ == "__main__":
    try:
        classify_to_25_percent()
    except KeyboardInterrupt:
        print("\n⏹️  Interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")