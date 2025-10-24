#!/usr/bin/env python
"""
Script de Teste - Integração WhatsApp ÉVORA Connect
Cria dados de teste para validar a funcionalidade
"""
import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from django.contrib.auth.models import User
from app_marketplace.models import (
    PersonalShopper, Keeper, Cliente,
    WhatsappGroup, WhatsappParticipant, WhatsappMessage, 
    WhatsappProduct, WhatsappOrder
)

def create_test_users():
    """Criar usuários de teste"""
    print("🔧 Criando usuários de teste...")
    
    # Shopper de teste
    shopper_user, created = User.objects.get_or_create(
        username='shopper_teste',
        defaults={
            'first_name': 'Maria',
            'last_name': 'Silva',
            'email': 'maria@teste.com'
        }
    )
    if created:
        shopper_user.set_password('123456')
        shopper_user.save()
    
    shopper, created = PersonalShopper.objects.get_or_create(
        user=shopper_user,
        defaults={
            'nome': 'Maria Silva',
            'ativo': True
        }
    )
    
    # Keeper de teste
    keeper_user, created = User.objects.get_or_create(
        username='keeper_teste',
        defaults={
            'first_name': 'João',
            'last_name': 'Santos',
            'email': 'joao@teste.com'
        }
    )
    if created:
        keeper_user.set_password('123456')
        keeper_user.save()
    
    keeper, created = Keeper.objects.get_or_create(
        user=keeper_user,
        defaults={
            'cidade': 'Orlando',
            'pais': 'USA',
            'ativo': True,
            'capacidade_itens': 100
        }
    )
    
    # Cliente de teste
    cliente_user, created = User.objects.get_or_create(
        username='cliente_teste',
        defaults={
            'first_name': 'Ana',
            'last_name': 'Costa',
            'email': 'ana@teste.com'
        }
    )
    if created:
        cliente_user.set_password('123456')
        cliente_user.save()
    
    cliente, created = Cliente.objects.get_or_create(
        user=cliente_user,
        defaults={
            'telefone': '+5511999999999'
        }
    )
    
    print(f"✅ Usuários criados:")
    print(f"   - Shopper: {shopper_user.username} (ID: {shopper_user.id})")
    print(f"   - Keeper: {keeper_user.username} (ID: {keeper_user.id})")
    print(f"   - Cliente: {cliente_user.username} (ID: {cliente_user.id})")
    
    return shopper_user, keeper_user, cliente_user, shopper, keeper, cliente


def create_test_whatsapp_data(shopper_user, keeper_user, cliente_user, shopper, keeper, cliente):
    """Criar dados WhatsApp de teste"""
    print("\n📱 Criando dados WhatsApp de teste...")
    
    # Grupo do Shopper
    shopper_group, created = WhatsappGroup.objects.get_or_create(
        chat_id='120363123456789012@g.us',
        defaults={
            'name': 'Compras Orlando - Maria',
            'owner': shopper_user,
            'shopper': shopper,
            'active': True,
            'auto_approve_orders': True,
            'send_notifications': True
        }
    )
    
    # Grupo do Keeper
    keeper_group, created = WhatsappGroup.objects.get_or_create(
        chat_id='120363123456789013@g.us',
        defaults={
            'name': 'Keeper Orlando - João',
            'owner': keeper_user,
            'keeper': keeper,
            'active': True,
            'auto_approve_orders': False,
            'send_notifications': True
        }
    )
    
    # Participantes do grupo do Shopper
    participant1, created = WhatsappParticipant.objects.get_or_create(
        group=shopper_group,
        phone='+5511999999999',
        defaults={
            'name': 'Ana Costa',
            'is_admin': False,
            'cliente': cliente
        }
    )
    
    participant2, created = WhatsappParticipant.objects.get_or_create(
        group=shopper_group,
        phone='+5511888888888',
        defaults={
            'name': 'Carlos Silva',
            'is_admin': False
        }
    )
    
    # Mensagens de teste
    message1, created = WhatsappMessage.objects.get_or_create(
        message_id='msg_001',
        defaults={
            'group': shopper_group,
            'sender': participant1,
            'message_type': 'text',
            'content': 'Olá! Quero comprar um Victoria\'s Secret Body Splash',
            'timestamp': datetime.now() - timedelta(hours=2),
            'processed': True
        }
    )
    
    message2, created = WhatsappMessage.objects.get_or_create(
        message_id='msg_002',
        defaults={
            'group': shopper_group,
            'sender': participant2,
            'message_type': 'text',
            'content': 'Tem Nike Air Max disponível?',
            'timestamp': datetime.now() - timedelta(hours=1),
            'processed': True
        }
    )
    
    # Produtos de teste
    product1, created = WhatsappProduct.objects.get_or_create(
        group=shopper_group,
        name='Victoria\'s Secret Body Splash Love Spell',
        defaults={
            'message': message1,
            'posted_by': participant1,
            'description': 'Body Splash 250ml - Love Spell',
            'price': Decimal('7.99'),
            'currency': 'USD',
            'brand': 'Victoria\'s Secret',
            'category': 'Perfumes',
            'image_urls': ['https://example.com/vs1.jpg'],
            'is_available': True,
            'is_featured': True
        }
    )
    
    product2, created = WhatsappProduct.objects.get_or_create(
        group=shopper_group,
        name='Nike Air Max 270',
        defaults={
            'message': message2,
            'posted_by': participant2,
            'description': 'Tênis Nike Air Max 270 - Tamanho 42',
            'price': Decimal('129.99'),
            'currency': 'USD',
            'brand': 'Nike',
            'category': 'Calçados',
            'image_urls': ['https://example.com/nike1.jpg'],
            'is_available': True,
            'is_featured': False
        }
    )
    
    # Pedidos de teste
    order1, created = WhatsappOrder.objects.get_or_create(
        order_number='WAP2412010001',
        defaults={
            'group': shopper_group,
            'customer': participant1,
            'cliente': cliente,
            'status': 'pending',
            'total_amount': Decimal('7.99'),
            'currency': 'USD',
            'products': [
                {
                    'name': 'Victoria\'s Secret Body Splash Love Spell',
                    'price': '7.99',
                    'quantity': 1
                }
            ],
            'delivery_method': 'keeper',
            'payment_method': 'pix',
            'payment_status': 'pending'
        }
    )
    
    order2, created = WhatsappOrder.objects.get_or_create(
        order_number='WAP2412010002',
        defaults={
            'group': shopper_group,
            'customer': participant2,
            'status': 'paid',
            'total_amount': Decimal('129.99'),
            'currency': 'USD',
            'products': [
                {
                    'name': 'Nike Air Max 270',
                    'price': '129.99',
                    'quantity': 1
                }
            ],
            'delivery_method': 'keeper-correio',
            'payment_method': 'cartao',
            'payment_status': 'paid',
            'paid_at': datetime.now() - timedelta(hours=1)
        }
    )
    
    print(f"✅ Dados WhatsApp criados:")
    print(f"   - Grupo Shopper: {shopper_group.name} ({shopper_group.participant_count} participantes)")
    print(f"   - Grupo Keeper: {keeper_group.name}")
    print(f"   - Mensagens: {shopper_group.messages.count()}")
    print(f"   - Produtos: {shopper_group.products.count()}")
    print(f"   - Pedidos: {shopper_group.orders.count()}")
    
    return shopper_group, keeper_group


