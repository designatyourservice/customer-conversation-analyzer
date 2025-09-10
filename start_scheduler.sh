#!/bin/bash

# Script para iniciar o agendador em background
# Execução: ./start_scheduler.sh

echo "🕐 Iniciando Agendador de Classificação..."
echo "📅 Horário de execução: HOJE às 22:00"

cd "/Users/thomazkrause/workspace/python-apps/dog-food"

# Executar em background com log
nohup python3 scheduled_classification.py > scheduler.log 2>&1 &

# Obter PID do processo
PID=$!

echo "✅ Agendador iniciado com PID: $PID"
echo "📄 Log salvo em: scheduler.log"
echo "🔍 Para acompanhar: tail -f scheduler.log"
echo "⏹️  Para cancelar: kill $PID"

# Salvar PID para controle
echo $PID > scheduler.pid

echo ""
echo "📊 Status atual das classificações:"
python3 -c "
from session_classifier import SessionClassifier
c = SessionClassifier()
s = c.get_classification_stats()
remaining = s['total_sessions'] - s['total_classified']
print(f'  ✅ Classificadas: {s[\"total_classified\"]:,}')
print(f'  📋 Restantes: {remaining:,}')
print(f'  💰 Custo estimado: \${remaining * 0.00009:.4f} USD')
print(f'  ⏱️  Tempo estimado: ~{remaining / 6.5 / 60:.1f} horas')
c.close()
"

echo ""
echo "🎯 O sistema classificará automaticamente às 22:00!"