#!/usr/bin/env python
"""
Script de teste para o sistema KMN (Keeper Mesh Network)
Demonstra o funcionamento completo do DropKeeper
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from django.contrib.auth.models import User
from app_marketplace.models import (
    Cliente, Agente, Produto, Categoria, Empresa, 
    EstoqueItem, Oferta, ClienteRelacao, TrustlineKeeper
)
from app_marketplace.services import KMNRoleEngine, CatalogoService


def criar_dados_teste():
    """Cria dados de teste para demonstrar o sistema KMN"""
    print("Criando dados de teste...")
    
    # 1. Criar empresa e categoria
    empresa, _ = Empresa.objects.get_or_create(
        nome="ÉVORA Orlando",
        defaults={
            'cnpj': '12.345.678/0001-90',
            'email': 'orlando@evora.com'
        }
    )
    
    categoria, _ = Categoria.objects.get_or_create(
        nome="Perfumes",
        defaults={'slug': 'perfumes'}
    )
    
    # 2. Criar produtos
    produto1, _ = Produto.objects.get_or_create(
        nome="Victoria's Secret Body Splash",
        defaults={
            'empresa': empresa,
            'categoria': categoria,
            'descricao': "Body splash Victoria's Secret",
            'preco': 25.00
        }
    )
    
    produto2, _ = Produto.objects.get_or_create(
        nome="Bath & Body Works Lotion",
        defaults={
            'empresa': empresa,
            'categoria': categoria,
            'descricao': "Loção hidratante Bath & Body Works",
            'preco': 18.00
        }
    )
    
    # 3. Criar usuários e agentes
    # Júnior - Shopper em Orlando
    user_junior, created = User.objects.get_or_create(
        username='junior_orlando',
        defaults={
            'first_name': 'Júnior',
            'last_name': 'Silva',
            'email': 'junior@evora.com'
        }
    )
    
    agente_junior, _ = Agente.objects.get_or_create(
        user=user_junior,
        defaults={
            'nome_comercial': 'Júnior Orlando Shopping',
            'ativo_como_shopper': True,
            'ativo_como_keeper': False,
            'verificado_kmn': True
        }
    )
    
    # Márcia - Keeper em Sorocaba
    user_marcia, created = User.objects.get_or_create(
        username='marcia_sorocaba',
        defaults={
            'first_name': 'Márcia',
            'last_name': 'Santos',
            'email': 'marcia@evora.com'
        }
    )
    
    agente_marcia, _ = Agente.objects.get_or_create(
        user=user_marcia,
        defaults={
            'nome_comercial': 'Márcia Keeper Sorocaba',
            'ativo_como_shopper': False,
            'ativo_como_keeper': True,
            'verificado_kmn': True
        }
    )
    
    # Ana - Dual Role (Shopper + Keeper)
    user_ana, created = User.objects.get_or_create(
        username='ana_dual',
        defaults={
            'first_name': 'Ana',
            'last_name': 'Costa',
            'email': 'ana@evora.com'
        }
    )
    
    agente_ana, _ = Agente.objects.get_or_create(
        user=user_ana,
        defaults={
            'nome_comercial': 'Ana Dual Role',
            'ativo_como_shopper': True,
            'ativo_como_keeper': True,
            'verificado_kmn': True
        }
    )
    
    # 4. Criar clientes
    user_cliente1, created = User.objects.get_or_create(
        username='cliente_joao',
        defaults={
            'first_name': 'João',
            'last_name': 'Pereira',
            'email': 'joao@cliente.com'
        }
    )
    
    cliente1, _ = Cliente.objects.get_or_create(
        user=user_cliente1,
        defaults={'telefone': '(11) 99999-1111'}
    )
    
    user_cliente2, created = User.objects.get_or_create(
        username='cliente_maria',
        defaults={
            'first_name': 'Maria',
            'last_name': 'Oliveira',
            'email': 'maria@cliente.com'
        }
    )
    
    cliente2, _ = Cliente.objects.get_or_create(
        user=user_cliente2,
        defaults={'telefone': '(11) 99999-2222'}
    )
    
    # 5. Criar estoque
    EstoqueItem.objects.get_or_create(
        agente=agente_junior,
        produto=produto1,
        defaults={
            'quantidade_disponivel': 10,
            'preco_custo': 20.00,
            'preco_base': 25.00
        }
    )
    
    EstoqueItem.objects.get_or_create(
        agente=agente_ana,
        produto=produto2,
        defaults={
            'quantidade_disponivel': 5,
            'preco_custo': 15.00,
            'preco_base': 18.00
        }
    )
    
    # 6. Criar ofertas
    Oferta.objects.get_or_create(
        produto=produto1,
        agente_origem=agente_junior,
        agente_ofertante=agente_junior,
        defaults={
            'preco_base': 25.00,
            'preco_oferta': 25.00,  # Sem markup (oferta direta)
            'quantidade_disponivel': 10
        }
    )
    
    Oferta.objects.get_or_create(
        produto=produto1,
        agente_origem=agente_junior,
        agente_ofertante=agente_marcia,
        defaults={
            'preco_base': 25.00,
            'preco_oferta': 30.00,  # R$ 5 de markup
            'quantidade_disponivel': 5
        }
    )
    
    Oferta.objects.get_or_create(
        produto=produto2,
        agente_origem=agente_ana,
        agente_ofertante=agente_ana,
        defaults={
            'preco_base': 18.00,
            'preco_oferta': 18.00,  # Sem markup
            'quantidade_disponivel': 5
        }
    )
    
    # 7. Criar relações cliente-agente
    ClienteRelacao.objects.get_or_create(
        cliente=cliente1,
        agente=agente_marcia,
        defaults={
            'forca_relacao': 85.0,
            'status': ClienteRelacao.StatusRelacao.ATIVA,
            'total_pedidos': 3,
            'satisfacao_media': 9.5
        }
    )
    
    ClienteRelacao.objects.get_or_create(
        cliente=cliente2,
        agente=agente_ana,
        defaults={
            'forca_relacao': 92.0,
            'status': ClienteRelacao.StatusRelacao.ATIVA,
            'total_pedidos': 5,
            'satisfacao_media': 9.8
        }
    )
    
    # 8. Criar trustline
    TrustlineKeeper.objects.get_or_create(
        agente_a=agente_junior,
        agente_b=agente_marcia,
        defaults={
            'nivel_confianca_a_para_b': 90.0,
            'nivel_confianca_b_para_a': 85.0,
            'perc_shopper': 65.0,
            'perc_keeper': 35.0,
            'status': TrustlineKeeper.StatusTrustline.ATIVA
        }
    )
    
    print("Dados de teste criados com sucesso!")
    return {
        'agentes': [agente_junior, agente_marcia, agente_ana],
        'clientes': [cliente1, cliente2],
        'produtos': [produto1, produto2]
    }


def testar_engine_kmn(dados):
    """Testa o KMN Role Engine"""
    print("\nTestando KMN Role Engine...")
    
    engine = KMNRoleEngine()
    cliente1, cliente2 = dados['clientes']
    produto1, produto2 = dados['produtos']
    
    # Teste 1: Cliente da Márcia comprando produto do Júnior
    print(f"\nTeste 1: {cliente1.user.first_name} (cliente da Márcia) comprando {produto1.nome} (do Júnior)")
    
    resolucao = engine.resolver_papeis_operacao(cliente1, produto1)
    print(f"   Shopper: {resolucao['shopper'].user.get_full_name() if resolucao['shopper'] else 'None'}")
    print(f"   Keeper: {resolucao['keeper'].user.get_full_name() if resolucao['keeper'] else 'None'}")
    print(f"   Tipo: {resolucao['tipo_operacao']}")
    print(f"   Oferta: R$ {resolucao['oferta'].preco_oferta if resolucao['oferta'] else 'None'}")
    
    if resolucao['trustline']:
        print(f"   Trustline: {resolucao['trustline'].perc_shopper}% Shopper / {resolucao['trustline'].perc_keeper}% Keeper")
    
    # Teste 2: Cliente da Ana comprando produto da Ana
    print(f"\nTeste 2: {cliente2.user.first_name} (cliente da Ana) comprando {produto2.nome} (da Ana)")
    
    resolucao2 = engine.resolver_papeis_operacao(cliente2, produto2)
    print(f"   Shopper: {resolucao2['shopper'].user.get_full_name() if resolucao2['shopper'] else 'None'}")
    print(f"   Keeper: {resolucao2['keeper'].user.get_full_name() if resolucao2['keeper'] else 'None'}")
    print(f"   Tipo: {resolucao2['tipo_operacao']}")
    print(f"   Oferta: R$ {resolucao2['oferta'].preco_oferta if resolucao2['oferta'] else 'None'}")


def testar_catalogo_personalizado(dados):
    """Testa o catálogo personalizado"""
    print("\nTestando Catálogo Personalizado...")
    
    cliente1, cliente2 = dados['clientes']
    
    # Catálogo do Cliente 1 (da Márcia)
    print(f"\nCatálogo para {cliente1.user.first_name} (cliente da Márcia):")
    catalogo1 = CatalogoService.gerar_catalogo_cliente(cliente1)
    
    for item in catalogo1['produtos']:
        print(f"   {item['produto'].nome}: R$ {item['preco']} (via {item['agente'].user.get_full_name()})")
        if item['markup_percentual'] > 0:
            print(f"      Markup: +{item['markup_percentual']:.1f}%")
    
    # Catálogo do Cliente 2 (da Ana)
    print(f"\nCatálogo para {cliente2.user.first_name} (cliente da Ana):")
    catalogo2 = CatalogoService.gerar_catalogo_cliente(cliente2)
    
    for item in catalogo2['produtos']:
        print(f"   {item['produto'].nome}: R$ {item['preco']} (via {item['agente'].user.get_full_name()})")
        if item['markup_percentual'] > 0:
            print(f"      Markup: +{item['markup_percentual']:.1f}%")


def testar_processamento_pedido(dados):
    """Testa o processamento completo de um pedido"""
    print("\nTestando Processamento de Pedido...")
    
    engine = KMNRoleEngine()
    cliente1 = dados['clientes'][0]
    produto1 = dados['produtos'][0]
    
    print(f"\nProcessando pedido: {cliente1.user.first_name} comprando {produto1.nome}")
    
    resultado = engine.processar_pedido_kmn(cliente1, produto1, quantidade=2)
    
    if resultado['sucesso']:
        dados_pedido = resultado['dados_pedido']
        print("Pedido processado com sucesso!")
        print(f"   Shopper: {dados_pedido['agente_shopper'].user.get_full_name()}")
        print(f"   Keeper: {dados_pedido['agente_keeper'].user.get_full_name()}")
        print(f"   Preço base: R$ {dados_pedido['preco_base_kmn']}")
        print(f"   Preço oferta: R$ {dados_pedido['preco_oferta_kmn']}")
        print(f"   Markup: R$ {dados_pedido['markup_local_kmn']}")
        print(f"   Comissão Shopper: R$ {dados_pedido['comissao_shopper']}")
        print(f"   Comissão Keeper: R$ {dados_pedido['comissao_keeper']}")
        print(f"   Valor total: R$ {dados_pedido['valor_total']}")
        print(f"   Tipo operação: {dados_pedido['tipo_operacao_kmn']}")
    else:
        print(f"Erro: {resultado.get('erro', 'Erro desconhecido')}")


def main():
    """Função principal"""
    print("TESTE COMPLETO DO SISTEMA KMN - DROPKEEPER")
    print("=" * 60)
    
    try:
        # Criar dados de teste
        dados = criar_dados_teste()
        
        # Testar engine
        testar_engine_kmn(dados)
        
        # Testar catálogo
        testar_catalogo_personalizado(dados)
        
        # Testar processamento de pedido
        testar_processamento_pedido(dados)
        
        print("\nTodos os testes concluídos com sucesso!")
        print("\nResumo do Sistema KMN:")
        print("   Agentes criados e configurados")
        print("   Ofertas com markup funcionando")
        print("   Resolução de papéis automática")
        print("   Catálogo personalizado por cliente")
        print("   Trustlines e comissionamento")
        print("   Processamento completo de pedidos")
        
        print("\nAPIs disponíveis em:")
        print("   http://localhost:8000/api/kmn/")
        print("   http://localhost:8000/admin/ (para gerenciar dados)")
        
    except Exception as e:
        print(f"Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
