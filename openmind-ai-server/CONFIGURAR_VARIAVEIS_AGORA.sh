#!/bin/bash
# Script para configurar variáveis do OpenMind.org no servidor SinapUm
# Execute: ssh root@69.169.102.84 'bash -s' < CONFIGURAR_VARIAVEIS_AGORA.sh

echo "🔧 Configurando variáveis do OpenMind.org no servidor SinapUm..."

cd /opt/openmind-ai || { echo "❌ Erro: Diretório /opt/openmind-ai não encontrado!"; exit 1; }

# Verificar se .env existe
if [ ! -f .env ]; then
    echo "❌ Arquivo .env não encontrado! Criando..."
    touch .env
fi

# Backup do .env atual
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
echo "✅ Backup criado: .env.backup.$(date +%Y%m%d_%H%M%S)"

# Variáveis a configurar
OPENMIND_AI_API_KEY="om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1"
OPENMIND_ORG_API_KEY="om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1"
OPENMIND_ORG_BASE_URL="https://api.openmind.org/api/core/openai"
OPENMIND_ORG_MODEL="qwen2.5-vl-72b-instruct"

# Remover variáveis antigas se existirem
sed -i '/^OPENMIND_AI_API_KEY=/d' .env
sed -i '/^OPENMIND_ORG_API_KEY=/d' .env
sed -i '/^OPENMIND_ORG_BASE_URL=/d' .env
sed -i '/^OPENMIND_ORG_MODEL=/d' .env

# Adicionar variáveis
echo "" >> .env
echo "# Autenticação do próprio servidor" >> .env
echo "OPENMIND_AI_API_KEY=$OPENMIND_AI_API_KEY" >> .env
echo "" >> .env
echo "# OpenMind.org - LLM principal (você já pagou!)" >> .env
echo "OPENMIND_ORG_API_KEY=$OPENMIND_ORG_API_KEY" >> .env
echo "OPENMIND_ORG_BASE_URL=$OPENMIND_ORG_BASE_URL" >> .env
echo "OPENMIND_ORG_MODEL=$OPENMIND_ORG_MODEL" >> .env

echo "✅ Variáveis adicionadas ao .env"

# Verificar se as variáveis foram adicionadas
echo ""
echo "📋 Variáveis configuradas:"
grep "OPENMIND" .env | grep -v "^#"

# Testar se o Python consegue ler as variáveis
echo ""
echo "🧪 Testando leitura das variáveis..."
python3 << EOF
import sys
import os
sys.path.insert(0, '/opt/openmind-ai')
from app.core.config import settings

print("OPENMIND_ORG_API_KEY:", "✅ Configurada" if settings.OPENMIND_ORG_API_KEY else "❌ Não configurada")
print("OPENMIND_ORG_BASE_URL:", settings.OPENMIND_ORG_BASE_URL or "❌ Não configurada")
print("OPENMIND_ORG_MODEL:", settings.OPENMIND_ORG_MODEL or "❌ Não configurada")
EOF

echo ""
echo "🔄 Reiniciando serviço openmind-ai..."
systemctl restart openmind-ai

echo ""
echo "⏳ Aguardando 3 segundos..."
sleep 3

echo ""
echo "📊 Status do serviço:"
systemctl status openmind-ai --no-pager -l | head -15

echo ""
echo "✅ Configuração concluída!"
echo ""
echo "📝 Próximos passos:"
echo "1. Teste fazendo upload de uma imagem"
echo "2. Verifique os logs: journalctl -u openmind-ai -f"
echo "3. Os dados devem ser reais, não genéricos!"

