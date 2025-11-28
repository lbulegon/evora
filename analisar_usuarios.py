#!/usr/bin/env python
"""
Script para analisar usuários e suas características no sistema ÉVORA.

Uso:
    python analisar_usuarios.py
    python analisar_usuarios.py --detalhado
    python analisar_usuarios.py --por-tipo
"""

import os
import sys
import django
from django.db.models import Count, Q, Sum, Avg
from decimal import Decimal

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from django.contrib.auth.models import User
from app_marketplace.models import (
    Cliente, PersonalShopper, Keeper, Agente,
    RelacionamentoClienteShopper, ClienteRelacao,
    WhatsappGroup, Pacote, Pedido,
    TrustlineKeeper, Oferta, EstoqueItem
)


def print_separator(title=""):
    """Imprime um separador visual"""
    if title:
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}\n")
    else:
        print(f"\n{'-'*70}\n")


def analisar_distribuicao_usuarios():
    """Analisa a distribuição de tipos de usuários"""
    print_separator("📊 DISTRIBUIÇÃO DE USUÁRIOS")
    
    total_usuarios = User.objects.count()
    print(f"Total de usuários no sistema: {total_usuarios}")
    
    # Contar por tipo
    clientes = Cliente.objects.count()
    shoppers = PersonalShopper.objects.count()
    keepers = Keeper.objects.count()
    agentes = Agente.objects.count()
    
    print(f"\nPor tipo de perfil:")
    print(f"  👤 Clientes:           {clientes:>5}")
    print(f"  🛍️  Personal Shoppers:  {shoppers:>5}")
    print(f"  📦 Keepers:            {keepers:>5}")
    print(f"  🌐 Agentes KMN:        {agentes:>5}")
    
    # Usuários com múltiplos perfis
    usuarios_multi_perfil = []
    for user in User.objects.all():
        perfis = []
        if user.is_cliente:
            perfis.append("Cliente")
        if user.is_shopper:
            perfis.append("Shopper")
        if user.is_keeper:
            perfis.append("Keeper")
        if user.is_agente:
            perfis.append("Agente")
        
        if len(perfis) > 1:
            usuarios_multi_perfil.append((user.username, perfis))
    
    if usuarios_multi_perfil:
        print(f"\nUsuários com múltiplos perfis: {len(usuarios_multi_perfil)}")
        for username, perfis in usuarios_multi_perfil[:10]:
            print(f"  - {username}: {', '.join(perfis)}")
        if len(usuarios_multi_perfil) > 10:
            print(f"  ... e mais {len(usuarios_multi_perfil) - 10} usuários")


def analisar_clientes():
    """Analisa características dos clientes"""
    print_separator("👤 ANÁLISE DE CLIENTES")
    
    total = Cliente.objects.count()
    print(f"Total de clientes: {total}")
    
    if total == 0:
        print("Nenhum cliente cadastrado.")
        return
    
    # Clientes com telefone
    com_telefone = Cliente.objects.exclude(telefone='').count()
    print(f"Clientes com telefone: {com_telefone} ({com_telefone/total*100:.1f}%)")
    
    # Relacionamentos
    relacionamentos = RelacionamentoClienteShopper.objects.count()
    seguindo = RelacionamentoClienteShopper.objects.filter(status='seguindo').count()
    print(f"\nRelacionamentos com Shoppers:")
    print(f"  Total: {relacionamentos}")
    print(f"  Seguindo: {seguindo}")
    
    # Clientes com pedidos
    clientes_com_pedidos = Cliente.objects.filter(
        user__pedido__isnull=False
    ).distinct().count()
    print(f"\nClientes com pedidos: {clientes_com_pedidos}")
    
    # Clientes com pacotes
    clientes_com_pacotes = Cliente.objects.filter(
        pacotes__isnull=False
    ).distinct().count()
    print(f"Clientes com pacotes: {clientes_com_pacotes}")
    
    # Clientes na rede KMN
    clientes_kmn = Cliente.objects.filter(
        relacoes_agente__isnull=False
    ).distinct().count()
    print(f"Clientes na rede KMN: {clientes_kmn}")


