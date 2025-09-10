#!/usr/bin/env python3
"""
Script agendado para classificar o restante das sessões às 22:00
"""

import schedule
import time
from datetime import datetime
import subprocess
import sys
from session_classifier import SessionClassifier

def run_full_classification():
    """Executa classificação completa do restante das sessões"""
    
    print(f"\n🕐 CLASSIFICAÇÃO AGENDADA INICIADA - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 70)
    
    # Verificar status atual
    classifier = SessionClassifier()
    stats = classifier.get_classification_stats()
    remaining = stats['total_sessions'] - stats['total_classified']
    
    print(f"📊 Status atual:")
    print(f"  ✅ Classificadas: {stats['total_classified']:,}")
    print(f"  📋 Restantes: {remaining:,}")
    print(f"  💰 Custo estimado: ${remaining * 0.00009:.4f} USD")
    print(f"  ⏱️  Tempo estimado: ~{remaining / 6.5 / 60:.1f} horas")
    
    classifier.close()
    
    if remaining <= 0:
        print("✅ Todas as sessões já foram classificadas!")
        return
    
    print(f"\n🚀 Iniciando classificação massiva de {remaining:,} sessões...")
    print("📦 Processamento otimizado em lotes de 100")
    print("-" * 70)
    
    # Executar script de classificação massiva
    try:
        # Criar e executar script de classificação completa
        script_content = f'''#!/usr/bin/env python3
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
        
        print(f"\\n📦 LOTE {{batch_num}} - {{len(sessions)}} sessões")
        print(f"⏰ {{datetime.now().strftime('%H:%M:%S')}}")
        
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
                            print(f"  ✅ {{i}}/{{len(sessions)}} - {{classification['category'][:15]}} (conf: {{classification.get('confidence', 0):.2f}})")
                
                # Pausa mínima
                time.sleep(0.15)
                
            except Exception as e:
                print(f"  ❌ Erro: {{str(e)[:50]}}...")
        
        total_processed += batch_classified
        elapsed = datetime.now() - start_time
        rate = total_processed / elapsed.total_seconds() * 60
        
        print(f"\\n📊 Lote {{batch_num}}: {{batch_classified}} classificadas")
        print(f"  📈 Total: {{total_processed}} | Taxa: {{rate:.1f}}/min | Tempo: {{elapsed}}")
        
        # Backup a cada 500
        if total_processed % 500 == 0:
            try:
                classifier.export_classifications_to_csv(f"backup_night_{{total_processed}}.csv")
                print(f"💾 Backup: backup_night_{{total_processed}}.csv")
            except:
                pass
        
        batch_num += 1
        time.sleep(0.5)  # Pausa entre lotes
    
    # Relatório final
    final_stats = classifier.get_classification_stats()
    elapsed = datetime.now() - start_time
    
    print(f"\\n🎉 CLASSIFICAÇÃO NOTURNA COMPLETA!")
    print("=" * 50)
    print(f"✅ Total processado: {{total_processed:,}} sessões")
    print(f"📊 Total no banco: {{final_stats['total_classified']:,}} sessões")
    print(f"⏱️  Tempo total: {{elapsed}}")
    print(f"⚡ Taxa média: {{total_processed/elapsed.total_seconds()*60:.1f}} sessões/min")
    print(f"💰 Custo total: ${{total_processed * 0.00009:.4f}} USD")
    
    # Distribuição final
    if final_stats['categories']:
        print(f"\\n📈 DISTRIBUIÇÃO FINAL:")
        for category, count in sorted(final_stats['categories'].items(), key=lambda x: x[1], reverse=True):
            percentage = count / final_stats['total_classified'] * 100
            print(f"  {{category:<18}}: {{count:4d}} ({{percentage:5.1f}}%)")
    
    # Exportar resultado final
    classifier.export_classifications_to_csv("FINAL_COMPLETE_CLASSIFICATIONS.csv")
    print(f"\\n📄 Arquivo final: FINAL_COMPLETE_CLASSIFICATIONS.csv")
    print(f"🕐 Finalizado em: {{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}}")
    
    classifier.close()

if __name__ == "__main__":
    try:
        classify_remaining_sessions()
    except Exception as e:
        print(f"❌ Erro: {{e}}")
'''
        
        # Salvar script temporário
        with open("/Users/thomazkrause/workspace/python-apps/dog-food/night_classification.py", "w") as f:
            f.write(script_content)
        
        # Executar classificação
        subprocess.run([sys.executable, "night_classification.py"], 
                      cwd="/Users/thomazkrause/workspace/python-apps/dog-food",
                      check=True)
        
    except Exception as e:
        print(f"❌ Erro na execução: {e}")

def schedule_classification():
    """Configura o agendamento para às 22:00"""
    
    print("⏰ AGENDADOR DE CLASSIFICAÇÃO ATIVADO")
    print("=" * 50)
    print(f"🕐 Horário atual: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("📅 Agendado para: HOJE às 22:00")
    print("🎯 Tarefa: Classificar restante das sessões")
    print("\n⏳ Aguardando horário agendado...")
    print("💡 Para cancelar, pressione Ctrl+C")
    
    # Agendar para 22:00
    schedule.every().day.at("22:00").do(run_full_classification)
    
    # Verificar se já passou das 22:00 hoje
    now = datetime.now()
    target_time = now.replace(hour=22, minute=0, second=0, microsecond=0)
    
    if now >= target_time:
        print("⚠️  Já passou das 22:00 hoje!")
        print("🔄 Reagendando para 22:00 de amanhã...")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # Verificar a cada 30 segundos
    except KeyboardInterrupt:
        print("\n⏹️  Agendamento cancelado pelo usuário")

if __name__ == "__main__":
    schedule_classification()