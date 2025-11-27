#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para criar dados de teste para o sistema VitrineZap + KMN
Cria agentes, clientes, produtos, ofertas e trustlines para demonstração
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
    Categoria, Produto, EstoqueItem, Oferta, TrustlineKeeper,
    RoleStats, EnderecoEntrega, Empresa
)

def criar_dados_teste():
    """Cria estrutura completa de dados para teste do KMN"""
    
    print("CRIANDO DADOS DE TESTE - VitrineZap + KMN")
    print("=" * 50)
    
    # 1. CRIAR EMPRESA BASE
    print("\nCriando empresa base...")
    empresa, created = Empresa.objects.get_or_create(
        nome="EVORA Marketplace",
        defaults={
            'cnpj': '12.345.678/0001-90',
            'endereco': 'Rua das Startups, 123',
            'telefone': '(11) 99999-0000',
            'email': 'contato@evora.com'
        }
    )
    
    # 2. CRIAR CATEGORIAS
    print("Criando categorias...")
    categorias = {}
    cat_data = [
        ('Eletrônicos', 'Smartphones, tablets, acessórios'),
        ('Moda', 'Roupas, calçados, acessórios'),
        ('Casa & Jardim', 'Decoração, utensílios, plantas'),
        ('Esporte', 'Equipamentos esportivos e fitness')
    ]
    
    for nome, desc in cat_data:
        cat, created = Categoria.objects.get_or_create(
            nome=nome,
            defaults={'descricao': desc}
        )
        categorias[nome] = cat
        if created:
            print(f"  OK Categoria: {nome}")
    
    # 3. CRIAR USUÁRIOS E AGENTES
    print("\nCriando agentes...")
    
    # AGENTE 1: SHOPPER PURO (Júnior - São Paulo)
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
            'bio': 'Especialista em eletrônicos e gadgets. Atua em São Paulo.',
            'ativo': True
        }
    )
    
    # Agente KMN para Júnior
    agente_junior, created = Agente.objects.get_or_create(
        user=user_junior,
        defaults={
            'personal_shopper': ps_junior,
            'nome_comercial': 'Junior Tech SP',
            'bio_agente': 'Shopper especializado em tecnologia. Forte em São Paulo e região.',
            'ativo_como_shopper': True,
            'ativo_como_keeper': False,
            'score_shopper': Decimal('8.5'),
            'score_keeper': Decimal('3.0'),
            'verificado_kmn': True
        }
    )
    if created:
        print("  OK Junior Santos (Shopper) - São Paulo")
    
    # AGENTE 2: KEEPER PURO (Márcia - Rio de Janeiro)
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
            'endereco': 'Rua das Flores, 456 - Copacabana, RJ',
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
            'bio_agente': 'Keeper com foco em moda e lifestyle. Base no Rio de Janeiro.',
            'ativo_como_shopper': False,
            'ativo_como_keeper': True,
            'score_shopper': Decimal('4.0'),
            'score_keeper': Decimal('9.2'),
            'verificado_kmn': True
        }
    )
    if created:
        print("  OK Marcia Silva (Keeper) - Rio de Janeiro")
    
    # AGENTE 3: SHOPPER-KEEPER HÍBRIDO (Ana - Belo Horizonte)
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
            'bio': 'Personal Shopper e Keeper híbrida. Especialista em casa e decoração.',
            'ativo': True
        }
    )
    
    keeper_ana, created = Keeper.objects.get_or_create(
        user=user_ana,
        defaults={
            'nome': 'Ana Costa - BH',
            'endereco': 'Av. Afonso Pena, 789 - Centro, BH',
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
            'bio_agente': 'Agente completa: compra, guarda e entrega. Especialista em casa e decoração.',
            'ativo_como_shopper': True,
            'ativo_como_keeper': True,
            'score_shopper': Decimal('7.8'),
            'score_keeper': Decimal('8.1'),
            'verificado_kmn': True
        }
    )
    if created:
        print("  OK Ana Costa (Shopper-Keeper) - Belo Horizonte")
    
    # 4. CRIAR CLIENTES
    print("\nCriando clientes...")
    
    clientes_data = [
        {
            'username': 'joao_cliente',
            'first_name': 'Joao',
            'last_name': 'Oliveira',
            'email': 'joao@cliente.com',
            'telefone': '(11) 91111-1111',
            'endereco': 'Rua A, 100 - Vila Madalena, SP'
        },
        {
            'username': 'maria_cliente',
            'first_name': 'Maria',
            'last_name': 'Santos',
            'email': 'maria@cliente.com',
            'telefone': '(21) 92222-2222',
            'endereco': 'Av. Atlantica, 200 - Copacabana, RJ'
        },
        {
            'username': 'pedro_cliente',
            'first_name': 'Pedro',
            'last_name': 'Lima',
            'email': 'pedro@cliente.com',
            'telefone': '(31) 93333-3333',
            'endereco': 'Rua B, 300 - Savassi, BH'
        },
        {
            'username': 'carla_cliente',
            'first_name': 'Carla',
            'last_name': 'Ferreira',
            'email': 'carla@cliente.com',
            'telefone': '(11) 94444-4444',
            'endereco': 'Rua C, 400 - Jardins, SP'
        },
        {
            'username': 'roberto_cliente',
            'first_name': 'Roberto',
            'last_name': 'Alves',
            'email': 'roberto@cliente.com',
            'telefone': '(21) 95555-5555',
            'endereco': 'Rua D, 500 - Ipanema, RJ'
        }
    ]
    
    clientes = {}
    for cliente_data in clientes_data:
        # Criar usuário
        user_cliente, created = User.objects.get_or_create(
            username=cliente_data['username'],
            defaults={
                'first_name': cliente_data['first_name'],
                'last_name': cliente_data['last_name'],
                'email': cliente_data['email']
            }
        )
        if created:
            user_cliente.set_password('123456')
            user_cliente.save()
        
        # Criar cliente
        cliente, created = Cliente.objects.get_or_create(
            user=user_cliente,
            defaults={
                'telefone': cliente_data['telefone'],
                'data_nascimento': timezone.now().date() - timedelta(days=365*30)
            }
        )
        
        clientes[cliente_data['username']] = cliente
        
        if created:
            print(f"  OK {cliente_data['first_name']} {cliente_data['last_name']}")
    
    # 5. CRIAR RELAÇÕES CLIENTE-AGENTE
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
    
    # Carla - Cliente em múltiplas carteiras
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
            'forca_relacao': Decimal('72.0'),
            'total_pedidos': 8,
            'ultimo_contato': timezone.now() - timedelta(days=4)
        }
    )
    
    print("  OK Relações cliente-agente criadas")
    
    # 6. CRIAR PRODUTOS
    print("\nCriando produtos...")
    
    produtos_data = [
        {
            'nome': 'iPhone 15 Pro 128GB',
            'categoria': categorias['Eletrônicos'],
            'descricao': 'iPhone 15 Pro com 128GB, cor Natural Titanium',
            'preco_referencia': Decimal('7999.00'),
            'sku': 'IPH15P-128-NT'
        },
        {
            'nome': 'Samsung Galaxy S24 Ultra',
            'categoria': categorias['Eletrônicos'],
            'descricao': 'Galaxy S24 Ultra 256GB, cor Titanium Black',
            'preco_referencia': Decimal('6499.00'),
            'sku': 'SGS24U-256-TB'
        },
        {
            'nome': 'Vestido Floral Primavera',
            'categoria': categorias['Moda'],
            'descricao': 'Vestido midi floral, tecido viscose, tamanho M',
            'preco_referencia': Decimal('189.90'),
            'sku': 'VEST-FLOR-M'
        },
        {
            'nome': 'Tenis Nike Air Max 270',
            'categoria': categorias['Moda'],
            'descricao': 'Tenis Nike Air Max 270, cor branco/preto, tamanho 42',
            'preco_referencia': Decimal('599.90'),
            'sku': 'NIKE-AM270-42'
        }
    ]
    
    produtos = {}
    for prod_data in produtos_data:
        produto, created = Produto.objects.get_or_create(
            sku=prod_data['sku'],
            defaults={
                'nome': prod_data['nome'],
                'categoria': prod_data['categoria'],
                'descricao': prod_data['descricao'],
                'preco': prod_data['preco_referencia'],
                'ativo': True
            }
        )
        produtos[prod_data['sku']] = produto
        
        if created:
            print(f"  OK {prod_data['nome']}")
    
    # 7. CRIAR TRUSTLINES
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
    
    print("  OK Trustlines criadas")
    
    print("\n" + "=" * 50)
    print("DADOS DE TESTE CRIADOS COM SUCESSO!")
    print("=" * 50)
    
    # RESUMO
    print("\nRESUMO DOS DADOS CRIADOS:")
    print(f"Agentes: {Agente.objects.count()}")
    print(f"Clientes: {Cliente.objects.count()}")
    print(f"Relações Cliente-Agente: {ClienteRelacao.objects.count()}")
    print(f"Produtos: {Produto.objects.count()}")
    print(f"Trustlines: {TrustlineKeeper.objects.count()}")
    
    print("\nCREDENCIAIS DE TESTE:")
    print("Todos os usuários têm senha: 123456")
    print("- junior_sp (Shopper)")
    print("- marcia_rj (Keeper)")
    print("- ana_bh (Shopper-Keeper)")
    print("- joao_cliente, maria_cliente, pedro_cliente, carla_cliente, roberto_cliente")
    
    print("\nPROXIMOS PASSOS:")
    print("1. Acesse: http://127.0.0.1:8000/kmn/")
    print("2. Faça login com qualquer agente")
    print("3. Explore o dashboard KMN")
    
    return True

if __name__ == '__main__':
    try:
        criar_dados_teste()
    except Exception as e:
        print(f"ERRO ao criar dados: {e}")
        import traceback
        traceback.print_exc()
