"""
Serviços de integração com gateways de pagamento
"""
import requests
import json
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from .models import Pagamento, TransacaoGateway


class PaymentGatewayService:
    """Serviço base para integração com gateways"""
    
    def __init__(self, gateway_name):
        self.gateway_name = gateway_name
        self.api_key = getattr(settings, f'{gateway_name.upper()}_API_KEY', '')
        self.secret_key = getattr(settings, f'{gateway_name.upper()}_SECRET_KEY', '')
        self.webhook_secret = getattr(settings, f'{gateway_name.upper()}_WEBHOOK_SECRET', '')
    
    def criar_pagamento(self, pagamento: Pagamento) -> dict:
        """
        Cria um pagamento no gateway e retorna dados do checkout.
        Deve ser implementado por cada gateway específico.
        """
        raise NotImplementedError("Subclasses devem implementar criar_pagamento")
    
    def validar_webhook(self, payload: dict, signature: str) -> bool:
        """
        Valida a assinatura do webhook.
        Deve ser implementado por cada gateway específico.
        """
        raise NotImplementedError("Subclasses devem implementar validar_webhook")
    
    def processar_webhook(self, payload: dict) -> dict:
        """
        Processa webhook do gateway e retorna dados normalizados.
        Deve ser implementado por cada gateway específico.
        """
        raise NotImplementedError("Subclasses devem implementar processar_webhook")


