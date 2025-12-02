"""
Endpoint de análise de imagens de produtos
"""
import time
from fastapi import APIRouter, File, UploadFile, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from app.core.security import verify_api_key
from app.core.image_analyzer import analyze_product_image
from app.core.config import settings
from app.models.schemas import AnalyzeResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/analyze-product-image",
    response_model=AnalyzeResponse,
    summary="Analisa imagem de produto",
    description="Extrai informações de um produto a partir de uma imagem no formato JSON ÉVORA"
)
async def analyze_product_image_endpoint(
    image: UploadFile = File(..., description="Imagem do produto para análise"),
    _: bool = Depends(verify_api_key)
):
    """
    Analisa uma imagem de produto e retorna dados no formato JSON ÉVORA
    
    - **image**: Arquivo de imagem (JPEG, PNG, WebP)
    - **Authorization**: Bearer token (API key)
    
    Retorna dados extraídos do produto no formato JSON ÉVORA.
    """
    start_time = time.time()
    
    try:
        # Validar tipo de arquivo
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Arquivo deve ser uma imagem",
                headers={"error_code": "INVALID_IMAGE"}
            )
        
        # Validar formato
        file_extension = image.filename.split('.')[-1].lower() if image.filename else ''
        if file_extension not in settings.allowed_formats_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Formato de imagem não suportado. Formatos permitidos: {settings.ALLOWED_IMAGE_FORMATS}",
                headers={"error_code": "UNSUPPORTED_FORMAT"}
            )
        
        # Ler dados da imagem
        image_data = await image.read()
        
        # Validar tamanho
        if len(image_data) > settings.max_image_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Imagem muito grande. Tamanho máximo: {settings.MAX_IMAGE_SIZE_MB}MB",
                headers={"error_code": "IMAGE_TOO_LARGE"}
            )
        
        # Analisar imagem
        logger.info(f"Analisando imagem: {image.filename}, tamanho: {len(image_data)} bytes")
        
        product_data = analyze_product_image(image_data, image.filename or 'image.jpg')
        
        # Calcular tempo de processamento
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(f"Análise concluída em {processing_time_ms}ms")
        
        return AnalyzeResponse(
            success=True,
            data=product_data,
            confidence=0.95,  # TODO: Calcular confiança real baseada no modelo
            processing_time_ms=processing_time_ms
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar imagem: {str(e)}", exc_info=True)
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return AnalyzeResponse(
            success=False,
            error=f"Erro ao processar imagem: {str(e)}",
            error_code="PROCESSING_ERROR",
            processing_time_ms=processing_time_ms
        )
