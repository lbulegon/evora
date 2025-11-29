#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script simples para criar dados de teste KMN
Foca apenas nos modelos que sabemos que existem
"""
import os
import django
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from django.contrib.auth.models import User
from app_marketplace.models import (
    Cliente, PersonalShopper, Keeper, Agente, ClienteRelacao,
    TrustlineKeeper, RoleStats
)

def criar_dados_kmn():
    """Cria dados básicos para teste do KMN"""
    
    print("CRIANDO DADOS KMN - VitrineZap")
    print("=" * 40)
    
    # 1. CRIAR AGENTES
    print("\nCriando agentes...")
    
    # AGENTE 1: SHOPPER (Júnior - São Paulo)
    user_junior, created = User.objects.get_or_create(
        username='junior_sp',
        defaults={
            'first_name': 'Junior',
            'last_name': 'Santos',
            'email': 'junior@vitrinezap.com'
        }
    )
    if created:
        user_junior.set_password('123456')
        user_junior.save()
    
    # PersonalShopper para Júnior
    ps_junior, created = PersonalShopper.objects.get_or_create(
        user=user_junior,
        defaults={
            'nome': 'Junior Santos - SP',
            'bio': 'Especialista em eletrônicos',
            'ativo': True
        }
    )
    
    # Agente KMN para Júnior
    agente_junior, created = Agente.objects.get_or_create(
        user=user_junior,
        defaults={
            'personal_shopper': ps_junior,
            'nome_comercial': 'Junior Tech SP',
            'bio_agente': 'Shopper especializado em tecnologia',
            'ativo_como_shopper': True,
            'ativo_como_keeper': False,
            'score_shopper': Decimal('8.5'),
            'score_keeper': Decimal('3.0'),
            'verificado_kmn': True
        }
    )
    if created:
        print("  OK Junior Santos (Shopper)")
    
    # AGENTE 2: KEEPER (Márcia - Rio de Janeiro)
    user_marcia, created = User.objects.get_or_create(
        username='marcia_rj',
        defaults={
            'first_name': 'Marcia',
            'last_name': 'Silva',
            'email': 'marcia@vitrinezap.com'
        }
    )
    if created:
        user_marcia.set_password('123456')
        user_marcia.save()
    
    # Keeper para Márcia
    keeper_marcia, created = Keeper.objects.get_or_create(
        user=user_marcia,
        defaults={
            'nome': 'Marcia Silva - RJ',
            'endereco': 'Rio de Janeiro, RJ',
            'telefone': '(21) 98888-7777',
            'ativo': True
        }
    )
    
    # Agente KMN para Márcia
    agente_marcia, created = Agente.objects.get_or_create(
        user=user_marcia,
        defaults={
            'keeper': keeper_marcia,
            'nome_comercial': 'Marcia Store RJ',
            'bio_agente': 'Keeper especializada em moda',
            'ativo_como_shopper': False,
            'ativo_como_keeper': True,
            'score_shopper': Decimal('4.0'),
            'score_keeper': Decimal('9.2'),
            'verificado_kmn': True
        }
    )
    if created:
        print("  OK Marcia Silva (Keeper)")
    
    # AGENTE 3: HÍBRIDO (Ana - Belo Horizonte)
    user_ana, created = User.objects.get_or_create(
        username='ana_bh',
        defaults={
            'first_name': 'Ana',
            'last_name': 'Costa',
            'email': 'ana@vitrinezap.com'
        }
    )
    if created:
        user_ana.set_password('123456')
        user_ana.save()
    
    # PersonalShopper e Keeper para Ana
    ps_ana, created = PersonalShopper.objects.get_or_create(
        user=user_ana,
        defaults={
            'nome': 'Ana Costa - BH',
            'bio': 'Personal Shopper e Keeper híbrida',
            'ativo': True
        }
    )
    
    keeper_ana, created = Keeper.objects.get_or_create(
        user=user_ana,
        defaults={
            'nome': 'Ana Costa - BH',
            'endereco': 'Belo Horizonte, MG',
            'telefone': '(31) 97777-6666',
            'ativo': True
        }
    )
    
    # Agente KMN para Ana (Híbrido)
    agente_ana, created = Agente.objects.get_or_create(
        user=user_ana,
        defaults={
            'personal_shopper': ps_ana,
            'keeper': keeper_ana,
            'nome_comercial': 'Ana Home & Style',
            'bio_agente': 'Agente completa: compra, guarda e entrega',
            'ativo_como_shopper': True,
            'ativo_como_keeper': True,
            'score_shopper': Decimal('7.8'),
            'score_keeper': Decimal('8.1'),
            'verificado_kmn': True
        }
    )
    if created:
        print("  OK Ana Costa (Shopper-Keeper)")
    
    # 2. CRIAR CLIENTES
    print("\nCriando clientes...")
    
    clientes_data = [
        ('joao_cliente', 'Joao', 'Oliveira', 'joao@cliente.com'),
        ('maria_cliente', 'Maria', 'Santos', 'maria@cliente.com'),
        ('pedro_cliente', 'Pedro', 'Lima', 'pedro@cliente.com'),
        ('carla_cliente', 'Carla', 'Ferreira', 'carla@cliente.com'),
        ('roberto_cliente', 'Roberto', 'Alves', 'roberto@cliente.com')
    ]
    
    clientes = {}
    for username, first_name, last_name, email in clientes_data:
        # Criar usuário
        user_cliente, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email': email
            }
        )
        if created:
            user_cliente.set_password('123456')
            user_cliente.save()
        
        # Criar cliente
        cliente, created = Cliente.objects.get_or_create(
            user=user_cliente,
            defaults={
                'telefone': f'(11) 9999-{len(clientes):04d}',
                'data_nascimento': timezone.now().date() - timedelta(days=365*30)
            }
        )
        
        clientes[username] = cliente
        
        if created:
            print(f"  OK {first_name} {last_name}")
    
    # 3. CRIAR RELAÇÕES CLIENTE-AGENTE
    print("\nCriando relações cliente-agente...")
    
    # João - Cliente forte do Júnior
    ClienteRelacao.objects.get_or_create(
        cliente=clientes['joao_cliente'],
        agente=agente_junior,
        defaults={
            'forca_relacao': Decimal('85.0'),
            'total_pedidos': 12,
            'ultimo_contato': timezone.now() - timedelta(days=2)
        }
    )
    
    # Maria - Cliente forte da Márcia
    ClienteRelacao.objects.get_or_create(
        cliente=clientes['maria_cliente'],
        agente=agente_marcia,
        defaults={
            'forca_relacao': Decimal('92.0'),
            'total_pedidos': 18,
            'ultimo_contato': timezone.now() - timedelta(days=1)
        }
    )
    
    # Pedro - Cliente forte da Ana
    ClienteRelacao.objects.get_or_create(
        cliente=clientes['pedro_cliente'],
        agente=agente_ana,
        defaults={
            'forca_relacao': Decimal('78.0'),
            'total_pedidos': 8,
            'ultimo_contato': timezone.now() - timedelta(days=3)
        }
    )
    
    # Carla - Cliente em múltiplas carteiras (caso interessante)
    ClienteRelacao.objects.get_or_create(
        cliente=clientes['carla_cliente'],
        agente=agente_junior,
        defaults={
            'forca_relacao': Decimal('65.0'),
            'total_pedidos': 5,
            'ultimo_contato': timezone.now() - timedelta(days=7)
        }
    )
    ClienteRelacao.objects.get_or_create(
        cliente=clientes['carla_cliente'],
        agente=agente_marcia,
        defaults={
            'forca_relacao': Decimal('72.0'),  # Márcia tem relação mais forte
            'total_pedidos': 8,
            'ultimo_contato': timezone.now() - timedelta(days=4)
        }
    )
    
    # Roberto - Cliente novo, apenas com Ana
    ClienteRelacao.objects.get_or_create(
        cliente=clientes['roberto_cliente'],
        agente=agente_ana,
        defaults={
            'forca_relacao': Decimal('45.0'),
            'total_pedidos': 2,
            'ultimo_contato': timezone.now() - timedelta(days=10)
        }
    )
    
    print("  OK Relações criadas")
    
    # 4. CRIAR TRUSTLINES
    print("\nCriando trustlines...")
    
    # Trustline Júnior ↔ Márcia
    TrustlineKeeper.objects.get_or_create(
        agente_a=agente_junior,
        agente_b=agente_marcia,
        defaults={
            'nivel_confianca': Decimal('85.0'),
            'perc_shopper': Decimal('65.0'),
            'perc_keeper': Decimal('35.0'),
            'ativo': True
        }
    )
    
    # Trustline Júnior ↔ Ana
    TrustlineKeeper.objects.get_or_create(
        agente_a=agente_junior,
        agente_b=agente_ana,
        defaults={
            'nivel_confianca': Decimal('78.0'),
            'perc_shopper': Decimal('60.0'),
            'perc_keeper': Decimal('40.0'),
            'ativo': True
        }
    )
    
    # Trustline Márcia ↔ Ana
    TrustlineKeeper.objects.get_or_create(
        agente_a=agente_marcia,
        agente_b=agente_ana,
        defaults={
            'nivel_confianca': Decimal('82.0'),
            'perc_shopper': Decimal('58.0'),
            'perc_keeper': Decimal('42.0'),
            'ativo': True
        }
    )
    
    print("  OK Trustlines criadas")
    
    # 5. CRIAR ROLE STATS
    print("\nCriando estatísticas...")
    
    # Stats para Júnior
    RoleStats.objects.get_or_create(
        agente=agente_junior,
        defaults={
            'pedidos_como_shopper': 25,
            'pedidos_como_keeper': 3,
            'receita_como_shopper': Decimal('45000.00'),
            'receita_como_keeper': Decimal('1200.00'),
            'score_medio_avaliacoes': Decimal('4.7'),
            'total_avaliacoes': 28
        }
    )
    
    # Stats para Márcia
    RoleStats.objects.get_or_create(
        agente=agente_marcia,
        defaults={
            'pedidos_como_shopper': 2,
            'pedidos_como_keeper': 32,
            'receita_como_shopper': Decimal('800.00'),
            'receita_como_keeper': Decimal('18500.00'),
            'score_medio_avaliacoes': Decimal('4.9'),
            'total_avaliacoes': 34
        }
    )
    
    # Stats para Ana
    RoleStats.objects.get_or_create(
        agente=agente_ana,
        defaults={
            'pedidos_como_shopper': 18,
            'pedidos_como_keeper': 15,
            'receita_como_shopper': Decimal('12000.00'),
            'receita_como_keeper': Decimal('8500.00'),
            'score_medio_avaliacoes': Decimal('4.6'),
            'total_avaliacoes': 33
        }
    )
    
    print("  OK Estatísticas criadas")
    
    print("\n" + "=" * 40)
    print("DADOS KMN CRIADOS COM SUCESSO!")
    print("=" * 40)
    
    # RESUMO
    print(f"\nAgentes: {Agente.objects.count()}")
    print(f"Clientes: {Cliente.objects.count()}")
    print(f"Relações: {ClienteRelacao.objects.count()}")
    print(f"Trustlines: {TrustlineKeeper.objects.count()}")
    print(f"Role Stats: {RoleStats.objects.count()}")
    
    print("\nCREDENCIAIS (senha: 123456):")
    print("- junior_sp (Shopper)")
    print("- marcia_rj (Keeper)")
    print("- ana_bh (Shopper-Keeper)")
    print("- joao_cliente, maria_cliente, pedro_cliente, carla_cliente, roberto_cliente")
    
    print("\nTESTE INTERESSANTE:")
    print("Carla está na carteira do Junior (65%) e da Marcia (72%)")
    print("Sistema deve escolher oferta da Marcia (força maior)")
    
    print("\nACESSE: http://127.0.0.1:8000/kmn/")
    
    return True

if __name__ == '__main__':
    try:
        criar_dados_kmn()
    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()





