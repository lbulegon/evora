#!/bin/bash

# Script para atualizar o código no servidor SinapUm

echo "🔧 Atualizando código no servidor..."

cd /opt/openmind-ai

# Backup do config.py atual
cp app/core/config.py app/core/config.py.backup

# O código já foi atualizado localmente com extra = "ignore"
# Você precisa copiar o arquivo atualizado ou fazer git pull

echo "✅ Reiniciando serviço..."
systemctl restart openmind-ai
systemctl status openmind-ai --no-pager | head -10
