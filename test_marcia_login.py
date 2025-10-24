#!/usr/bin/env python
"""
Teste de login da Marcia
"""
import requests
import json

def test_marcia_login():
    """Testar login da Marcia"""
    base_url = "http://127.0.0.1:8000"
    
    # Criar sessão
    session = requests.Session()
    
    # 1. Acessar página de login para obter CSRF token
    print("🔐 Testando login da Marcia...")
    
    try:
        # Acessar página de login
        login_page = session.get(f"{base_url}/login/")
        print(f"✅ Página de login acessada: {login_page.status_code}")
        
        # Fazer login
        login_data = {
            'username': 'marcia',
            'password': '123456',
            'csrfmiddlewaretoken': session.cookies.get('csrftoken', '')
        }
        
        login_response = session.post(f"{base_url}/login/", data=login_data)
        print(f"✅ Login realizado: {login_response.status_code}")
        
        if login_response.status_code == 200:
            print("🎉 Login bem-sucedido!")
            
            # Testar acesso ao dashboard
            dashboard_response = session.get(f"{base_url}/shopper/dashboard/")
            print(f"✅ Dashboard acessado: {dashboard_response.status_code}")
            
            # Testar acesso aos produtos
            products_response = session.get(f"{base_url}/shopper/products/")
            print(f"✅ Página de produtos acessada: {products_response.status_code}")
            
            if products_response.status_code == 200:
                print("🎯 Sistema funcionando perfeitamente!")
                print("\n📋 Próximos passos:")
                print("1. Acesse: http://127.0.0.1:8000/login/")
                print("2. Login: marcia / 123456")
                print("3. Vá para: Produtos")
                print("4. Crie um produto com estabelecimento")
            else:
                print("❌ Erro ao acessar produtos")
        else:
            print("❌ Erro no login")
            
    except requests.exceptions.ConnectionError:
        print("❌ Servidor não está rodando!")
        print("Execute: python manage.py runserver")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == '__main__':
    test_marcia_login()
