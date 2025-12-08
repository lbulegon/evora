# 🔧 Modificação Necessária no SinapUm - Upload de Imagens

## 📋 Contexto

O projeto Évora precisa que as imagens sejam salvas no servidor SinapUm, não no Railway. Isso porque:
- O Railway tem armazenamento volátil (arquivos são perdidos ao reiniciar)
- O SinapUm tem armazenamento persistente
- Centraliza o gerenciamento de imagens em um único servidor

---

## ✅ Modificações Aplicadas no Évora

### 1. Removido Salvamento Local
- ✅ Código modificado para **NÃO salvar** imagens localmente no Railway
- ✅ Imagens são processadas em memória e enviadas diretamente para o SinapUm
- ✅ Código preparado para usar URLs retornadas pelo SinapUm

### 2. Código Atualizado
**Arquivos modificados:**
- `app_marketplace/product_photo_views.py` - Não salva mais localmente
- `app_marketplace/services.py` - Extrai URL retornada pelo SinapUm

---

## 🔧 Modificação Necessária no SinapUm

### Endpoint: `/api/v1/analyze-product-image`

**Arquivo:** `openmind-ai-server/app/api/v1/endpoints/analyze.py`

**Modificação necessária:**

1. **Salvar a imagem no servidor SinapUm** após receber o upload
2. **Retornar a URL da imagem salva** na resposta JSON

### Código Sugerido:

```python
import os
import uuid
from pathlib import Path
from fastapi import UploadFile
from django.conf import settings  # Se usar Django settings

@router.post("/analyze-product-image")
async def analyze_product_image_endpoint(
    image: UploadFile = File(...),
    _: bool = Depends(verify_api_key)
):
    # ... código existente de validação ...
    
    # Ler dados da imagem
    image_data = await image.read()
    
    # ========== NOVO: Salvar imagem no servidor ==========
    # Criar diretório de uploads se não existir
    upload_dir = Path(settings.MEDIA_ROOT) / 'uploads'
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Gerar nome único para a imagem
    file_extension = image.filename.split('.')[-1].lower() if image.filename else 'jpg'
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = upload_dir / unique_filename
    
    # Salvar imagem
    with open(file_path, 'wb') as f:
        f.write(image_data)
    
    # Construir URL da imagem salva
    image_url = f"{settings.MEDIA_URL}uploads/{unique_filename}"
    # Se MEDIA_URL for relativo, construir URL absoluta
    if not image_url.startswith('http'):
        # Usar URL base do SinapUm (ex: http://69.169.102.84:8000)
        base_url = getattr(settings, 'BASE_URL', 'http://69.169.102.84:8000')
        image_url = f"{base_url}{image_url}"
    
    # ========== FIM NOVO ==========
    
    # Analisar imagem (código existente)
    product_data = analyze_product_image(image_data, image.filename or 'image.jpg')
    
    # Calcular tempo de processamento
    processing_time_ms = int((time.time() - start_time) * 1000)
    
    logger.info(f"Análise concluída em {processing_time_ms}ms, imagem salva: {image_url}")
    
    return AnalyzeResponse(
        success=True,
        data=product_data,
        confidence=0.95,
        processing_time_ms=processing_time_ms,
        image_url=image_url  # NOVO: Retornar URL da imagem salva
    )
```

### Atualizar Schema de Resposta:

**Arquivo:** `openmind-ai-server/app/models/schemas.py`

```python
class AnalyzeResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    processing_time_ms: Optional[int] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    image_url: Optional[str] = None  # NOVO: URL da imagem salva
```

---

## 📋 Checklist de Implementação

### No SinapUm:

- [ ] Modificar endpoint `/api/v1/analyze-product-image` para salvar imagem
- [ ] Retornar `image_url` na resposta JSON
- [ ] Atualizar schema `AnalyzeResponse` para incluir `image_url`
- [ ] Configurar `MEDIA_ROOT` e `MEDIA_URL` no settings do SinapUm
- [ ] Configurar rota para servir arquivos de mídia (se necessário)
- [ ] Testar salvamento e retorno de URL

### No Évora (já feito):

- [x] Removido salvamento local de imagens
- [x] Código preparado para usar URL do SinapUm
- [x] Extração de `image_url` da resposta do SinapUm
- [x] Uso da URL no JSON do produto

---

## 🔄 Fluxo Atualizado

### Antes (Évora salvava localmente):
1. Upload de imagem → Évora salva em `media/uploads/`
2. Évora envia para SinapUm para análise
3. Évora usa caminho local no JSON

### Depois (SinapUm salva):
1. Upload de imagem → Évora processa em memória
2. Évora envia para SinapUm para análise
3. **SinapUm salva em `media/uploads/` e retorna URL**
4. Évora usa URL do SinapUm no JSON

---

## ✅ Benefícios

1. **Armazenamento Persistente** - Imagens não são perdidas ao reiniciar
2. **Centralização** - Todas as imagens em um único servidor
3. **Escalabilidade** - Fácil migrar para S3 ou similar no futuro
4. **Consistência** - Mesma fonte de verdade para imagens

---

## 📝 Notas

- O SinapUm deve ter `MEDIA_ROOT` e `MEDIA_URL` configurados
- A URL retornada deve ser acessível publicamente
- Considerar usar CDN ou S3 para produção em escala
- Implementar limpeza de imagens antigas (cron job)

---

**Status:** ⏳ Aguardando implementação no SinapUm

