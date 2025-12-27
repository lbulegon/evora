#!/usr/bin/env python
"""
Teste do Fluxo Completo WhatsApp ÉVORA/VitrineZap
==================================================

Testa o fluxo completo seguindo os princípios fundadores:
1. Grupo → Intenção Social Assistida
2. Click-to-Chat → Conversa Contextualizada
3. Privado → Carrinho Invisível
4. Fechamento → WhatsappOrder
5. Prova Social → Retorno ao Grupo

Execute: python test_whatsapp_flow_completo.py
"""

import os
import sys
import django
from decimal import Decimal
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from app_marketplace.models import (
    WhatsappGroup, WhatsappParticipant, WhatsappConversation,
    OfertaProduto, IntencaoSocial, ConversaContextualizada, CarrinhoInvisivel,
    ProdutoJSON, PersonalShopper, WhatsappOrder
)
from app_marketplace.whatsapp_flow_engine import WhatsAppFlowEngine

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")

def print_step(msg):
    print(f"\n{Colors.BOLD}{Colors.YELLOW}━━━ {msg} ━━━{Colors.RESET}")

def criar_dados_teste():
    """Cria dados de teste necessários"""
    print_step("CRIANDO DADOS DE TESTE")
    
    # Criar usuário shopper
    shopper_user, _ = User.objects.get_or_create(
        username='shopper_flow_teste',
        defaults={
            'first_name': 'Maria',
            'last_name': 'Shopper',
            'email': 'maria.shopper@teste.com'
        }
    )
    
    shopper, _ = PersonalShopper.objects.get_or_create(
        user=shopper_user,
        defaults={'nome': 'Maria Shopper', 'ativo': True}
    )
    print_success(f"Shopper criado: {shopper.nome}")
    
    # Criar grupo WhatsApp
    grupo, _ = WhatsappGroup.objects.get_or_create(
        chat_id='120363123456789@g.us',
        defaults={
            'name': 'Grupo de Teste ÉVORA',
            'owner': shopper_user
        }
    )
    print_success(f"Grupo criado: {grupo.name}")
    
    # Criar participante (cliente)
    participante, _ = WhatsappParticipant.objects.get_or_create(
        phone='5511999999999',
        group=grupo,
        defaults={
            'name': 'João Cliente'
        }
    )
    print_success(f"Participante criado: {participante.name}")
    
    # Criar produto
    produto, _ = ProdutoJSON.objects.get_or_create(
        nome_produto='Victoria\'s Secret Body Splash',
        defaults={
            'marca': 'Victoria\'s Secret',
            'categoria': 'Perfumaria',
            'criado_por': shopper_user,
            'dados_json': {
                'nome_produto': 'Victoria\'s Secret Body Splash',
                'marca': 'Victoria\'s Secret',
                'categoria': 'Perfumaria',
                'preco': '89.90',
                'moeda': 'BRL',
                'ativo': True
            }
        }
    )
    print_success(f"Produto criado: {produto.nome_produto}")
    
    return {
        'shopper_user': shopper_user,
        'shopper': shopper,
        'grupo': grupo,
        'participante': participante,
        'produto': produto
    }

def testar_intencao_social(dados, flow_engine):
    """Testa intenção social no grupo"""
    print_step("TESTE 1: INTENÇÃO SOCIAL NO GRUPO")
    
    # Criar oferta
    oferta = OfertaProduto.objects.create(
        produto=dados['produto'],
        grupo=dados['grupo'],
        mensagem_postada='📦 Victoria\'s Secret Body Splash\n💰 R$ 89,90',
        preco_exibido=Decimal('89.90'),
        moeda='BRL',
        criado_por=dados['shopper_user']
    )
    print_success(f"Oferta criada: {oferta.oferta_id}")
    
    # Simular mensagem de intenção no grupo
    mensagem_intencao = "❤️ eu quero!"
    resultado = flow_engine.processar_mensagem_grupo(
        grupo=dados['grupo'],
        participante=dados['participante'],
        mensagem=mensagem_intencao,
        mensagem_id='MSG_TEST_001',
        tipo_mensagem='texto'
    )
    
    if resultado.get('tipo') == 'intencao_social':
        print_success(f"Intenção social registrada: {resultado.get('intencao_id')}")
        
        # Verificar se intenção foi salva
        intencao = IntencaoSocial.objects.get(id=resultado['intencao_id'])
        print_success(f"Intenção confirmada no banco: {intencao.tipo} - {intencao.conteudo}")
        
        return {'oferta': oferta, 'intencao': intencao}
    else:
        print_error(f"Falha ao processar intenção social: {resultado}")
        return None

