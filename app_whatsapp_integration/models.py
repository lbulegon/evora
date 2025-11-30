"""
Models - WhatsApp Integration
==============================

Modelos para armazenar contatos e logs de mensagens do WhatsApp.
"""

from django.db import models
from django.contrib.auth.models import User
from app_marketplace.models import Cliente, PersonalShopper, AddressKeeper


class WhatsAppContact(models.Model):
    """
    Contato WhatsApp vinculado a um usuário do sistema
    
    Relaciona números de telefone com Users, Clientes, Shoppers ou Keepers.
    """
    phone = models.CharField(
        max_length=20,
        unique=True,
        help_text="Número do WhatsApp (formato: +5511999999999)"
    )
    
    # Vinculação com usuários do sistema (pode ser User, Cliente, Shopper ou Keeper)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='whatsapp_contacts',
        help_text="Usuário vinculado (se for User direto)"
    )
    
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='whatsapp_contacts',
        help_text="Cliente vinculado"
    )
    
    shopper = models.ForeignKey(
        PersonalShopper,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='whatsapp_contacts',
        help_text="Personal Shopper vinculado"
    )
    
    keeper = models.ForeignKey(
        AddressKeeper,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='whatsapp_contacts',
        help_text="Address Keeper vinculado"
    )
    
    # Dados do contato
    name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Nome do contato (do WhatsApp)"
    )
    
    is_verified = models.BooleanField(
        default=False,
        help_text="Contato verificado no sistema"
    )
    
    # Metadados
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Contato WhatsApp'
        verbose_name_plural = 'Contatos WhatsApp'
        ordering = ['-last_message_at', '-created_at']
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['user', 'cliente', 'shopper', 'keeper']),
        ]
    
    def __str__(self):
        return f"{self.phone} - {self.name or 'Sem nome'}"
    
    @property
    def user_type(self):
        """Retorna o tipo de usuário vinculado"""
        if self.user:
            if self.user.is_superuser:
                return 'admin'
            elif self.cliente:
                return 'cliente'
            elif self.shopper:
                return 'shopper'
            elif self.keeper:
                return 'keeper'
        return 'unknown'
    
    def get_linked_user(self):
        """Retorna o User vinculado (se houver)"""
        if self.user:
            return self.user
        elif self.cliente and self.cliente.user:
            return self.cliente.user
        elif self.shopper and self.shopper.user:
            return self.shopper.user
        elif self.keeper and self.keeper.user:
            return self.keeper.user
        return None


class WhatsAppMessageLog(models.Model):
    """
    Log de mensagens recebidas do WhatsApp
    
    Armazena todas as mensagens recebidas para histórico e análise.
    """
    
    class MessageType(models.TextChoices):
        TEXT = 'text', 'Texto'
        IMAGE = 'image', 'Imagem'
        VIDEO = 'video', 'Vídeo'
        AUDIO = 'audio', 'Áudio'
        DOCUMENT = 'document', 'Documento'
        LOCATION = 'location', 'Localização'
        CONTACT = 'contact', 'Contato'
        UNKNOWN = 'unknown', 'Desconhecido'
    
    class MessageDirection(models.TextChoices):
        INBOUND = 'inbound', 'Recebida'
        OUTBOUND = 'outbound', 'Enviada'
    
    # Dados da mensagem
    message_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="ID único da mensagem (do provedor)"
    )
    
    contact = models.ForeignKey(
        WhatsAppContact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages',
        help_text="Contato que enviou/recebeu a mensagem"
    )
    
    phone = models.CharField(
        max_length=20,
        help_text="Número de telefone (backup se contact for None)"
    )
    
    direction = models.CharField(
        max_length=10,
        choices=MessageDirection.choices,
        default=MessageDirection.INBOUND,
        help_text="Direção da mensagem"
    )
    
    message_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.TEXT,
        help_text="Tipo de mensagem"
    )
    
    content = models.TextField(
        help_text="Conteúdo da mensagem (texto ou URL de mídia)"
    )
    
    # Processamento
    processed = models.BooleanField(
        default=False,
        help_text="Mensagem foi processada pelo sistema"
    )
    
    reply_sent = models.BooleanField(
        default=False,
        help_text="Resposta foi enviada"
    )
    
    reply_content = models.TextField(
        blank=True,
        help_text="Conteúdo da resposta enviada (se houver)"
    )
    
    # Metadados
    raw_payload = models.JSONField(
        default=dict,
        blank=True,
        help_text="Payload completo recebido do provedor"
    )
    
    timestamp = models.DateTimeField(
        help_text="Timestamp da mensagem (do WhatsApp)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Log de Mensagem WhatsApp'
        verbose_name_plural = 'Logs de Mensagens WhatsApp'
        ordering = ['-timestamp', '-created_at']
        indexes = [
            models.Index(fields=['phone', '-timestamp']),
            models.Index(fields=['contact', '-timestamp']),
            models.Index(fields=['processed', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.phone} - {self.message_type} - {self.timestamp}"
