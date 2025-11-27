#!/usr/bin/env python
"""
Script simplificado para criar dados de teste do VitrineZap + KMN
"""
import os
import django

# Configura o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

from app_marketplace.models import (
    Empresa, Categoria, Produto, Cliente, PersonalShopper, Keeper, 
    EnderecoEntrega, Agente, ClienteRelacao, EstoqueItem, Oferta, 
    TrustlineKeeper, RoleStats
)

def criar_dados():
    print("CRIANDO DADOS DE TESTE - VitrineZap KMN")
    print("=" * 50)
    
    # 1. EMPRESA
    try:
        empresa = Empresa.objects.get(nome="EVORA")
    except Empresa.DoesNotExist:
        empresa, created = Empresa.objects.get_or_create(
            cnpj='98.765.432/0001-10',
            defaults={
                'nome': 'EVORA',
                'telefone': '(11) 99999-0000',
                'email': 'contato@evora.com.br'
            }
        )
    print(f"OK Empresa: {empresa.nome}")
    
    # 2. CATEGORIAS
    categoria_eletronicos, created = Categoria.objects.get_or_create(
        nome='Eletronicos',
        defaults={'descricao': 'Smartphones, tablets, acessorios'}
    )
    
    categoria_moda, created = Categoria.objects.get_or_create(
        nome='Moda Feminina',
        defaults={'descricao': 'Roupas, sapatos, acessorios'}
    )
    
    print("OK Categorias criadas")
    
    # 3. USUARIOS E AGENTES
    
    # Shopper-Keeper: Junior (SP)
    user_junior, created = User.objects.get_or_create(
        username='junior_sp',
        defaults={
            'first_name': 'Junior',
            'last_name': 'Santos',
            'email': 'junior@vitrinezap.com',
            'is_active': True
        }
    )
    if created:
        user_junior.set_password('123456')
        user_junior.save()
    
    shopper_junior, created = PersonalShopper.objects.get_or_create(
        user=user_junior,
        defaults={
            'nome': 'Junior Santos - SP',
            'telefone': '(11) 99999-1111',
            'especialidade': 'Eletronicos e Moda',
            'ativo': True,
            'taxa_comissao': Decimal('15.00')
        }
    )
    
    agente_junior, created = Agente.objects.get_or_create(
        user=user_junior,
        defaults={
            'personal_shopper': shopper_junior,
            'nome_comercial': 'Junior Tech SP',
            'bio_agente': 'Especialista em eletronicos e moda em Sao Paulo',
            'score_keeper': Decimal('7.5'),
            'score_shopper': Decimal('9.2'),
            'ativo_como_shopper': True,
            'ativo_como_keeper': True,
            'verificado_kmn': True
        }
    )
    print(f"OK Shopper-Keeper: {agente_junior.nome_comercial}")
    
    # Keeper: Marcia (RJ)
    user_marcia, created = User.objects.get_or_create(
        username='marcia_rj',
        defaults={
            'first_name': 'Marcia',
            'last_name': 'Silva',
            'email': 'marcia@vitrinezap.com',
            'is_active': True
        }
    )
    if created:
        user_marcia.set_password('123456')
        user_marcia.save()
    
    keeper_marcia, created = Keeper.objects.get_or_create(
        user=user_marcia,
        defaults={
            'apelido_local': 'Marcia Silva - RJ',
            'rua': 'Rua das Flores, 456',
            'bairro': 'Copacabana',
            'cidade': 'Rio de Janeiro',
            'estado': 'RJ',
            'capacidade_itens': 500,
            'ativo': True
        }
    )
    
    agente_marcia, created = Agente.objects.get_or_create(
        user=user_marcia,
        defaults={
            'keeper': keeper_marcia,
            'nome_comercial': 'Marcia Store RJ',
            'bio_agente': 'Keeper especializada em moda feminina no Rio',
            'score_keeper': Decimal('9.8'),
            'score_shopper': Decimal('6.5'),
            'ativo_como_keeper': True,
            'ativo_como_shopper': False,
            'verificado_kmn': True
        }
    )
    print(f"OK Keeper: {agente_marcia.nome_comercial}")
    
    # Shopper: Ana (BH)
    user_ana, created = User.objects.get_or_create(
        username='ana_bh',
        defaults={
            'first_name': 'Ana',
            'last_name': 'Costa',
            'email': 'ana@vitrinezap.com',
            'is_active': True
        }
    )
    if created:
        user_ana.set_password('123456')
        user_ana.save()
    
    shopper_ana, created = PersonalShopper.objects.get_or_create(
        user=user_ana,
        defaults={
            'nome': 'Ana Costa - BH',
            'telefone': '(31) 99999-3333',
            'especialidade': 'Casa e Decoracao',
            'ativo': True,
            'taxa_comissao': Decimal('12.00')
        }
    )
    
    agente_ana, created = Agente.objects.get_or_create(
        user=user_ana,
        defaults={
            'personal_shopper': shopper_ana,
            'nome_comercial': 'Ana Decor BH',
            'bio_agente': 'Especialista em casa e decoracao em BH',
            'score_keeper': Decimal('5.0'),
            'score_shopper': Decimal('8.7'),
            'ativo_como_shopper': True,
            'ativo_como_keeper': False,
            'verificado_kmn': True
        }
    )
    print(f"OK Shopper: {agente_ana.nome_comercial}")
    
    # 4. CLIENTES
    clientes = []
    
    # Cliente 1: Joao
    user_joao, created = User.objects.get_or_create(
        username='joao_cliente',
        defaults={
            'first_name': 'Joao',
            'last_name': 'Oliveira',
            'email': 'joao@cliente.com',
            'is_active': True
        }
    )
    if created:
        user_joao.set_password('123456')
        user_joao.save()
    
    cliente_joao, created = Cliente.objects.get_or_create(
        user=user_joao,
        defaults={
            'telefone': '(11) 98888-1111',
            'data_nascimento': timezone.now().date() - timedelta(days=10000)
        }
    )
    clientes.append(cliente_joao)
    
    # Cliente 2: Maria
    user_maria, created = User.objects.get_or_create(
        username='maria_cliente',
        defaults={
            'first_name': 'Maria',
            'last_name': 'Santos',
            'email': 'maria@cliente.com',
            'is_active': True
        }
    )
    if created:
        user_maria.set_password('123456')
        user_maria.save()
    
    cliente_maria, created = Cliente.objects.get_or_create(
        user=user_maria,
        defaults={
            'telefone': '(21) 98888-2222',
            'data_nascimento': timezone.now().date() - timedelta(days=9000)
        }
    )
    clientes.append(cliente_maria)
    
    # Cliente 3: Pedro
    user_pedro, created = User.objects.get_or_create(
        username='pedro_cliente',
        defaults={
            'first_name': 'Pedro',
            'last_name': 'Lima',
            'email': 'pedro@cliente.com',
            'is_active': True
        }
    )
    if created:
        user_pedro.set_password('123456')
        user_pedro.save()
    
    cliente_pedro, created = Cliente.objects.get_or_create(
        user=user_pedro,
        defaults={
            'telefone': '(31) 98888-3333',
            'data_nascimento': timezone.now().date() - timedelta(days=8000)
        }
    )
    clientes.append(cliente_pedro)
    
    # Cliente 4: Carla
    user_carla, created = User.objects.get_or_create(
        username='carla_cliente',
        defaults={
            'first_name': 'Carla',
            'last_name': 'Ferreira',
            'email': 'carla@cliente.com',
            'is_active': True
        }
    )
    if created:
        user_carla.set_password('123456')
        user_carla.save()
    
    cliente_carla, created = Cliente.objects.get_or_create(
        user=user_carla,
        defaults={
            'telefone': '(11) 98888-4444',
            'data_nascimento': timezone.now().date() - timedelta(days=7500)
        }
    )
    clientes.append(cliente_carla)
    
    # Cliente 5: Lucas
    user_lucas, created = User.objects.get_or_create(
        username='lucas_cliente',
        defaults={
            'first_name': 'Lucas',
            'last_name': 'Rocha',
            'email': 'lucas@cliente.com',
            'is_active': True
        }
    )
    if created:
        user_lucas.set_password('123456')
        user_lucas.save()
    
    cliente_lucas, created = Cliente.objects.get_or_create(
        user=user_lucas,
        defaults={
            'telefone': '(21) 98888-5555',
            'data_nascimento': timezone.now().date() - timedelta(days=7000)
        }
    )
    clientes.append(cliente_lucas)
    
    print("OK 5 Clientes criados")
    
    # 5. RELACOES CLIENTE-AGENTE
    
    # Joao - Primario do Junior
    ClienteRelacao.objects.get_or_create(
        cliente=cliente_joao,
        agente=agente_junior,
        defaults={
            'forca_relacao': Decimal('85.5'),
            'total_pedidos': 12,
            'ultimo_pedido': timezone.now() - timedelta(days=5),
            'status': 'ativa'
        }
    )
    
    # Maria - Primaria da Marcia
    ClienteRelacao.objects.get_or_create(
        cliente=cliente_maria,
        agente=agente_marcia,
        defaults={
            'forca_relacao': Decimal('92.8'),
            'total_pedidos': 18,
            'ultimo_pedido': timezone.now() - timedelta(days=2),
            'status': 'ativa'
        }
    )
    
    # Pedro - Primario da Ana
    ClienteRelacao.objects.get_or_create(
        cliente=cliente_pedro,
        agente=agente_ana,
        defaults={
            'forca_relacao': Decimal('78.3'),
            'total_pedidos': 8,
            'ultimo_pedido': timezone.now() - timedelta(days=10),
            'status': 'ativa'
        }
    )
    
    # Carla - Compartilhada (Junior primario)
    ClienteRelacao.objects.get_or_create(
        cliente=cliente_carla,
        agente=agente_junior,
        defaults={
            'forca_relacao': Decimal('65.7'),
            'total_pedidos': 6,
            'ultimo_pedido': timezone.now() - timedelta(days=15),
            'status': 'ativa'
        }
    )
    
    ClienteRelacao.objects.get_or_create(
        cliente=cliente_carla,
        agente=agente_ana,
        defaults={
            'forca_relacao': Decimal('58.9'),
            'total_pedidos': 4,
            'ultimo_pedido': timezone.now() - timedelta(days=20),
            'status': 'ativa'
        }
    )
    
    # Lucas - Compartilhado (Marcia primaria)
    ClienteRelacao.objects.get_or_create(
        cliente=cliente_lucas,
        agente=agente_marcia,
        defaults={
            'forca_relacao': Decimal('72.1'),
            'total_pedidos': 9,
            'ultimo_pedido': timezone.now() - timedelta(days=8),
            'status': 'ativa'
        }
    )
    
    ClienteRelacao.objects.get_or_create(
        cliente=cliente_lucas,
        agente=agente_junior,
        defaults={
            'forca_relacao': Decimal('68.4'),
            'total_pedidos': 7,
            'ultimo_pedido': timezone.now() - timedelta(days=12),
            'status': 'ativa'
        }
    )
    
    print("OK Relacoes Cliente-Agente criadas")
    
    # 6. TRUSTLINES
    
    # Junior <-> Marcia
    TrustlineKeeper.objects.get_or_create(
        agente_a=agente_junior,
        agente_b=agente_marcia,
        defaults={
            'nivel_confianca': Decimal('88.5'),
            'perc_shopper': Decimal('65.0'),
            'perc_keeper': Decimal('35.0'),
            'ativo': True
        }
    )
    
    # Junior <-> Ana
    TrustlineKeeper.objects.get_or_create(
        agente_a=agente_junior,
        agente_b=agente_ana,
        defaults={
            'nivel_confianca': Decimal('76.2'),
            'perc_shopper': Decimal('60.0'),
            'perc_keeper': Decimal('40.0'),
            'ativo': True
        }
    )
    
    # Marcia <-> Ana
    TrustlineKeeper.objects.get_or_create(
        agente_a=agente_marcia,
        agente_b=agente_ana,
        defaults={
            'nivel_confianca': Decimal('82.7'),
            'perc_shopper': Decimal('55.0'),
            'perc_keeper': Decimal('45.0'),
            'ativo': True
        }
    )
    
    print("OK Trustlines criadas")
    
    # 7. PRODUTOS
    
    # iPhone - Junior tem
    produto_iphone, created = Produto.objects.get_or_create(
        nome='iPhone 15 Pro 256GB',
        defaults={
            'categoria': categoria_eletronicos,
            'descricao': 'Smartphone Apple iPhone 15 Pro com 256GB',
            'preco': Decimal('6999.00'),
            'ativo': True
        }
    )
    
    EstoqueItem.objects.get_or_create(
        produto=produto_iphone,
        agente=agente_junior,
        defaults={
            'quantidade_disponivel': 3,
            'preco_custo': Decimal('4899.30'),
            'localizacao': 'Estoque Junior SP'
        }
    )
    
    # Vestido - Marcia tem
    produto_vestido, created = Produto.objects.get_or_create(
        nome='Vestido Floral Verao',
        defaults={
            'categoria': categoria_moda,
            'descricao': 'Vestido floral leve para o verao, tamanho M',
            'preco': Decimal('189.90'),
            'ativo': True
        }
    )
    
    EstoqueItem.objects.get_or_create(
        produto=produto_vestido,
        agente=agente_marcia,
        defaults={
            'quantidade_disponivel': 5,
            'preco_custo': Decimal('132.93'),
            'localizacao': 'Estoque Marcia RJ'
        }
    )
    
    print("OK Produtos e estoque criados")
    
    # 8. OFERTAS COM MARKUP
    
    # iPhone - Junior oferece por 6999, Marcia revende por 7299
    Oferta.objects.get_or_create(
        produto=produto_iphone,
        agente_origem=agente_junior,
        agente_ofertante=agente_junior,
        defaults={
            'preco_base': Decimal('6999.00'),
            'preco_oferta': Decimal('6999.00'),
            'quantidade_disponivel': 3,
            'ativo': True
        }
    )
    
    Oferta.objects.get_or_create(
        produto=produto_iphone,
        agente_origem=agente_junior,
        agente_ofertante=agente_marcia,
        defaults={
            'preco_base': Decimal('6999.00'),
            'preco_oferta': Decimal('7299.00'),  # Markup de R$ 300
            'quantidade_disponivel': 3,
            'ativo': True,
            'exclusiva_para_clientes': True
        }
    )
    
    # Vestido - Marcia oferece por 189.90, Ana revende por 219.90
    Oferta.objects.get_or_create(
        produto=produto_vestido,
        agente_origem=agente_marcia,
        agente_ofertante=agente_marcia,
        defaults={
            'preco_base': Decimal('189.90'),
            'preco_oferta': Decimal('189.90'),
            'quantidade_disponivel': 5,
            'ativo': True
        }
    )
    
    Oferta.objects.get_or_create(
        produto=produto_vestido,
        agente_origem=agente_marcia,
        agente_ofertante=agente_ana,
        defaults={
            'preco_base': Decimal('189.90'),
            'preco_oferta': Decimal('219.90'),  # Markup de R$ 30
            'quantidade_disponivel': 5,
            'ativo': True,
            'exclusiva_para_clientes': True
        }
    )
    
    print("OK Ofertas com markup criadas")
    
    # 9. ROLE STATS
    for agente in [agente_junior, agente_marcia, agente_ana]:
        RoleStats.objects.get_or_create(
            agente=agente,
            defaults={
                'pedidos_como_keeper': 10,
                'pedidos_como_shopper': 8,
                'receita_como_keeper': Decimal('2500.00'),
                'receita_como_shopper': Decimal('1800.00'),
                'score_medio_avaliacoes': Decimal('4.5'),
                'total_avaliacoes': 25
            }
        )
    
    print("OK Role Stats criadas")
    
    # RESUMO FINAL
    print("\n" + "=" * 50)
    print("DADOS DE TESTE CRIADOS COM SUCESSO!")
    print("=" * 50)
    
    print("\nAGENTES:")
    print(f"  Junior Santos (junior_sp/123456) - Shopper-Keeper SP")
    print(f"  Marcia Silva (marcia_rj/123456) - Keeper RJ")
    print(f"  Ana Costa (ana_bh/123456) - Shopper BH")
    
    print("\nCLIENTES:")
    print(f"  Joao (joao_cliente/123456) - Primario do Junior")
    print(f"  Maria (maria_cliente/123456) - Primaria da Marcia")
    print(f"  Pedro (pedro_cliente/123456) - Primario da Ana")
    print(f"  Carla (carla_cliente/123456) - Compartilhada (Junior>Ana)")
    print(f"  Lucas (lucas_cliente/123456) - Compartilhado (Marcia>Junior)")
    
    print("\nPRODUTOS COM MARKUP:")
    print(f"  iPhone 15 Pro - Junior: R$ 6.999 | Marcia: R$ 7.299 (+R$ 300)")
    print(f"  Vestido Floral - Marcia: R$ 189,90 | Ana: R$ 219,90 (+R$ 30)")
    
    print("\nTRUSTLINES:")
    print(f"  Junior <-> Marcia (Confianca: 88.5%)")
    print(f"  Junior <-> Ana (Confianca: 76.2%)")
    print(f"  Marcia <-> Ana (Confianca: 82.7%)")
    
    print("\nPARA TESTAR:")
    print("  1. Acesse: http://127.0.0.1:8000/login/")
    print("  2. Login com junior_sp/123456")
    print("  3. Va no menu KMN > Dashboard KMN")
    print("  4. Explore ofertas, trustlines e clientes")
    
    return True

if __name__ == '__main__':
    try:
        criar_dados()
    except Exception as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()