def testar_click_to_chat(dados, flow_engine, oferta):
    """Testa click-to-chat"""
    print_step("TESTE 2: CLICK-TO-CHAT")
    
    # Criar conversa contextualizada (click-to-chat)
    # O método cria a conversa automaticamente se não existir
    try:
        conversa_contextualizada = flow_engine.iniciar_click_to_chat(
            oferta_id=oferta.oferta_id,
            participante=dados['participante'],
            grupo=dados['grupo']
        )
        
        print_success(f"Conversa contextualizada criada: ID {conversa_contextualizada.id}")
        print_success(f"Status: {conversa_contextualizada.get_status_display()}")
        print_success(f"Conversa ID: {conversa_contextualizada.conversa.conversation_id}")
        return conversa_contextualizada
    except Exception as e:
        print_error(f"Falha ao criar conversa contextualizada: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def testar_carrinho_invisivel(dados, flow_engine, conversa_contextualizada):
    """Testa carrinho invisível"""
    print_step("TESTE 3: CARRINHO INVISÍVEL")
    
    # Adicionar item ao carrinho (o método pega produto e preço da oferta automaticamente)
    try:
        carrinho = flow_engine.adicionar_ao_carrinho_invisivel(
            conversa_contextualizada=conversa_contextualizada,
            quantidade=2
        )
        
        print_success("Item adicionado ao carrinho invisível")
        print_info(f"Itens no carrinho: {len(carrinho.itens)}")
        print_info(f"Total: {carrinho.moeda} {carrinho.total}")
        
        for item in carrinho.itens:
            print_info(f"  - {item.get('nome')}: {item.get('quantidade')}x {item.get('preco')}")
        
        return carrinho
    except Exception as e:
        print_error(f"Falha ao adicionar ao carrinho: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def testar_fechamento_pedido(dados, flow_engine, conversa_contextualizada):
    """Testa fechamento do pedido"""
    print_step("TESTE 4: FECHAMENTO E CRIAÇÃO DO PEDIDO")
    
    # Finalizar pedido
    resultado = flow_engine.finalizar_pedido(conversa_contextualizada)
    
    if resultado.get('sucesso'):
        pedido_numero = resultado.get('pedido_numero')
        pedido_id = resultado.get('pedido_id')
        
        print_success(f"Pedido criado com sucesso!")
        print_info(f"Número do pedido: {pedido_numero}")
        print_info(f"ID: {pedido_id}")
        print_info(f"Total: {resultado['carrinho']['moeda']} {resultado['carrinho']['total']}")
        print_info(f"Produtos: {len(resultado.get('produtos', []))}")
        
        # Verificar pedido no banco
        try:
            pedido = WhatsappOrder.objects.get(id=pedido_id)
            print_success(f"Pedido confirmado no banco: {pedido.order_number}")
            print_info(f"Status: {pedido.get_status_display()}")
            print_info(f"Cliente: {pedido.customer.name}")
            print_info(f"Grupo: {pedido.group.name}")
            print_info(f"Total: {pedido.currency} {pedido.total_amount}")
            
            # Verificar produtos
            if pedido.products:
                print_info("Produtos no pedido:")
                for produto in pedido.products:
                    print_info(f"  - {produto.get('nome')}: {produto.get('quantidade')}x")
            
            # Verificar conversa fechada
            conversa_contextualizada.refresh_from_db()
            if conversa_contextualizada.status == ConversaContextualizada.StatusConversa.FECHADA:
                print_success("Conversa marcada como fechada")
            else:
                print_error(f"Conversa não foi fechada. Status: {conversa_contextualizada.status}")
            
            return pedido
        except WhatsappOrder.DoesNotExist:
            print_error(f"Pedido {pedido_id} não encontrado no banco")
            return None
    else:
        print_error(f"Falha ao finalizar pedido: {resultado.get('erro')}")
        return None

def testar_fluxo_completo():
    """Executa todos os testes do fluxo completo"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 70)
    print("TESTE DO FLUXO COMPLETO WHATSAPP ÉVORA/VITRINEZAP")
    print("=" * 70)
    print(f"{Colors.RESET}\n")
    
    try:
        # Criar dados de teste
        dados = criar_dados_teste()
        
        # Inicializar flow engine
        flow_engine = WhatsAppFlowEngine()
        
        # Teste 1: Intenção Social
        resultado_intencao = testar_intencao_social(dados, flow_engine)
        if not resultado_intencao:
            print_error("Teste de intenção social falhou. Abortando.")
            return False
        
        oferta = resultado_intencao['oferta']
        
        # Teste 2: Click-to-Chat
        conversa_contextualizada = testar_click_to_chat(dados, flow_engine, oferta)
        if not conversa_contextualizada:
            print_error("Teste de click-to-chat falhou. Abortando.")
            return False
        
        # Teste 3: Carrinho Invisível
        carrinho = testar_carrinho_invisivel(dados, flow_engine, conversa_contextualizada)
        if not carrinho:
            print_error("Teste de carrinho invisível falhou. Abortando.")
            return False
        
        # Teste 4: Fechamento e Pedido
        pedido = testar_fechamento_pedido(dados, flow_engine, conversa_contextualizada)
        if not pedido:
            print_error("Teste de fechamento falhou. Abortando.")
            return False
        
        # Resumo final
        print_step("RESUMO DO TESTE")
        print_success("✅ Todos os testes passaram!")
        print_info(f"Oferta: {oferta.oferta_id}")
        print_info(f"Intenção Social: {resultado_intencao['intencao'].id}")
        print_info(f"Conversa Contextualizada: {conversa_contextualizada.id}")
        print_info(f"Carrinho: {len(carrinho.itens)} itens, Total: {carrinho.moeda} {carrinho.total}")
        print_info(f"Pedido: {pedido.order_number} - Status: {pedido.get_status_display()}")
        
        print(f"\n{Colors.GREEN}{Colors.BOLD}")
        print("=" * 70)
        print("🎉 FLUXO COMPLETO TESTADO COM SUCESSO! 🎉")
        print("=" * 70)
        print(f"{Colors.RESET}\n")
        
        return True
        
    except Exception as e:
        print_error(f"Erro durante teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    sucesso = testar_fluxo_completo()
    sys.exit(0 if sucesso else 1)

