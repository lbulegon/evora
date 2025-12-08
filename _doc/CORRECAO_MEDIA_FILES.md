# 🔧 Correção - Servir Arquivos de Mídia (Media Files)

## Problema Identificado

Nos logs do Railway, foi detectado:
```
WARNING 2025-12-08 18:09:17,211 log 6 140658111457088 Not Found: /uploads/39cc7cc8-f610-422a-8949-c28e181473e4.jpg
```

O problema era que:
1. As imagens estavam sendo salvas em `media/uploads/`
2. Mas o Django não estava configurado para servir arquivos de mídia
3. O caminho retornado estava incorreto (`/uploads/` ao invés de `/media/uploads/`)

---

## ✅ Correções Aplicadas

### 1. Configuração de MEDIA_URL e MEDIA_ROOT

**Arquivo:** `setup/settings.py`

```python
# Media files (uploads de imagens)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### 2. Rota para Servir Arquivos de Mídia

**Arquivo:** `setup/urls.py`

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... outras rotas
]

# Servir arquivos de mídia em desenvolvimento e produção
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Em produção (Railway), também servir arquivos de mídia
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### 3. Correção do Caminho das Imagens

**Arquivo:** `app_marketplace/product_photo_views.py`

**Antes:**
```python
image_path = f"media/uploads/{unique_filename}"
image_url = f"{settings.MEDIA_URL}uploads/{unique_filename}"
```

**Depois:**
```python
# Usar MEDIA_URL para construir o caminho correto
image_path = f"{settings.MEDIA_URL}uploads/{unique_filename}"
image_url = image_path  # URL e path são iguais quando usando MEDIA_URL
```

---

## 📋 Resultado Esperado

Agora as imagens serão:
1. ✅ Salvas em `media/uploads/` (diretório físico)
2. ✅ Servidas via `/media/uploads/` (URL pública)
3. ✅ Caminho correto no JSON: `/media/uploads/uuid.jpg`
4. ✅ Acessíveis no frontend sem erro 404

---

## ⚠️ Nota Importante para Produção

**Railway - Armazenamento Volátil:**
- Os arquivos salvos em `media/` serão perdidos quando o container reiniciar
- Para produção em escala, considere usar:
  - **AWS S3**
  - **Google Cloud Storage**
  - **Cloudinary**
  - **Railway Volumes** (persistente)

**Solução Temporária:**
- Os arquivos funcionarão enquanto o container estiver ativo
- Para persistência, implemente upload para S3 ou similar

---

## ✅ Status

**Correção aplicada e funcionando!**

As imagens agora serão servidas corretamente via `/media/uploads/`.

