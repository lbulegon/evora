"""
Teste da função build_image_url
"""
def build_image_url(img_path, openmind_url="http://69.169.102.84:5000/api/v1"):
    """Teste da função build_image_url"""
    media_url = "/media/"
    
    if not img_path:
        return None
    if isinstance(img_path, str):
        # Se já é URL completa (HTTP/HTTPS), retornar como está
        if img_path.startswith('http://') or img_path.startswith('https://'):
            return img_path
        
        # Se o path não começa com /, é provável que seja uma imagem do SinapUm
        if not img_path.startswith('/'):
            # É uma imagem do SinapUm - construir URL completa
            if openmind_url:
                # Remover /api/v1 se existir para obter base URL do servidor
                sinapum_base = openmind_url.replace('/api/v1', '').rstrip('/')
                # Limpar o path (remover / no início se houver)
                clean_path = img_path.lstrip('/')
                
                # Se o path já começa com "media/", não adicionar /media/ novamente
                if clean_path.startswith('media/'):
                    return f"{sinapum_base}/{clean_path}"
                else:
                    # Caso contrário, adicionar /media/ antes do path
                    return f"{sinapum_base}/media/{clean_path}"
            else:
                # Fallback: tentar construir com IP padrão
                clean_path = img_path.lstrip('/')
                if clean_path.startswith('media/'):
                    return f"http://69.169.102.84:5000/{clean_path}"
                else:
                    return f"http://69.169.102.84:5000/media/{clean_path}"
        
        # Se começa com /, pode ser:
        # - Path local (tentar MEDIA_URL local primeiro)
        # - Path do SinapUm que começa com /media/
        if img_path.startswith('/media/'):
            # Pode ser do SinapUm ou local
            # Se não começar com http, assumir que é local
            if openmind_url and ('produtos/temp' in img_path or 'photo_' in img_path):
                # Parece ser do SinapUm (tem padrões típicos)
                sinapum_base = openmind_url.replace('/api/v1', '').rstrip('/')
                return f"{sinapum_base}{img_path}"
            # Caso contrário, retornar como path local
            return img_path
        
        # Path absoluto local (sem /media)
        if img_path.startswith('/'):
            return img_path
        
        # Caso contrário, adicionar MEDIA_URL local
        if img_path.startswith(media_url.lstrip('/')):
            return f"/{img_path}"
        return f"{media_url}{img_path}".replace('//', '/')
    return None

# Testes
test_cases = [
    ("media/uploads/7cc806f7-e22d-45ba-8aab-6513f1715c09.jpg", "Path com media/"),
    ("photo_0.jpg", "Path simples"),
    ("produtos/temp/15/20251202_043814_temp.jpg", "Path produtos/temp"),
    ("/media/uploads/test.jpg", "Path absoluto com /media/"),
    ("http://69.169.102.84:5000/media/uploads/test.jpg", "URL completa"),
]

print("Testando build_image_url:")
print("=" * 80)
for path, desc in test_cases:
    result = build_image_url(path)
    print(f"\n[{desc}]")
    print(f"  Input:  {path}")
    print(f"  Output: {result}")
    if result:
        expected = "http://69.169.102.84:5000/media/uploads/7cc806f7-e22d-45ba-8aab-6513f1715c09.jpg"
        if "media/media" in result:
            print(f"  [ERRO] URL tem 'media/media' duplicado!")
        else:
            print(f"  [OK]")


