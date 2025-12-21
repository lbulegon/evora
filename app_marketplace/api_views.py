"""
API Views para KMN (Keeper Mesh Network)
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth.models import User

from .models import (
    Agente, Cliente, ClienteRelacao, Produto, EstoqueItem,
    Oferta, TrustlineKeeper, RoleStats, Pedido, EnderecoEntrega,
    ProdutoJSON, OfertaProduto
)
from .serializers import (
    AgenteSerializer, ClienteSerializer, ClienteRelacaoSerializer,
    ProdutoSerializer, EstoqueItemSerializer, OfertaSerializer,
    OfertaCreateSerializer, TrustlineKeeperSerializer, TrustlineCreateSerializer,
    RoleStatsSerializer, CatalogoSerializer, PedidoKMNCreateSerializer,
    PedidoKMNSerializer, ScoreAgenteSerializer, ProdutoJSONSerializer,
    OfertaProdutoSerializer
)
from .services import KMNRoleEngine, KMNStatsService, CatalogoService


class AgenteViewSet(viewsets.ModelViewSet):
    """ViewSet para Agentes KMN"""
    queryset = Agente.objects.all()
    serializer_class = AgenteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros
        ativo_keeper = self.request.query_params.get('ativo_keeper')
        ativo_shopper = self.request.query_params.get('ativo_shopper')
        verificado = self.request.query_params.get('verificado')
        
        if ativo_keeper is not None:
            queryset = queryset.filter(ativo_como_keeper=ativo_keeper.lower() == 'true')
        if ativo_shopper is not None:
            queryset = queryset.filter(ativo_como_shopper=ativo_shopper.lower() == 'true')
        if verificado is not None:
            queryset = queryset.filter(verificado_kmn=verificado.lower() == 'true')
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def score(self, request, pk=None):
        """Retorna score detalhado do agente"""
        agente = self.get_object()
        score_data = KMNStatsService.calcular_score_agente(agente)
        serializer = ScoreAgenteSerializer(score_data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Retorna estatísticas do agente"""
        agente = self.get_object()
        try:
            stats = agente.stats
            serializer = RoleStatsSerializer(stats)
            return Response(serializer.data)
        except RoleStats.DoesNotExist:
            return Response({'detail': 'Estatísticas não encontradas'}, status=404)
    
    @action(detail=True, methods=['get'])
    def clientes(self, request, pk=None):
        """Lista clientes do agente"""
        agente = self.get_object()
        relacoes = ClienteRelacao.objects.filter(
            agente=agente,
            status=ClienteRelacao.StatusRelacao.ATIVA
        ).order_by('-forca_relacao')
        
        serializer = ClienteRelacaoSerializer(relacoes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def trustlines(self, request, pk=None):
        """Lista trustlines do agente"""
        agente = self.get_object()
        trustlines = TrustlineKeeper.objects.filter(
            models.Q(agente_a=agente) | models.Q(agente_b=agente),
            status=TrustlineKeeper.StatusTrustline.ATIVA
        )
        
        serializer = TrustlineKeeperSerializer(trustlines, many=True)
        return Response(serializer.data)


class ClienteViewSet(viewsets.ModelViewSet):
    """ViewSet para Clientes"""
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def catalogo(self, request, pk=None):
        """Retorna catálogo personalizado para o cliente"""
        cliente = self.get_object()
        catalogo = CatalogoService.gerar_catalogo_cliente(cliente)
        serializer = CatalogoSerializer(catalogo)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def agentes(self, request, pk=None):
        """Lista agentes relacionados ao cliente"""
        cliente = self.get_object()
        relacoes = ClienteRelacao.objects.filter(
            cliente=cliente,
            status=ClienteRelacao.StatusRelacao.ATIVA
        ).order_by('-forca_relacao')
        
        serializer = ClienteRelacaoSerializer(relacoes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def owner_primario(self, request, pk=None):
        """Retorna o owner primário do cliente"""
        cliente = self.get_object()
        engine = KMNRoleEngine()
        owner = engine.get_primary_owner(cliente.id)
        
        if owner:
            serializer = AgenteSerializer(owner)
            return Response(serializer.data)
        else:
            return Response({'detail': 'Owner primário não encontrado'}, status=404)


class ProdutoViewSet(viewsets.ModelViewSet):
    """ViewSet para Produtos"""
    queryset = Produto.objects.filter(ativo=True)
    serializer_class = ProdutoSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def ofertas(self, request, pk=None):
        """Lista ofertas do produto"""
        produto = self.get_object()
        ofertas = Oferta.objects.filter(
            produto=produto,
            ativo=True,
            quantidade_disponivel__gt=0
        ).order_by('preco_oferta')
        
        serializer = OfertaSerializer(ofertas, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def escolher_oferta(self, request, pk=None):
        """Escolhe a oferta correta para um cliente específico"""
        produto = self.get_object()
        cliente_id = request.data.get('cliente_id')
        
        if not cliente_id:
            return Response({'error': 'cliente_id é obrigatório'}, status=400)
        
        try:
            cliente = Cliente.objects.get(id=cliente_id)
            engine = KMNRoleEngine()
            oferta = engine.escolher_oferta_para_cliente(cliente, produto)
            
            if oferta:
                serializer = OfertaSerializer(oferta)
                return Response({
                    'oferta': serializer.data,
                    'debug': engine.debug_info
                })
            else:
                return Response({
                    'error': 'Nenhuma oferta disponível',
                    'debug': engine.debug_info
                }, status=404)
                
        except Cliente.DoesNotExist:
            return Response({'error': 'Cliente não encontrado'}, status=404)


class OfertaViewSet(viewsets.ModelViewSet):
    """ViewSet para Ofertas"""
    queryset = Oferta.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OfertaCreateSerializer
        return OfertaSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros
        produto_id = self.request.query_params.get('produto_id')
        agente_id = self.request.query_params.get('agente_id')
        ativo = self.request.query_params.get('ativo')
        
        if produto_id:
            queryset = queryset.filter(produto_id=produto_id)
        if agente_id:
            queryset = queryset.filter(agente_ofertante_id=agente_id)
        if ativo is not None:
            queryset = queryset.filter(ativo=ativo.lower() == 'true')
        
        return queryset
    
    def perform_create(self, serializer):
        # Definir agente ofertante como o usuário atual (se for agente)
        if hasattr(self.request.user, 'agente'):
            serializer.save(agente_ofertante=self.request.user.agente)
        else:
            return Response({'error': 'Usuário não é um agente'}, status=400)


class EstoqueItemViewSet(viewsets.ModelViewSet):
    """ViewSet para Itens de Estoque"""
    queryset = EstoqueItem.objects.all()
    serializer_class = EstoqueItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros
        agente_id = self.request.query_params.get('agente_id')
        produto_id = self.request.query_params.get('produto_id')
        disponivel = self.request.query_params.get('disponivel')
        
        if agente_id:
            queryset = queryset.filter(agente_id=agente_id)
        if produto_id:
            queryset = queryset.filter(produto_id=produto_id)
        if disponivel is not None:
            if disponivel.lower() == 'true':
                queryset = queryset.filter(quantidade_disponivel__gt=0)
        
        return queryset
    
    def perform_create(self, serializer):
        # Definir agente como o usuário atual (se for agente)
        if hasattr(self.request.user, 'agente'):
            serializer.save(agente=self.request.user.agente)
        else:
            return Response({'error': 'Usuário não é um agente'}, status=400)


class TrustlineKeeperViewSet(viewsets.ModelViewSet):
    """ViewSet para Trustlines KMN"""
    queryset = TrustlineKeeper.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TrustlineCreateSerializer
        return TrustlineKeeperSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros
        agente_id = self.request.query_params.get('agente_id')
        status_filter = self.request.query_params.get('status')
        
        if agente_id:
            queryset = queryset.filter(
                models.Q(agente_a_id=agente_id) | models.Q(agente_b_id=agente_id)
            )
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    def perform_create(self, serializer):
        # Definir agente_a como o usuário atual (se for agente)
        if hasattr(self.request.user, 'agente'):
            serializer.save(agente_a=self.request.user.agente)
        else:
            return Response({'error': 'Usuário não é um agente'}, status=400)
    
    @action(detail=True, methods=['post'])
    def aceitar(self, request, pk=None):
        """Aceita uma trustline pendente"""
        trustline = self.get_object()
        
        # Verificar se o usuário é um dos agentes da trustline
        user_agente = getattr(request.user, 'agente', None)
        if not user_agente or user_agente not in [trustline.agente_a, trustline.agente_b]:
            return Response({'error': 'Não autorizado'}, status=403)
        
        if trustline.status == TrustlineKeeper.StatusTrustline.PENDENTE:
            trustline.status = TrustlineKeeper.StatusTrustline.ATIVA
            trustline.aceito_em = timezone.now()
            trustline.save()
            
            serializer = TrustlineKeeperSerializer(trustline)
            return Response(serializer.data)
        else:
            return Response({'error': 'Trustline não está pendente'}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def criar_pedido_kmn(request):
    """
    Cria um pedido usando o sistema KMN completo.
    """
    serializer = PedidoKMNCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    
    # Verificar se o usuário é um cliente
    try:
        cliente = request.user.cliente
    except:
        return Response({'error': 'Usuário não é um cliente'}, status=400)
    
    try:
        with transaction.atomic():
            # Buscar dados
            produto = get_object_or_404(Produto, id=serializer.validated_data['produto_id'])
            endereco = get_object_or_404(EnderecoEntrega, id=serializer.validated_data['endereco_entrega_id'])
            quantidade = serializer.validated_data['quantidade']
            
            # Processar via KMN Engine
            engine = KMNRoleEngine()
            resultado = engine.processar_pedido_kmn(cliente, produto, quantidade)
            
            if not resultado['sucesso']:
                return Response({
                    'error': resultado.get('erro', 'Erro ao processar pedido'),
                    'debug': resultado.get('debug', {})
                }, status=400)
            
            # Criar pedido
            dados = resultado['dados_pedido']
            pedido = Pedido.objects.create(
                cliente=cliente,
                endereco_entrega=endereco,
                valor_total=dados['valor_total'],
                observacoes=serializer.validated_data.get('observacoes', ''),
                # Campos KMN serão adicionados via migration
            )
            
            # Atualizar estatísticas
            KMNStatsService.atualizar_stats_pedido(
                pedido, 
                dados['agente_shopper'], 
                dados['agente_keeper']
            )
            
            # Serializar resposta
            response_serializer = PedidoKMNSerializer(pedido)
            return Response({
                'pedido': response_serializer.data,
                'kmn_data': dados,
                'debug': resultado.get('debug', {})
            }, status=201)
            
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def catalogo_cliente(request, cliente_id):
    """
    Retorna catálogo personalizado para um cliente específico.
    """
    try:
        cliente = get_object_or_404(Cliente, id=cliente_id)
        
        # Verificar permissão (cliente pode ver seu próprio catálogo, agentes podem ver de seus clientes)
        user_agente = getattr(request.user, 'agente', None)
        if request.user != cliente.user and not user_agente:
            return Response({'error': 'Não autorizado'}, status=403)
        
        catalogo = CatalogoService.gerar_catalogo_cliente(cliente)
        serializer = CatalogoSerializer(catalogo)
        return Response(serializer.data)
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def score_agente(request, agente_id):
    """
    Retorna score detalhado de um agente.
    """
    try:
        agente = get_object_or_404(Agente, id=agente_id)
        score_data = KMNStatsService.calcular_score_agente(agente)
        serializer = ScoreAgenteSerializer(score_data)
        return Response(serializer.data)
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolver_operacao(request):
    """
    Resolve uma operação KMN (papéis, ofertas, comissionamento).
    """
    cliente_id = request.data.get('cliente_id')
    produto_id = request.data.get('produto_id')
    
    if not cliente_id or not produto_id:
        return Response({'error': 'cliente_id e produto_id são obrigatórios'}, status=400)
    
    try:
        cliente = get_object_or_404(Cliente, id=cliente_id)
        produto = get_object_or_404(Produto, id=produto_id)
        
        engine = KMNRoleEngine()
        resolucao = engine.resolver_papeis_operacao(cliente, produto)
        
        # Serializar dados
        response_data = {
            'shopper': AgenteSerializer(resolucao['shopper']).data if resolucao['shopper'] else None,
            'keeper': AgenteSerializer(resolucao['keeper']).data if resolucao['keeper'] else None,
            'canal_entrada': AgenteSerializer(resolucao['canal_entrada']).data if resolucao['canal_entrada'] else None,
            'oferta': OfertaSerializer(resolucao['oferta']).data if resolucao['oferta'] else None,
            'tipo_operacao': resolucao['tipo_operacao'],
            'trustline': TrustlineKeeperSerializer(resolucao['trustline']).data if resolucao['trustline'] else None,
            'debug': resolucao['debug']
        }
        
        return Response(response_data)
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)


class ProdutoJSONViewSet(viewsets.ModelViewSet):
    """ViewSet para ProdutoJSON (produtos cadastrados por foto)"""
    queryset = ProdutoJSON.objects.all()
    serializer_class = ProdutoJSONSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por usuário se for shopper
        if hasattr(self.request.user, 'personalshopper'):
            queryset = queryset.filter(criado_por=self.request.user)
        
        # Filtros opcionais
        grupo_id = self.request.query_params.get('grupo_id')
        categoria = self.request.query_params.get('categoria')
        marca = self.request.query_params.get('marca')
        
        if grupo_id:
            queryset = queryset.filter(grupo_whatsapp_id=grupo_id)
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        if marca:
            queryset = queryset.filter(marca=marca)
        
        return queryset.order_by('-criado_em')


@api_view(['GET'])
@permission_classes([AllowAny])  # Permitir acesso do agente (com API key)
def buscar_oferta_por_id(request, oferta_id):
    """
    Busca uma OfertaProduto por oferta_id.
    Usado pelo agente ágnosto para buscar preço e informações do produto.
    """
    try:
        oferta = OfertaProduto.objects.get(oferta_id=oferta_id, ativo=True)
        serializer = OfertaProdutoSerializer(oferta)
        return Response(serializer.data)
    except OfertaProduto.DoesNotExist:
        return Response(
            {'error': f'Oferta com ID {oferta_id} não encontrada ou inativa'},
            status=status.HTTP_404_NOT_FOUND
        )




