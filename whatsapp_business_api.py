#!/usr/bin/env python
"""
Integração WhatsApp Business API - Python Nativo
Alternativa ao WPPConnect descontinuado
"""
import requests
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

class WhatsAppBusinessAPI:
    """Classe para integração com WhatsApp Business API"""
    
    def __init__(self, access_token: str, phone_number_id: str, verify_token: str = None):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.verify_token = verify_token
        self.base_url = f"https://graph.facebook.com/v18.0/{phone_number_id}"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
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
        
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()
    
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
        
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()
    
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
        
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()
    
    def get_business_profile(self) -> Dict:
        """Obter perfil do negócio"""
        url = f"{self.base_url}/whatsapp_business_profile"
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def update_business_profile(self, profile_data: Dict) -> Dict:
        """Atualizar perfil do negócio"""
        url = f"{self.base_url}/whatsapp_business_profile"
        response = requests.post(url, headers=self.headers, json=profile_data)
        return response.json()

class WhatsAppWebhookHandler:
    """Handler para webhooks do WhatsApp Business API"""
    
    def __init__(self, verify_token: str):
        self.verify_token = verify_token
    
    def verify_webhook(self, hub_mode: str, hub_challenge: str, hub_verify_token: str) -> Optional[str]:
        """Verificar webhook"""
        if hub_mode == "subscribe" and hub_verify_token == self.verify_token:
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
    """Gerenciador de grupos WhatsApp (simulado)"""
    
    def __init__(self, api: WhatsAppBusinessAPI):
        self.api = api
        self.groups = {}  # Simulação de grupos
    
    def create_group(self, name: str, participants: List[str]) -> Dict:
        """Criar grupo (simulado - WhatsApp Business API não suporta criação de grupos)"""
        group_id = f"group_{len(self.groups) + 1}@{name.lower().replace(' ', '_')}"
        
        self.groups[group_id] = {
            "id": group_id,
            "name": name,
            "participants": participants,
            "created_at": datetime.now().isoformat()
        }
        
        return self.groups[group_id]
    
    def get_groups(self) -> List[Dict]:
        """Obter lista de grupos"""
        return list(self.groups.values())
    
    def send_to_group(self, group_id: str, message: str) -> Dict:
        """Enviar mensagem para grupo (simulado)"""
        if group_id in self.groups:
            # Em um cenário real, você enviaria para cada participante
            group = self.groups[group_id]
            results = []
            
            for participant in group["participants"]:
                result = self.api.send_text_message(participant, f"[{group['name']}] {message}")
                results.append(result)
            
            return {"success": True, "results": results}
        else:
            return {"success": False, "error": "Grupo não encontrado"}

# Exemplo de uso
def main():
    """Exemplo de uso da API"""
    
    # Configuração (substitua pelos seus valores)
    ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "seu_token_aqui")
    PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "seu_phone_id")
    VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "seu_verify_token")
    
    # Inicializar API
    api = WhatsAppBusinessAPI(ACCESS_TOKEN, PHONE_NUMBER_ID, VERIFY_TOKEN)
    
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
    result = group_manager.send_to_group(group["id"], "Bem-vindos ao grupo de vendas!")
    print("✅ Mensagem enviada para grupo:", result)

if __name__ == "__main__":
    main()