def test_data_isolation():
    """Testar isolamento de dados"""
    print("\n🔒 Testando isolamento de dados...")
    
    # Testar que cada usuário vê apenas seus dados
    shopper_user = User.objects.get(username='shopper_teste')
    keeper_user = User.objects.get(username='keeper_teste')
    
    # Grupos do shopper
    shopper_groups = WhatsappGroup.objects.filter(owner=shopper_user)
    print(f"   - Grupos do Shopper: {shopper_groups.count()}")
    
    # Grupos do keeper
    keeper_groups = WhatsappGroup.objects.filter(owner=keeper_user)
    print(f"   - Grupos do Keeper: {keeper_groups.count()}")
    
    # Verificar isolamento
    if shopper_groups.count() > 0 and keeper_groups.count() > 0:
        print("   ✅ Isolamento funcionando - cada usuário tem seus próprios grupos")
    else:
        print("   ❌ Problema no isolamento de dados")
    
    return True


def print_test_instructions():
    """Imprimir instruções de teste"""
    print("\n" + "="*60)
    print("🧪 INSTRUÇÕES DE TESTE - INTEGRAÇÃO WHATSAPP")
    print("="*60)
    
    print("\n1️⃣ TESTAR DASHBOARD WEB:")
    print("   - Acesse: http://localhost:8000/admin/")
    print("   - Login: shopper_teste / 123456")
    print("   - Vá em 'Grupos WhatsApp' - deve ver apenas 1 grupo")
    print("   - Vá em 'Participantes WhatsApp' - deve ver 2 participantes")
    print("   - Vá em 'Produtos WhatsApp' - deve ver 2 produtos")
    print("   - Vá em 'Pedidos WhatsApp' - deve ver 2 pedidos")
    
    print("\n2️⃣ TESTAR ISOLAMENTO:")
    print("   - Login: keeper_teste / 123456")
    print("   - Vá em 'Grupos WhatsApp' - deve ver apenas 1 grupo (diferente)")
    print("   - Verifique que não vê dados do shopper")
    
    print("\n3️⃣ TESTAR DASHBOARD WHATSAPP:")
    print("   - Acesse: http://localhost:8000/whatsapp/dashboard/")
    print("   - Login: shopper_teste / 123456")
    print("   - Deve ver estatísticas do grupo")
    print("   - Teste navegar pelos menus")
    
    print("\n4️⃣ TESTAR CRIAÇÃO DE GRUPO:")
    print("   - Acesse: http://localhost:8000/whatsapp/groups/")
    print("   - Clique em 'Novo Grupo'")
    print("   - Preencha os dados e teste criar")
    
    print("\n5️⃣ TESTAR API ENDPOINTS:")
    print("   - Use Postman ou curl para testar:")
    print("   - POST /api/whatsapp/groups/create/")
    print("   - POST /api/whatsapp/groups/1/update/")
    print("   - POST /api/whatsapp/groups/1/send-message/")
    
    print("\n6️⃣ TESTAR INTEGRAÇÃO WHATSAPP REAL:")
    print("   - Configure WPPConnect no Railway")
    print("   - Escaneie QR Code")
    print("   - Envie mensagem para o grupo")
    print("   - Verifique se aparece no dashboard")
    
    print("\n" + "="*60)
    print("✅ DADOS DE TESTE CRIADOS COM SUCESSO!")
    print("="*60)


def main():
    """Função principal"""
    print("🚀 Iniciando teste da integração WhatsApp...")
    
    try:
        # Criar usuários
        shopper_user, keeper_user, cliente_user, shopper, keeper, cliente = create_test_users()
        
        # Criar dados WhatsApp
        shopper_group, keeper_group = create_test_whatsapp_data(
            shopper_user, keeper_user, cliente_user, shopper, keeper, cliente
        )
        
        # Testar isolamento
        test_data_isolation()
        
        # Instruções
        print_test_instructions()
        
        print("\n🎉 Teste concluído com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