def analisar_shoppers():
    """Analisa características dos Personal Shoppers"""
    print_separator("🛍️  ANÁLISE DE PERSONAL SHOPPERS")
    
    total = PersonalShopper.objects.count()
    print(f"Total de Personal Shoppers: {total}")
    
    if total == 0:
        print("Nenhum Personal Shopper cadastrado.")
        return
    
    # Status
    ativos = PersonalShopper.objects.filter(ativo=True).count()
    print(f"Shoppers ativos: {ativos} ({ativos/total*100:.1f}%)")
    
    # Com empresa
    com_empresa = PersonalShopper.objects.exclude(empresa__isnull=True).count()
    print(f"Shoppers com empresa: {com_empresa}")
    
    # Com redes sociais
    com_redes = PersonalShopper.objects.exclude(
        Q(facebook='') & Q(instagram='') & Q(tiktok='')
    ).count()
    print(f"Shoppers com redes sociais: {com_redes}")
    
    # Relacionamentos
    total_clientes = RelacionamentoClienteShopper.objects.filter(
        status='seguindo'
    ).values('personal_shopper').distinct().count()
    print(f"\nShoppers com clientes: {total_clientes}")
    
    # Grupos WhatsApp
    grupos = WhatsappGroup.objects.filter(
        shopper__isnull=False
    ).count()
    print(f"Grupos WhatsApp criados: {grupos}")
    
    # Agentes KMN
    agentes_shopper = Agente.objects.exclude(personal_shopper__isnull=True).count()
    print(f"Shoppers na rede KMN: {agentes_shopper}")


def analisar_keepers():
    """Analisa características dos Keepers"""
    print_separator("📦 ANÁLISE DE KEEPERS")
    
    total = Keeper.objects.count()
    print(f"Total de Keepers: {total}")
    
    if total == 0:
        print("Nenhum Keeper cadastrado.")
        return
    
    # Status
    ativos = Keeper.objects.filter(ativo=True).count()
    verificados = Keeper.objects.filter(verificado=True).count()
    print(f"Keepers ativos: {ativos} ({ativos/total*100:.1f}%)")
    print(f"Keepers verificados: {verificados} ({verificados/total*100:.1f}%)")
    
    # Localização
    com_endereco = Keeper.objects.exclude(
        Q(cidade='') | Q(estado='')
    ).count()
    print(f"Keepers com endereço completo: {com_endereco}")
    
    # Capacidade
    stats = Keeper.objects.aggregate(
        capacidade_total=Sum('capacidade_itens'),
        capacidade_media=Avg('capacidade_itens'),
        taxa_media=Avg('taxa_guarda_dia')
    )
    print(f"\nCapacidade total: {stats['capacidade_total'] or 0} itens")
    print(f"Capacidade média: {stats['capacidade_media'] or 0:.1f} itens")
    print(f"Taxa média de guarda: R$ {stats['taxa_media'] or 0:.2f}/dia")
    
    # Opções
    aceita_retirada = Keeper.objects.filter(aceita_retirada=True).count()
    aceita_envio = Keeper.objects.filter(aceita_envio=True).count()
    print(f"\nAceita retirada: {aceita_retirada}")
    print(f"Aceita envio: {aceita_envio}")
    
    # Pacotes
    pacotes_total = Pacote.objects.filter(keeper__isnull=False).count()
    pacotes_em_guarda = Pacote.objects.filter(
        keeper__isnull=False,
        status='em_guarda'
    ).count()
    print(f"\nPacotes recebidos: {pacotes_total}")
    print(f"Pacotes em guarda: {pacotes_em_guarda}")
    
    # Agentes KMN
    agentes_keeper = Agente.objects.exclude(keeper__isnull=True).count()
    print(f"Keepers na rede KMN: {agentes_keeper}")


def analisar_agentes():
    """Analisa características dos Agentes KMN"""
    print_separator("🌐 ANÁLISE DE AGENTES KMN")
    
    total = Agente.objects.count()
    print(f"Total de Agentes KMN: {total}")
    
    if total == 0:
        print("Nenhum Agente KMN cadastrado.")
        return
    
    # Papéis
    como_shopper = Agente.objects.filter(ativo_como_shopper=True).count()
    como_keeper = Agente.objects.filter(ativo_como_keeper=True).count()
    dual_role = Agente.objects.filter(
        ativo_como_shopper=True,
        ativo_como_keeper=True
    ).count()
    
    print(f"Ativos como Shopper: {como_shopper}")
    print(f"Ativos como Keeper: {como_keeper}")
    print(f"Dual Role (ambos): {dual_role}")
    
    # Verificação
    verificados = Agente.objects.filter(verificado_kmn=True).count()
    print(f"Verificados pela rede: {verificados}")
    
    # Scores
    stats = Agente.objects.aggregate(
        score_keeper_medio=Avg('score_keeper'),
        score_shopper_medio=Avg('score_shopper')
    )
    print(f"\nScore médio Keeper: {stats['score_keeper_medio'] or 0:.2f}/10")
    print(f"Score médio Shopper: {stats['score_shopper_medio'] or 0:.2f}/10")
    
    # Trustlines
    trustlines = TrustlineKeeper.objects.filter(status='ativa').count()
    print(f"\nTrustlines ativas: {trustlines}")
    
    # Ofertas
    ofertas = Oferta.objects.filter(ativo=True).count()
    print(f"Ofertas ativas: {ofertas}")
    
    # Estoque
    estoque_items = EstoqueItem.objects.filter(ativo=True).count()
    print(f"Itens em estoque: {estoque_items}")
    
    # Relações com clientes
    relacoes = ClienteRelacao.objects.filter(status='ativa').count()
    print(f"Relações ativas com clientes: {relacoes}")


