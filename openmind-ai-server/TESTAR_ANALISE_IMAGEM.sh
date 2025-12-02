#!/bin/bash
# Script para testar análise de imagem no servidor OpenMind AI

echo "🧪 Testando análise de imagem no OpenMind AI"
echo ""

# Verificar se OpenAI API Key está configurada
echo "1. Verificando configuração OpenAI API Key..."
cd /opt/openmind-ai
source venv/bin/activate

OPENAI_KEY=$(python3 -c "from app.core.config import settings; print(settings.OPENAI_API_KEY)" 2>/dev/null || echo "")

if [ -z "$OPENAI_KEY" ] || [ "$OPENAI_KEY" == "" ]; then
    echo "❌ OPENAI_API_KEY não está configurada!"
    echo ""
    echo "Para corrigir:"
    echo "1. Obtenha uma chave em: https://platform.openai.com/api-keys"
    echo "2. Edite o arquivo .env:"
    echo "   nano /opt/openmind-ai/.env"
    echo "3. Adicione:"
    echo "   OPENAI_API_KEY=sk-sua-chave-aqui"
    echo "4. Reinicie o serviço:"
    echo "   systemctl restart openmind-ai"
    exit 1
else
    echo "✅ OPENAI_API_KEY configurada"
fi

echo ""
echo "2. Verificando status do serviço..."
systemctl is-active openmind-ai > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Serviço está rodando"
else
    echo "❌ Serviço não está rodando!"
    echo "   Inicie com: systemctl start openmind-ai"
    exit 1
fi

echo ""
echo "3. Testando health check..."
HEALTH=$(curl -s http://localhost:8000/health)
if [ $? -eq 0 ]; then
    echo "✅ Health check OK"
    echo "   Resposta: $HEALTH"
else
    echo "❌ Health check falhou!"
    exit 1
fi

echo ""
echo "4. Para testar análise de imagem:"
echo "   curl -X POST http://localhost:8000/api/v1/analyze-product-image \\"
echo "     -H \"Authorization: Bearer om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1\" \\"
echo "     -F \"image=@/caminho/para/imagem.jpg\""
echo ""
echo "5. Ver logs em tempo real:"
echo "   journalctl -u openmind-ai -f"
echo ""
echo "✅ Diagnóstico concluído!"
