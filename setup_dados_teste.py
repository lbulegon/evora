#!/usr/bin/env python
"""
Script para criar dados de teste do VitrineZap + KMN
Cria perfis, clientes, produtos, ofertas e trustlines para demonstração
"""
import os
import sys
import django
from decimal import Decimal
from datetime import timedelta
import random

# Configura o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

# Agora importa os modelos Django
from django.contrib.auth.models import User
from django.utils import timezone

from app_marketplace.models import (
    Empresa, Categoria, Produto, Cliente, PersonalShopper, Keeper, 
    EnderecoEntrega, Agente, ClienteRelacao, EstoqueItem, Oferta, 
    TrustlineKeeper, RoleStats, Pedido, ItemPedido
)

def criar_dados_teste():
    """Cria estrutura completa de dados para teste do KMN"""
    
    print("CRIANDO DADOS DE TESTE - VitrineZap KMN")
    print("=" * 50)
    
    # ============================================================================
    # 1. CRIAR EMPRESA BASE
    # ============================================================================
    
    empresa, created = Empresa.objects.get_or_create(
        nome="ÉVORA",
        defaults={
            'cnpj': '12.345.678/0001-90',
            'endereco': 'Rua da Inovação, 123',
            'telefone': '(11) 99999-0000',
            'email': 'contato@evora.com.br'
        }
    )
    print(f"OK Empresa: {empresa.nome}")
    
    # ============================================================================
    # 2. CRIAR CATEGORIAS
    # ============================================================================
    
    categorias_data = [
        {'nome': 'Eletrônicos', 'descricao': 'Smartphones, tablets, acessórios'},
        {'nome': 'Moda Feminina', 'descricao': 'Roupas, sapatos, acessórios'},
        {'nome': 'Casa e Decoração', 'descricao': 'Móveis, decoração, utilidades'},
        {'nome': 'Esporte e Lazer', 'descricao': 'Equipamentos esportivos, jogos'},
        {'nome': 'Beleza e Cuidados', 'descricao': 'Cosméticos, perfumes, cuidados'}
    ]
    
    categorias = {}
    for cat_data in categorias_data:
        categoria, created = Categoria.objects.get_or_create(
            nome=cat_data['nome'],
            defaults={'descricao': cat_data['descricao']}
        )
        categorias[cat_data['nome']] = categoria
        print(f"✅ Categoria: {categoria.nome}")
    
    # ============================================================================
    # 3. CRIAR USUÁRIOS E PERFIS
    # ============================================================================
    
    # 3.1 SHOPPER (Júnior - São Paulo)
    user_junior, created = User.objects.get_or_create(
        username='junior_sp',
        defaults={
            'first_name': 'Júnior',
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
            'nome': 'Júnior Santos - SP',
            'telefone': '(11) 99999-1111',
            'especialidade': 'Eletrônicos e Moda',
            'ativo': True,
            'taxa_comissao': Decimal('15.00')
        }
    )
    
    agente_junior, created = Agente.objects.get_or_create(
        user=user_junior,
        defaults={
            'personal_shopper': shopper_junior,
            'nome_comercial': 'Júnior Tech SP',
            'bio_agente': 'Especialista em eletrônicos e moda em São Paulo',
            'score_keeper': Decimal('7.5'),
            'score_shopper': Decimal('9.2'),
            'ativo_como_shopper': True,
            'ativo_como_keeper': True,
            'verificado_kmn': True
        }
    )
    print(f"✅ Shopper-Keeper: {agente_junior.nome_comercial}")
    
    # 3.2 KEEPER (Márcia - Rio de Janeiro)
    user_marcia, created = User.objects.get_or_create(
        username='marcia_rj',
        defaults={
            'first_name': 'Márcia',
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
            'nome': 'Márcia Silva - RJ',
            'endereco': 'Rua das Flores, 456 - Copacabana',
            'telefone': '(21) 99999-2222',
            'capacidade_armazenamento': 500,
            'ativo': True
        }
    )
    
    agente_marcia, created = Agente.objects.get_or_create(
        user=user_marcia,
        defaults={
            'keeper': keeper_marcia,
            'nome_comercial': 'Márcia Store RJ',
            'bio_agente': 'Keeper especializada em moda feminina e beleza no Rio',
            'score_keeper': Decimal('9.8'),
            'score_shopper': Decimal('6.5'),
            'ativo_como_keeper': True,
            'ativo_como_shopper': False,
            'verificado_kmn': True
        }
    )
    print(f"✅ Keeper: {agente_marcia.nome_comercial}")
    
    # 3.3 SHOPPER PURO (Ana - Belo Horizonte)
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
            'especialidade': 'Casa, Decoração e Esportes',
            'ativo': True,
            'taxa_comissao': Decimal('12.00')
        }
    )
    
    agente_ana, created = Agente.objects.get_or_create(
        user=user_ana,
        defaults={
            'personal_shopper': shopper_ana,
            'nome_comercial': 'Ana Decor BH',
            'bio_agente': 'Especialista em casa, decoração e esportes em BH',
            'score_keeper': Decimal('5.0'),
            'score_shopper': Decimal('8.7'),
            'ativo_como_shopper': True,
            'ativo_como_keeper': False,
            'verificado_kmn': True
        }
    )
    print(f"✅ Shopper: {agente_ana.nome_comercial}")
    
    # ============================================================================
    # 4. CRIAR CLIENTES
    # ============================================================================
    
    clientes_data = [
        {
            'username': 'joao_cliente',
            'first_name': 'João',
            'last_name': 'Oliveira',
            'email': 'joao@cliente.com',
            'telefone': '(11) 98888-1111',
            'endereco': 'Rua A, 100 - São Paulo/SP',
            'cep': '01234-567'
        },
        {
            'username': 'maria_cliente',
            'first_name': 'Maria',
            'last_name': 'Santos',
            'email': 'maria@cliente.com',
            'telefone': '(21) 98888-2222',
            'endereco': 'Av. B, 200 - Rio de Janeiro/RJ',
            'cep': '20123-456'
        },
        {
            'username': 'pedro_cliente',
            'first_name': 'Pedro',
            'last_name': 'Lima',
            'email': 'pedro@cliente.com',
            'telefone': '(31) 98888-3333',
            'endereco': 'Rua C, 300 - Belo Horizonte/MG',
            'cep': '30123-789'
        },
        {
            'username': 'carla_cliente',
            'first_name': 'Carla',
            'last_name': 'Ferreira',
            'email': 'carla@cliente.com',
            'telefone': '(11) 98888-4444',
            'endereco': 'Av. D, 400 - São Paulo/SP',
            'cep': '04567-890'
        },
        {
            'username': 'lucas_cliente',
            'first_name': 'Lucas',
            'last_name': 'Rocha',
            'email': 'lucas@cliente.com',
            'telefone': '(21) 98888-5555',
            'endereco': 'Rua E, 500 - Rio de Janeiro/RJ',
            'cep': '22345-123'
        }
    ]
    
    clientes = []
    for cliente_data in clientes_data:
        # Criar usuário
        user_cliente, created = User.objects.get_or_create(
            username=cliente_data['username'],
            defaults={
                'first_name': cliente_data['first_name'],
                'last_name': cliente_data['last_name'],
                'email': cliente_data['email'],
                'is_active': True
            }
        )
        if created:
            user_cliente.set_password('123456')
            user_cliente.save()
        
        # Criar perfil de cliente
        cliente, created = Cliente.objects.get_or_create(
            user=user_cliente,
            defaults={
                'telefone': cliente_data['telefone'],
                'data_nascimento': timezone.now().date() - timedelta(days=random.randint(7000, 15000))
            }
        )
        
        # Criar endereço
        endereco, created = EnderecoEntrega.objects.get_or_create(
            cliente=cliente,
            defaults={
                'nome': f"Casa {cliente_data['first_name']}",
                'endereco': cliente_data['endereco'],
                'cep': cliente_data['cep'],
                'cidade': cliente_data['endereco'].split(' - ')[1].split('/')[0],
                'estado': cliente_data['endereco'].split('/')[-1],
                'principal': True
            }
        )
        
        clientes.append(cliente)
        print(f"✅ Cliente: {cliente.user.get_full_name()}")
    
    # ============================================================================
    # 5. CRIAR RELAÇÕES CLIENTE-AGENTE
    # ============================================================================
    
    # João (SP) - Primário do Júnior, Secundário da Márcia
    ClienteRelacao.objects.get_or_create(
        cliente=clientes[0],  # João
        agente=agente_junior,
        defaults={
            'forca_relacao': Decimal('85.5'),
            'total_pedidos': 12,
            'ultimo_pedido': timezone.now() - timedelta(days=5),
            'status': 'ativa'
        }
    )
    
    ClienteRelacao.objects.get_or_create(
        cliente=clientes[0],  # João
        agente=agente_marcia,
        defaults={
            'forca_relacao': Decimal('45.2'),
            'total_pedidos': 3,
            'ultimo_pedido': timezone.now() - timedelta(days=25),
            'status': 'ativa'
        }
    )
    
    # Maria (RJ) - Primária da Márcia
    ClienteRelacao.objects.get_or_create(
        cliente=clientes[1],  # Maria
        agente=agente_marcia,
        defaults={
            'forca_relacao': Decimal('92.8'),
            'total_pedidos': 18,
            'ultimo_pedido': timezone.now() - timedelta(days=2),
            'status': 'ativa'
        }
    )
    
    # Pedro (BH) - Primário da Ana
    ClienteRelacao.objects.get_or_create(
        cliente=clientes[2],  # Pedro
        agente=agente_ana,
        defaults={
            'forca_relacao': Decimal('78.3'),
            'total_pedidos': 8,
            'ultimo_pedido': timezone.now() - timedelta(days=10),
            'status': 'ativa'
        }
    )
    
    # Carla (SP) - Compartilhada entre Júnior e Ana
    ClienteRelacao.objects.get_or_create(
        cliente=clientes[3],  # Carla
        agente=agente_junior,
        defaults={
            'forca_relacao': Decimal('65.7'),
            'total_pedidos': 6,
            'ultimo_pedido': timezone.now() - timedelta(days=15),
            'status': 'ativa'
        }
    )
    
    ClienteRelacao.objects.get_or_create(
        cliente=clientes[3],  # Carla
        agente=agente_ana,
        defaults={
            'forca_relacao': Decimal('58.9'),
            'total_pedidos': 4,
            'ultimo_pedido': timezone.now() - timedelta(days=20),
            'status': 'ativa'
        }
    )
    
    # Lucas (RJ) - Compartilhado entre Márcia e Júnior
    ClienteRelacao.objects.get_or_create(
        cliente=clientes[4],  # Lucas
        agente=agente_marcia,
        defaults={
            'forca_relacao': Decimal('72.1'),
            'total_pedidos': 9,
            'ultimo_pedido': timezone.now() - timedelta(days=8),
            'status': 'ativa'
        }
    )
    
    ClienteRelacao.objects.get_or_create(
        cliente=clientes[4],  # Lucas
        agente=agente_junior,
        defaults={
            'forca_relacao': Decimal('68.4'),
            'total_pedidos': 7,
            'ultimo_pedido': timezone.now() - timedelta(days=12),
            'status': 'ativa'
        }
    )
    
    print("✅ Relações Cliente-Agente criadas")
    
    # ============================================================================
    # 6. CRIAR TRUSTLINES
    # ============================================================================
    
    # Trustline Júnior ↔ Márcia
    trustline_jm, created = TrustlineKeeper.objects.get_or_create(
        agente_a=agente_junior,
        agente_b=agente_marcia,
        defaults={
            'nivel_confianca': Decimal('88.5'),
            'perc_shopper': Decimal('65.0'),
            'perc_keeper': Decimal('35.0'),
            'ativo': True,
            'regras_adicionais': {
                'categoria_preferida': 'Moda Feminina',
                'limite_valor': 1000.00,
                'prazo_envio': 2
            }
        }
    )
    
    # Trustline Júnior ↔ Ana
    trustline_ja, created = TrustlineKeeper.objects.get_or_create(
        agente_a=agente_junior,
        agente_b=agente_ana,
        defaults={
            'nivel_confianca': Decimal('76.2'),
            'perc_shopper': Decimal('60.0'),
            'perc_keeper': Decimal('40.0'),
            'ativo': True,
            'regras_adicionais': {
                'categoria_preferida': 'Casa e Decoração',
                'limite_valor': 800.00,
                'prazo_envio': 3
            }
        }
    )
    
    # Trustline Márcia ↔ Ana
    trustline_ma, created = TrustlineKeeper.objects.get_or_create(
        agente_a=agente_marcia,
        agente_b=agente_ana,
        defaults={
            'nivel_confianca': Decimal('82.7'),
            'perc_shopper': Decimal('55.0'),
            'perc_keeper': Decimal('45.0'),
            'ativo': True,
            'regras_adicionais': {
                'categoria_preferida': 'Beleza e Cuidados',
                'limite_valor': 600.00,
                'prazo_envio': 4
            }
        }
    )
    
    print("✅ Trustlines criadas")
    
    # ============================================================================
    # 7. CRIAR PRODUTOS
    # ============================================================================
    
    produtos_data = [
        {
            'nome': 'iPhone 15 Pro 256GB',
            'categoria': 'Eletrônicos',
            'descricao': 'Smartphone Apple iPhone 15 Pro com 256GB de armazenamento',
            'preco': Decimal('6999.00'),
            'agente_estoque': agente_junior,
            'quantidade': 3
        },
        {
            'nome': 'Vestido Floral Verão',
            'categoria': 'Moda Feminina',
            'descricao': 'Vestido floral leve para o verão, tamanho M',
            'preco': Decimal('189.90'),
            'agente_estoque': agente_marcia,
            'quantidade': 5
        },
        {
            'nome': 'Sofá 3 Lugares Cinza',
            'categoria': 'Casa e Decoração',
            'descricao': 'Sofá moderno de 3 lugares na cor cinza',
            'preco': Decimal('1299.00'),
            'agente_estoque': agente_ana,
            'quantidade': 2
        },
        {
            'nome': 'Tênis Nike Air Max',
            'categoria': 'Esporte e Lazer',
            'descricao': 'Tênis Nike Air Max para corrida, tamanho 42',
            'preco': Decimal('459.90'),
            'agente_estoque': agente_junior,
            'quantidade': 4
        },
        {
            'nome': 'Perfume Chanel N°5',
            'categoria': 'Beleza e Cuidados',
            'descricao': 'Perfume feminino Chanel N°5, 100ml',
            'preco': Decimal('899.00'),
            'agente_estoque': agente_marcia,
            'quantidade': 6
        },
        {
            'nome': 'Smart TV 55" 4K',
            'categoria': 'Eletrônicos',
            'descricao': 'Smart TV LED 55 polegadas 4K Ultra HD',
            'preco': Decimal('2199.00'),
            'agente_estoque': agente_ana,
            'quantidade': 2
        }
    ]
    
    produtos = []
    for prod_data in produtos_data:
        # Criar produto
        produto, created = Produto.objects.get_or_create(
            nome=prod_data['nome'],
            defaults={
                'categoria': categorias[prod_data['categoria']],
                'descricao': prod_data['descricao'],
                'preco': prod_data['preco'],
                'ativo': True
            }
        )
        produtos.append(produto)
        
        # Criar item de estoque
        estoque, created = EstoqueItem.objects.get_or_create(
            produto=produto,
            agente=prod_data['agente_estoque'],
            defaults={
                'quantidade_disponivel': prod_data['quantidade'],
                'quantidade_reservada': 0,
                'preco_custo': prod_data['preco'] * Decimal('0.7'),  # 70% do preço final
                'localizacao': f"Estoque {prod_data['agente_estoque'].nome_comercial}"
            }
        )
        
        print(f"✅ Produto: {produto.nome} ({prod_data['agente_estoque'].nome_comercial})")
    
    # ============================================================================
    # 8. CRIAR OFERTAS (COM MARKUP)
    # ============================================================================
    
    # iPhone - Júnior tem o produto, Márcia revende com markup
    oferta_iphone_junior, created = Oferta.objects.get_or_create(
        produto=produtos[0],  # iPhone
        agente_origem=agente_junior,
        agente_ofertante=agente_junior,
        defaults={
            'preco_base': Decimal('6999.00'),
            'preco_oferta': Decimal('6999.00'),
            'quantidade_disponivel': 3,
            'ativo': True,
            'exclusiva_para_clientes': False
        }
    )
    
    oferta_iphone_marcia, created = Oferta.objects.get_or_create(
        produto=produtos[0],  # iPhone
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
    
    # Vestido - Márcia tem o produto, Ana revende com markup
    oferta_vestido_marcia, created = Oferta.objects.get_or_create(
        produto=produtos[1],  # Vestido
        agente_origem=agente_marcia,
        agente_ofertante=agente_marcia,
        defaults={
            'preco_base': Decimal('189.90'),
            'preco_oferta': Decimal('189.90'),
            'quantidade_disponivel': 5,
            'ativo': True,
            'exclusiva_para_clientes': False
        }
    )
    
    oferta_vestido_ana, created = Oferta.objects.get_or_create(
        produto=produtos[1],  # Vestido
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
    
    # Criar ofertas para outros produtos (sem markup para simplicidade)
    for i, produto in enumerate(produtos[2:], 2):
        agente_dono = produtos_data[i]['agente_estoque']
        oferta, created = Oferta.objects.get_or_create(
            produto=produto,
            agente_origem=agente_dono,
            agente_ofertante=agente_dono,
            defaults={
                'preco_base': produto.preco,
                'preco_oferta': produto.preco,
                'quantidade_disponivel': produtos_data[i]['quantidade'],
                'ativo': True,
                'exclusiva_para_clientes': False
            }
        )
    
    print("✅ Ofertas criadas (com markup)")
    
    # ============================================================================
    # 9. CRIAR ROLE STATS
    # ============================================================================
    
    for agente in [agente_junior, agente_marcia, agente_ana]:
        stats, created = RoleStats.objects.get_or_create(
            agente=agente,
            defaults={
                'pedidos_como_keeper': random.randint(5, 20),
                'pedidos_como_shopper': random.randint(3, 15),
                'receita_como_keeper': Decimal(random.uniform(1000, 5000)),
                'receita_como_shopper': Decimal(random.uniform(800, 4000)),
                'score_medio_avaliacoes': Decimal(random.uniform(4.2, 4.9)),
                'total_avaliacoes': random.randint(10, 50)
            }
        )
    
    print("✅ Role Stats criadas")
    
    # ============================================================================
    # 10. RESUMO FINAL
    # ============================================================================
    
    print("\n" + "=" * 50)
    print("🎉 DADOS DE TESTE CRIADOS COM SUCESSO!")
    print("=" * 50)
    
    print("\n👥 AGENTES CRIADOS:")
    print(f"   🔹 {agente_junior.nome_comercial} (Shopper-Keeper)")
    print(f"   🔹 {agente_marcia.nome_comercial} (Keeper)")
    print(f"   🔹 {agente_ana.nome_comercial} (Shopper)")
    
    print("\n👤 CLIENTES CRIADOS:")
    for cliente in clientes:
        print(f"   🔸 {cliente.user.get_full_name()}")
    
    print("\n🤝 TRUSTLINES:")
    print(f"   🔗 Júnior ↔ Márcia (Confiança: 88.5%)")
    print(f"   🔗 Júnior ↔ Ana (Confiança: 76.2%)")
    print(f"   🔗 Márcia ↔ Ana (Confiança: 82.7%)")
    
    print("\n📦 PRODUTOS E OFERTAS:")
    print(f"   📱 iPhone 15 Pro - Júnior: R$ 6.999 | Márcia: R$ 7.299 (+R$ 300)")
    print(f"   👗 Vestido Floral - Márcia: R$ 189,90 | Ana: R$ 219,90 (+R$ 30)")
    print(f"   🛋️ Sofá 3 Lugares - Ana: R$ 1.299")
    print(f"   👟 Tênis Nike - Júnior: R$ 459,90")
    print(f"   💄 Perfume Chanel - Márcia: R$ 899")
    print(f"   📺 Smart TV 55\" - Ana: R$ 2.199")
    
    print("\n🔑 CREDENCIAIS DE ACESSO:")
    print("   👤 junior_sp / 123456 (Shopper-Keeper)")
    print("   👤 marcia_rj / 123456 (Keeper)")
    print("   👤 ana_bh / 123456 (Shopper)")
    print("   👤 joao_cliente / 123456 (Cliente)")
    print("   👤 maria_cliente / 123456 (Cliente)")
    print("   👤 pedro_cliente / 123456 (Cliente)")
    print("   👤 carla_cliente / 123456 (Cliente)")
    print("   👤 lucas_cliente / 123456 (Cliente)")
    
    print("\n🚀 PRÓXIMOS PASSOS:")
    print("   1. Acesse: http://127.0.0.1:8000/login/")
    print("   2. Faça login com qualquer usuário")
    print("   3. Teste o menu KMN (para agentes)")
    print("   4. Explore ofertas e trustlines")
    print("   5. Simule pedidos entre agentes")
    
    print("\n📊 PARA TESTAR KMN:")
    print("   • Login como Júnior → Dashboard KMN")
    print("   • Veja ofertas com markup")
    print("   • Teste catálogo personalizado")
    print("   • Simule pedidos cooperados")
    
    return True

if __name__ == '__main__':
    try:
        criar_dados_teste()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