class MercadoPagoService(PaymentGatewayService):
    """Integração com Mercado Pago"""
    
    def __init__(self):
        super().__init__('mercadopago')
        self.base_url = 'https://api.mercadopago.com'
        self.access_token = self.api_key
    
    def criar_pagamento(self, pagamento: Pagamento) -> dict:
        """
        Cria pagamento no Mercado Pago e retorna dados do checkout
        """
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Montar payload conforme método
        if pagamento.metodo == Pagamento.Metodo.PIX:
            payload = {
                'transaction_amount': float(pagamento.valor),
                'description': f'Pedido {pagamento.pedido.codigo or pagamento.pedido.id}',
                'payment_method_id': 'pix',
                'payer': {
                    'email': pagamento.pedido.cliente_email or 'cliente@example.com',
                    'first_name': pagamento.pedido.cliente_nome.split()[0] if pagamento.pedido.cliente_nome else 'Cliente',
                }
            }
        else:  # Cartão
            payload = {
                'transaction_amount': float(pagamento.valor),
                'description': f'Pedido {pagamento.pedido.codigo or pagamento.pedido.id}',
                'payment_method_id': 'credit_card',
                'payer': {
                    'email': pagamento.pedido.cliente_email or 'cliente@example.com',
                }
            }
        
        try:
            response = requests.post(
                f'{self.base_url}/v1/payments',
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            # Atualizar pagamento com dados do gateway
            pagamento.gateway_payment_id = str(data.get('id', ''))
            
            if pagamento.metodo == Pagamento.Metodo.PIX:
                # Para Pix, buscar QR Code
                if 'point_of_interaction' in data:
                    qr_code_data = data['point_of_interaction'].get('transaction_data', {})
                    pagamento.gateway_qr_code = qr_code_data.get('qr_code', '')
                    pagamento.gateway_qr_code_base64 = qr_code_data.get('qr_code_base64', '')
                    pagamento.gateway_checkout_url = None
                else:
                    pagamento.gateway_checkout_url = data.get('transaction_details', {}).get('external_resource_url', '')
            else:
                pagamento.gateway_checkout_url = data.get('transaction_details', {}).get('external_resource_url', '')
            
            pagamento.save()
            
            # Registrar transação
            TransacaoGateway.objects.create(
                pagamento=pagamento,
                tipo_evento='payment_created',
                payload=data
            )
            
            return {
                'success': True,
                'gateway_payment_id': pagamento.gateway_payment_id,
                'checkout_url': pagamento.gateway_checkout_url,
                'qr_code': pagamento.gateway_qr_code,
                'qr_code_base64': pagamento.gateway_qr_code_base64
            }
        
        except requests.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def validar_webhook(self, payload: dict, signature: str) -> bool:
        """
        Valida webhook do Mercado Pago
        """
        # Implementar validação de assinatura HMAC se necessário
        # Por enquanto, retorna True (em produção, validar)
        return True
    
    def processar_webhook(self, payload: dict) -> dict:
        """
        Processa webhook do Mercado Pago e retorna dados normalizados
        """
        action = payload.get('action', '')
        data = payload.get('data', {})
        
        payment_id = data.get('id', '')
        status_map = {
            'pending': Pagamento.Status.PENDENTE,
            'approved': Pagamento.Status.CONFIRMADO,
            'rejected': Pagamento.Status.RECUSADO,
            'cancelled': Pagamento.Status.CANCELADO,
            'refunded': Pagamento.Status.CANCELADO,
        }
        
        return {
            'gateway_payment_id': str(payment_id),
            'status': status_map.get(data.get('status', ''), Pagamento.Status.PENDENTE),
            'tipo_evento': f'payment_{action}',
            'payload': payload
        }


class StripeService(PaymentGatewayService):
    """Integração com Stripe"""
    
    def __init__(self):
        super().__init__('stripe')
        self.base_url = 'https://api.stripe.com/v1'
        self.api_key = self.secret_key  # Stripe usa secret_key
    
    def criar_pagamento(self, pagamento: Pagamento) -> dict:
        """
        Cria pagamento no Stripe e retorna dados do checkout
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Criar PaymentIntent
        payload = {
            'amount': int(pagamento.valor * 100),  # Stripe usa centavos
            'currency': pagamento.moeda.lower(),
            'description': f'Pedido {pagamento.pedido.codigo or pagamento.pedido.id}',
        }
        
        try:
            response = requests.post(
                f'{self.base_url}/payment_intents',
                headers=headers,
                data=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            # Atualizar pagamento
            pagamento.gateway_payment_id = data.get('id', '')
            pagamento.gateway_checkout_url = data.get('next_action', {}).get('redirect_to_url', {}).get('url', '')
            pagamento.save()
            
            # Registrar transação
            TransacaoGateway.objects.create(
                pagamento=pagamento,
                tipo_evento='payment_created',
                payload=data
            )
            
            return {
                'success': True,
                'gateway_payment_id': pagamento.gateway_payment_id,
                'checkout_url': pagamento.gateway_checkout_url,
            }
        
        except requests.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def validar_webhook(self, payload: dict, signature: str) -> bool:
        """
        Valida webhook do Stripe usando assinatura
        """
        # Implementar validação de assinatura HMAC
        # Por enquanto, retorna True
        return True
    
    def processar_webhook(self, payload: dict) -> dict:
        """
        Processa webhook do Stripe
        """
        event_type = payload.get('type', '')
        data = payload.get('data', {}).get('object', {})
        
        payment_id = data.get('id', '')
        status_map = {
            'requires_payment_method': Pagamento.Status.PENDENTE,
            'requires_confirmation': Pagamento.Status.PENDENTE,
            'requires_action': Pagamento.Status.PENDENTE,
            'processing': Pagamento.Status.PENDENTE,
            'succeeded': Pagamento.Status.CONFIRMADO,
            'requires_capture': Pagamento.Status.CONFIRMADO,
            'canceled': Pagamento.Status.CANCELADO,
            'payment_failed': Pagamento.Status.RECUSADO,
        }
        
        return {
            'gateway_payment_id': payment_id,
            'status': status_map.get(data.get('status', ''), Pagamento.Status.PENDENTE),
            'tipo_evento': event_type,
            'payload': payload
        }


def get_gateway_service(gateway_name: str) -> PaymentGatewayService:
    """
    Factory para obter serviço do gateway correto
    """
    gateway_map = {
        'mercadopago': MercadoPagoService,
        'stripe': StripeService,
    }
    
    service_class = gateway_map.get(gateway_name.lower())
    if not service_class:
        raise ValueError(f"Gateway '{gateway_name}' não suportado")
    
    return service_class()


def enviar_notificacao_whatsapp(pedido, template: str, **kwargs):
    """
    Stub para envio de notificação via WhatsApp.
    Implementar integração com Twilio/WhatsApp API depois.
    """
    # TODO: Implementar integração com WhatsApp
    print(f"[STUB] Enviando WhatsApp para {pedido.cliente_whatsapp}: {template}")
    return True

