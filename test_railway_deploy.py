#!/usr/bin/env python
"""
Script para testar deploy no Railway
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

def test_railway_config():
    """Testar configuração Railway"""
    print("🚂 Testando configuração Railway...")
    
    # Verificar variáveis de ambiente
    railway_env = os.getenv('RAILWAY_ENVIRONMENT')
    print(f"RAILWAY_ENVIRONMENT: {railway_env}")
    
    # Verificar configurações do Django
    from django.conf import settings
    
    print(f"DEBUG: {settings.DEBUG}")
    print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    print(f"DATABASE ENGINE: {settings.DATABASES['default']['ENGINE']}")
    
    # Verificar banco de dados
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Conexão com banco OK")
    except Exception as e:
        print(f"❌ Erro no banco: {e}")
    
    # Verificar migrações pendentes
    try:
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'showmigrations'])
        print("✅ Migrações OK")
    except Exception as e:
        print(f"❌ Erro nas migrações: {e}")
    
    # Verificar arquivos estáticos
    static_root = settings.STATIC_ROOT
    if static_root and static_root.exists():
        print(f"✅ STATIC_ROOT: {static_root}")
    else:
        print(f"⚠️ STATIC_ROOT não encontrado: {static_root}")
    
    print("\n🎯 Configuração Railway testada!")

def test_local_config():
    """Testar configuração local"""
    print("💻 Testando configuração local...")
    
    # Simular ambiente local
    if 'RAILWAY_ENVIRONMENT' in os.environ:
        del os.environ['RAILWAY_ENVIRONMENT']
    
    # Recarregar configurações
    from importlib import reload
    import setup.settings
    reload(setup.settings)
    
    from django.conf import settings
    
    print(f"DEBUG: {settings.DEBUG}")
    print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    print(f"DATABASE ENGINE: {settings.DATABASES['default']['ENGINE']}")
    
    print("\n🎯 Configuração local testada!")

def main():
    """Função principal"""
    print("🔍 DIAGNÓSTICO RAILWAY vs LOCAL")
    print("=" * 50)
    
    # Testar configuração local
    test_local_config()
    
    print("\n" + "=" * 50)
    
    # Simular ambiente Railway
    os.environ['RAILWAY_ENVIRONMENT'] = 'production'
    os.environ['PGDATABASE'] = 'test_db'
    os.environ['PGUSER'] = 'test_user'
    os.environ['PGPASSWORD'] = 'test_pass'
    os.environ['PGHOST'] = 'localhost'
    os.environ['PGPORT'] = '5432'
    
    # Testar configuração Railway
    test_railway_config()
    
    print("\n" + "=" * 50)
    print("✅ Diagnóstico concluído!")
    
    print("\n📋 PRÓXIMOS PASSOS:")
    print("1. Verificar logs Railway: railway logs --tail")
    print("2. Verificar variáveis: railway variables")
    print("3. Fazer deploy: git push origin main")
    print("4. Testar URL Railway")

if __name__ == '__main__':
    main()
