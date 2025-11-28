"""
Models para WhatsApp Integration
Modelos para armazenar contatos e logs de mensagens do WhatsApp
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class WhatsAppContact(models.Model):
    """
    Model para armazenar informações de contatos do WhatsApp
    
    Relaciona números de telefone com usuários do sistema (Keeper, Shopper, Cliente)
    """
    
    # Número de telefone no formato internacional (ex: 5511999999999)
    phone_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name="Número de Telefone",
        help_text="Número no formato internacional (ex: 5511999999999)"
    )
    
    # Relacionamento opcional com User do Django
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='whatsapp_contacts',
        verbose_name="Usuário",
        help_text="Usuário associado a este número (opcional)"
    )
    
    # Nome do contato (pode vir do WhatsApp ou ser definido manualmente)
    name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Nome",
        help_text="Nome do contato"
    )
    
    # Tipo de contato no sistema Évora/VitrineZap
    CONTACT_TYPE_CHOICES = [
        ('cliente', 'Cliente Final'),
        ('keeper', 'Keeper'),
        ('shopper', 'Personal Shopper'),
        ('unknown', 'Desconhecido'),
    ]
    
    contact_type = models.CharField(
        max_length=20,
        choices=CONTACT_TYPE_CHOICES,
        default='unknown',
        db_index=True,
        verbose_name="Tipo de Contato",
        help_text="Tipo de contato no sistema"
    )
    
    # Status do contato
    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Se o contato está ativo"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em"
    )
    
    # Metadata adicional (JSON field para flexibilidade)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Metadados",
        help_text="Informações adicionais sobre o contato"
    )
    
    class Meta:
        verbose_name = "Contato WhatsApp"
        verbose_name_plural = "Contatos WhatsApp"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['contact_type', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.phone_number} ({self.get_contact_type_display()})"
    
    def normalize_phone(self):
        """Normaliza o número de telefone"""
        # Remove caracteres não numéricos
        return ''.join(filter(str.isdigit, self.phone_number))


class WhatsAppMessageLog(models.Model):
    """
    Model para armazenar logs de mensagens recebidas e enviadas via WhatsApp
    
    Registra todas as interações para auditoria e processamento futuro
    """
    
    # Contato que enviou/recebeu a mensagem
    contact = models.ForeignKey(
        WhatsAppContact,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name="Contato",
        help_text="Contato associado à mensagem"
    )
    
    # Direção da mensagem
    DIRECTION_CHOICES = [
        ('incoming', 'Recebida'),
        ('outgoing', 'Enviada'),
    ]
    
    direction = models.CharField(
        max_length=10,
        choices=DIRECTION_CHOICES,
        db_index=True,
        verbose_name="Direção",
        help_text="Se a mensagem foi recebida ou enviada"
    )
    
    # Conteúdo da mensagem
    message_text = models.TextField(
        verbose_name="Texto da Mensagem",
        help_text="Conteúdo da mensagem"
    )
    
    # ID da mensagem do provedor (para rastreamento)
    provider_message_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="ID da Mensagem (Provedor)",
        help_text="ID da mensagem retornado pelo provedor"
    )
    
    # Tipo de mensagem
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Texto'),
        ('image', 'Imagem'),
        ('document', 'Documento'),
        ('audio', 'Áudio'),
        ('video', 'Vídeo'),
        ('location', 'Localização'),
        ('unknown', 'Desconhecido'),
    ]
    
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPE_CHOICES,
        default='text',
        verbose_name="Tipo de Mensagem"
    )
    
    # Status de processamento
    PROCESSING_STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('processed', 'Processada'),
        ('error', 'Erro'),
        ('ignored', 'Ignorada'),
    ]
    
    processing_status = models.CharField(
        max_length=20,
        choices=PROCESSING_STATUS_CHOICES,
        default='pending',
        db_index=True,
        verbose_name="Status de Processamento"
    )
    
    # Resposta automática enviada (se houver)
    auto_reply_sent = models.BooleanField(
        default=False,
        verbose_name="Resposta Automática Enviada",
        help_text="Se uma resposta automática foi enviada"
    )
    
    # Timestamp da mensagem
    message_timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name="Timestamp da Mensagem",
        help_text="Quando a mensagem foi enviada/recebida"
    )
    
    # Timestamp de criação do log
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )
    
    # Metadata adicional
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Metadados",
        help_text="Informações adicionais sobre a mensagem"
    )
    
    class Meta:
        verbose_name = "Log de Mensagem WhatsApp"
        verbose_name_plural = "Logs de Mensagens WhatsApp"
        ordering = ['-message_timestamp']
        indexes = [
            models.Index(fields=['contact', '-message_timestamp']),
            models.Index(fields=['direction', 'processing_status']),
            models.Index(fields=['provider_message_id']),
        ]
    
    def __str__(self):
        return f"{self.get_direction_display()} - {self.contact.phone_number} - {self.message_text[:50]}"
    
    def mark_as_processed(self):
        """Marca a mensagem como processada"""
        self.processing_status = 'processed'
        self.save(update_fields=['processing_status'])
    
    def mark_as_error(self):
        """Marca a mensagem como erro"""
        self.processing_status = 'error'
        self.save(update_fields=['processing_status'])

