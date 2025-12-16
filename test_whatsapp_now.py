"""
Teste rápido de envio de produto via WhatsApp
"""
import requests
import json
import sys

BASE_URL = "https://evora-product.up.railway.app"

def test_status():
    """Testa status da instância"""
    print("=" * 60)
    print("1. Verificando status da instancia Evolution API...")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/whatsapp/status/", timeout=10)
        print(f"Status HTTP: {response.status_code}")
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        if data.get('success'):
            instance = data.get('instance', {})
            status = instance.get('status', 'unknown')
            print(f"\n[OK] Instancia: {instance.get('name')} - Status: {status}")
            if status != 'open':
                print("[ATENCAO] Instancia nao esta conectada (status != 'open')")
                print("   O envio pode falhar. Verifique a conexao do WhatsApp.")
            return status == 'open'
        else:
            print(f"\n[ERRO] {data.get('error')}")
            return False
    except Exception as e:
        print(f"\n[ERRO] Erro ao verificar status: {str(e)}")
        return False

def test_send_product(phone, use_product_id=False, product_id=None):
    """Testa envio de produto"""
    print("\n" + "=" * 60)
    print("2. Testando envio de produto via WhatsApp...")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/whatsapp/send-product/"
    
    if use_product_id and product_id:
        payload = {
            "phone": phone,
            "product_id": product_id
        }
        print(f"📤 Enviando produto ID {product_id} para {phone}")
    else:
        payload = {
            "phone": phone,
            "product_data": {
                "produto": {
                    "nome": "Cerveja Polar - Teste",
                    "marca": "Polar",
                    "categoria": "Bebidas",
                    "subcategoria": "Cerveja",
                    "preco": "R$ 5,99",
                    "descricao": "Cerveja Polar gelada, 1 litro. Teste de envio via WhatsApp."
                }
            }
        }
        print(f"📤 Enviando produto (dados diretos) para {phone}")
    
    print(f"\nURL: {url}")
    print(f"Payload:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"\nResposta (Status HTTP: {response.status_code}):")
        result = response.json()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if response.status_code == 200 and result.get('success'):
            print("\n[SUCESSO] Produto enviado via WhatsApp")
            print("   Verifique seu WhatsApp para ver a mensagem.")
            return True
        else:
            print(f"\n[ERRO] {result.get('error', 'Erro desconhecido')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Erro ao fazer requisição: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    import io
    # Configurar encoding UTF-8 para Windows
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("\n" + "=" * 60)
    print("TESTE DE ENVIO DE PRODUTOS VIA WHATSAPP")
    print("=" * 60)
    
    # Verificar status primeiro
    status_ok = test_status()
    
    if not status_ok:
        print("\n[AVISO] A instancia nao esta conectada.")
        resposta = input("Deseja continuar mesmo assim? (s/n): ").strip().lower()
        if resposta != 's':
            print("Teste cancelado.")
            sys.exit(0)
    
    # Pedir número de telefone
    print("\n" + "=" * 60)
    phone = input("Digite o numero do WhatsApp (formato: +5511999999999): ").strip()
    
    if not phone:
        print("[ERRO] Numero nao fornecido. Saindo...")
        sys.exit(1)
    
    # Verificar formato
    if not phone.startswith('+'):
        print("[AVISO] Numero nao comeca com '+'. Adicionando automaticamente...")
        if phone.startswith('55'):
            phone = f"+{phone}"
        else:
            phone = f"+55{phone}"
        print(f"   Numero formatado: {phone}")
    
    # Escolher tipo de teste
    print("\n" + "=" * 60)
    print("Escolha o tipo de teste:")
    print("1. Enviar produto usando product_id (ID: 23 - Del Valle)")
    print("2. Enviar produto usando dados diretos (teste simples)")
    print("=" * 60)
    
    choice = input("\nEscolha (1 ou 2): ").strip()
    
    if choice == "1":
        test_send_product(phone, use_product_id=True, product_id=23)
    elif choice == "2":
        test_send_product(phone, use_product_id=False)
    else:
        print("[AVISO] Opcao invalida. Usando teste com dados diretos...")
        test_send_product(phone, use_product_id=False)
    
    print("\n" + "=" * 60)
    print("[OK] Teste concluido!")
    print("=" * 60)

