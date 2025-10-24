#!/usr/bin/env python
"""
WhatsApp Cloud API - Compatível com Python e Flutter
Alternativa ao WPPConnect descontinuado
"""
import os
import requests
import json
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class WhatsAppMessage:
    to: str
    message: str
    message_type: str = "text"
    media_url: Optional[str] = None
    caption: Optional[str] = None

@dataclass
class WhatsAppGroup:
    id: str
    name: str
    participants: int
    created_at: str

class WhatsAppCloudAPI:
    """WhatsApp Cloud API - Funciona com Python e Flutter"""
    
    def __init__(self, access_token: str = None, phone_number_id: str = None):
        self.access_token = access_token or os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.phone_number_id = phone_number_id or os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.base_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def send_text_message(self, to: str, message: str) -> Dict:
        """Enviar mensagem de texto"""
        url = f"{self.base_url}/messages"
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def send_media_message(self, to: str, media_type: str, media_url: str, caption: str = None) -> Dict:
        """Enviar mídia (imagem, vídeo, documento)"""
        url = f"{self.base_url}/messages"
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": media_type,
            media_type: {
                "link": media_url,
                "caption": caption
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def send_template_message(self, to: str, template_name: str, language_code: str = "pt_BR", components: List = None) -> Dict:
        """Enviar mensagem template"""
        url = f"{self.base_url}/messages"
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": components or []
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def get_business_profile(self) -> Dict:
        """Obter perfil do negócio"""
        url = f"{self.base_url}/whatsapp_business_profile"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def verify_webhook(self, hub_mode: str, hub_challenge: str, hub_verify_token: str) -> Optional[str]:
        """Verificar webhook"""
        verify_token = os.getenv('WHATSAPP_VERIFY_TOKEN')
        if hub_mode == "subscribe" and hub_verify_token == verify_token:
            return hub_challenge
        return None
    
    def handle_webhook(self, webhook_data: Dict) -> Dict:
        """Processar webhook recebido"""
        try:
            entry = webhook_data.get("entry", [])
            for item in entry:
                changes = item.get("changes", [])
                for change in changes:
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    
                    for message in messages:
                        self.process_message(message)
            
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def process_message(self, message: Dict):
        """Processar mensagem recebida"""
        from_number = message.get("from")
        message_type = message.get("type")
        message_id = message.get("id")
        timestamp = message.get("timestamp")
        
        print(f"📨 Nova mensagem de {from_number}: {message_type}")
        
        # Aqui você pode implementar:
        # - Detecção de comandos
        # - Processamento de pedidos
        # - Respostas automáticas
        # - Integração com ÉVORA

class WhatsAppGroupManager:
    """Gerenciador de grupos (simulado - Cloud API não suporta grupos diretamente)"""
    
    def __init__(self, api: WhatsAppCloudAPI):
        self.api = api
        self.groups = {}  # Simulação de grupos
    
    def create_group(self, name: str, participants: List[str]) -> WhatsAppGroup:
        """Criar grupo (simulado)"""
        group_id = f"group_{len(self.groups) + 1}@{name.lower().replace(' ', '_')}"
        
        group = WhatsAppGroup(
            id=group_id,
            name=name,
            participants=len(participants),
            created_at=datetime.now().isoformat()
        )
        
        self.groups[group_id] = group
        return group
    
    def get_groups(self) -> List[WhatsAppGroup]:
        """Obter lista de grupos"""
        return list(self.groups.values())
    
    def send_to_group(self, group_id: str, message: str) -> Dict:
        """Enviar mensagem para grupo (simulado)"""
        if group_id not in self.groups:
            return {"success": False, "error": "Grupo não encontrado"}
        
        group = self.groups[group_id]
        results = []
        
        # Em um cenário real, você enviaria para cada participante
        # Por enquanto, apenas simular
        for participant in ["+5511999999999", "+5511888888888"]:  # Participantes simulados
            result = self.api.send_text_message(participant, f"[{group.name}] {message}")
            results.append(result)
        
        return {"success": True, "results": results}

# Exemplo de uso
def main():
    """Exemplo de uso da API"""
    
    # Configuração
    ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "seu_token_aqui")
    PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "seu_phone_id")
    
    # Inicializar API
    api = WhatsAppCloudAPI(ACCESS_TOKEN, PHONE_NUMBER_ID)
    
    # Exemplo: Enviar mensagem
    try:
        result = api.send_text_message("+5511999999999", "Olá! Esta é uma mensagem do ÉVORA Connect.")
        print("✅ Mensagem enviada:", result)
    except Exception as e:
        print("❌ Erro ao enviar mensagem:", e)
    
    # Exemplo: Gerenciar grupos
    group_manager = WhatsAppGroupManager(api)
    
    # Criar grupo
    group = group_manager.create_group("Grupo de Vendas", ["+5511999999999", "+5511888888888"])
    print("✅ Grupo criado:", group)
    
    # Enviar para grupo
    result = group_manager.send_to_group(group.id, "Bem-vindos ao grupo de vendas!")
    print("✅ Mensagem enviada para grupo:", result)

if __name__ == "__main__":
    main()
