#!/bin/bash
# Script para configurar as variáveis do OpenMind.org no servidor SinapUm

cd /opt/openmind-ai

# Verificar se as variáveis já existem e remover se necessário
sed -i '/^OPENMIND_ORG_API_KEY=/d' .env
sed -i '/^OPENMIND_ORG_BASE_URL=/d' .env
sed -i '/^OPENMIND_ORG_MODEL=/d' .env

# Adicionar as variáveis
echo "OPENMIND_ORG_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1" >> .env
echo "OPENMIND_ORG_BASE_URL=https://api.openmind.org/api/core/openai" >> .env
echo "OPENMIND_ORG_MODEL=qwen2.5-vl-72b-instruct" >> .env

# Mostrar o .env atualizado
echo "=== Arquivo .env atualizado ==="
cat .env

# Reiniciar o serviço
echo ""
echo "=== Reiniciando serviço ==="
systemctl restart openmind-ai
sleep 2
systemctl status openmind-ai --no-pager -l

echo ""
echo "✅ Configuração concluída!"




ssh root@69.169.102.84
