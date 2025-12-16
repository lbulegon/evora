"""
Teste simples de envio de produto - sem verificar status
"""
import requests
import json
import sys

BASE_URL = "https://evora-product.up.railway.app"

def test_send_product(phone):
    """Testa envio de produto"""
    print("=" * 60)
    print("TESTE DE ENVIO DE PRODUTO VIA WHATSAPP")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/whatsapp/send-product/"
    
    # Usar dados diretos (não precisa de produto no banco)
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
    
    print(f"\nEnviando produto para: {phone}")
    print(f"URL: {url}")
    print(f"\nPayload:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"\n" + "=" * 60)
        print(f"RESPOSTA (Status HTTP: {response.status_code})")
        print("=" * 60)
        print(f"Response Text: {response.text[:500]}")
        
        try:
            result = response.json()
            print(json.dumps(result, indent=2, ensure_ascii=False))
        except:
            print("Resposta nao e JSON valido")
            result = {"error": response.text}
        
        if response.status_code == 200 and result.get('success'):
            print("\n[SUCESSO] Produto enviado via WhatsApp!")
            print("Verifique seu WhatsApp para ver a mensagem.")
            return True
        else:
            print(f"\n[ERRO] {result.get('error', 'Erro desconhecido')}")
            return False
            
    except Exception as e:
        print(f"\n[ERRO] Erro ao fazer requisicao: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
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
        print(f"Numero formatado: {phone}")
    
    # Executar teste
    test_send_product(phone)
    
    print("\n" + "=" * 60)
    print("Teste concluido!")
    print("=" * 60)

