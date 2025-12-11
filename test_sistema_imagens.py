"""
Teste completo do sistema de imagens do SinapUm
Valida que a função build_image_url funciona corretamente e que as URLs são construídas adequadamente
"""
import sys
import os
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from app_marketplace.utils import build_image_url
from django.conf import settings
import requests

def test_build_image_url():
    """Testa a função build_image_url com vários cenários"""
    print("=" * 80)
    print("TESTE: build_image_url")
    print("=" * 80)
    
    # Configurar URL do SinapUm
    openmind_url = getattr(settings, 'OPENMIND_AI_URL', 'http://69.169.102.84:8000/api/v1')
    
    test_cases = [
        # (input, expected_pattern, description)
        (
            "media/uploads/7cc806f7-e22d-45ba-8aab-6513f1715c09.jpg",
            "69.169.102.84:8000/media/uploads/",
            "Path com media/ (mais comum)"
        ),
        (
            "photo_0.jpg",
            "69.169.102.84:8000/media/photo_0.jpg",
            "Path simples sem media/"
        ),
        (
            "produtos/temp/15/20251202_043814_temp.jpg",
            "69.169.102.84:8000/media/produtos/temp/",
            "Path produtos/temp"
        ),
        (
            "http://69.169.102.84:8000/media/uploads/test.jpg",
            "http://69.169.102.84:8000/media/uploads/test.jpg",
            "URL completa (deve retornar como está)"
        ),
        (
            "/media/uploads/test.jpg",
            "/media/uploads/test.jpg",
            "Path absoluto local"
        ),
        (
            None,
            None,
            "Path None (deve retornar None)"
        ),
        (
            "",
            None,
            "Path vazio (deve retornar None)"
        ),
    ]
    
    print(f"\nURL base configurada: {openmind_url}\n")
    
    passed = 0
    failed = 0
    
    for input_path, expected_pattern, description in test_cases:
        try:
            result = build_image_url(input_path, openmind_url=openmind_url)
            
            # Verificar resultado
            if expected_pattern is None:
                success = result is None
                expected_str = "None"
            else:
                success = expected_pattern in result if result else False
                expected_str = f"contém '{expected_pattern}'"
            
            status = "[OK] PASSOU" if success else "[ERRO] FALHOU"
            
            print(f"{status} - {description}")
            print(f"  Input:    {input_path}")
            print(f"  Output:   {result}")
            print(f"  Esperado: {expected_str}")
            
            if success:
                passed += 1
            else:
                failed += 1
                if result:
                    # Verificar se não tem duplicação de /media/
                    if "/media/media/" in result:
                        print(f"  [ERRO] URL tem duplicacao de /media/")
            
            print()
            
        except Exception as e:
            print(f"[ERRO] ERRO - {description}")
            print(f"  Input:    {input_path}")
            print(f"  Erro:     {e}")
            print()
            failed += 1
    
    print(f"\nResultado: {passed} passaram, {failed} falharam")
    return failed == 0


def test_acesso_servidor():
    """Testa se o servidor SinapUm está acessível"""
    print("=" * 80)
    print("TESTE: Acesso ao Servidor SinapUm")
    print("=" * 80)
    
    base_url = "http://69.169.102.84:8000"
    test_image = "media/uploads/7cc806f7-e22d-45ba-8aab-6513f1715c09.jpg"
    
    tests = [
        ("Root", f"{base_url}/"),
        ("Health", f"{base_url}/health"),
        ("Imagem específica", f"{base_url}/{test_image}"),
    ]
    
    passed = 0
    failed = 0
    
    for name, url in tests:
        try:
            response = requests.get(url, timeout=5)
            status = "[OK]" if response.status_code == 200 else "[AVISO]"
            
            print(f"{status} {name}")
            print(f"  URL: {url}")
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                if "Imagem" in name:
                    print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                    print(f"  Tamanho: {len(response.content)} bytes")
                else:
                    print(f"  Resposta: {response.text[:100]}")
                passed += 1
            else:
                failed += 1
            
            print()
            
        except requests.exceptions.ConnectionError:
            print(f"[ERRO] {name} - Erro de conexao")
            print(f"  URL: {url}")
            print(f"  O servidor pode estar offline ou inacessível\n")
            failed += 1
        except requests.exceptions.Timeout:
            print(f"[ERRO] {name} - Timeout")
            print(f"  URL: {url}\n")
            failed += 1
        except Exception as e:
            print(f"[ERRO] {name} - Erro: {e}")
            print(f"  URL: {url}\n")
            failed += 1
    
    print(f"Resultado: {passed} passaram, {failed} falharam")
    return failed == 0


