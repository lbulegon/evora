#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para criar dados de teste compatíveis com os modelos reais
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
    Empresa, Categoria, Produto, Cliente, PersonalShopper, Keeper, 
    Agente, ClienteRelacao, TrustlineKeeper, RoleStats, EstoqueItem, Oferta
)

def criar_dados_reais():
    """Cria dados de teste usando a estrutura real dos modelos"""
    
    print("CRIANDO DADOS DE TESTE - VitrineZap KMN")
    print("=" * 50)
    
    # 1. CRIAR EMPRESA
    print("\nCriando empresa...")
    empresa, created = Empresa.objects.get_or_create(
        cnpj="12.345.678/0001-90",
        defaults={
            'nome': 'EVORA Marketplace',
            'email': 'contato@evora.com',
            'telefone': '(11) 99999-0000'
        }
    )
    if created:
        print("  OK Empresa EVORA criada")
    
    # 2. CRIAR CATEGORIAS
    print("\nCriando categorias...")
    categorias = {}
    cat_data = [
        ('Eletrônicos', 'eletronicos'),
        ('Moda', 'moda'),
        ('Casa', 'casa'),
        ('Esporte', 'esporte')
    ]
    
    for nome, slug in cat_data:
        cat, created = Categoria.objects.get_or_create(
            slug=slug,
            defaults={'nome': nome}
        )
        categorias[nome] = cat
        if created:
            print(f"  OK Categoria: {nome}")
    
    # 3. CRIAR PRODUTOS
    print("\nCriando produtos...")
    produtos_data = [
        {
            'nome': 'iPhone 15 Pro 128GB',
            'categoria': categorias['Eletrônicos'],
            'descricao': 'iPhone 15 Pro com 128GB, cor Natural Titanium',
            'preco': Decimal('7999.00')
        },
        {
            'nome': 'Vestido Floral Primavera',
            'categoria': categorias['Moda'],
            'descricao': 'Vestido midi floral, tecido viscose, tamanho M',
            'preco': Decimal('189.90')
        },
        {
            'nome': 'Luminária LED Smart',
            'categoria': categorias['Casa'],
            'descricao': 'Luminária LED com controle por app, RGB, 12W',
            'preco': Decimal('129.90')
        },
        {
            'nome': 'Halteres Ajustáveis',
            'categoria': categorias['Esporte'],
            'descricao': 'Par de halteres ajustáveis de 5 a 20kg cada',
            'preco': Decimal('899.90')
        }
    ]
    
    produtos = {}
    for i, prod_data in enumerate(produtos_data):
        produto, created = Produto.objects.get_or_create(
            empresa=empresa,
            nome=prod_data['nome'],
            defaults={
                'descricao': prod_data['descricao'],
                'preco': prod_data['preco'],
                'categoria': prod_data['categoria'],
                'ativo': True
            }
        )
        produtos[f'produto_{i+1}'] = produto
        if created:
            print(f"  OK {prod_data['nome']}")
    
    # 4. CRIAR USUÁRIOS E AGENTES
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
    
    ps_junior, created = PersonalShopper.objects.get_or_create(
        user=user_junior,
        defaults={
            'nome': 'Junior Santos - SP',
            'bio': 'Especialista em eletrônicos e gadgets',
            'ativo': True
        }
    )
    
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
    
    keeper_marcia, created = Keeper.objects.get_or_create(
        user=user_marcia,
        defaults={
            'apelido_local': 'Copacabana - RJ',
            'rua': 'Rua das Flores',
            'numero': '456',
            'bairro': 'Copacabana',
            'cidade': 'Rio de Janeiro',
            'estado': 'RJ',
            'cep': '22000-000',
            'capacidade_kg': Decimal('50.0'),
            'taxa_recebimento': Decimal('5.00'),
            'taxa_armazenamento_dia': Decimal('2.00'),
            'ativo': True
        }
    )
    
    agente_marcia, created = Agente.objects.get_or_create(
        user=user_marcia,
        defaults={
            'keeper': keeper_marcia,
            'nome_comercial': 'Marcia Store RJ',
            'bio_agente': 'Keeper especializada em moda e lifestyle',
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
            'apelido_local': 'Centro - BH',
            'rua': 'Av. Afonso Pena',
            'numero': '789',
            'bairro': 'Centro',
            'cidade': 'Belo Horizonte',
            'estado': 'MG',
            'cep': '30000-000',
            'capacidade_kg': Decimal('30.0'),
            'taxa_recebimento': Decimal('4.00'),
            'taxa_armazenamento_dia': Decimal('1.50'),
            'ativo': True
        }
    )
    
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
    
    # 5. CRIAR CLIENTES
    print("\nCriando clientes...")
    clientes_data = [
        ('joao_cliente', 'Joao', 'Oliveira', 'joao@cliente.com', '(11) 91111-1111'),
        ('maria_cliente', 'Maria', 'Santos', 'maria@cliente.com', '(21) 92222-2222'),
        ('pedro_cliente', 'Pedro', 'Lima', 'pedro@cliente.com', '(31) 93333-3333'),
        ('carla_cliente', 'Carla', 'Ferreira', 'carla@cliente.com', '(11) 94444-4444'),
        ('roberto_cliente', 'Roberto', 'Alves', 'roberto@cliente.com', '(21) 95555-5555')
    ]
    
    clientes = {}
    for username, first_name, last_name, email, telefone in clientes_data:
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
        
        cliente, created = Cliente.objects.get_or_create(
            user=user_cliente,
            defaults={
                'telefone': telefone,
                'data_nascimento': timezone.now().date() - timedelta(days=365*30)
            }
        )
        
        clientes[username] = cliente
        if created:
            print(f"  OK {first_name} {last_name}")
    
    # 6. CRIAR RELAÇÕES CLIENTE-AGENTE
    print("\nCriando relações cliente-agente...")
    
    relacoes = [
        (clientes['joao_cliente'], agente_junior, Decimal('85.0'), 12),
        (clientes['maria_cliente'], agente_marcia, Decimal('92.0'), 18),
        (clientes['pedro_cliente'], agente_ana, Decimal('78.0'), 8),
        (clientes['carla_cliente'], agente_junior, Decimal('65.0'), 5),
        (clientes['carla_cliente'], agente_marcia, Decimal('72.0'), 8),  # Conflito interessante
        (clientes['roberto_cliente'], agente_ana, Decimal('45.0'), 2)
    ]
    
    for cliente, agente, forca, pedidos in relacoes:
        ClienteRelacao.objects.get_or_create(
            cliente=cliente,
            agente=agente,
            defaults={
                'forca_relacao': forca,
                'total_pedidos': pedidos,
                'ultimo_contato': timezone.now() - timedelta(days=forca/10)
            }
        )
    
    print("  OK Relações criadas")
    
    # 7. CRIAR TRUSTLINES
    print("\nCriando trustlines...")
    
    trustlines = [
        (agente_junior, agente_marcia, Decimal('85.0'), Decimal('65.0'), Decimal('35.0')),
        (agente_junior, agente_ana, Decimal('78.0'), Decimal('60.0'), Decimal('40.0')),
        (agente_marcia, agente_ana, Decimal('82.0'), Decimal('58.0'), Decimal('42.0'))
    ]
    
    for agente_a, agente_b, confianca, perc_shopper, perc_keeper in trustlines:
        TrustlineKeeper.objects.get_or_create(
            agente_a=agente_a,
            agente_b=agente_b,
            defaults={
                'nivel_confianca': confianca,
                'perc_shopper': perc_shopper,
                'perc_keeper': perc_keeper,
                'ativo': True
            }
        )
    
    print("  OK Trustlines criadas")
    
    # 8. CRIAR ROLE STATS
    print("\nCriando estatísticas...")
    
    stats_data = [
        (agente_junior, 25, 3, Decimal('45000.00'), Decimal('1200.00'), Decimal('4.7'), 28),
        (agente_marcia, 2, 32, Decimal('800.00'), Decimal('18500.00'), Decimal('4.9'), 34),
        (agente_ana, 18, 15, Decimal('12000.00'), Decimal('8500.00'), Decimal('4.6'), 33)
    ]
    
    for agente, ped_shopper, ped_keeper, rec_shopper, rec_keeper, score, avaliacoes in stats_data:
        RoleStats.objects.get_or_create(
            agente=agente,
            defaults={
                'pedidos_como_shopper': ped_shopper,
                'pedidos_como_keeper': ped_keeper,
                'receita_como_shopper': rec_shopper,
                'receita_como_keeper': rec_keeper,
                'score_medio_avaliacoes': score,
                'total_avaliacoes': avaliacoes
            }
        )
    
    print("  OK Estatísticas criadas")
    
    print("\n" + "=" * 50)
    print("DADOS DE TESTE CRIADOS COM SUCESSO!")
    print("=" * 50)
    
    # RESUMO
    print(f"\nEmpresa: {Empresa.objects.count()}")
    print(f"Categorias: {Categoria.objects.count()}")
    print(f"Produtos: {Produto.objects.count()}")
    print(f"Agentes: {Agente.objects.count()}")
    print(f"Clientes: {Cliente.objects.count()}")
    print(f"Relações: {ClienteRelacao.objects.count()}")
    print(f"Trustlines: {TrustlineKeeper.objects.count()}")
    print(f"Role Stats: {RoleStats.objects.count()}")
    
    print("\nCREDENCIAIS (senha: 123456):")
    print("- junior_sp (Shopper)")
    print("- marcia_rj (Keeper)")
    print("- ana_bh (Shopper-Keeper)")
    print("- Clientes: joao_cliente, maria_cliente, pedro_cliente, carla_cliente, roberto_cliente")
    
    print("\nCENARIOS DE TESTE:")
    print("1. Joao (cliente do Junior) - venda direta")
    print("2. Maria (cliente da Marcia) - venda cooperada")
    print("3. Carla (cliente de ambos) - conflito: Marcia tem força maior (72% vs 65%)")
    
    return True

if __name__ == '__main__':
    try:
        criar_dados_reais()
    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()
