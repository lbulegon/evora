#!/bin/bash

# Script para adicionar variáveis OpenMind.org no servidor SinapUm

echo "🔧 Adicionando variáveis OpenMind.org ao .env..."

cd /opt/openmind-ai || exit 1

# Verificar se as variáveis já existem
if grep -q "OPENMIND_ORG_API_KEY" .env; then
    echo "⚠️  Variáveis OpenMind.org já existem no .env"
    echo "📋 Conteúdo atual:"
    grep "OPENMIND_ORG" .env
else
    echo "# OpenMind.org - LLM principal (você já pagou!)" >> .env
    echo "OPENMIND_ORG_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1" >> .env
    echo "OPENMIND_ORG_BASE_URL=https://api.openmind.org/api/core/openai" >> .env
    echo "OPENMIND_ORG_MODEL=qwen2.5-vl-72b-instruct" >> .env
    echo "✅ Variáveis adicionadas!"
fi

echo ""
echo "📋 Últimas linhas do .env:"
tail -5 .env

echo ""
echo "🔄 Reiniciando serviço..."
systemctl restart openmind-ai

echo ""
echo "✅ Status do serviço:"
systemctl status openmind-ai --no-pager | head -5

echo ""
echo "🎉 Concluído! Servidor configurado para usar OpenMind.org"