def test_integracao_produto_json():
    """Testa se a função funciona com dados reais de ProdutoJSON"""
    print("=" * 80)
    print("TESTE: Integração com ProdutoJSON")
    print("=" * 80)
    
    try:
        from app_marketplace.models import ProdutoJSON
        
        # Buscar um produto real
        produto = ProdutoJSON.objects.first()
        
        if not produto:
            print("[AVISO] Nenhum ProdutoJSON encontrado no banco de dados")
            print("   Criando teste simulado...\n")
            
            # Simular dados
            dados_json = {
                "produto": {
                    "imagens": [
                        "media/uploads/7cc806f7-e22d-45ba-8aab-6513f1715c09.jpg",
                        "photo_0.jpg"
                    ]
                }
            }
            imagem_original = "media/uploads/7cc806f7-e22d-45ba-8aab-6513f1715c09.jpg"
        else:
            print(f"[OK] Produto encontrado: {produto.nome_produto} (ID: {produto.id})\n")
            dados_json = produto.dados_json or {}
            imagem_original = produto.imagem_original
        
        # Testar extração de imagens
        produto_data = dados_json.get('produto', {})
        imagens = produto_data.get('imagens', [])
        
        print("Testando extração de imagens:")
        print(f"  imagem_original: {imagem_original}")
        print(f"  imagens array: {imagens}\n")
        
        image_urls = []
        
        # 1. Testar imagem_original
        if imagem_original:
            url = build_image_url(imagem_original)
            if url:
                image_urls.append(url)
                print(f"[OK] imagem_original -> {url}")
        
        # 2. Testar array de imagens
        if imagens:
            for img in imagens:
                if isinstance(img, str):
                    url = build_image_url(img)
                    if url and url not in image_urls:
                        image_urls.append(url)
                        print(f"[OK] imagem array -> {url}")
        
        print(f"\nTotal de URLs geradas: {len(image_urls)}")
        for i, url in enumerate(image_urls, 1):
            print(f"  {i}. {url}")
        
        # Verificar se nenhuma URL tem duplicação
        duplicacoes = [url for url in image_urls if "/media/media/" in url]
        if duplicacoes:
            print(f"\n[ERRO] {len(duplicacoes)} URL(s) com duplicacao de /media/:")
            for url in duplicacoes:
                print(f"     {url}")
            return False
        else:
            print(f"\n[OK] Nenhuma duplicacao de /media/ encontrada")
            return True
        
    except Exception as e:
        print(f"[ERRO] Erro ao testar integracao: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Executa todos os testes"""
    print("\n" + "=" * 80)
    print("TESTE COMPLETO DO SISTEMA DE IMAGENS")
    print("=" * 80 + "\n")
    
    results = []
    
    # Teste 1: Função build_image_url
    results.append(("build_image_url", test_build_image_url()))
    
    # Teste 2: Acesso ao servidor
    results.append(("Acesso ao Servidor", test_acesso_servidor()))
    
    # Teste 3: Integração com ProdutoJSON
    results.append(("Integração ProdutoJSON", test_integracao_produto_json()))
    
    # Resumo final
    print("\n" + "=" * 80)
    print("RESUMO FINAL")
    print("=" * 80)
    
    for name, passed in results:
        status = "[OK] PASSOU" if passed else "[ERRO] FALHOU"
        print(f"{status} - {name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} testes passaram")
    
    if total_passed == total_tests:
        print("\n[SUCESSO] Todos os testes passaram! O sistema esta funcionando corretamente.")
        return 0
    else:
        print(f"\n[AVISO] {total_tests - total_passed} teste(s) falharam. Revise os problemas acima.")
        return 1


if __name__ == "__main__":
    exit(main())

