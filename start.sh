#!/bin/bash
set -e  # Parar em caso de erro

echo "=========================================="
echo "Iniciando aplicação VitrineZap..."
echo "=========================================="

# Verificar variáveis de ambiente
echo "Variáveis de ambiente:"
echo "PORT: $PORT"
echo "RAILWAY_ENVIRONMENT: ${RAILWAY_ENVIRONMENT:-não definido}"
echo "PGHOST: ${PGHOST:-não definido}"

# Ativar ambiente virtual se existir
if [ -d "/app/.venv" ]; then
    echo "Ativando ambiente virtual..."
    source /app/.venv/bin/activate
    PYTHON_CMD="/app/.venv/bin/python"
    GUNICORN_CMD="/app/.venv/bin/gunicorn"
    echo "Usando ambiente virtual: $PYTHON_CMD"
else
    PYTHON_CMD="python"
    GUNICORN_CMD="gunicorn"
    echo "Usando Python do sistema: $PYTHON_CMD"
fi

# Verificar versão do Python
echo "Python version:"
$PYTHON_CMD --version

# Executar migrações
echo "=========================================="
echo "Executando migrações..."
echo "=========================================="
$PYTHON_CMD manage.py migrate --noinput || {
    echo "ERRO: Falha ao executar migrações!"
    exit 1
}

# Coletar arquivos estáticos (já feito no build, mas garantindo)
echo "=========================================="
echo "Coletando arquivos estáticos..."
echo "=========================================="
$PYTHON_CMD manage.py collectstatic --noinput || {
    echo "AVISO: Falha ao coletar arquivos estáticos (continuando...)"
}

# Criar superusuário se não existir (opcional)
echo "=========================================="
echo "Verificando superusuário..."
echo "=========================================="
$PYTHON_CMD manage.py shell -c "
from django.contrib.auth.models import User
import os
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@vitrinezap.com', os.getenv('ADMIN_PASSWORD', 'admin123'))
    print('Superusuário criado')
else:
    print('Superusuário já existe')
" || {
    echo "AVISO: Falha ao verificar/criar superusuário (continuando...)"
}

# Verificar se o servidor pode iniciar
echo "=========================================="
echo "Verificando configuração do Django..."
echo "=========================================="
$PYTHON_CMD manage.py check --deploy || {
    echo "AVISO: Alguns checks falharam (continuando...)"
}

# Iniciar servidor
echo "=========================================="
echo "Iniciando servidor gunicorn na porta $PORT..."
echo "=========================================="
exec $GUNICORN_CMD setup.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    --capture-output


