from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator


# ============================================================================
# MODELOS BASE - Empresa, Categoria, Produto
# ============================================================================

class Empresa(models.Model):
    nome      = models.CharField(max_length=100)
    cnpj      = models.CharField(max_length=18, unique=True)
    email     = models.EmailField()
    telefone  = models.CharField(max_length=20, blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'

    def __str__(self):
        return self.nome


class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'

    def __str__(self):
        return self.nome


class Produto(models.Model):
    empresa      = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='produtos')
    nome         = models.CharField(max_length=100)
    descricao    = models.TextField()
    preco        = models.DecimalField(max_digits=10, decimal_places=2)
    categoria    = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name='produtos')
    imagem       = models.ImageField(upload_to='produtos/', blank=True, null=True)
    criado_em    = models.DateTimeField(auto_now_add=True)
    ativo        = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['-criado_em']

    def __str__(self):
        return self.nome


# ============================================================================
# PERFIS DE USUÁRIO - Cliente, PersonalShopper, Keeper
# ============================================================================

class Cliente(models.Model):
    user      = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cliente')
    telefone  = models.CharField(max_length=20, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def personal_shoppers(self):
        """Retorna personal shoppers que este cliente segue"""
        return PersonalShopper.objects.filter(
            relacionamento_clienteshopper__cliente=self,
            relacionamento_clienteshopper__status='seguindo'
        )

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class PersonalShopper(models.Model):
    user      = models.OneToOneField(User, on_delete=models.CASCADE, related_name='personalshopper')
    nome      = models.CharField(max_length=150, blank=True)
    bio       = models.TextField(blank=True)
    
    # Redes sociais
    facebook  = models.URLField(blank=True)
    tiktok    = models.URLField(blank=True)
    twitter   = models.URLField(blank=True)
    linkedin  = models.URLField(blank=True)
    pinterest = models.URLField(blank=True)
    youtube   = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    
    empresa   = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True, related_name='personal_shoppers')
    ativo     = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Personal Shopper'
        verbose_name_plural = 'Personal Shoppers'

    def clientes(self):
        """Retorna clientes que seguem este personal shopper"""
        return Cliente.objects.filter(
            relacionamento_clienteshopper__personal_shopper=self,
            relacionamento_clienteshopper__status='seguindo'
        )

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Keeper(models.Model):
    """Address Keeper - pessoa que recebe, guarda e despacha produtos"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='keeper')
    
    # Localização do ponto de guarda
    apelido_local = models.CharField(max_length=100, blank=True, help_text="Ex: Vila Angélica - Sorocaba")
    rua           = models.CharField(max_length=200, blank=True)
    numero        = models.CharField(max_length=20, blank=True)
    complemento   = models.CharField(max_length=100, blank=True)
    bairro        = models.CharField(max_length=100, blank=True)
    cidade        = models.CharField(max_length=100, blank=True)
    estado        = models.CharField(max_length=2, blank=True)
    cep           = models.CharField(max_length=12, blank=True)
    pais          = models.CharField(max_length=50, default='Brasil')
    
    # Capacidade e taxas
    capacidade_itens  = models.PositiveIntegerField(default=0, help_text="Capacidade aproximada (qtde de volumes)")
    ocupacao_percent  = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # calculado
    taxa_guarda_dia   = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text="R$/dia por volume")
    taxa_motoboy      = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text="Preço base (opcional)")
    
    # Opções
    aceita_retirada = models.BooleanField(default=True)
    aceita_envio    = models.BooleanField(default=True)
    
    # Status
    verificado = models.BooleanField(default=False)
    ativo      = models.BooleanField(default=True)
    criado_em  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Keeper'
        verbose_name_plural = 'Keepers'

    def __str__(self):
        return f"Keeper {self.user.get_full_name() or self.user.username} - {self.apelido_local or self.cidade}"


class RelacionamentoClienteShopper(models.Model):
    """Relacionamento entre Cliente e Personal Shopper"""
    
    class Status(models.TextChoices):
        SOLICITADO = 'solicitado', 'Solicitado'
        SEGUINDO   = 'seguindo', 'Seguindo'
        RECUSADO   = 'recusado', 'Recusado'
        BLOQUEADO  = 'bloqueado', 'Bloqueado'

    cliente          = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    personal_shopper = models.ForeignKey(PersonalShopper, on_delete=models.CASCADE)
    status           = models.CharField(max_length=20, choices=Status.choices, default=Status.SOLICITADO)
    data_criacao     = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('cliente', 'personal_shopper')
        verbose_name = 'Relacionamento Cliente-Shopper'
        verbose_name_plural = 'Relacionamentos Cliente-Shopper'

    def __str__(self):
        return f"{self.cliente.user.username} ↔ {self.personal_shopper.user.username} ({self.get_status_display()})"


# ============================================================================
# SISTEMA DE PACOTES (Address Keeper)
# ============================================================================

class Pacote(models.Model):
    """Pacote/Volume gerenciado por um Keeper"""
    
    class Status(models.TextChoices):
        CRIADO           = 'criado', 'Criado'
        AGUARDANDO_RECEB = 'aguardando_receb', 'Aguardando recebimento'
        RECEBIDO         = 'recebido', 'Recebido'
        EM_GUARDA        = 'em_guarda', 'Em guarda'
        PRONTO_ENVIO     = 'pronto_envio', 'Pronto para envio/retirada'
        DESPACHADO       = 'despachado', 'Despachado'
        ENTREGUE         = 'entregue', 'Entregue'
        DEVOLVIDO        = 'devolvido', 'Devolvido'
        CANCELADO        = 'cancelado', 'Cancelado'

    class ConfirmacaoVisual(models.TextChoices):
        NENHUMA  = 'nenhuma', '—'
        APROVADO = 'aprovado', '👍'
        AMOR     = 'amor', '❤️'

    codigo_publico   = models.CharField(max_length=20, unique=True, help_text="Código que o cliente usa para referência")
    cliente          = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='pacotes')
    personal_shopper = models.ForeignKey(PersonalShopper, on_delete=models.SET_NULL, null=True, blank=True, related_name='pacotes')
    keeper           = models.ForeignKey(Keeper, on_delete=models.SET_NULL, null=True, blank=True, related_name='pacotes')

    descricao        = models.CharField(max_length=200, blank=True)
    valor_declarado  = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    peso_kg          = models.DecimalField(max_digits=7, decimal_places=3, default=0)
    dimensoes_cm     = models.CharField(max_length=50, blank=True, help_text="LxAxP em cm")

    status              = models.CharField(max_length=20, choices=Status.choices, default=Status.CRIADO)
    confirmacao_visual  = models.CharField(max_length=20, choices=ConfirmacaoVisual.choices, default=ConfirmacaoVisual.NENHUMA)

    recebido_em   = models.DateTimeField(null=True, blank=True)
    guarda_inicio = models.DateTimeField(null=True, blank=True)
    guarda_fim    = models.DateTimeField(null=True, blank=True)

    foto_recebimento = models.ImageField(upload_to='pacotes/', null=True, blank=True)
    observacoes      = models.TextField(blank=True)

    criado_em     = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pacote'
        verbose_name_plural = 'Pacotes'
        ordering = ['-criado_em']

    def dias_em_guarda(self):
        """Calcula quantos dias o pacote está em guarda"""
        if self.guarda_inicio:
            dt_end = self.guarda_fim or timezone.now()
            return max(0, (dt_end - self.guarda_inicio).days)
        return 0

    def custo_guarda_estimado(self):
        """Calcula o custo estimado de guarda"""
        if not self.keeper or not self.keeper.taxa_guarda_dia:
            return 0
        return self.dias_em_guarda() * float(self.keeper.taxa_guarda_dia)

    def __str__(self):
        return f"Pacote {self.codigo_publico} ({self.get_status_display()})"


class MovimentoPacote(models.Model):
    """Auditoria de movimentações do pacote"""
    pacote     = models.ForeignKey(Pacote, on_delete=models.CASCADE, related_name='movimentos')
    status     = models.CharField(max_length=20, choices=Pacote.Status.choices)
    mensagem   = models.CharField(max_length=200, blank=True)
    criado_em  = models.DateTimeField(auto_now_add=True)
    autor      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = 'Movimento de Pacote'
        verbose_name_plural = 'Movimentos de Pacotes'
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.pacote.codigo_publico} - {self.get_status_display()} em {self.criado_em.strftime('%d/%m/%Y %H:%M')}"


class FotoPacote(models.Model):
    """Múltiplas fotos do pacote"""
    pacote    = models.ForeignKey(Pacote, on_delete=models.CASCADE, related_name='fotos')
    imagem    = models.ImageField(upload_to='pacotes/')
    legenda   = models.CharField(max_length=140, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Foto de Pacote'
        verbose_name_plural = 'Fotos de Pacotes'
        ordering = ['-criado_em']

    def __str__(self):
        return f"Foto do {self.pacote.codigo_publico}"


class OpcaoEnvio(models.Model):
    """Opções de envio disponibilizadas pelo Keeper"""
    
    class Tipo(models.TextChoices):
        RETIRADA_LOCAL = 'retirada_local', 'Retirada local'
        MOTOBOY        = 'motoboy', 'Motoboy'
        CORREIOS       = 'correios', 'Correios'
        COURIER        = 'courier', 'Courier (FedEx/UPS/DHL)'
        VIAJANTE       = 'viajante', 'Viajante'

    keeper       = models.ForeignKey(Keeper, on_delete=models.CASCADE, related_name='opcoes_envio')
    tipo         = models.CharField(max_length=20, choices=Tipo.choices)
    cidade       = models.CharField(max_length=100, blank=True)
    valor_base   = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    observacoes  = models.CharField(max_length=200, blank=True)
    ativo        = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Opção de Envio'
        verbose_name_plural = 'Opções de Envio'

    def __str__(self):
        cidade_str = f" - {self.cidade}" if self.cidade else ""
        return f"{self.get_tipo_display()}{cidade_str} (R$ {self.valor_base})"


# ============================================================================
# SISTEMA DE PEDIDOS E PAGAMENTOS
# ============================================================================

class EnderecoEntrega(models.Model):
    cliente     = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='enderecos')
    apelido     = models.CharField(max_length=50, blank=True, help_text="Ex: Casa, Trabalho, etc.")
    rua         = models.CharField(max_length=200)
    numero      = models.CharField(max_length=10)
    complemento = models.CharField(max_length=200, blank=True)
    bairro      = models.CharField(max_length=100, blank=True)
    cidade      = models.CharField(max_length=100)
    estado      = models.CharField(max_length=2)
    cep         = models.CharField(max_length=9)
    padrao      = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Endereço de Entrega'
        verbose_name_plural = 'Endereços de Entrega'

    def __str__(self):
        return f"{self.apelido or 'Endereço'} - {self.rua}, {self.numero}, {self.cidade}/{self.estado}"


class CupomDesconto(models.Model):
    codigo              = models.CharField(max_length=20, unique=True)
    descricao           = models.TextField(blank=True)
    desconto_percentual = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    ativo               = models.BooleanField(default=True)
    valido_ate          = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Cupom de Desconto'
        verbose_name_plural = 'Cupons de Desconto'

    def __str__(self):
        return f"{self.codigo} - {self.desconto_percentual}%"


class Pedido(models.Model):
    """Pedido de produtos ou serviços"""
    
    class Status(models.TextChoices):
        PENDENTE      = 'pendente', 'Pendente'
        PAGO          = 'pago', 'Pago'
        EM_PREPARACAO = 'em_preparacao', 'Em preparação'
        ENVIADO       = 'enviado', 'Enviado'
        ENTREGUE      = 'entregue', 'Entregue'
        CANCELADO     = 'cancelado', 'Cancelado'

    class MetodoPagamento(models.TextChoices):
        PIX            = 'pix', 'PIX'
        CARTAO_CREDITO = 'cartao_credito', 'Cartão de Crédito'
        CARTAO_DEBITO  = 'cartao_debito', 'Cartão de Débito'
        BOLETO         = 'boleto', 'Boleto'
        DINHEIRO       = 'dinheiro', 'Dinheiro'

    cliente             = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='pedidos')
    endereco_entrega    = models.ForeignKey(EnderecoEntrega, on_delete=models.CASCADE)
    cupom               = models.ForeignKey(CupomDesconto, null=True, blank=True, on_delete=models.SET_NULL)
    
    criado_em           = models.DateTimeField(auto_now_add=True)
    atualizado_em       = models.DateTimeField(auto_now=True)
    status              = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE)
    metodo_pagamento    = models.CharField(max_length=20, choices=MetodoPagamento.choices, blank=True, null=True)
    valor_total         = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    observacoes         = models.TextField(blank=True)
    codigo_rastreamento = models.CharField(max_length=100, blank=True, null=True)
    is_revisado         = models.BooleanField(default=False)
    is_prioritario      = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-criado_em']

    def calcular_total(self):
        """Calcula o total do pedido com itens e cupom"""
        total = sum(item.subtotal() for item in self.itens.all())
        if self.cupom and self.cupom.ativo:
            total -= total * (self.cupom.desconto_percentual / 100)
        self.valor_total = total
        return total

    def salvar_com_total(self):
        """Salva o pedido recalculando o total"""
        self.valor_total = self.calcular_total()
        self.save()

    def __str__(self):
        return f"Pedido #{self.id} - {self.cliente.user.username} - {self.get_status_display()}"


class ItemPedido(models.Model):
    """Item de um pedido"""
    pedido         = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='itens')
    produto        = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade     = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    cupom          = models.ForeignKey(CupomDesconto, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'Item de Pedido'
        verbose_name_plural = 'Itens de Pedido'

    def subtotal(self):
        """Calcula o subtotal do item"""
        return self.quantidade * self.preco_unitario

    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome}"


class PagamentoIntent(models.Model):
    """Intenção de pagamento com suporte a parcelamento e links externos"""
    
    class Metodo(models.TextChoices):
        PIX            = 'pix', 'PIX'
        CARTAO_CREDITO = 'cartao_credito', 'Cartão de Crédito'
        CARTAO_DEBITO  = 'cartao_debito', 'Cartão de Débito'
        BOLETO         = 'boleto', 'Boleto'
        LINK_EXTERNO   = 'link_externo', 'Link Externo'

    class Status(models.TextChoices):
        CRIADO    = 'criado', 'Criado'
        PENDENTE  = 'pendente', 'Pendente'
        PAGO      = 'pago', 'Pago'
        FALHOU    = 'falhou', 'Falhou'
        CANCELADO = 'cancelado', 'Cancelado'

    pedido          = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='pagamentos')
    metodo          = models.CharField(max_length=20, choices=Metodo.choices)
    status          = models.CharField(max_length=20, choices=Status.choices, default=Status.CRIADO)
    valor_total     = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    entrada_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Ex: 50.00 = 50%")
    gateway_ref     = models.CharField(max_length=120, blank=True, help_text="ID do link/QR no provedor")
    criado_em       = models.DateTimeField(auto_now_add=True)
    atualizado_em   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pagamento Intent'
        verbose_name_plural = 'Pagamentos Intent'
        ordering = ['-criado_em']

    def __str__(self):
        return f"Pagamento {self.get_metodo_display()} - Pedido #{self.pedido.id} ({self.get_status_display()})"


class PagamentoSplit(models.Model):
    """Split de pagamento entre múltiplos favorecidos"""
    intent     = models.ForeignKey(PagamentoIntent, on_delete=models.CASCADE, related_name='splits')
    favorecido = models.ForeignKey(User, on_delete=models.CASCADE)
    percentual = models.DecimalField(max_digits=5, decimal_places=2, help_text="Ex: 10.00 = 10%")
    valor      = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Split de Pagamento'
        verbose_name_plural = 'Splits de Pagamento'

    def __str__(self):
        return f"{self.favorecido.username} - {self.percentual}% (R$ {self.valor})"


class PedidoPacote(models.Model):
    """Relacionamento entre Pedido e Pacote"""
    pedido     = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='pacotes_relacionados')
    pacote     = models.ForeignKey(Pacote, on_delete=models.CASCADE, related_name='pedidos_relacionados')
    finalidade = models.CharField(max_length=50, blank=True, help_text="guarda, reembalagem, envio, etc.")

    class Meta:
        verbose_name = 'Pedido-Pacote'
        verbose_name_plural = 'Pedidos-Pacotes'

    def __str__(self):
        return f"Pedido #{self.pedido.id} → Pacote {self.pacote.codigo_publico}"


# ============================================================================
# EVENTOS E ESTABELECIMENTOS
# ============================================================================

class Estabelecimento(models.Model):
    nome        = models.CharField(max_length=150)
    endereco    = models.CharField(max_length=300, blank=True)
    telefone    = models.CharField(max_length=20, blank=True)
    email       = models.EmailField(blank=True)
    descricao   = models.TextField(blank=True)
    criado_em   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Estabelecimento'
        verbose_name_plural = 'Estabelecimentos'

    def __str__(self):
        return self.nome


class Evento(models.Model):
    """Eventos organizados por Personal Shoppers"""
    
    class Status(models.TextChoices):
        ATIVO      = 'ativo', 'Ativo'
        ENCERRADO  = 'encerrado', 'Encerrado'
        PRIVADO    = 'privado', 'Privado'

    personal_shopper = models.ForeignKey(PersonalShopper, on_delete=models.CASCADE, related_name='eventos')
    titulo           = models.CharField(max_length=100)
    descricao        = models.TextField(blank=True)
    data_inicio      = models.DateTimeField()
    data_fim         = models.DateTimeField()
    clientes         = models.ManyToManyField(Cliente, related_name='eventos', blank=True)
    estabelecimentos = models.ManyToManyField(Estabelecimento, related_name='eventos', blank=True)
    status           = models.CharField(max_length=20, choices=Status.choices, default=Status.ATIVO)
    criado_em        = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
        ordering = ['-data_inicio']

    def __str__(self):
        return f"{self.titulo} - {self.personal_shopper.user.get_full_name()}"


class ProdutoEvento(models.Model):
    """Produtos vinculados a eventos"""
    evento       = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='produto_eventos')
    produto      = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='produto_eventos')
    importado_de = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='importacoes')

    class Meta:
        unique_together = ('evento', 'produto')
        verbose_name = 'Produto de Evento'
        verbose_name_plural = 'Produtos de Eventos'

    def __str__(self):
        return f"{self.produto.nome} no evento {self.evento.titulo}"


# ============================================================================
# CHAT-COMMERCE: captura de intenções de compra
# ============================================================================

class IntentCompra(models.Model):
    """Captura de mensagens 'QUERO' transformadas em pedidos"""
    
    class Status(models.TextChoices):
        NOVO        = 'novo', 'Novo'
        PROCESSADO  = 'processado', 'Processado'
        ERRO        = 'erro', 'Erro'

    cliente          = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='intents')
    personal_shopper = models.ForeignKey(PersonalShopper, on_delete=models.SET_NULL, null=True, blank=True)
    origem_mid       = models.CharField(max_length=120, blank=True, help_text="ID msg externa (WhatsApp, etc)")
    texto_bruto      = models.TextField()
    interpretado     = models.JSONField(default=dict, blank=True)
    status           = models.CharField(max_length=20, choices=Status.choices, default=Status.NOVO)
    criado_em        = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Intent de Compra'
        verbose_name_plural = 'Intents de Compra'
        ordering = ['-criado_em']

    def __str__(self):
        return f"Intent {self.id} - {self.cliente.user.username} ({self.get_status_display()})"


# ============================================================================
# INTEGRAÇÃO COM OPENAI
# ============================================================================

class OpenAIKey(models.Model):
    nome             = models.CharField(max_length=100)
    chave_secreta    = models.CharField(max_length=255)
    criado           = models.DateTimeField(auto_now_add=True)
    usado_ultima_vez = models.DateTimeField(null=True, blank=True)
    criado_por       = models.CharField(max_length=100)
    permissoes       = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Chave OpenAI'
        verbose_name_plural = 'Chaves OpenAI'

    def __str__(self):
        return self.nome


# ============================================================================
# INTEGRAÇÃO WHATSAPP - VINCULAÇÃO E TOKENS
# ============================================================================

class WhatsappGroup(models.Model):
    """Grupo do WhatsApp vinculado a um PersonalShopper"""
    chat_id      = models.CharField(max_length=120, unique=True, help_text="JID do grupo (ex: 12036...@g.us)")
    name         = models.CharField(max_length=160, blank=True)
    shopper      = models.ForeignKey(PersonalShopper, on_delete=models.CASCADE, related_name='whatsapp_groups')
    created_at   = models.DateTimeField(default=timezone.now)
    active       = models.BooleanField(default=True)
    meta         = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'Grupo WhatsApp'
        verbose_name_plural = 'Grupos WhatsApp'

    def __str__(self):
        return f"{self.name or self.chat_id} → {self.shopper.user.username}"


class GroupLinkRequest(models.Model):
    """Token temporário para vincular grupo WhatsApp a um Shopper"""
    shopper    = models.ForeignKey(PersonalShopper, on_delete=models.CASCADE, related_name='link_tokens')
    token      = models.CharField(max_length=16, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    used_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Token de Vinculação'
        verbose_name_plural = 'Tokens de Vinculação'

    @property
    def is_valid(self):
        """Verifica se o token ainda é válido"""
        return self.used_at is None and timezone.now() <= self.expires_at

    @staticmethod
    def generate_token(shopper: 'PersonalShopper', ttl_minutes: int = 30):
        """Gera um novo token de vinculação"""
        import secrets
        import string
        from datetime import timedelta
        
        alphabet = string.ascii_uppercase + string.digits
        token = ''.join(secrets.choice(alphabet) for _ in range(6))
        
        return GroupLinkRequest.objects.create(
            shopper=shopper,
            token=token,
            expires_at=timezone.now() + timedelta(minutes=ttl_minutes)
        )

    def __str__(self):
        status = "Usado" if self.used_at else ("Válido" if self.is_valid else "Expirado")
        return f"{self.token} [{status}] - {self.shopper.user.username}"


class ShopperOnboardingToken(models.Model):
    """Token para cadastro de novo Shopper via WhatsApp"""
    token      = models.CharField(max_length=16, unique=True)
    phone      = models.CharField(max_length=32, blank=True, help_text="Telefone que vai usar (opcional)")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shopper_tokens_created')
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    used_at    = models.DateTimeField(null=True, blank=True)
    used_by    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='shopper_token_used')

    class Meta:
        verbose_name = 'Token de Cadastro Shopper'
        verbose_name_plural = 'Tokens de Cadastro Shopper'

    @property
    def is_valid(self):
        return self.used_at is None and timezone.now() <= self.expires_at

    def __str__(self):
        status = "Usado" if self.used_at else ("Válido" if self.is_valid else "Expirado")
        return f"SHOP-{self.token} [{status}]"


class KeeperOnboardingToken(models.Model):
    """Token para cadastro de novo Keeper via WhatsApp"""
    token      = models.CharField(max_length=16, unique=True)
    phone      = models.CharField(max_length=32, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='keeper_tokens_created')
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    used_at    = models.DateTimeField(null=True, blank=True)
    used_by    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='keeper_token_used')

    class Meta:
        verbose_name = 'Token de Cadastro Keeper'
        verbose_name_plural = 'Tokens de Cadastro Keeper'

    @property
    def is_valid(self):
        return self.used_at is None and timezone.now() <= self.expires_at

    def __str__(self):
        status = "Usado" if self.used_at else ("Válido" if self.is_valid else "Expirado")
        return f"KEEP-{self.token} [{status}]"


# ============================================================================
# EXTENSÕES DO USER MODEL (helpers)
# ============================================================================

# Adiciona propriedades convenientes ao User
User.add_to_class('is_cliente', property(lambda u: hasattr(u, 'cliente')))
User.add_to_class('is_shopper', property(lambda u: hasattr(u, 'personalshopper')))
User.add_to_class('is_keeper', property(lambda u: hasattr(u, 'keeper')))
