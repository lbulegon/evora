"""
Signals para integração WhatsApp - criação automática de conversas
Paradigma: Grupo → Pedido → Conversa Individual
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import WhatsappOrder
from .conversations_views import create_conversation_after_order


@receiver(post_save, sender=WhatsappOrder)
def create_conversation_on_order_creation(sender, instance, created, **kwargs):
    """
    Signal: Cria conversa individual automaticamente quando pedido é criado
    Paradigma Umbler Talk: Após compra, atendimento é individualizado
    """
    if created:
        # Criar conversa apenas quando pedido é criado (não atualizado)
        create_conversation_after_order(instance)

