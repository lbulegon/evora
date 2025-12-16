"""
Script de teste para envio de produtos via WhatsApp
====================================================

Este script demonstra como testar o endpoint de envio de produtos.

Uso:
    python test_send_product_whatsapp.py
"""

import requests
import json
import os
from django.conf import settings

# Configurações
BASE_URL = os.getenv('BASE_URL', 'https://evora-product.up.railway.app')
# Para testar localmente, use: BASE_URL = 'http://localhost:8000'

def test_send_product_with_id(phone: str, product_id: int):
    """
    Testa envio de produto usando product_id (busca no banco)
    """
    url = f"{BASE_URL}/api/whatsapp/send-product/"
    
    payload = {
        "phone": phone,
        "product_id": product_id
    }
    
    print(f"\n📤 Testando envio de produto (ID: {product_id}) para {phone}")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"\n📥 Resposta (Status: {response.status_code}):")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        if response.status_code == 200:
            print("\n✅ Sucesso! Produto enviado via WhatsApp")
        else:
            print(f"\n❌ Erro: {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ Erro ao fazer requisição: {str(e)}")


def test_send_product_with_data(phone: str):
    """
    Testa envio de produto usando product_data (dados diretos)
    """
    url = f"{BASE_URL}/api/whatsapp/send-product/"
    
    payload = {
        "phone": phone,
        "product_data": {
            "produto": {
                "nome": "Cerveja Polar",
                "marca": "Polar",
                "categoria": "Bebidas",
                "subcategoria": "Cerveja",
                "preco": "R$ 5,99",
                "descricao": "Cerveja Polar gelada, 1 litro. Desde 1912."
            }
        },
        "image_url": "https://via.placeholder.com/500"  # URL de imagem de exemplo
    }
    
    print(f"\n📤 Testando envio de produto (dados diretos) para {phone}")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"\n📥 Resposta (Status: {response.status_code}):")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        if response.status_code == 200:
            print("\n✅ Sucesso! Produto enviado via WhatsApp")
        else:
            print(f"\n❌ Erro: {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ Erro ao fazer requisição: {str(e)}")


def list_products():
    """
    Lista produtos disponíveis no banco (via Django shell ou admin)
    """
    print("\n📋 Para listar produtos no banco, use:")
    print("   python manage.py shell")
    print("\n   E execute:")
    print("   from app_marketplace.models import ProdutoJSON, Produto")
    print("   print('Produtos JSON:', ProdutoJSON.objects.count())")
    print("   print('Produtos Tradicionais:', Produto.objects.count())")
    print("   for p in ProdutoJSON.objects.all()[:5]:")
    print("       print(f'ID: {p.id} - {p.nome_produto}')")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTE DE ENVIO DE PRODUTOS VIA WHATSAPP")
    print("=" * 60)
    
    # Substitua pelo seu número de WhatsApp (formato: +5511999999999)
    PHONE = input("\n📱 Digite o número do WhatsApp (formato: +5511999999999): ").strip()
    
    if not PHONE:
        print("❌ Número não fornecido. Saindo...")
        exit(1)
    
    print("\n" + "=" * 60)
    print("Escolha o tipo de teste:")
    print("1. Enviar produto usando product_id (busca no banco)")
    print("2. Enviar produto usando product_data (dados diretos)")
    print("3. Listar produtos disponíveis")
    print("=" * 60)
    
    choice = input("\nEscolha (1, 2 ou 3): ").strip()
    
    if choice == "1":
        product_id = input("Digite o ID do produto: ").strip()
        try:
            product_id = int(product_id)
            test_send_product_with_id(PHONE, product_id)
        except ValueError:
            print("❌ ID inválido. Deve ser um número.")
    
    elif choice == "2":
        test_send_product_with_data(PHONE)
    
    elif choice == "3":
        list_products()
    
    else:
        print("❌ Opção inválida")

