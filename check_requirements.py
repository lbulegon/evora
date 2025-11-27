#!/usr/bin/env python
"""
Script para verificar se todas as dependências estão instaladas e funcionando
"""
import sys

def check_requirements():
    """Verifica se todas as dependências essenciais estão funcionando"""
    print("VERIFICAÇÃO DE DEPENDÊNCIAS - VitrineZap (ÉVORA) + KMN")
    print("=" * 50)
    
    # Lista de dependências essenciais
    dependencies = [
        ('django', 'Django framework'),
        ('rest_framework', 'Django REST Framework'),
        ('corsheaders', 'Django CORS Headers'),
        ('django_filters', 'Django Filter'),
        ('drf_yasg', 'DRF YASG (Swagger)'),
        ('requests', 'HTTP Requests'),
        ('httpx', 'Async HTTP Client'),
        ('openai', 'OpenAI API'),
        ('redis', 'Redis Client'),
        ('django_redis', 'Django Redis'),
        ('PIL', 'Pillow (Images)'),
        ('psycopg2', 'PostgreSQL Driver'),
    ]
    
    failed = []
    
    for module, description in dependencies:
        try:
            __import__(module)
            print(f"OK {description}")
        except ImportError as e:
            print(f"ERROR {description}: {e}")
            failed.append(module)
    
    print("\n" + "=" * 50)
    
    if failed:
        print(f"ERRO: {len(failed)} dependências faltando:")
        for module in failed:
            print(f"  - {module}")
        print("\nPara instalar:")
        print("pip install -r requirements.txt")
        return False
    else:
        print("SUCESSO: Todas as dependências estão instaladas!")
        
        # Verificar versões específicas
        print("\nVersões instaladas:")
        try:
            import django
            print(f"  Django: {django.get_version()}")
        except:
            pass
            
        try:
            import rest_framework
            print(f"  DRF: {rest_framework.VERSION}")
        except:
            pass
            
        try:
            import openai
            print(f"  OpenAI: {openai.__version__}")
        except:
            pass
        
        return True

def check_django_setup():
    """Verifica se o Django está configurado corretamente"""
    print("\n" + "=" * 50)
    print("VERIFICAÇÃO DJANGO SETUP")
    print("=" * 50)
    
    try:
        import os
        import django
        
        # Setup Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
        django.setup()
        
        # Verificar apps instalados
        from django.conf import settings
        
        required_apps = [
            'rest_framework',
            'corsheaders', 
            'django_filters',
            'app_marketplace',
        ]
        
        missing_apps = []
        for app in required_apps:
            if app not in settings.INSTALLED_APPS:
                missing_apps.append(app)
        
        if missing_apps:
            print(f"ERRO: Apps faltando no INSTALLED_APPS:")
            for app in missing_apps:
                print(f"  - {app}")
            return False
        else:
            print("OK: Todos os apps necessários estão instalados")
            
        # Verificar modelos KMN
        try:
            from app_marketplace.models import Agente, Oferta, TrustlineKeeper
            print("OK: Modelos KMN importados com sucesso")
        except ImportError as e:
            print(f"ERRO: Problema com modelos KMN: {e}")
            return False
            
        # Verificar APIs
        try:
            from app_marketplace.api_views import AgenteViewSet
            print("OK: APIs KMN importadas com sucesso")
        except ImportError as e:
            print(f"ERRO: Problema com APIs KMN: {e}")
            return False
            
        # Verificar serviços
        try:
            from app_marketplace.services import KMNRoleEngine
            print("OK: Serviços KMN importados com sucesso")
        except ImportError as e:
            print(f"ERRO: Problema com serviços KMN: {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"ERRO: Problema na configuração Django: {e}")
        return False

def main():
    """Função principal"""
    success = True
    
    # Verificar dependências
    if not check_requirements():
        success = False
    
    # Verificar Django setup
    if not check_django_setup():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("SUCESSO: Sistema pronto para uso!")
        print("\nPara iniciar:")
        print("  python manage.py runserver")
        print("\nPara testar:")
        print("  python test_kmn_system.py")
        print("  python test_frontend_integration.py")
    else:
        print("ERRO: Corrija os problemas acima antes de continuar")
        sys.exit(1)

if __name__ == '__main__':
    main()
