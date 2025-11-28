#!/usr/bin/env python
"""
Script de migração de dados para a reestruturação oficial do VitrineZap/Évora/KMN.

Este script migra dados existentes para os novos modelos:
- Cria CarteiraCliente para cada Agente/User existente
- Migra Clientes para CarteiraCliente
- Migra TrustlineKeeper para LigacaoMesh
- Atualiza Pedidos com tipo_cliente e carteira_cliente

Uso:
    python manage.py shell < scripts/migrar_dados_reestruturacao.py
    ou
    python scripts/migrar_dados_reestruturacao.py
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from django.contrib.auth.models import User
from app_marketplace.models import (
    Cliente, PersonalShopper, Keeper, Agente,
    CarteiraCliente, LigacaoMesh, TrustlineKeeper,
    Pedido, ClienteRelacao
)
from decimal import Decimal


def criar_carteiras_para_agentes():
    """
    Cria CarteiraCliente para cada Agente/User que tem clientes.
    """
    print("\n" + "="*70)
    print("1. CRIANDO CARTEIRAS DE CLIENTES")
    print("="*70)
    
    carteiras_criadas = 0
    
    # Criar carteira para cada Agente
    agentes = Agente.objects.all()
    for agente in agentes:
        # Verificar se já tem carteira
        carteira_existente = CarteiraCliente.objects.filter(owner=agente.user).first()
        if not carteira_existente:
            carteira = CarteiraCliente.objects.create(
                owner=agente.user,
                nome_exibicao=f"Carteira {agente.user.username}",
                metadados={
                    "tipo": "agente_kmn",
                    "agente_id": agente.id,
                    "migrado_de": "Agente"
                }
            )
            carteiras_criadas += 1
            print(f"  ✅ Carteira criada para {agente.user.username}")
        else:
            print(f"  ⏭️  Carteira já existe para {agente.user.username}")
    
    # Criar carteira para Personal Shoppers sem Agente
    shoppers = PersonalShopper.objects.all()
    for shopper in shoppers:
        # Verificar se já tem carteira (via Agente ou direto)
        if not hasattr(shopper.user, 'agente'):
            carteira_existente = CarteiraCliente.objects.filter(owner=shopper.user).first()
            if not carteira_existente:
                carteira = CarteiraCliente.objects.create(
                    owner=shopper.user,
                    nome_exibicao=f"Carteira {shopper.user.username}",
                    metadados={
                        "tipo": "personal_shopper",
                        "shopper_id": shopper.id,
                        "migrado_de": "PersonalShopper"
                    }
                )
                carteiras_criadas += 1
                print(f"  ✅ Carteira criada para Shopper {shopper.user.username}")
    
    # Criar carteira para Keepers sem Agente
    keepers = Keeper.objects.all()
    for keeper in keepers:
        # Verificar se já tem carteira (via Agente ou direto)
        if not hasattr(keeper.user, 'agente'):
            carteira_existente = CarteiraCliente.objects.filter(owner=keeper.user).first()
            if not carteira_existente:
                carteira = CarteiraCliente.objects.create(
                    owner=keeper.user,
                    nome_exibicao=f"Carteira {keeper.user.username}",
                    metadados={
                        "tipo": "keeper",
                        "keeper_id": keeper.id,
                        "migrado_de": "Keeper"
                    }
                )
                carteiras_criadas += 1
                print(f"  ✅ Carteira criada para Keeper {keeper.user.username}")
    
    print(f"\n📊 Total de carteiras criadas: {carteiras_criadas}")
    return carteiras_criadas


def migrar_clientes_para_carteiras():
    """
    Migra Clientes existentes para CarteiraCliente baseado em ClienteRelacao.
    """
    print("\n" + "="*70)
    print("2. MIGRANDO CLIENTES PARA CARTEIRAS")
    print("="*70)
    
    clientes_migrados = 0
    
    # Migrar clientes baseado em ClienteRelacao
    relacoes = ClienteRelacao.objects.filter(status='ativa')
    for relacao in relacoes:
        cliente = relacao.cliente
        agente = relacao.agente
        
        # Buscar carteira do agente
        carteira = CarteiraCliente.objects.filter(owner=agente.user).first()
        
        if carteira and not cliente.wallet:
            cliente.wallet = carteira
            cliente.contato = {
                "telefone": cliente.telefone or "",
                "migrado_de": "ClienteRelacao"
            }
            cliente.metadados = {
                "forca_relacao": float(relacao.forca_relacao),
                "total_pedidos": relacao.total_pedidos,
                "migrado_de": "ClienteRelacao"
            }
            cliente.save()
            clientes_migrados += 1
            print(f"  ✅ Cliente {cliente.user.username} → Carteira {agente.user.username}")
    
    # Migrar clientes sem relação (criar carteira padrão)
    clientes_sem_wallet = Cliente.objects.filter(wallet__isnull=True)
    for cliente in clientes_sem_wallet:
        # Tentar encontrar relação com algum agente
        relacao = ClienteRelacao.objects.filter(cliente=cliente, status='ativa').first()
        
        if relacao:
            carteira = CarteiraCliente.objects.filter(owner=relacao.agente.user).first()
            if carteira:
                cliente.wallet = carteira
                cliente.save()
                clientes_migrados += 1
                print(f"  ✅ Cliente {cliente.user.username} → Carteira {relacao.agente.user.username}")
        else:
            # Cliente sem relação - criar carteira padrão ou deixar null
            print(f"  ⚠️  Cliente {cliente.user.username} sem relação ativa - wallet permanece null")
    
    print(f"\n📊 Total de clientes migrados: {clientes_migrados}")
    return clientes_migrados


def migrar_trustlines_para_mesh():
    """
    Migra TrustlineKeeper para LigacaoMesh.
    """
    print("\n" + "="*70)
    print("3. MIGRANDO TRUSTLINES PARA LIGAÇÕES MESH")
    print("="*70)
    
    mesh_criadas = 0
    
    trustlines = TrustlineKeeper.objects.filter(status='ativa')
    for trustline in trustlines:
        # Verificar se já existe LigacaoMesh
        mesh_existente = LigacaoMesh.objects.filter(
            agente_a=trustline.agente_a.user,
            agente_b=trustline.agente_b.user
        ).first()
        
        if not mesh_existente:
            # Determinar tipo de mesh baseado em confiança
            # Se ambos têm alta confiança (>80), é Mesh Forte
            confianca_media = (trustline.nivel_confianca_a_para_b + trustline.nivel_confianca_b_para_a) / 2
            
            tipo_mesh = LigacaoMesh.TipoMesh.FORTE if confianca_media >= 80 else LigacaoMesh.TipoMesh.FRACA
            
            # Configuração financeira
            config_financeira = {
                "taxa_evora": Decimal('0.10'),  # 10% padrão
                "venda_clientes_shopper": {
                    "alpha_s": Decimal('1.0')
                },
                "venda_clientes_keeper": {
                    "alpha_s": Decimal(str(trustline.perc_shopper / 100)),
                    "alpha_k": Decimal(str(trustline.perc_keeper / 100))
                }
            }
            
            mesh = LigacaoMesh.objects.create(
                agente_a=trustline.agente_a.user,
                agente_b=trustline.agente_b.user,
                tipo=tipo_mesh,
                ativo=True,
                config_financeira=config_financeira,
                metadados={
                    "migrado_de": "TrustlineKeeper",
                    "trustline_id": trustline.id,
                    "nivel_confianca_original": float(confianca_media)
                },
                aceito_em=trustline.aceito_em or trustline.criado_em
            )
            mesh_criadas += 1
            print(f"  ✅ Mesh {tipo_mesh} criada: {trustline.agente_a.user.username} ↔ {trustline.agente_b.user.username}")
        else:
            print(f"  ⏭️  Mesh já existe: {trustline.agente_a.user.username} ↔ {trustline.agente_b.user.username}")
    
    print(f"\n📊 Total de ligações mesh criadas: {mesh_criadas}")
    return mesh_criadas


def atualizar_pedidos():
    """
    Atualiza Pedidos existentes com tipo_cliente, carteira_cliente, shopper e keeper.
    """
    print("\n" + "="*70)
    print("4. ATUALIZANDO PEDIDOS")
    print("="*70)
    
    pedidos_atualizados = 0
    
    pedidos = Pedido.objects.all()
    for pedido in pedidos:
        atualizado = False
        
        # 1. Atualizar carteira_cliente
        if pedido.cliente.wallet and not pedido.carteira_cliente:
            pedido.carteira_cliente = pedido.cliente.wallet
            atualizado = True
        
        # 2. Determinar shopper (se não definido)
        if not pedido.shopper:
            # Tentar encontrar via PersonalShopper ou Agente
            if hasattr(pedido.cliente.user, 'personalshopper'):
                pedido.shopper = pedido.cliente.user.personalshopper.user
                atualizado = True
            elif pedido.cliente.wallet:
                # Usar owner da carteira como shopper inicial
                pedido.shopper = pedido.cliente.wallet.owner
                atualizado = True
        
        # 3. Determinar tipo_cliente e keeper
        if pedido.shopper and pedido.carteira_cliente:
            pedido.determinar_tipo_cliente(pedido.shopper)
            atualizado = True
        
        # 4. Atualizar preços
        if not pedido.preco_base or not pedido.preco_final:
            pedido.atualizar_precos()
            atualizado = True
        
        if atualizado:
            pedido.save()
            pedidos_atualizados += 1
            tipo_str = pedido.get_tipo_cliente_display() if pedido.tipo_cliente else "não definido"
            print(f"  ✅ Pedido #{pedido.id} - tipo: {tipo_str}")
    
    print(f"\n📊 Total de pedidos atualizados: {pedidos_atualizados}")
    return pedidos_atualizados


def main():
    """Executa todas as migrações"""
    print("\n" + "="*70)
    print("MIGRAÇÃO DE DADOS - REESTRUTURAÇÃO OFICIAL")
    print("VitrineZap/Évora/KMN")
    print("="*70)
    
    try:
        # 1. Criar carteiras
        carteiras = criar_carteiras_para_agentes()
        
        # 2. Migrar clientes
        clientes = migrar_clientes_para_carteiras()
        
        # 3. Migrar trustlines
        mesh = migrar_trustlines_para_mesh()
        
        # 4. Atualizar pedidos
        pedidos = atualizar_pedidos()
        
        # Resumo final
        print("\n" + "="*70)
        print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*70)
        print(f"📊 Resumo:")
        print(f"   - Carteiras criadas: {carteiras}")
        print(f"   - Clientes migrados: {clientes}")
        print(f"   - Ligações mesh criadas: {mesh}")
        print(f"   - Pedidos atualizados: {pedidos}")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERRO durante migração: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    main()

