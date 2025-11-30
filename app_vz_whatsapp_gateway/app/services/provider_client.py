"""
WhatsApp Provider Client
========================

Cliente para comunicação com provedores de WhatsApp (Z-API, Evolution API, UltraMsg, etc.)

Este módulo abstrai a comunicação com diferentes provedores via HTTP/REST.
"""

import httpx
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class WhatsAppProviderClient:
    """
    Cliente para comunicação com provedores de WhatsApp
    
    Suporta múltiplos provedores através de configuração de URL base.
    """
    
    def __init__(self, base_url: str, api_key: str):
        """
        Inicializar cliente do provedor
        
        Args:
            base_url: URL base da API do provedor (ex: https://api.z-api.io)
            api_key: Chave de API do provedor
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = 30.0
        
        if not self.base_url or not self.api_key:
            logger.warning("Provider não configurado completamente")
    
    async def send_text(self, phone: str, message: str) -> Dict:
        """
        Enviar mensagem de texto via WhatsApp
        
        Args:
            phone: Número do telefone (formato: 5511999999999)
            message: Texto da mensagem
            
        Returns:
            Dict com 'success' (bool) e 'error' (str) se houver
        """
        if not self.base_url or not self.api_key:
            return {
                "success": False,
                "error": "Provider não configurado"
            }
        
        # Normalizar número de telefone
        phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if not phone.startswith("+"):
            phone = f"+{phone}"
        
        # Tentar diferentes formatos de API (compatibilidade com múltiplos provedores)
        endpoints_to_try = [
            f"{self.base_url}/send-text",  # Z-API
            f"{self.base_url}/messages/send",  # Evolution API
            f"{self.base_url}/send-message",  # UltraMsg
        ]
        
        payloads_to_try = [
            # Formato Z-API
            {
                "phone": phone,
                "message": message
            },
            # Formato Evolution API
            {
                "number": phone,
                "text": message
            },
            # Formato UltraMsg
            {
                "to": phone,
                "body": message
            }
        ]
        
        headers = {
            "Content-Type": "application/json",
            "apikey": self.api_key,  # Z-API
            "Authorization": f"Bearer {self.api_key}",  # Evolution API
            "api-key": self.api_key,  # UltraMsg
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Tentar cada combinação de endpoint/payload
            for endpoint in endpoints_to_try:
                for payload in payloads_to_try:
                    try:
                        # Tentar com diferentes headers
                        for header_key, header_value in headers.items():
                            try:
                                response = await client.post(
                                    endpoint,
                                    json=payload,
                                    headers={header_key: header_value}
                                )
                                
                                if response.status_code in [200, 201]:
                                    logger.info(f"Mensagem enviada via {endpoint}")
                                    return {
                                        "success": True,
                                        "provider_response": response.json()
                                    }
                            except Exception as e:
                                continue
                    except Exception as e:
                        logger.debug(f"Tentativa falhou para {endpoint}: {str(e)}")
                        continue
        
        # Se nenhuma tentativa funcionou
        logger.error(f"Falha ao enviar mensagem para {phone}")
        return {
            "success": False,
            "error": "Falha ao comunicar com provedor de WhatsApp"
        }
    
    async def send_image(self, phone: str, image_url: str, caption: str = "") -> Dict:
        """
        Enviar imagem via WhatsApp (implementação futura)
        
        Args:
            phone: Número do telefone
            image_url: URL da imagem
            caption: Legenda da imagem
            
        Returns:
            Dict com resultado
        """
        # TODO: Implementar quando necessário
        return {
            "success": False,
            "error": "Funcionalidade ainda não implementada"
        }
    
    async def send_document(self, phone: str, document_url: str, filename: str = "") -> Dict:
        """
        Enviar documento via WhatsApp (implementação futura)
        
        Args:
            phone: Número do telefone
            document_url: URL do documento
            filename: Nome do arquivo
            
        Returns:
            Dict com resultado
        """
        # TODO: Implementar quando necessário
        return {
            "success": False,
            "error": "Funcionalidade ainda não implementada"
        }
