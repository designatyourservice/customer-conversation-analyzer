#!/bin/bash
# Script para iniciar o Conversation Analyzer

echo "🚀 INICIANDO CONVERSATION ANALYZER"
echo "=================================="

# Verificar se Python está disponível
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não está instalado"
    exit 1
fi

# Verificar se Flask está instalado
if ! python3 -c "import flask" &> /dev/null; then
    echo "📦 Instalando Flask..."
    pip install flask
fi

# Verificar se banco de dados existe
if [ ! -f "talqui.db" ]; then
    echo "❌ Banco de dados talqui.db não encontrado!"
    echo "   Certifique-se de que o arquivo talqui.db está no diretório atual"
    exit 1
fi

# Matar processos na porta se existirem
echo "🧹 Liberando porta 5001..."
lsof -ti:5001 | xargs kill -9 2>/dev/null || true

# Iniciar aplicação
echo "🌐 Iniciando servidor em http://localhost:5001"
echo "   Pressione Ctrl+C para parar"
echo ""

python3 conversation_analyzer_app.py