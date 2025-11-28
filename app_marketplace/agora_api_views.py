"""
API Views para ÁGORA - Feed Social do Évora
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Sum, F, Case, When, IntegerField
from django.utils import timezone
from django.contrib.auth.models import User

from .models import (
    PublicacaoAgora, EngajamentoAgora, Produto, Evento,
    PersonalShopper, Cliente, RelacionamentoClienteShopper
)
from .serializers import (
    PublicacaoAgoraSerializer, PublicacaoAgoraCreateSerializer,
    EngajamentoAgoraSerializer, EngajamentoAgoraCreateSerializer,
    PublicacaoAgoraAnalyticsSerializer
)


class PublicacaoAgoraViewSet(viewsets.ModelViewSet):
    """ViewSet para Publicações do Ágora"""
    queryset = PublicacaoAgora.objects.filter(ativo=True)
    permission_classes = [AllowAny]  # Feed público, mas criação requer auth
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PublicacaoAgoraCreateSerializer
        return PublicacaoAgoraSerializer
    
    def get_permissions(self):
        """Criação requer autenticação, leitura é pública"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [AllowAny()]
    
    def get_queryset(self):
        """Feed com algoritmo de recomendação"""
        queryset = PublicacaoAgora.objects.filter(ativo=True).select_related(
            'autor', 'produto', 'evento'
        ).prefetch_related('engajamentos')
        
        # Filtros opcionais
        autor_id = self.request.query_params.get('autor_id')
        produto_id = self.request.query_params.get('produto_id')
        evento_id = self.request.query_params.get('evento_id')
        mesh_type = self.request.query_params.get('mesh_type')
        
        if autor_id:
            queryset = queryset.filter(autor_id=autor_id)
        if produto_id:
            queryset = queryset.filter(produto_id=produto_id)
        if evento_id:
            queryset = queryset.filter(evento_id=evento_id)
        if mesh_type:
            queryset = queryset.filter(mesh_type=mesh_type)
        
        # Ordenação por algoritmo de recomendação
        # Combina spark_score, PPA e engajamento
        queryset = queryset.annotate(
            total_engajamentos=Count('engajamentos'),
            total_likes_anotado=Count('engajamentos', filter=Q(engajamentos__tipo='like')),
            total_views_anotado=Count('engajamentos', filter=Q(engajamentos__tipo='view')),
        ).order_by(
            '-spark_score',
            '-ppa',
            '-total_engajamentos',
            '-criado_em'
        )
        
        return queryset
    
    def perform_create(self, serializer):
        """Define o autor automaticamente"""
        serializer.save(autor=self.request.user)
    
    @action(detail=True, methods=['post'])
    def registrar_engajamento(self, request, pk=None):
        """Registra um engajamento (like, view, add_carrinho, etc.)"""
        publicacao = self.get_object()
        tipo = request.data.get('tipo')
        view_time_segundos = request.data.get('view_time_segundos', 0)
        
        if tipo not in [choice[0] for choice in EngajamentoAgora.TipoEngajamento.choices]:
            return Response(
                {'error': 'Tipo de engajamento inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Criar engajamento
        engajamento = EngajamentoAgora.objects.create(
            publicacao=publicacao,
            usuario=request.user if request.user.is_authenticated else None,
            tipo=tipo,
            view_time_segundos=view_time_segundos if tipo == 'view' else 0,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        serializer = EngajamentoAgoraSerializer(engajamento)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def _get_client_ip(self, request):
        """Obtém o IP do cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@api_view(['GET'])
@permission_classes([AllowAny])
def agora_feed(request):
    """
    Endpoint principal do feed Ágora.
    Retorna publicações ordenadas por algoritmo de recomendação.
    """
    limit = int(request.GET.get('limit', 10))
    offset = int(request.GET.get('offset', 0))
    
    # Algoritmo de recomendação determinístico
    queryset = PublicacaoAgora.objects.filter(ativo=True).select_related(
        'autor', 'produto', 'evento'
    ).prefetch_related('engajamentos')
    
    # Anotar estatísticas
    queryset = queryset.annotate(
        total_views_anotado=Count('engajamentos', filter=Q(engajamentos__tipo='view')),
        total_likes_anotado=Count('engajamentos', filter=Q(engajamentos__tipo='like')),
        total_add_carrinho_anotado=Count('engajamentos', filter=Q(engajamentos__tipo='add_carrinho')),
        total_compartilhar_anotado=Count('engajamentos', filter=Q(engajamentos__tipo='compartilhar')),
        total_view_time_anotado=Sum('engajamentos__view_time_segundos', filter=Q(engajamentos__tipo='view'))
    )
    
    # Ordenação: spark_score + PPA + engajamento + recência
    queryset = queryset.order_by(
        '-spark_score',
        '-ppa',
        '-total_likes_anotado',
        '-total_views_anotado',
        '-criado_em'
    )
    
    # Paginação
    publicacoes = queryset[offset:offset + limit]
    
    serializer = PublicacaoAgoraSerializer(publicacoes, many=True)
    
    return Response({
        'results': serializer.data,
        'count': queryset.count(),
        'next': f"?limit={limit}&offset={offset + limit}" if offset + limit < queryset.count() else None,
        'previous': f"?limit={limit}&offset={max(0, offset - limit)}" if offset > 0 else None
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def agora_publicar(request):
    """
    Endpoint para criar uma publicação no Ágora.
    Apenas Shoppers e Keepers podem publicar.
    """
    if not (request.user.is_shopper or request.user.is_agente):
        return Response(
            {'error': 'Apenas Shoppers e Keepers podem publicar'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = PublicacaoAgoraCreateSerializer(data=request.data)
    if serializer.is_valid():
        publicacao = serializer.save(autor=request.user)
        
        # Calcular spark_score inicial (pode ser melhorado depois)
        publicacao.spark_score = calcular_spark_score_inicial(publicacao)
        publicacao.save()
        
        response_serializer = PublicacaoAgoraSerializer(publicacao)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def agora_analytics(request):
    """
    Endpoint para analytics/ranking do Ágora.
    Retorna top publicações por spark_score e engajamento.
    """
    limit = int(request.GET.get('limit', 50))
    
    queryset = PublicacaoAgora.objects.filter(ativo=True).select_related(
        'autor', 'produto'
    ).prefetch_related('engajamentos')
    
    # Anotar todas as estatísticas
    queryset = queryset.annotate(
        total_views_anotado=Count('engajamentos', filter=Q(engajamentos__tipo='view')),
        total_likes_anotado=Count('engajamentos', filter=Q(engajamentos__tipo='like')),
        total_add_carrinho_anotado=Count('engajamentos', filter=Q(engajamentos__tipo='add_carrinho')),
        total_compartilhar_anotado=Count('engajamentos', filter=Q(engajamentos__tipo='compartilhar')),
        total_view_time_anotado=Sum('engajamentos__view_time_segundos', filter=Q(engajamentos__tipo='view'))
    ).order_by('-spark_score', '-total_likes_anotado')[:limit]
    
    # Montar dados para serializer
    analytics_data = []
    for pub in queryset:
        analytics_data.append({
            'id': pub.id,
            'autor_id': pub.autor.id,
            'autor_nome': pub.autor.get_full_name() or pub.autor.username,
            'produto_id': pub.produto.id if pub.produto else None,
            'produto_nome': pub.produto.nome if pub.produto else None,
            'produto_imagem': pub.produto.imagem if pub.produto else None,
            'video_url': pub.video_url,
            'imagem_url': pub.imagem_url,
            'spark_score': pub.spark_score,
            'ppa': pub.ppa,
            'mesh_type': pub.mesh_type,
            'total_views': pub.total_views_anotado or 0,
            'total_likes': pub.total_likes_anotado or 0,
            'total_add_carrinho': pub.total_add_carrinho_anotado or 0,
            'total_compartilhar': pub.total_compartilhar_anotado or 0,
            'total_view_time': int(pub.total_view_time_anotado or 0),
            'criado_em': pub.criado_em
        })
    
    serializer = PublicacaoAgoraAnalyticsSerializer(analytics_data, many=True)
    return Response(serializer.data)


def calcular_spark_score_inicial(publicacao):
    """
    Calcula o SparkScore inicial de uma publicação.
    Versão determinística inicial - pode ser melhorada com IA depois.
    """
    score = 0.0
    
    # Base: 10 pontos
    score += 10.0
    
    # Produto vinculado: +20
    if publicacao.produto:
        score += 20.0
    
    # Vídeo: +15 (mais engajamento)
    if publicacao.video_url:
        score += 15.0
    elif publicacao.imagem_url:
        score += 10.0
    
    # Evento/Campanha ativa: +25
    if publicacao.evento:
        agora = timezone.now()
        if publicacao.evento.data_inicio <= agora <= publicacao.evento.data_fim:
            score += 25.0
    
    # Mesh type: Mall = +5, Mesh Forte = +15, Mesh Fraca = +10
    if publicacao.mesh_type == PublicacaoAgora.TipoMesh.MALL:
        score += 5.0
    elif publicacao.mesh_type == PublicacaoAgora.TipoMesh.MESH_FORTE:
        score += 15.0
    elif publicacao.mesh_type == PublicacaoAgora.TipoMesh.MESH_FRACA:
        score += 10.0
    
    # PPA: multiplicador (0.0-1.0) * 30
    score += float(publicacao.ppa) * 30.0
    
    # Limitar a 100
    return min(score, 100.0)

