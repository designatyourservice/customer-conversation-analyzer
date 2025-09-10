#!/bin/bash

echo "🚀 OTIMIZAÇÃO DE SISTEMA MACOS"
echo "=============================="

echo "1. 🗑️  Limpando cache de usuário..."
rm -rf ~/Library/Caches/* 2>/dev/null || true

echo "2. 🧹 Limpando arquivos temporários..."
find /tmp -user $(whoami) -delete 2>/dev/null || true
find ~/Downloads -name "*.tmp" -delete 2>/dev/null || true

echo "3. ⏹️  Parando processos pesados..."
pkill -f streamlit 2>/dev/null || true
pkill -f jupyter 2>/dev/null || true

echo "4. 💾 Status da memória ANTES:"
top -l 1 -s 0 | grep "PhysMem"

echo "5. 🔄 Forçando liberação de memória..."
# Simular purge sem sudo
sync
echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || echo "   (comando alternativo não disponível)"

echo "6. 🧽 Limpando DNS cache..."
dscacheutil -flushcache 2>/dev/null || true

echo "7. 📱 Reiniciando Dock e Finder..."
killall Dock 2>/dev/null || true
killall Finder 2>/dev/null || true

sleep 3

echo "8. 💾 Status da memória DEPOIS:"
top -l 1 -s 0 | grep "PhysMem"

echo ""
echo "✅ OTIMIZAÇÃO CONCLUÍDA!"
echo "💡 Recomendações adicionais:"
echo "   - Reiniciar o sistema para máxima otimização"
echo "   - Fechar abas desnecessárias do navegador"
echo "   - Verificar Activity Monitor para processos pesados"

# Verificar agendador
echo ""
echo "🕐 Verificando agendador às 22:00..."
if [ -f "/Users/thomazkrause/workspace/python-apps/dog-food/scheduler.pid" ]; then
    PID=$(cat /Users/thomazkrause/workspace/python-apps/dog-food/scheduler.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ Agendador ainda ativo (PID: $PID)"
    else
        echo "❌ Agendador não está rodando - reiniciar se necessário"
        echo "🔄 Para reiniciar: ./start_scheduler.sh"
    fi
else
    echo "❌ Agendador não foi iniciado"
fi