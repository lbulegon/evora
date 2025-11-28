"""
WhatsApp Provider Client
Cliente para comunicação com provedores de WhatsApp (Z-API, Evolution API, UltraMsg, etc.)
"""

import os
import logging
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)


class WhatsAppProviderClient:
    """
    Cliente para comunicação com provedores de WhatsApp via HTTP/REST
    
    Suporta múltiplos provedores:
    - Z-API
    - Evolution API
    - UltraMsg
    - Outros compatíveis com REST API
    """
    
    def __init__(self, base_url: str, api_key: str):
        """
        Inicializa o cliente do provedor
        
        Args:
            base_url: URL base do provedor (ex: https://api.z-api.io)
            api_key: Chave de API do provedor
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.provider_type = self._detect_provider_type()
        
        logger.info(f"🔌 Cliente WhatsApp inicializado: {self.provider_type}")
        logger.info(f"📡 Base URL: {self.base_url}")
    
    def _detect_provider_type(self) -> str:
        """Detecta o tipo de provedor baseado na URL"""
        url_lower = self.base_url.lower()
        
        if "z-api" in url_lower:
            return "z-api"
        elif "evolution" in url_lower:
            return "evolution"
        elif "ultramsg" in url_lower:
            return "ultramsg"
        else:
            return "generic"
    
    async def send_text(
        self,
        phone: str,
        message: str,
        instance_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envia mensagem de texto via WhatsApp
        
        Args:
            phone: Número de telefone (formato: 5511999999999)
            message: Texto da mensagem
            instance_id: ID da instância (opcional, depende do provedor)
        
        Returns:
            Dict com resultado do envio
        """
        if not self.base_url or not self.api_key:
            raise ValueError("Provider não configurado (PROVIDER_BASE_URL e PROVIDER_API_KEY)")
        
        # Normalizar número de telefone
        phone = self._normalize_phone(phone)
        
        # Preparar payload baseado no tipo de provedor
        if self.provider_type == "z-api":
            return await self._send_zapi(phone, message, instance_id)
        elif self.provider_type == "evolution":
            return await self._send_evolution(phone, message, instance_id)
        elif self.provider_type == "ultramsg":
            return await self._send_ultramsg(phone, message, instance_id)
        else:
            return await self._send_generic(phone, message, instance_id)
    
    async def _send_zapi(
        self,
        phone: str,
        message: str,
        instance_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Envia mensagem via Z-API"""
        instance = instance_id or os.getenv("ZAPI_INSTANCE_ID", "default")
        url = f"{self.base_url}/instances/{instance}/token/{self.api_key}/send-text"
        
        payload = {
            "phone": phone,
            "message": message
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def _send_evolution(
        self,
        phone: str,
        message: str,
        instance_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Envia mensagem via Evolution API"""
        instance = instance_id or os.getenv("EVOLUTION_INSTANCE", "default")
        url = f"{self.base_url}/message/sendText/{instance}"
        
        payload = {
            "number": phone,
            "text": message
        }
        
        headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def _send_ultramsg(
        self,
        phone: str,
        message: str,
        instance_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Envia mensagem via UltraMsg"""
        url = f"{self.base_url}/api/send"
        
        payload = {
            "token": self.api_key,
            "to": phone,
            "body": message
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def _send_generic(
        self,
        phone: str,
        message: str,
        instance_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Método genérico para provedores não específicos
        Tenta endpoint padrão: POST /send-text ou /send
        """
        # Tentar endpoint /send-text primeiro
        endpoints = [
            f"{self.base_url}/send-text",
            f"{self.base_url}/send",
            f"{self.base_url}/message/send"
        ]
        
        payload = {
            "phone": phone,
            "message": message,
            "text": message,  # Alguns provedores usam "text"
            "to": phone,  # Alguns provedores usam "to"
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for endpoint in endpoints:
                try:
                    response = await client.post(
                        endpoint,
                        json=payload,
                        headers=headers
                    )
                    response.raise_for_status()
                    return response.json()
                except httpx.HTTPError:
                    continue
            
            raise Exception("Não foi possível enviar mensagem - nenhum endpoint funcionou")
    
    def _normalize_phone(self, phone: str) -> str:
        """
        Normaliza número de telefone para formato padrão
        
        Remove caracteres especiais e garante formato internacional
        """
        # Remover caracteres não numéricos
        phone = ''.join(filter(str.isdigit, phone))
        
        # Se não começar com código do país, assumir Brasil (55)
        if not phone.startswith('55') and len(phone) <= 11:
            phone = '55' + phone
        
        return phone
    
    async def send_image(
        self,
        phone: str,
        image_url: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envia imagem via WhatsApp (implementação futura)
        
        Args:
            phone: Número de telefone
            image_url: URL da imagem
            caption: Legenda da imagem (opcional)
        """
        # TODO: Implementar envio de imagem
        raise NotImplementedError("Envio de imagem será implementado em breve")
    
    async def send_document(
        self,
        phone: str,
        document_url: str,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envia documento via WhatsApp (implementação futura)
        
        Args:
            phone: Número de telefone
            document_url: URL do documento
            filename: Nome do arquivo (opcional)
        """
        # TODO: Implementar envio de documento
        raise NotImplementedError("Envio de documento será implementado em breve")

