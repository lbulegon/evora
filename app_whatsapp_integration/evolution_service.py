"""
Evolution API Service
=====================

Serviço para comunicação com Evolution API (WhatsApp).
Todas as operações são centralizadas no Django e armazenadas no PostgreSQL.
"""

import requests
import logging
from typing import Dict, Optional, List
from django.conf import settings
from django.utils import timezone
from .models import EvolutionInstance, EvolutionMessage, WhatsAppContact

logger = logging.getLogger(__name__)


class EvolutionAPIService:
    """
    Serviço para comunicação com Evolution API
    """
    
    def __init__(self):
        """Inicializar serviço Evolution API"""
        self.base_url = getattr(settings, 'EVOLUTION_API_URL', 'http://69.169.102.84:8004')
        self.api_key = getattr(settings, 'EVOLUTION_API_KEY', 'GKvy6psn-8HHpBQ4HAHKFOXnwjHR-oSzeGZzCaws0xg')
        self.instance_name = getattr(settings, 'EVOLUTION_INSTANCE_NAME', 'default')
        self.timeout = 30
        
        if not self.base_url or not self.api_key:
            logger.warning("Evolution API não configurada completamente")
    
    def _get_headers(self) -> Dict[str, str]:
        """Retorna headers para requisições"""
        return {
            "Content-Type": "application/json",
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def _normalize_phone(self, phone: str) -> str:
        """Normaliza número de telefone para formato Evolution API"""
        # Remove caracteres especiais
        phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        
        # Garante que começa com +
        if not phone.startswith("+"):
            # Se começa com 55 (Brasil), adiciona +
            if phone.startswith("55"):
                phone = f"+{phone}"
            else:
                # Assumir que é número brasileiro sem código do país
                phone = f"+55{phone}"
        
        return phone
    
    def get_instance_status(self, instance_name: Optional[str] = None) -> Dict:
        """
        Verifica status da instância e sincroniza com banco Django
        
        Returns:
            Dict com status da instância
        """
        try:
            instance_name = instance_name or self.instance_name
            
            # Buscar ou criar instância no banco
            instance, created = EvolutionInstance.objects.get_or_create(
                name=instance_name,
                defaults={'status': EvolutionInstance.InstanceStatus.UNKNOWN}
            )
            
            # Buscar status da Evolution API
            url = f"{self.base_url}/instance/fetchInstances"
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # A Evolution API pode retornar uma lista diretamente ou um dict com 'instance'
                if isinstance(data, list):
                    instances = data
                elif isinstance(data, dict):
                    instances = data.get('instance', [])
                else:
                    instances = []
                
                # Procurar instância específica
                evolution_instance_data = None
                for inst in instances:
                    # Verificar se inst é um dict antes de usar .get()
                    if isinstance(inst, dict) and inst.get('instanceName') == instance_name:
                        evolution_instance_data = inst
                        break
                
                if evolution_instance_data:
                    # Atualizar instância no banco
                    status_map = {
                        'open': EvolutionInstance.InstanceStatus.OPEN,
                        'close': EvolutionInstance.InstanceStatus.CLOSE,
                        'connecting': EvolutionInstance.InstanceStatus.CONNECTING,
                        'unpaired': EvolutionInstance.InstanceStatus.UNPAIRED,
                    }
                    
                    evolution_status = evolution_instance_data.get('status', '').lower()
                    instance.status = status_map.get(evolution_status, EvolutionInstance.InstanceStatus.UNKNOWN)
                    instance.phone_number = evolution_instance_data.get('phoneNumber')
                    instance.phone_name = evolution_instance_data.get('phoneName')
                    instance.last_sync = timezone.now()
                    instance.metadata = evolution_instance_data
                    instance.save()
                    
                    return {
                        'success': True,
                        'data': {
                            'status': evolution_status,
                            'phone_number': instance.phone_number,
                            'phone_name': instance.phone_name,
                        },
                        'status': evolution_status,
                        'instance': {
                            'id': instance.id,
                            'name': instance.name,
                            'status': instance.status,
                            'phone_number': instance.phone_number,
                            'phone_name': instance.phone_name,
                            'is_active': instance.is_active,
                            'is_default': instance.is_default,
                        }
                    }
                else:
                    # Instância não existe na Evolution API
                    instance.status = EvolutionInstance.InstanceStatus.UNKNOWN
                    instance.save()
                    
                    return {
                        'success': False,
                        'error': f'Instância {instance_name} não encontrada na Evolution API'
                    }
            else:
                return {
                    'success': False,
                    'error': f'Erro ao buscar instância: {response.status_code}'
                }
        except Exception as e:
            logger.error(f"Erro ao verificar status da instância: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_text_message(self, phone: str, message: str, instance_name: Optional[str] = None) -> Dict:
        """
        Envia mensagem de texto
        
        Args:
            phone: Número do telefone (formato: +5511999999999)
            message: Texto da mensagem
            
        Returns:
            Dict com resultado
        """
        try:
            instance_name = instance_name or self.instance_name
            phone = self._normalize_phone(phone)
            
            # Buscar instância no banco
            try:
                instance = EvolutionInstance.objects.get(name=instance_name)
            except EvolutionInstance.DoesNotExist:
                return {
                    'success': False,
                    'error': f'Instância {instance_name} não encontrada no banco'
                }
            
            # Buscar ou criar contato
            contact, _ = WhatsAppContact.objects.get_or_create(
                phone=phone,
                defaults={'name': ''}
            )
            
            # Enviar mensagem via Evolution API
            url = f"{self.base_url}/message/sendText/{instance_name}"
            
            payload = {
                "number": phone,
                "text": message
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            if response.status_code in [200, 201]:
                response_data = response.json()
                evolution_message_id = response_data.get('key', {}).get('id', f"msg_{timezone.now().timestamp()}")
                
                # Salvar mensagem no banco Django
                evolution_message = EvolutionMessage.objects.create(
                    instance=instance,
                    contact=contact,
                    evolution_message_id=evolution_message_id,
                    phone=phone,
                    direction=EvolutionMessage.MessageDirection.OUTBOUND,
                    message_type=EvolutionMessage.MessageType.TEXT,
                    content=message,
                    status=EvolutionMessage.MessageStatus.SENT,
                    timestamp=timezone.now(),
                    raw_payload=response_data
                )
                
                logger.info(f"Mensagem enviada para {phone} e salva no banco (ID: {evolution_message.id})")
                return {
                    'success': True,
                    'message_id': evolution_message.id,
                    'evolution_message_id': evolution_message_id,
                    'data': response_data
                }
            else:
                error_msg = f"Erro ao enviar mensagem: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_msg)
                except:
                    error_msg = f"{error_msg} - {response.text}"
                
                # Salvar mensagem com erro no banco
                evolution_message = EvolutionMessage.objects.create(
                    instance=instance,
                    contact=contact,
                    evolution_message_id=f"error_{timezone.now().timestamp()}",
                    phone=phone,
                    direction=EvolutionMessage.MessageDirection.OUTBOUND,
                    message_type=EvolutionMessage.MessageType.TEXT,
                    content=message,
                    status=EvolutionMessage.MessageStatus.ERROR,
                    error_message=error_msg,
                    timestamp=timezone.now(),
                    raw_payload={'error': error_msg}
                )
                
                logger.error(f"{error_msg} para {phone}")
                return {
                    'success': False,
                    'error': error_msg,
                    'message_id': evolution_message.id
                }
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para {phone}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_image(self, phone: str, image_url: str, caption: str = "") -> Dict:
        """
        Envia imagem
        
        Args:
            phone: Número do telefone
            image_url: URL da imagem
            caption: Legenda da imagem
            
        Returns:
            Dict com resultado
        """
        try:
            phone = self._normalize_phone(phone)
            
            url = f"{self.base_url}/message/sendMedia/{self.instance_name}"
            
            payload = {
                "number": phone,
                "mediatype": "image",
                "media": image_url,
                "caption": caption
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Imagem enviada para {phone}")
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                error_msg = f"Erro ao enviar imagem: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_msg)
                except:
                    pass
                
                logger.error(f"{error_msg} para {phone}")
                return {
                    'success': False,
                    'error': error_msg
                }
        except Exception as e:
            logger.error(f"Erro ao enviar imagem para {phone}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_product_message(self, phone: str, product_data: Dict, image_url: Optional[str] = None) -> Dict:
        """
        Envia mensagem com informações de produto
        
        Args:
            phone: Número do telefone
            product_data: Dados do produto (nome, descrição, preço, etc)
            image_url: URL da imagem do produto (opcional)
            
        Returns:
            Dict com resultado
        """
        try:
            # Construir mensagem formatada
            produto = product_data.get('produto', {})
            nome = produto.get('nome', 'Produto')
            descricao = produto.get('descricao', '')
            preco = produto.get('preco', '')
            categoria = produto.get('categoria', '')
            marca = produto.get('marca', '')
            
            message = f"🛍️ *{nome}*\n\n"
            
            if marca:
                message += f"🏷️ Marca: {marca}\n"
            if categoria:
                message += f"📂 Categoria: {categoria}\n"
            if preco:
                message += f"💰 Preço: {preco}\n"
            if descricao:
                message += f"\n📝 {descricao[:200]}...\n" if len(descricao) > 200 else f"\n📝 {descricao}\n"
            
            # Se tiver imagem, enviar imagem com legenda
            if image_url:
                return self.send_image(phone, image_url, message)
            else:
                # Enviar apenas texto
                return self.send_text_message(phone, message)
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem de produto para {phone}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_instance(self, instance_name: Optional[str] = None) -> Dict:
        """
        Cria uma nova instância
        
        Args:
            instance_name: Nome da instância (opcional, usa default se não fornecido)
            
        Returns:
            Dict com resultado
        """
        try:
            instance = instance_name or self.instance_name
            url = f"{self.base_url}/instance/create"
            
            payload = {
                "instanceName": instance,
                "token": self.api_key,
                "qrcode": True
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            if response.status_code in [200, 201]:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f'Erro ao criar instância: {response.status_code}'
                }
        except Exception as e:
            logger.error(f"Erro ao criar instância: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_qrcode(self, instance_name: Optional[str] = None) -> Dict:
        """
        Obtém QR Code para conectar WhatsApp
        
        Args:
            instance_name: Nome da instância (opcional)
            
        Returns:
            Dict com QR Code
        """
        try:
            instance = instance_name or self.instance_name
            url = f"{self.base_url}/instance/connect/{instance}"
            
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f'Erro ao obter QR Code: {response.status_code}'
                }
        except Exception as e:
            logger.error(f"Erro ao obter QR Code: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

