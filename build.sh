#!/bin/bash
# Script de build para Railway
# Coleta arquivos estáticos antes de iniciar o servidor

echo "🔨 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "✅ Build concluído!"


