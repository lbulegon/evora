#!/bin/bash

echo "Iniciando aplicação VitrineZap..."

# Executar migrações
echo "Executando migrações..."
python manage.py migrate --noinput

# Coletar arquivos estáticos
echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

# Criar superusuário se não existir (opcional)
echo "Verificando superusuário..."
python manage.py shell -c "
from django.contrib.auth.models import User
import os
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@vitrinezap.com', os.getenv('ADMIN_PASSWORD', 'admin123'))
    print('Superusuário criado')
else:
    print('Superusuário já existe')
"

# Iniciar servidor
echo "Iniciando servidor gunicorn..."
exec gunicorn setup.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --log-level info \
    --access-logfile - \
    --error-logfile -


