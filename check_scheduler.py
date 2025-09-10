#!/usr/bin/env python3
"""
Script para verificar status do agendador
"""

import os
import subprocess
from datetime import datetime

def check_scheduler_status():
    """Verifica se o agendador está rodando"""
    
    print("🔍 VERIFICADOR DE AGENDADOR")
    print("=" * 40)
    print(f"🕐 Horário atual: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Verificar se existe PID salvo
    pid_file = "/Users/thomazkrause/workspace/python-apps/dog-food/scheduler.pid"
    
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                pid = f.read().strip()
            
            # Verificar se processo está rodando
            try:
                result = subprocess.run(['ps', '-p', pid], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ Agendador ATIVO (PID: {pid})")
                    print("📅 Agendado para: HOJE às 22:00")
                    
                    # Verificar log
                    log_file = "/Users/thomazkrause/workspace/python-apps/dog-food/scheduler.log"
                    if os.path.exists(log_file):
                        print(f"📄 Log disponível: scheduler.log")
                        
                        # Mostrar últimas linhas do log
                        try:
                            with open(log_file, 'r') as f:
                                lines = f.readlines()
                                if lines:
                                    print("\n📝 Últimas linhas do log:")
                                    for line in lines[-3:]:
                                        print(f"   {line.strip()}")
                        except:
                            pass
                    
                    # Comandos úteis
                    print(f"\n🛠️  Comandos úteis:")
                    print(f"   Acompanhar log: tail -f scheduler.log")
                    print(f"   Cancelar: kill {pid}")
                    
                else:
                    print(f"❌ Agendador NÃO está rodando (PID {pid} não encontrado)")
                    print("🔄 Para reiniciar: ./start_scheduler.sh")
                    
            except Exception as e:
                print(f"❌ Erro ao verificar processo: {e}")
                
        except Exception as e:
            print(f"❌ Erro ao ler PID: {e}")
    else:
        print("❌ Agendador NÃO foi iniciado")
        print("🚀 Para iniciar: ./start_scheduler.sh")
    
    # Status das classificações
    try:
        from session_classifier import SessionClassifier
        classifier = SessionClassifier()
        stats = classifier.get_classification_stats()
        remaining = stats['total_sessions'] - stats['total_classified']
        
        print(f"\n📊 Status das Classificações:")
        print(f"   ✅ Classificadas: {stats['total_classified']:,}")
        print(f"   📋 Restantes: {remaining:,}")
        print(f"   📈 Progresso: {(stats['total_classified']/stats['total_sessions']*100):.1f}%")
        
        classifier.close()
        
        # Calcular tempo até 22:00
        now = datetime.now()
        target = now.replace(hour=22, minute=0, second=0, microsecond=0)
        
        if now < target:
            time_remaining = target - now
            hours = int(time_remaining.total_seconds() // 3600)
            minutes = int((time_remaining.total_seconds() % 3600) // 60)
            print(f"\n⏰ Tempo até execução: {hours}h {minutes}min")
        else:
            print(f"\n⚠️  Horário de execução já passou!")
            
    except Exception as e:
        print(f"❌ Erro ao obter status: {e}")

if __name__ == "__main__":
    check_scheduler_status()