"""
Views da API de Pagamentos - Checkout e Webhooks
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from decimal import Decimal

from .models import Pedido, ItemPedido, Pagamento, TransacaoGateway, Produto, Evento
from .serializers import (
    CheckoutCreateSerializer, PedidoSerializer, PagamentoSerializer
)
from .payment_services import get_gateway_service, enviar_notificacao_whatsapp


@api_view(['POST'])
@permission_classes([AllowAny])
def criar_pedido_checkout(request):
    """
    Endpoint para criar pedido + iniciar pagamento.
    POST /api/v1/checkout/criar-pedido/
    """
    serializer = CheckoutCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    cliente_data = data['cliente']
    itens_data = data['itens']
    pagamento_data = data['pagamento']
    entrega_data = data.get('entrega', {})
    evento_id = data.get('evento_id')
    
    try:
        with transaction.atomic():
            # Criar pedido
            pedido = Pedido.objects.create(
                cliente_nome=cliente_data['nome'],
                cliente_whatsapp=cliente_data['whatsapp'],
                cliente_email=cliente_data.get('email', ''),
                valor_frete=Decimal(str(entrega_data.get('frete', 0))),
                valor_taxas=Decimal(str(entrega_data.get('taxas', 0))),
                moeda='BRL',  # Por enquanto fixo, pode ser dinâmico depois
                status=Pedido.Status.AGUARDANDO_PAGAMENTO,
            )
            
            # Gerar código único
            pedido.gerar_codigo()
            pedido.save()
            
            # Vincular evento se fornecido
            if evento_id:
                try:
                    evento = Evento.objects.get(id=evento_id)
                    pedido.evento = evento
                    pedido.save()
                except Evento.DoesNotExist:
                    pass
            
            # Criar itens do pedido
            valor_subtotal = Decimal('0.00')
            for item_data in itens_data:
                produto = get_object_or_404(Produto, id=item_data['produto_id'], ativo=True)
                quantidade = item_data['quantidade']
                preco_unitario = produto.preco
                
                ItemPedido.objects.create(
                    pedido=pedido,
                    produto=produto,
                    quantidade=quantidade,
                    preco_unitario=preco_unitario,
                    descricao=produto.nome,  # Snapshot
                    moeda='BRL'
                )
                
                valor_subtotal += preco_unitario * quantidade
            
            # Calcular total
            pedido.valor_subtotal = valor_subtotal
            pedido.calcular_total()
            pedido.save()
            
            # Criar pagamento
            pagamento = Pagamento.objects.create(
                pedido=pedido,
                metodo=pagamento_data['metodo'],
                valor=pedido.valor_total,
                moeda=pedido.moeda,
                status=Pagamento.Status.CRIADO,
                gateway=pagamento_data['gateway']
            )
            
            # Criar pagamento no gateway
            gateway_service = get_gateway_service(pagamento_data['gateway'])
            resultado = gateway_service.criar_pagamento(pagamento)
            
            if not resultado.get('success'):
                return Response(
                    {'error': 'Erro ao criar pagamento no gateway', 'details': resultado.get('error')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Atualizar status do pagamento
            pagamento.status = Pagamento.Status.PENDENTE
            pagamento.save()
            
            # Serializar resposta
            pedido_serializer = PedidoSerializer(pedido)
            pagamento_serializer = PagamentoSerializer(pagamento)
            
            # Enviar notificação WhatsApp (stub)
            enviar_notificacao_whatsapp(
                pedido,
                'pedido_criado',
                codigo=pedido.codigo,
                link_pagamento=pagamento.gateway_checkout_url
            )
            
            return Response({
                'pedido_codigo': pedido.codigo,
                'pedido_id': pedido.id,
                'valor_total': str(pedido.valor_total),
                'moeda': pedido.moeda,
                'pagamento': pagamento_serializer.data
            }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def webhook_mercadopago(request):
    """
    Webhook do Mercado Pago.
    POST /api/v1/pagamentos/webhook/mercadopago/
    """
    import json
    
    try:
        payload = json.loads(request.body)
        signature = request.META.get('HTTP_X_SIGNATURE', '')
        
        # Validar webhook
        gateway_service = get_gateway_service('mercadopago')
        if not gateway_service.validar_webhook(payload, signature):
            return Response({'error': 'Assinatura inválida'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Processar webhook
        dados = gateway_service.processar_webhook(payload)
        gateway_payment_id = dados['gateway_payment_id']
        
        # Buscar pagamento
        try:
            pagamento = Pagamento.objects.get(gateway_payment_id=gateway_payment_id)
        except Pagamento.DoesNotExist:
            return Response({'error': 'Pagamento não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
        # Registrar transação
        TransacaoGateway.objects.create(
            pagamento=pagamento,
            tipo_evento=dados['tipo_evento'],
            payload=dados['payload']
        )
        
        # Atualizar status do pagamento
        status_anterior = pagamento.status
        pagamento.status = dados['status']
        pagamento.save()
        
        # Atualizar pedido conforme status do pagamento
        if pagamento.status == Pagamento.Status.CONFIRMADO:
            pagamento.confirmar()
            enviar_notificacao_whatsapp(
                pagamento.pedido,
                'pagamento_aprovado',
                codigo=pagamento.pedido.codigo
            )
        elif pagamento.status == Pagamento.Status.RECUSADO:
            pagamento.recusar()
            enviar_notificacao_whatsapp(
                pagamento.pedido,
                'pagamento_recusado',
                codigo=pagamento.pedido.codigo,
                link_regerar=f"/api/v1/pagamentos/{pagamento.pedido.codigo}/regerar-link/"
            )
        
        return Response({'status': 'ok', 'pagamento_id': pagamento.id})
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def webhook_stripe(request):
    """
    Webhook do Stripe.
    POST /api/v1/pagamentos/webhook/stripe/
    """
    import json
    
    try:
        payload = json.loads(request.body)
        signature = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        
        # Validar webhook
        gateway_service = get_gateway_service('stripe')
        if not gateway_service.validar_webhook(payload, signature):
            return Response({'error': 'Assinatura inválida'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Processar webhook
        dados = gateway_service.processar_webhook(payload)
        gateway_payment_id = dados['gateway_payment_id']
        
        # Buscar pagamento
        try:
            pagamento = Pagamento.objects.get(gateway_payment_id=gateway_payment_id)
        except Pagamento.DoesNotExist:
            return Response({'error': 'Pagamento não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
        # Registrar transação
        TransacaoGateway.objects.create(
            pagamento=pagamento,
            tipo_evento=dados['tipo_evento'],
            payload=dados['payload']
        )
        
        # Atualizar status
        pagamento.status = dados['status']
        pagamento.save()
        
        # Atualizar pedido
        if pagamento.status == Pagamento.Status.CONFIRMADO:
            pagamento.confirmar()
        elif pagamento.status == Pagamento.Status.RECUSADO:
            pagamento.recusar()
        
        return Response({'status': 'ok', 'pagamento_id': pagamento.id})
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def regerar_link_pagamento(request, pedido_codigo):
    """
    Regerar link de pagamento para um pedido.
    POST /api/v1/pagamentos/{pedido_codigo}/regerar-link/
    """
    try:
        pedido = get_object_or_404(Pedido, codigo=pedido_codigo)
        
        # Verificar se tem pagamento
        if not hasattr(pedido, 'pagamento'):
            return Response(
                {'error': 'Pedido não possui pagamento'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        pagamento = pedido.pagamento
        
        # Só pode regerar se estiver pendente ou recusado
        if pagamento.status not in [Pagamento.Status.PENDENTE, Pagamento.Status.RECUSADO]:
            return Response(
                {'error': 'Pagamento não pode ser regerado neste status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Criar novo pagamento no gateway
        gateway_service = get_gateway_service(pagamento.gateway)
        resultado = gateway_service.criar_pagamento(pagamento)
        
        if not resultado.get('success'):
            return Response(
                {'error': 'Erro ao regerar pagamento', 'details': resultado.get('error')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Atualizar status
        pagamento.status = Pagamento.Status.PENDENTE
        pagamento.save()
        
        # Serializar resposta
        serializer = PagamentoSerializer(pagamento)
        
        return Response({
            'pagamento': serializer.data,
            'mensagem': 'Link de pagamento regerado com sucesso'
        })
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

