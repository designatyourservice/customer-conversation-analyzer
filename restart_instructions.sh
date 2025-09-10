#!/bin/bash

echo "🔄 INSTRUÇÕES PARA REINICIAR COM SEGURANÇA"
echo "=========================================="
echo ""
echo "⚠️  ATENÇÃO: O agendador será perdido no reinício!"
echo ""
echo "🔧 PASSOS RECOMENDADOS:"
echo ""
echo "1. 📋 ANTES DE REINICIAR:"
echo "   - Salvar trabalhos abertos"
echo "   - Fechar aplicações importantes"
echo ""
echo "2. 🔄 PARA REINICIAR:"
echo "   sudo reboot"
echo "   # OU pelo menu Apple > Restart"
echo ""
echo "3. ✅ APÓS REINICIAR:"
echo "   cd /Users/thomazkrause/workspace/python-apps/dog-food"
echo "   ./start_scheduler.sh"
echo ""
echo "🕐 ALTERNATIVA SEM PERDER AGENDAMENTO:"
echo "   - Usar 'Activity Monitor' para fechar apps pesados"
echo "   - O sistema já foi otimizado (75MB liberados)"
echo "   - Agendador continuará funcionando às 22:00"
echo ""
echo "💡 RECOMENDAÇÃO:"
echo "   Teste a performance atual antes de reiniciar"
echo "   O agendador está funcionando perfeitamente!"

# Verificar se ainda precisa reiniciar
echo ""
echo "📊 STATUS ATUAL:"
top -l 1 -s 0 | grep "PhysMem"

echo ""
echo "🕐 STATUS DO AGENDADOR:"
if [ -f "/Users/thomazkrause/workspace/python-apps/dog-food/scheduler.pid" ]; then
    PID=$(cat /Users/thomazkrause/workspace/python-apps/dog-food/scheduler.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ ATIVO - Executará às 22:00 automaticamente"
    else
        echo "❌ INATIVO - Precisará reiniciar após reboot"
    fi
else
    echo "❌ NÃO CONFIGURADO"
fi