def analisar_estatisticas_gerais():
    """Analisa estatísticas gerais do sistema"""
    print_separator("📈 ESTATÍSTICAS GERAIS")
    
    # Pedidos
    total_pedidos = Pedido.objects.count()
    pedidos_pagos = Pedido.objects.exclude(status='cancelado').count()
    receita_total = Pedido.objects.exclude(
        status='cancelado'
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    print(f"Pedidos:")
    print(f"  Total: {total_pedidos}")
    print(f"  Pagos/Ativos: {pedidos_pagos}")
    print(f"  Receita total: R$ {receita_total:,.2f}")
    
    # Pacotes
    total_pacotes = Pacote.objects.count()
    pacotes_em_guarda = Pacote.objects.filter(status='em_guarda').count()
    print(f"\nPacotes:")
    print(f"  Total: {total_pacotes}")
    print(f"  Em guarda: {pacotes_em_guarda}")
    
    # Grupos WhatsApp
    grupos = WhatsappGroup.objects.count()
    grupos_ativos = WhatsappGroup.objects.filter(active=True).count()
    print(f"\nGrupos WhatsApp:")
    print(f"  Total: {grupos}")
    print(f"  Ativos: {grupos_ativos}")


def analisar_detalhado():
    """Análise detalhada de cada tipo"""
    print_separator("🔍 ANÁLISE DETALHADA")
    
    # Top 5 Shoppers por clientes
    print("\nTop 5 Personal Shoppers (por número de clientes):")
    top_shoppers = PersonalShopper.objects.annotate(
        num_clientes=Count('relacionamento_clienteshopper', filter=Q(
            relacionamento_clienteshopper__status='seguindo'
        ))
    ).order_by('-num_clientes')[:5]
    
    for i, shopper in enumerate(top_shoppers, 1):
        print(f"  {i}. {shopper.user.username}: {shopper.num_clientes} clientes")
    
    # Top 5 Keepers por pacotes
    print("\nTop 5 Keepers (por número de pacotes):")
    top_keepers = Keeper.objects.annotate(
        num_pacotes=Count('pacotes')
    ).order_by('-num_pacotes')[:5]
    
    for i, keeper in enumerate(top_keepers, 1):
        print(f"  {i}. {keeper.user.username}: {keeper.num_pacotes} pacotes")
    
    # Top 5 Agentes por score
    print("\nTop 5 Agentes KMN (por score dual):")
    top_agentes = Agente.objects.filter(
        Q(ativo_como_shopper=True) | Q(ativo_como_keeper=True)
    ).order_by('-score_shopper', '-score_keeper')[:5]
    
    for i, agente in enumerate(top_agentes, 1):
        score = agente.dual_role_score
        roles = []
        if agente.ativo_como_shopper:
            roles.append("Shopper")
        if agente.ativo_como_keeper:
            roles.append("Keeper")
        print(f"  {i}. {agente.user.username} ({'/'.join(roles)}): {score:.2f}")


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analisar usuários do sistema ÉVORA')
    parser.add_argument('--detalhado', action='store_true', help='Análise detalhada')
    parser.add_argument('--por-tipo', action='store_true', help='Análise por tipo apenas')
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("  📊 ANÁLISE DE USUÁRIOS - ÉVORA/VitrineZap")
    print("="*70)
    
    # Análise básica
    analisar_distribuicao_usuarios()
    analisar_estatisticas_gerais()
    
    if args.por_tipo:
        # Análise por tipo
        analisar_clientes()
        analisar_shoppers()
        analisar_keepers()
        analisar_agentes()
    
    if args.detalhado:
        analisar_detalhado()
    
    print_separator()
    print("✅ Análise concluída!")
    print_separator()


if __name__ == '__main__':
    main()

