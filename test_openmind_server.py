#!/usr/bin/env python3
"""
Script de teste para o servidor OpenMind AI
"""
import requests
import json
import sys
from io import BytesIO
from PIL import Image
import os

# Configurações
SERVER_URL = "http://69.169.102.84:8000"
API_KEY = "om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1"

def print_section(title):
    """Imprime um separador visual"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_health_check():
    """Testa o endpoint de health check"""
    print_section("1. TESTE DE HEALTH CHECK")
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_root_endpoint():
    """Testa o endpoint raiz"""
    print_section("2. TESTE DO ENDPOINT RAIZ")
    try:
        response = requests.get(f"{SERVER_URL}/", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def create_test_image():
    """Cria uma imagem de teste simples"""
    # Criar uma imagem simples com texto
    img = Image.new('RGB', (400, 300), color='white')
    from PIL import ImageDraw, ImageFont
    
    draw = ImageDraw.Draw(img)
    # Tentar usar fonte padrão
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()
    
    draw.text((50, 100), "Produto Teste", fill='black', font=font)
    draw.text((50, 150), "Coca-Cola 350ml", fill='blue', font=font)
    
    # Salvar em buffer
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    return img_buffer

def test_analyze_endpoint_with_image_file(image_path=None):
    """Testa o endpoint de análise com uma imagem"""
    print_section("3. TESTE DE ANÁLISE DE IMAGEM")
    
    # Preparar imagem
    if image_path and os.path.exists(image_path):
        print(f"📷 Usando imagem local: {image_path}")
        with open(image_path, 'rb') as f:
            image_data = f.read()
        filename = os.path.basename(image_path)
    else:
        print("📷 Criando imagem de teste...")
        img_buffer = create_test_image()
        image_data = img_buffer.read()
        filename = "test_image.png"
    
    print(f"📦 Tamanho da imagem: {len(image_data)} bytes")
    
    # Preparar requisição
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    
    files = {
        "image": (filename, image_data, "image/png")
    }
    
    try:
        print(f"\n🚀 Enviando requisição para: {SERVER_URL}/api/v1/analyze-product-image")
        print(f"🔑 Usando API Key: {API_KEY[:20]}...")
        
        response = requests.post(
            f"{SERVER_URL}/api/v1/analyze-product-image",
            headers=headers,
            files=files,
            timeout=60
        )
        
        print(f"\n📊 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ SUCESSO! Resposta completa:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Extrair informações importantes
            if result.get('success'):
                data = result.get('data', {})
                print("\n📦 DADOS EXTRAÍDOS:")
                print(f"  Nome do Produto: {data.get('nome_produto', 'N/A')}")
                print(f"  Categoria: {data.get('categoria', 'N/A')}")
                print(f"  Subcategoria: {data.get('subcategoria', 'N/A')}")
                print(f"  Descrição: {data.get('descricao', 'N/A')[:100]}...")
                print(f"  Confiança: {result.get('confidence', 'N/A')}")
                print(f"  Tempo de Processamento: {result.get('processing_time_ms', 'N/A')}ms")
            else:
                print(f"\n⚠️  Erro na análise: {result.get('error', 'Desconhecido')}")
                print(f"   Código do erro: {result.get('error_code', 'N/A')}")
            
            return True
        else:
            print(f"\n❌ ERRO: Status {response.status_code}")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                print(f"Resposta texto: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Erro: Timeout - O servidor demorou mais de 60 segundos para responder")
        return False
    except Exception as e:
        print(f"❌ Erro ao fazer requisição: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_url_image(image_url):
    """Testa com uma imagem de URL"""
    print_section("4. TESTE COM IMAGEM DE URL")
    try:
        print(f"📥 Baixando imagem de: {image_url}")
        img_response = requests.get(image_url, timeout=10)
        img_response.raise_for_status()
        
        image_data = img_response.content
        filename = image_url.split('/')[-1] or "image.jpg"
        
        print(f"📦 Imagem baixada: {len(image_data)} bytes")
        
        # Usar a função de teste de análise
        return test_analyze_endpoint_with_image_file_data(image_data, filename)
    except Exception as e:
        print(f"❌ Erro ao baixar imagem: {e}")
        return False

def test_analyze_endpoint_with_image_file_data(image_data, filename):
    """Testa o endpoint com dados de imagem já carregados"""
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    
    files = {
        "image": (filename, image_data, "image/jpeg")
    }
    
    try:
        response = requests.post(
            f"{SERVER_URL}/api/v1/analyze-product-image",
            headers=headers,
            files=files,
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return True
        else:
            print(f"Erro: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_with_real_image_url():
    """Testa com uma imagem de produto real da internet"""
    print_section("4. TESTE COM IMAGEM REAL (URL)")
    
    # URLs de exemplo de produtos
    test_urls = [
        "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400",  # Tênis
        "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400",  # Óculos
    ]
    
    print("Escolha uma imagem de teste:")
    for i, url in enumerate(test_urls, 1):
        print(f"  {i}. {url}")
    
    try:
        choice = input("\nDigite o número (ou Enter para pular): ").strip()
        if not choice:
            print("Teste pulado.")
            return False
        
        idx = int(choice) - 1
        if 0 <= idx < len(test_urls):
            return test_with_url_image(test_urls[idx])
        else:
            print("Opção inválida.")
            return False
    except KeyboardInterrupt:
        print("\nTeste cancelado.")
        return False
    except Exception as e:
        print(f"Erro: {e}")
        return False

def main():
    """Função principal"""
    print("\n" + "🧪 "*20)
    print("  TESTE DO SERVIDOR OPENMIND AI")
    print("🧪 "*20)
    print(f"\n🔗 Servidor: {SERVER_URL}")
    print(f"🔑 API Key: {API_KEY[:20]}...")
    
    results = []
    
    # Teste 1: Health Check
    results.append(("Health Check", test_health_check()))
    
    # Teste 2: Root Endpoint
    results.append(("Root Endpoint", test_root_endpoint()))
    
    # Teste 3: Análise de Imagem
    # Verificar se foi passado um caminho de imagem como argumento
    image_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    if image_path:
        print(f"\n📷 Usando imagem fornecida: {image_path}")
    else:
        print(f"\n📷 Criando imagem de teste simples...")
        print("💡 Dica: Passe o caminho de uma imagem como argumento: python test_openmind_server.py caminho/para/imagem.jpg")
    
    result_analyze = test_analyze_endpoint_with_image_file(image_path)
    results.append(("Análise de Imagem", result_analyze))
    
    # Verificar se está retornando dados genéricos (fallback)
    if result_analyze:
        print("\n⚠️  AVISO: O servidor está retornando dados genéricos.")
        print("   Isso indica que as variáveis OPENMIND_ORG_* não estão configuradas no servidor.")
        print("   Configure as variáveis para obter análises reais da IA.")
    
    # Resumo
    print_section("RESUMO DOS TESTES")
    for test_name, passed in results:
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"  {test_name}: {status}")
    
    # Contagem
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    print(f"\n📊 Resultado: {passed_count}/{total_count} testes passaram")
    
    if passed_count == total_count:
        print("🎉 Todos os testes passaram!")
        print("\n💡 Próximos passos:")
        print("   1. Configure as variáveis OPENMIND_ORG_* no servidor SinapUm")
        print("   2. Teste com uma imagem real de produto")
        print("   3. Verifique os logs do servidor para debug")
        return 0
    else:
        print("⚠️  Alguns testes falharam")
        return 1

if __name__ == "__main__":
    sys.exit(main())

