"""
Teste de acesso às imagens no servidor SinapUm
"""
import requests
from urllib.parse import urljoin

# Configuração
SINAPUM_IP = "69.169.102.84"
SINAPUM_PORT = "5000"
SINAPUM_BASE = f"http://{SINAPUM_IP}:{SINAPUM_PORT}"

# URL da imagem que está sendo salva
imagem_path = "media/uploads/7cc806f7-e22d-45ba-8aab-6513f1715c09.jpg"
imagem_url = f"{SINAPUM_BASE}/{imagem_path}"

print("Testando acesso as imagens no servidor SinapUm")
print(f"   IP: {SINAPUM_IP}")
print(f"   Porta: {SINAPUM_PORT}")
print(f"   Base URL: {SINAPUM_BASE}")
print()

# 1. Testar endpoint raiz
print("1. Testando endpoint raiz (/)...")
try:
    response = requests.get(SINAPUM_BASE, timeout=5)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   [OK] Servidor esta respondendo")
    else:
        print(f"   [AVISO] Servidor respondeu mas com status {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"   [ERRO] Erro ao conectar: {e}")
print()

# 2. Testar endpoint /health
print("2. Testando endpoint /health...")
try:
    health_url = f"{SINAPUM_BASE}/health"
    response = requests.get(health_url, timeout=5)
    print(f"   URL: {health_url}")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   [OK] Health check OK")
        print(f"   Resposta: {response.text[:100]}")
    else:
        print(f"   [AVISO] Health check retornou {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"   [ERRO] Erro: {e}")
print()

# 3. Testar diretório /media/
print("3. Testando diretorio /media/...")
try:
    media_url = f"{SINAPUM_BASE}/media/"
    response = requests.get(media_url, timeout=5)
    print(f"   URL: {media_url}")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   [OK] Diretorio /media/ esta acessivel")
    elif response.status_code == 404:
        print(f"   [AVISO] Diretorio /media/ nao encontrado (pode ser normal se nao tiver listagem)")
    else:
        print(f"   [AVISO] Status {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"   [ERRO] Erro: {e}")
print()

# 4. Testar imagem específica
print("4. Testando imagem especifica...")
try:
    print(f"   URL: {imagem_url}")
    response = requests.get(imagem_url, timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   [OK] Imagem acessivel!")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"   Tamanho: {len(response.content)} bytes")
        print(f"   [OK] URL funcionando corretamente")
    elif response.status_code == 404:
        print(f"   [ERRO] Imagem nao encontrada (404)")
        print(f"   Verifique se o arquivo existe no servidor")
    else:
        print(f"   [AVISO] Status {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
except requests.exceptions.Timeout:
    print(f"   [ERRO] Timeout - servidor nao respondeu em 10 segundos")
except requests.exceptions.ConnectionError:
    print(f"   [ERRO] Erro de conexao - nao foi possivel conectar ao servidor")
    print(f"   Verifique se o servidor esta online e acessivel")
except requests.exceptions.RequestException as e:
    print(f"   [ERRO] Erro: {e}")
print()

# 5. Testar endpoint de análise (para confirmar que a API está funcionando)
print("5. Testando endpoint da API /api/v1/...")
try:
    api_url = f"{SINAPUM_BASE}/api/v1/"
    response = requests.get(api_url, timeout=5)
    print(f"   URL: {api_url}")
    print(f"   Status: {response.status_code}")
    if response.status_code in [200, 404, 405]:
        print(f"   [OK] API endpoint esta respondendo (status {response.status_code})")
    else:
        print(f"   [AVISO] Status {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"   [ERRO] Erro: {e}")
print()

print("=" * 60)
print("RESUMO:")
print(f"   Base URL: {SINAPUM_BASE}")
print(f"   Imagem testada: {imagem_path}")
print(f"   URL completa: {imagem_url}")
print()
print("NOTA: Se a imagem retornou 404, ela pode nao existir ainda.")
print("      Isso e normal se voce acabou de fazer upload e ainda nao salvou o produto.")

