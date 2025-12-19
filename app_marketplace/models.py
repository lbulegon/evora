from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from decimal import Decimal


# ============================================================================
# MODELOS BASE - Empresa, Categoria, Produto
# ============================================================================

class Empresa(models.Model):
    """
    Empresa/Estabelecimento - Representa lojas/comércios em qualquer localização.
    Pode ser usado para lojas de Orlando (USA), Paraguai, Brasil, etc.
    """
    # Identificação básica
    nome      = models.CharField(max_length=200, help_text="Nome da empresa/loja")
    cnpj      = models.CharField(max_length=18, unique=True, null=True, blank=True, help_text="CNPJ (opcional - para empresas brasileiras)")
    email     = models.EmailField()
    telefone  = models.CharField(max_length=20, blank=True)
    website   = models.URLField(blank=True, help_text="Site da empresa/loja")
    
    # Localização física (para estabelecimentos físicos)
    endereco  = models.TextField(blank=True, help_text="Endereço completo")
    cidade    = models.CharField(max_length=100, blank=True, help_text="Ex: Orlando, Ciudad del Este")
    estado    = models.CharField(max_length=50, blank=True, help_text="Ex: FL, Alto Paraná")
    pais      = models.CharField(max_length=50, default='Brasil', help_text="País onde está localizada")
    
    # Coordenadas geográficas (opcional)
    latitude  = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Informações operacionais
    horario_funcionamento = models.TextField(blank=True, help_text="Ex: Seg-Sex: 9h-18h, Sáb: 9h-14h")
    categorias = models.JSONField(default=list, blank=True, help_text="Categorias de produtos vendidos")
    
    # Status
    ativo = models.BooleanField(default=True)
    
    # Timestamps
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Empresa/Estabelecimento'
        verbose_name_plural = 'Empresas/Estabelecimentos'
        ordering = ['nome']

    def __str__(self):
        if self.cidade:
            return f"{self.nome} - {self.cidade}/{self.estado}"
        return self.nome


class Estabelecimento(models.Model):
    """
    Estabelecimento - Representa lojas/comércios físicos.
    Usado principalmente para lojas de Orlando (USA), Paraguai, etc.
    """
    # Identificação básica
    nome = models.CharField(max_length=150, help_text="Nome do estabelecimento")
    endereco = models.CharField(max_length=300, blank=True, help_text="Endereço completo")
    telefone = models.CharField(max_length=20, blank=True)
    
    # Localização
    cidade = models.CharField(max_length=100, default='Orlando', help_text="Ex: Orlando, Ciudad del Este")
    estado = models.CharField(max_length=50, default='FL', help_text="Ex: FL, Alto Paraná")
    pais = models.CharField(max_length=50, default='USA', help_text="País onde está localizado")
    
    # Coordenadas geográficas (opcional)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Informações operacionais
    website = models.URLField(blank=True, help_text="Site do estabelecimento")
    horario_funcionamento = models.TextField(blank=True, help_text="Ex: Seg-Sex: 9h-18h, Sáb: 9h-14h")
    categorias = models.JSONField(default=list, blank=True, help_text="Categorias de produtos vendidos")
    
    # Status
    ativo = models.BooleanField(default=True)
    
    # Timestamps
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Estabelecimento'
        verbose_name_plural = 'Estabelecimentos'
        ordering = ['nome']

    def __str__(self):
        if self.cidade:
            return f"{self.nome} - {self.cidade}/{self.estado}"
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
    """
    Produto do sistema (repositório geral).
    Sem vínculo obrigatório a empresa.
    """
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name='produtos')
    imagem = models.ImageField(upload_to='produtos/', blank=True, null=True)
    
    # NOVO CAMPO - Modelo Oficial
    criado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='produtos_criados',
        help_text="Shopper que criou este produto"
    )
    
    criado_em = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)

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
    """
    Cliente do sistema.
    Pode pertencer a uma CarteiraCliente (novo modelo oficial) ou manter relação direta com User (compatibilidade).
    """
    # Nova estrutura: Carteira de Clientes
    wallet = models.ForeignKey(
        'CarteiraCliente', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='clientes',
        help_text="Carteira à qual este cliente pertence (novo modelo oficial)"
    )
    
    # Estrutura antiga (mantida para compatibilidade)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cliente')
    telefone = models.CharField(max_length=20, blank=True)
    
    # Novos campos
    contato = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Informações de contato (telefone, email, WhatsApp, etc.)"
    )
    metadados = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadados adicionais do cliente"
    )
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['-criado_em']

    def personal_shoppers(self):
        """Retorna personal shoppers que este cliente segue"""
        return PersonalShopper.objects.filter(
            relacionamento_clienteshopper__cliente=self,
            relacionamento_clienteshopper__status='seguindo'
        )
    
    @property
    def owner_carteira(self):
        """Retorna o owner da carteira, se existir"""
        if self.wallet:
            return self.wallet.owner
        return None

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
    
    # Idioma preferido para respostas da IA
    idioma = models.CharField(
        max_length=10,
        default='pt-BR',
        choices=[
            ('pt-BR', 'Português (Brasil)'),
            ('en-US', 'English (US)'),
            ('es-ES', 'Español (España)'),
            ('fr-FR', 'Français'),
            ('de-DE', 'Deutsch'),
            ('it-IT', 'Italiano'),
        ],
        help_text="Idioma preferido para respostas da IA"
    )
    
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


class AddressKeeper(models.Model):
    """
    Address Keeper (Ponto de Guarda) - pessoa que recebe, guarda e despacha pacotes/produtos.
    
    NOTA: Este é diferente do "Keeper" oficial (vendedor passivo).
    O Keeper oficial é representado por User + CarteiraCliente, não por este modelo.
    Este modelo é apenas para pontos físicos de guarda de pacotes.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='address_keeper')
    
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
    
    # Idioma preferido para respostas da IA
    idioma = models.CharField(
        max_length=10,
        default='pt-BR',
        choices=[
            ('pt-BR', 'Português (Brasil)'),
            ('en-US', 'English (US)'),
            ('es-ES', 'Español (España)'),
            ('fr-FR', 'Français'),
            ('de-DE', 'Deutsch'),
            ('it-IT', 'Italiano'),
        ],
        help_text="Idioma preferido para respostas da IA"
    )
    
    # Status
    verificado = models.BooleanField(default=False)
    ativo      = models.BooleanField(default=True)
    criado_em  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Address Keeper (Ponto de Guarda)'
        verbose_name_plural = 'Address Keepers (Pontos de Guarda)'
        db_table = 'app_marketplace_addresskeeper'  # Nome da tabela no banco

    def __str__(self):
        return f"Address Keeper {self.user.get_full_name() or self.user.username} - {self.apelido_local or self.cidade}"


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
    address_keeper   = models.ForeignKey(AddressKeeper, on_delete=models.SET_NULL, null=True, blank=True, related_name='pacotes', help_text="Ponto de guarda que recebe/guarda este pacote")

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
        if not self.address_keeper or not self.address_keeper.taxa_guarda_dia:
            return 0
        return self.dias_em_guarda() * float(self.address_keeper.taxa_guarda_dia)

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

    address_keeper = models.ForeignKey(AddressKeeper, on_delete=models.CASCADE, null=True, blank=True, related_name='opcoes_envio', help_text="Ponto de guarda que oferece esta opção de envio")
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
    """
    Pedido de produtos ou serviços.
    Adaptado para o modelo oficial com tipo_cliente e carteira_cliente.
    """
    
    class Status(models.TextChoices):
        CRIADO                = 'criado', 'Criado'
        AGUARDANDO_PAGAMENTO  = 'aguardando_pagamento', 'Aguardando pagamento'
        PAGO                  = 'pago', 'Pago'
        CANCELADO             = 'cancelado', 'Cancelado'
        EM_PREPARACAO         = 'em_preparacao', 'Em preparação'
        EM_TRANSPORTE         = 'em_transporte', 'Em transporte'
        CONCLUIDO             = 'concluido', 'Concluído'

    class MetodoPagamento(models.TextChoices):
        PIX            = 'pix', 'PIX'
        CARTAO_CREDITO = 'cartao_credito', 'Cartão de Crédito'
        CARTAO_DEBITO  = 'cartao_debito', 'Cartão de Débito'
        BOLETO         = 'boleto', 'Boleto'
        DINHEIRO       = 'dinheiro', 'Dinheiro'
    
    class TipoCliente(models.TextChoices):
        DO_SHOPPER = 'do_shopper', 'Cliente do Shopper'
        DO_KEEPER = 'do_keeper', 'Cliente do Keeper'

    # Código único do pedido (EV-000123)
    codigo = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        help_text="Código único do pedido (ex: EV-000123)"
    )
    
    # Snapshot dos dados do cliente (para histórico)
    cliente_nome = models.CharField(max_length=150, blank=True, help_text="Nome do cliente no momento do pedido")
    cliente_whatsapp = models.CharField(max_length=20, blank=True, help_text="WhatsApp do cliente")
    cliente_email = models.EmailField(blank=True, null=True, help_text="Email do cliente")
    
    # Campos principais
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='pedidos', null=True, blank=True)
    endereco_entrega = models.ForeignKey(EnderecoEntrega, on_delete=models.CASCADE, null=True, blank=True)
    cupom = models.ForeignKey(CupomDesconto, null=True, blank=True, on_delete=models.SET_NULL)
    
    # NOVOS CAMPOS - Modelo Oficial
    carteira_cliente = models.ForeignKey(
        'CarteiraCliente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pedidos',
        help_text="Carteira à qual o cliente pertence"
    )
    tipo_cliente = models.CharField(
        max_length=20,
        choices=TipoCliente.choices,
        null=True,
        blank=True,
        help_text="Tipo de cliente: do_shopper ou do_keeper"
    )
    
    # Agentes envolvidos
    shopper = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pedidos_como_shopper',
        help_text="Shopper que criou/vendeu o pedido"
    )
    keeper = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pedidos_como_keeper',
        help_text="Keeper que fará a entrega (null se tipo_cliente='do_shopper')"
    )
    
    # Preços (modelo oficial)
    preco_base = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Preço base (custo) - P_base"
    )
    preco_final = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Preço final pago pelo cliente - P_final"
    )
    
    # Valores detalhados (conforme documento)
    valor_subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Valor subtotal (sem frete e taxas)"
    )
    valor_frete = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Valor do frete"
    )
    valor_taxas = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Valor de taxas adicionais"
    )
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    moeda = models.CharField(max_length=3, default='BRL', help_text="Moeda do pedido (BRL, USD, etc.)")
    
    # Evento/Campanha vinculada
    evento = models.ForeignKey(
        'Evento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pedidos',
        help_text="Evento/Campanha relacionada"
    )
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.CRIADO)
    metodo_pagamento = models.CharField(max_length=20, choices=MetodoPagamento.choices, blank=True, null=True)
    observacoes = models.TextField(blank=True)
    codigo_rastreamento = models.CharField(max_length=100, blank=True, null=True)
    is_revisado = models.BooleanField(default=False)
    is_prioritario = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-criado_em']

    def gerar_codigo(self):
        """Gera código único do pedido no formato EV-000123"""
        if not self.codigo:
            # Buscar último código
            ultimo_pedido = Pedido.objects.filter(codigo__isnull=False).order_by('-id').first()
            if ultimo_pedido and ultimo_pedido.codigo:
                try:
                    numero = int(ultimo_pedido.codigo.split('-')[1])
                    numero += 1
                except (ValueError, IndexError):
                    numero = 1
            else:
                numero = 1
            self.codigo = f"EV-{numero:06d}"
        return self.codigo
    
    def calcular_total(self):
        """Calcula o total do pedido com itens, frete, taxas e cupom"""
        # Subtotal dos itens
        self.valor_subtotal = sum(item.subtotal() for item in self.itens.all())
        
        # Aplicar cupom se houver
        total = self.valor_subtotal
        if self.cupom and self.cupom.ativo:
            total -= total * (self.cupom.desconto_percentual / 100)
        
        # Adicionar frete e taxas
        total += self.valor_frete + self.valor_taxas
        
        self.valor_total = total
        return total

    def salvar_com_total(self):
        """Salva o pedido recalculando o total"""
        self.valor_total = self.calcular_total()
        self.save()
    
    def determinar_tipo_cliente(self, shopper_user):
        """
        Determina automaticamente o tipo_cliente e keeper baseado na carteira.
        
        Regra oficial (DEFINIÇÃO DEFINITIVA):
        - Se cliente pertence à carteira do Shopper: 
          → tipo_cliente = "do_shopper", keeper = null
          → Shopper entrega para seus próprios clientes
        
        - Se cliente pertence à carteira do Keeper:
          → tipo_cliente = "do_keeper", keeper = wallet.owner
          → REQUER LigacaoMesh ativa entre shopper e keeper
          → Keeper entrega para seus próprios clientes
        
        IMPORTANTE: Não é possível vender para cliente do Keeper sem LigacaoMesh ativa.
        """
        if not self.carteira_cliente:
            # Se não tem carteira, tentar determinar pela carteira do cliente
            if self.cliente.wallet:
                self.carteira_cliente = self.cliente.wallet
            else:
                # Fallback: considerar como cliente do shopper
                self.tipo_cliente = self.TipoCliente.DO_SHOPPER
                self.keeper = None
                return
        
        # Determinar tipo baseado no owner da carteira
        wallet_owner = self.carteira_cliente.owner
        
        if wallet_owner == shopper_user:
            # Cliente do Shopper - Shopper entrega diretamente
            self.tipo_cliente = self.TipoCliente.DO_SHOPPER
            self.keeper = None
        else:
            # Cliente do Keeper - VERIFICAR SE EXISTE LIGAÇÃO MESH ATIVA
            # Conforme definição oficial: Keeper só participa se houver mesh configurada
            from django.db.models import Q
            
            mesh = LigacaoMesh.objects.filter(
                ativo=True
            ).filter(
                (Q(agente_a=shopper_user, agente_b=wallet_owner)) |
                (Q(agente_a=wallet_owner, agente_b=shopper_user))
            ).first()
            
            if mesh:
                # Mesh existe e está ativa - pode vender para cliente do Keeper
                self.tipo_cliente = self.TipoCliente.DO_KEEPER
                self.keeper = wallet_owner
            else:
                # Sem mesh ativa - NÃO pode vender para cliente do Keeper
                # Levantar exceção conforme regra de negócio
                raise ValidationError(
                    f"Não existe LigacaoMesh ativa entre {shopper_user.username} "
                    f"e {wallet_owner.username}. "
                    f"Para vender para clientes do Keeper, é necessário estabelecer "
                    f"uma LigacaoMesh (forte ou fraca) entre os agentes."
                )
    
    def atualizar_precos(self):
        """
        Atualiza preco_base e preco_final baseado nos itens do pedido.
        preco_base = soma dos custos dos produtos
        preco_final = valor_total (já calculado com cupons)
        """
        # Preço base = soma dos preços base dos produtos (se disponível)
        # Por enquanto, usa o preço do produto como base
        if not self.preco_base:
            self.preco_base = sum(item.produto.preco * item.quantidade for item in self.itens.all())
        
        # Preço final = valor_total (já calculado)
        if not self.preco_final:
            self.preco_final = self.valor_total

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
# SISTEMA DE PAGAMENTOS - GATEWAY
# ============================================================================

class Pagamento(models.Model):
    """
    Pagamento vinculado a um Pedido (relação 1:1).
    Integração com gateways de pagamento (Mercado Pago, Stripe, etc.)
    """
    
    class Metodo(models.TextChoices):
        PIX = 'pix', 'Pix'
        CARTAO = 'cartao', 'Cartão de Crédito'
        PI = 'pi', 'Pi Network'
        TOKEN = 'token', 'Token interno'
    
    class Status(models.TextChoices):
        CRIADO = 'criado', 'Criado'
        PENDENTE = 'pendente', 'Pendente'
        CONFIRMADO = 'confirmado', 'Confirmado'
        RECUSADO = 'recusado', 'Recusado'
        CANCELADO = 'cancelado', 'Cancelado'
        CHARGEBACK = 'chargeback', 'Chargeback'
    
    pedido = models.OneToOneField(
        Pedido,
        on_delete=models.CASCADE,
        related_name='pagamento',
        help_text="Pedido vinculado (1:1)"
    )
    metodo = models.CharField(
        max_length=20,
        choices=Metodo.choices,
        help_text="Método de pagamento"
    )
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Valor do pagamento"
    )
    moeda = models.CharField(
        max_length=3,
        default='BRL',
        help_text="Moeda (BRL, USD, etc.)"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CRIADO
    )
    
    # Dados do gateway
    gateway = models.CharField(
        max_length=50,
        help_text="Gateway utilizado (mercadopago, stripe, pagarme, etc.)"
    )
    gateway_payment_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="ID do pagamento no gateway"
    )
    gateway_checkout_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL do checkout/link de pagamento"
    )
    gateway_qr_code = models.TextField(
        blank=True,
        null=True,
        help_text="QR Code (para Pix)"
    )
    gateway_qr_code_base64 = models.TextField(
        blank=True,
        null=True,
        help_text="QR Code em base64 (para exibição)"
    )
    
    # Metadados
    metadados = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadados adicionais do pagamento"
    )
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    confirmado_em = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
        ordering = ['-criado_em']
    
    def __str__(self):
        return f"Pagamento {self.get_metodo_display()} - {self.pedido.codigo or f'Pedido #{self.pedido.id}'} ({self.get_status_display()})"
    
    def confirmar(self):
        """Confirma o pagamento e atualiza o pedido"""
        from django.utils import timezone
        self.status = self.Status.CONFIRMADO
        self.confirmado_em = timezone.now()
        self.save()
        
        # Atualizar pedido
        self.pedido.status = Pedido.Status.PAGO
        self.pedido.save()
        
        # Disparar notificações (stub)
        self._notificar_confirmacao()
    
    def recusar(self):
        """Recusa o pagamento"""
        self.status = self.Status.RECUSADO
        self.save()
        
        # Pedido volta para aguardando pagamento
        self.pedido.status = Pedido.Status.AGUARDANDO_PAGAMENTO
        self.pedido.save()
        
        # Disparar notificações (stub)
        self._notificar_recusa()
    
    def _notificar_confirmacao(self):
        """Notifica confirmação de pagamento (stub - implementar depois)"""
        pass
    
    def _notificar_recusa(self):
        """Notifica recusa de pagamento (stub - implementar depois)"""
        pass


class TransacaoGateway(models.Model):
    """
    Log detalhado de eventos vindos do gateway.
    Armazena todos os webhooks e eventos relacionados ao pagamento.
    """
    pagamento = models.ForeignKey(
        Pagamento,
        on_delete=models.CASCADE,
        related_name='transacoes',
        help_text="Pagamento relacionado"
    )
    tipo_evento = models.CharField(
        max_length=50,
        help_text="Tipo de evento (payment_created, payment_approved, payment_failed, etc.)"
    )
    payload = models.JSONField(
        default=dict,
        help_text="Payload completo do webhook/evento"
    )
    gateway_response = models.JSONField(
        default=dict,
        blank=True,
        help_text="Resposta do gateway (se aplicável)"
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Transação Gateway'
        verbose_name_plural = 'Transações Gateway'
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['pagamento', '-criado_em']),
            models.Index(fields=['tipo_evento', '-criado_em']),
        ]
    
    def __str__(self):
        return f"{self.tipo_evento} - {self.pagamento.pedido.codigo or f'Pedido #{self.pagamento.pedido.id}'} ({self.criado_em.strftime('%d/%m/%Y %H:%M')})"


# ============================================================================
# EVENTOS E ESTABELECIMENTOS
# ============================================================================



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
    # estabelecimentos = models.ManyToManyField(Estabelecimento, related_name='eventos', blank=True)
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


class AddressKeeperOnboardingToken(models.Model):
    """Token para cadastro de novo Address Keeper (ponto de guarda) via WhatsApp"""
    token      = models.CharField(max_length=16, unique=True)
    phone      = models.CharField(max_length=32, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='address_keeper_tokens_created')
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    used_at    = models.DateTimeField(null=True, blank=True)
    used_by    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='address_keeper_token_used')

    class Meta:
        verbose_name = 'Token de Cadastro Address Keeper'
        verbose_name_plural = 'Tokens de Cadastro Address Keeper'

    @property
    def is_valid(self):
        return self.used_at is None and timezone.now() <= self.expires_at

    def __str__(self):
        status = "Usado" if self.used_at else ("Válido" if self.is_valid else "Expirado")
        return f"ADDRKEEP-{self.token} [{status}]"


# ============================================================================
# MODELOS WHATSAPP - Grupos, Mensagens e Integração
# ============================================================================

class WhatsappGroup(models.Model):
    """Grupo WhatsApp vinculado a um PersonalShopper ou Address Keeper (ponto de guarda)"""
    chat_id = models.CharField(max_length=100, unique=True, help_text="ID do grupo no WhatsApp")
    name = models.CharField(max_length=200, help_text="Nome do grupo")
    
    # Usuário master (pode ser shopper ou keeper)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_whatsapp_groups')
    shopper = models.ForeignKey(PersonalShopper, on_delete=models.CASCADE, null=True, blank=True, related_name='whatsapp_groups')
    address_keeper = models.ForeignKey(AddressKeeper, on_delete=models.CASCADE, null=True, blank=True, related_name='whatsapp_groups', help_text="Address Keeper (ponto de guarda) dono deste grupo")
    
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    
    # Configurações do grupo
    auto_approve_orders = models.BooleanField(default=False, help_text="Aprovar pedidos automaticamente")
    send_notifications = models.BooleanField(default=True, help_text="Enviar notificações de status")
    max_participants = models.IntegerField(default=100, help_text="Máximo de participantes")
    
    class Meta:
        verbose_name = 'Grupo WhatsApp'
        verbose_name_plural = 'Grupos WhatsApp'
        ordering = ['-last_activity', '-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.owner.username})"
    
    @property
    def participant_count(self):
        return self.participants.count()
    
    @property
    def is_active(self):
        if self.shopper:
            return self.active and self.shopper.ativo
        elif self.address_keeper:
            return self.active and self.address_keeper.ativo
        return self.active
    
    @property
    def owner_type(self):
        """Retorna o tipo do proprietário: 'shopper' ou 'address_keeper'"""
        if self.shopper:
            return 'shopper'
        elif self.address_keeper:
            return 'address_keeper'
        return 'unknown'


class WhatsappParticipant(models.Model):
    """Participante de um grupo WhatsApp"""
    group = models.ForeignKey(WhatsappGroup, on_delete=models.CASCADE, related_name='participants')
    phone = models.CharField(max_length=20, help_text="Número do WhatsApp")
    name = models.CharField(max_length=100, blank=True, help_text="Nome no WhatsApp")
    is_admin = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    
    # Se for cliente cadastrado
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='whatsapp_participations')
    
    class Meta:
        verbose_name = 'Participante WhatsApp'
        verbose_name_plural = 'Participantes WhatsApp'
        unique_together = ['group', 'phone']
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.name or self.phone} em {self.group.name}"


class ParticipantPermissionRequest(models.Model):
    """
    Solicitação de permissão para adicionar cliente de outro shopper ao grupo.
    Quando um shopper quer adicionar um cliente que pertence à carteira de outro shopper,
    uma solicitação é criada e o dono da carteira pode aprovar ou rejeitar.
    """
    class Status(models.TextChoices):
        PENDENTE = 'pendente', 'Pendente'
        APROVADO = 'aprovado', 'Aprovado'
        REJEITADO = 'rejeitado', 'Rejeitado'
        EXPIRADO = 'expirado', 'Expirado'
    
    # Grupo e cliente
    group = models.ForeignKey(WhatsappGroup, on_delete=models.CASCADE, related_name='permission_requests')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='permission_requests')
    
    # Quem está solicitando (shopper que quer adicionar)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='permissions_requested')
    
    # Dono da carteira do cliente (quem precisa aprovar)
    carteira_owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='permissions_received')
    
    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE)
    
    # Mensagem opcional da solicitação
    message = models.TextField(blank=True, help_text="Mensagem opcional explicando a solicitação")
    
    # Resposta do dono da carteira
    response_message = models.TextField(blank=True, help_text="Resposta do dono da carteira")
    
    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Data de expiração da solicitação")
    
    class Meta:
        verbose_name = 'Solicitação de Permissão de Participante'
        verbose_name_plural = 'Solicitações de Permissão de Participantes'
        unique_together = ['group', 'cliente']
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['carteira_owner', 'status']),
            models.Index(fields=['requested_by', 'status']),
        ]
    
    def __str__(self):
        return f"Solicitação {self.get_status_display()} - {self.cliente} em {self.group.name}"
    
    @property
    def is_expired(self):
        """Verifica se a solicitação expirou"""
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() > self.expires_at
        return False
    
    def approve(self, response_message=''):
        """Aprova a solicitação"""
        from django.utils import timezone
        self.status = self.Status.APROVADO
        self.response_message = response_message
        self.responded_at = timezone.now()
        self.save()
    
    def reject(self, response_message=''):
        """Rejeita a solicitação"""
        from django.utils import timezone
        self.status = self.Status.REJEITADO
        self.response_message = response_message
        self.responded_at = timezone.now()
        self.save()


# ============================================================================
# SISTEMA DE CONVERSAS INDIVIDUAIS WHATSAPP - INSPIRADO NO UMBLER TALK
# Paradigma: Grupo para vendas/anúncios → Atendimento individual após compra
# ============================================================================

class WhatsappConversation(models.Model):
    """
    Conversa individual/ticket com cliente via WhatsApp
    Inspirado no Umbler Talk (https://www.umbler.com/br) e TalkRobo
    
    Paradigma:
    - GRUPO: Usado para vendas/anúncios de produtos (modo geral)
    - INDIVIDUAL: Após compra, atendimento é individualizado
    """
    STATUS_CHOICES = [
        ('new', 'Nova'),
        ('open', 'Aberta'),
        ('waiting', 'Aguardando Cliente'),
        ('pending', 'Pendente'),
        ('resolved', 'Resolvida'),
        ('closed', 'Fechada'),
    ]
    
    PRIORITY_CHOICES = [
        (1, 'Baixa'),
        (3, 'Normal'),
        (5, 'Média'),
        (7, 'Alta'),
        (9, 'Urgente'),
    ]
    
    # Identificação única
    conversation_id = models.CharField(max_length=50, unique=True, help_text="ID único da conversa")
    
    # Contexto da conversa
    group = models.ForeignKey(
        WhatsappGroup, 
        on_delete=models.CASCADE, 
        related_name='conversations',
        null=True,
        blank=True,
        help_text="Grupo onde iniciou (se veio de grupo)"
    )
    participant = models.ForeignKey(
        WhatsappParticipant, 
        on_delete=models.CASCADE, 
        related_name='conversations',
        help_text="Participante/cliente da conversa"
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='whatsapp_conversations',
        help_text="Cliente cadastrado (se vinculado)"
    )
    
    # Status e atribuição (estilo Umbler/TalkRobo)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_conversations',
        help_text="Agente/shopper responsável pelo atendimento"
    )
    
    # Organização (estilo Umbler Talk)
    tags = models.JSONField(
        default=list,
        help_text="Tags para categorizar: vendas, suporte, pedido, urgente, etc."
    )
    priority = models.IntegerField(
        choices=PRIORITY_CHOICES,
        default=3,
        help_text="Prioridade 1-9 (auto-calculada ou manual)"
    )
    
    # Metadados temporais
    first_message_at = models.DateTimeField(auto_now_add=True, help_text="Primeira mensagem")
    last_message_at = models.DateTimeField(auto_now=True, help_text="Última mensagem")
    first_response_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Quando foi respondida pela primeira vez"
    )
    resolved_at = models.DateTimeField(null=True, blank=True, help_text="Quando foi resolvida")
    closed_at = models.DateTimeField(null=True, blank=True, help_text="Quando foi fechada")
    
    # Estatísticas
    message_count = models.IntegerField(default=0, help_text="Total de mensagens")
    unread_count = models.IntegerField(default=0, help_text="Mensagens não lidas")
    response_time_avg = models.DurationField(
        null=True,
        blank=True,
        help_text="Tempo médio de resposta"
    )
    
    # Vinculação com pedidos (após compra)
    related_orders = models.ManyToManyField(
        'WhatsappOrder',
        blank=True,
        related_name='conversations',
        help_text="Pedidos relacionados a esta conversa"
    )
    
    # Contexto adicional
    source = models.CharField(
        max_length=50,
        default='group',
        choices=[
            ('group', 'Grupo'),
            ('direct', 'Direto'),
            ('after_purchase', 'Pós-Compra'),
            ('support', 'Suporte'),
        ],
        help_text="Origem da conversa"
    )
    notes = models.TextField(blank=True, help_text="Anotações internas do atendente")
    
    class Meta:
        verbose_name = 'Conversa WhatsApp'
        verbose_name_plural = 'Conversas WhatsApp'
        ordering = ['-last_message_at', '-priority']
        indexes = [
            models.Index(fields=['status', 'assigned_to']),
            models.Index(fields=['group', 'participant']),
            models.Index(fields=['cliente', 'status']),
            models.Index(fields=['last_message_at', 'status']),
        ]
    
    def __str__(self):
        return f"Conversa #{self.conversation_id} - {self.participant.name or self.participant.phone}"
    
    def save(self, *args, **kwargs):
        import secrets
        import string
        
        if not self.conversation_id:
            timestamp = timezone.now().strftime("%y%m%d")
            random = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
            self.conversation_id = f"CONV-{timestamp}-{random}"
        
        # Se mudou para resolvida, registrar data
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        
        # Se mudou para fechada, registrar data
        if self.status == 'closed' and not self.closed_at:
            self.closed_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def is_unread(self):
        """Verifica se há mensagens não lidas"""
        return self.unread_count > 0
    
    @property
    def waiting_time(self):
        """Tempo desde a última mensagem do cliente"""
        if self.last_message_at:
            return timezone.now() - self.last_message_at
        return None
    
    @property
    def first_response_time(self):
        """Tempo até primeira resposta"""
        if self.first_response_at and self.first_message_at:
            return self.first_response_at - self.first_message_at
        return None
    
    def calculate_priority(self):
        """Calcula prioridade automaticamente baseada em fatores"""
        priority = 3  # Normal
        
        # Tags
        if self.tags:
            tag_lower = [t.lower() for t in self.tags]
            if 'urgente' in tag_lower:
                priority = 9
            elif 'reclamação' in tag_lower:
                priority = 8
            elif 'vendas' in tag_lower:
                priority = 5
        
        # Tempo sem resposta
        if self.last_message_at:
            hours_since = (timezone.now() - self.last_message_at).total_seconds() / 3600
            if hours_since > 24:
                priority += 2
            elif hours_since > 12:
                priority += 1
        
        # Cliente VIP (muitos pedidos)
        if self.cliente:
            total_pedidos = self.cliente.whatsapp_orders.count()
            if total_pedidos > 10:
                priority += 1
        
        # Pedido relacionado aumenta prioridade
        if hasattr(self, 'related_orders') and self.related_orders.exists():
            priority += 1
        
        # Status
        if self.status == 'new':
            priority += 1
        
        return min(priority, 9)
    
    def auto_calculate_priority(self):
        """Atualiza prioridade automaticamente"""
        self.priority = self.calculate_priority()
        self.save(update_fields=['priority'])
    
    def mark_as_read(self, user=None):
        """Marca todas as mensagens como lidas"""
        from app_marketplace.models import WhatsappMessage
        unread_messages = WhatsappMessage.objects.filter(
            conversation=self,
            read=False
        )
        unread_messages.update(
            read=True,
            read_at=timezone.now()
        )
        self.unread_count = 0
        self.save(update_fields=['unread_count'])
    
    def add_tag(self, tag):
        """Adiciona uma tag"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.save(update_fields=['tags'])
    
    def remove_tag(self, tag):
        """Remove uma tag"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.save(update_fields=['tags'])
    
    def assign(self, agent):
        """Atribui conversa para um agente"""
        self.assigned_to = agent
        self.status = 'open'
        self.save(update_fields=['assigned_to', 'status'])
    
    def close(self):
        """Fecha a conversa"""
        self.status = 'closed'
        self.closed_at = timezone.now()
        self.save(update_fields=['status', 'closed_at'])


class ConversationNote(models.Model):
    """
    Notas internas sobre uma conversa (não visíveis ao cliente)
    Estilo Umbler/TalkRobo
    """
    conversation = models.ForeignKey(
        WhatsappConversation,
        on_delete=models.CASCADE,
        related_name='internal_notes'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversation_notes'
    )
    content = models.TextField(help_text="Conteúdo da nota")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Nota de Conversa'
        verbose_name_plural = 'Notas de Conversas'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Nota de {self.author.username} em {self.conversation.conversation_id}"


class WhatsappMessage(models.Model):
    """Mensagem do WhatsApp"""
    MESSAGE_TYPES = [
        ('text', 'Texto'),
        ('image', 'Imagem'),
        ('video', 'Vídeo'),
        ('audio', 'Áudio'),
        ('document', 'Documento'),
        ('location', 'Localização'),
        ('contact', 'Contato'),
    ]
    
    message_id = models.CharField(max_length=100, unique=True, help_text="ID da mensagem no WhatsApp")
    group = models.ForeignKey(WhatsappGroup, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    sender = models.ForeignKey(WhatsappParticipant, on_delete=models.CASCADE, related_name='sent_messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    content = models.TextField(help_text="Conteúdo da mensagem")
    media_url = models.URLField(blank=True, help_text="URL da mídia (se houver)")
    timestamp = models.DateTimeField(help_text="Quando foi enviada")
    processed = models.BooleanField(default=False, help_text="Se foi processada pelo sistema")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Sistema de conversas individuais (inspirado no Umbler Talk)
    conversation = models.ForeignKey(
        'WhatsappConversation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages',
        help_text="Conversa/ticket individual (após compra)"
    )
    read = models.BooleanField(default=False, help_text="Mensagem foi lida")
    read_at = models.DateTimeField(null=True, blank=True, help_text="Quando foi lida")
    is_from_customer = models.BooleanField(default=True, help_text="Mensagem veio do cliente")
    
    class Meta:
        verbose_name = 'Mensagem WhatsApp'
        verbose_name_plural = 'Mensagens WhatsApp'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['conversation', 'read']),
            models.Index(fields=['sender', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.sender.name}: {self.content[:50]}..."




class WhatsappProduct(models.Model):
    """Produto postado em grupo WhatsApp
    
    MVP: Shopper cria produtos diretamente no grupo.
    - group: obrigatório (produto pertence a um grupo)
    - message: opcional (pode ser criado direto pelo shopper ou vinculado a uma mensagem)
    - posted_by: obrigatório (quem postou/criou o produto)
    """
    group = models.ForeignKey(WhatsappGroup, on_delete=models.CASCADE, related_name='products')
    message = models.ForeignKey(WhatsappMessage, on_delete=models.CASCADE, related_name='products', null=True, blank=True, help_text="Mensagem do WhatsApp que originou este produto (opcional)")
    posted_by = models.ForeignKey(WhatsappParticipant, on_delete=models.CASCADE, related_name='posted_products', help_text="Participante que criou/postou este produto")
    
    # Dados do produto
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    brand = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=100, blank=True)
    
    # LOCALIZAÇÃO DO PRODUTO - ONDE ENCONTRAR
    estabelecimento = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='produtos_whatsapp', help_text="Empresa/Estabelecimento onde o produto pode ser encontrado", null=True, blank=True)
    localizacao_especifica = models.CharField(max_length=200, blank=True, help_text="Ex: Corredor 3, Prateleira A, Seção de Perfumes")
    codigo_barras = models.CharField(max_length=50, blank=True, help_text="Código de barras do produto")
    sku_loja = models.CharField(max_length=50, blank=True, help_text="SKU ou código interno da loja")
    
    # Imagens
    image_urls = models.JSONField(default=list, help_text="URLs das imagens")
    
    # Status
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Produto em destaque")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Produto WhatsApp'
        verbose_name_plural = 'Produtos WhatsApp'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.group.name}"


class PostScreenshot(models.Model):
    """
    Captura de screenshot de um post do WhatsApp.
    MVP: Sistema de captura de imagens dos posts.
    """
    post = models.ForeignKey(WhatsappProduct, on_delete=models.CASCADE, related_name='screenshots')
    group = models.ForeignKey(WhatsappGroup, on_delete=models.CASCADE, related_name='post_screenshots')
    
    # Imagem capturada
    screenshot_file = models.ImageField(
        upload_to='screenshots/posts/%Y/%m/%d/',
        help_text="Screenshot do post"
    )
    
    # Metadados
    captured_at = models.DateTimeField(auto_now_add=True)
    captured_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='captured_screenshots',
        help_text="Usuário que capturou a imagem"
    )
    
    # Informações da captura
    width = models.PositiveIntegerField(null=True, blank=True, help_text="Largura da imagem em pixels")
    height = models.PositiveIntegerField(null=True, blank=True, help_text="Altura da imagem em pixels")
    file_size = models.PositiveIntegerField(null=True, blank=True, help_text="Tamanho do arquivo em bytes")
    
    # Notas opcionais
    notes = models.TextField(blank=True, help_text="Notas sobre a captura")
    
    class Meta:
        verbose_name = 'Screenshot de Post'
        verbose_name_plural = 'Screenshots de Posts'
        ordering = ['-captured_at']
    
    def __str__(self):
        return f"Screenshot de {self.post.name} - {self.captured_at.strftime('%d/%m/%Y %H:%M')}"


class WhatsappOrder(models.Model):
    """Pedido criado via WhatsApp"""
    CHANNEL_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('site', 'Site'),
        ('instagram', 'Instagram'),
        ('store', 'Loja Física'),
        ('other', 'Outro'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('confirmed', 'Confirmado'),
        ('paid', 'Pago'),
        ('purchased', 'Comprado'),
        ('shipped', 'Enviado'),
        ('delivered', 'Entregue'),
        ('cancelled', 'Cancelado'),
    ]
    
    group = models.ForeignKey(WhatsappGroup, on_delete=models.CASCADE, related_name='orders')
    customer = models.ForeignKey(WhatsappParticipant, on_delete=models.CASCADE, related_name='orders')
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='whatsapp_orders')
    
    # Canal de origem
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='whatsapp', db_index=True)
    
    # Dados do pedido
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Produtos
    products = models.JSONField(default=list, help_text="Lista de produtos do pedido")
    
    # Entrega
    delivery_method = models.CharField(max_length=50, blank=True, help_text="Método de entrega escolhido")
    delivery_address = models.TextField(blank=True)
    
    # Pagamento
    payment_method = models.CharField(max_length=50, blank=True)
    payment_status = models.CharField(max_length=20, default='pending')
    payment_reference = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Pedido WhatsApp'
        verbose_name_plural = 'Pedidos WhatsApp'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Pedido {self.order_number} - {self.customer.name}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            from datetime import datetime
            timestamp = datetime.now().strftime("%y%m%d%H%M")
            self.order_number = f"WAP{timestamp}{self.id or 0:04d}"
        super().save(*args, **kwargs)


# ============================================================================
# SISTEMA KMN - DROPKEEPER + KEEPER MESH NETWORK
# ============================================================================

class Agente(models.Model):
    """
    Agente unificado que pode ser Shopper, Address Keeper (ponto de guarda) ou ambos.
    Compatível com PersonalShopper e AddressKeeper existentes.
    
    NOTA: O "Keeper" oficial (vendedor passivo) é representado por User + CarteiraCliente,
    não por este modelo Agente. Este modelo é para Address Keeper (ponto de guarda).
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agente')
    
    # Vinculação com modelos existentes
    personal_shopper = models.OneToOneField(PersonalShopper, on_delete=models.SET_NULL, null=True, blank=True, related_name='agente_profile')
    address_keeper = models.OneToOneField(AddressKeeper, on_delete=models.SET_NULL, null=True, blank=True, related_name='agente_profile', help_text="Address Keeper (ponto de guarda) associado a este agente")
    
    # Dados do agente
    nome_comercial = models.CharField(max_length=200, blank=True, help_text="Nome comercial do agente")
    bio_agente = models.TextField(blank=True, help_text="Biografia como agente KMN")
    
    # Scores de reputação
    score_keeper = models.DecimalField(max_digits=5, decimal_places=2, default=5.0, help_text="Score como Keeper (0-10)")
    score_shopper = models.DecimalField(max_digits=5, decimal_places=2, default=5.0, help_text="Score como Shopper (0-10)")
    
    # Status
    ativo_como_keeper = models.BooleanField(default=False)
    ativo_como_shopper = models.BooleanField(default=False)
    verificado_kmn = models.BooleanField(default=False, help_text="Verificado pela rede KMN")
    
    # Timestamps
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Agente KMN'
        verbose_name_plural = 'Agentes KMN'
        ordering = ['-score_keeper', '-score_shopper']
    
    @property
    def dual_role_score(self):
        """Score médio harmônico para agentes que fazem ambos os papéis"""
        if self.score_keeper > 0 and self.score_shopper > 0:
            return (2 * self.score_keeper * self.score_shopper) / (self.score_keeper + self.score_shopper)
        return max(self.score_keeper, self.score_shopper)
    
    @property
    def is_dual_role(self):
        """Verifica se o agente atua como Shopper e Keeper"""
        return self.ativo_como_keeper and self.ativo_como_shopper
    
    def __str__(self):
        roles = []
        if self.ativo_como_shopper:
            roles.append("Shopper")
        if self.ativo_como_keeper:
            roles.append("Keeper")
        role_str = "/".join(roles) if roles else "Inativo"
        return f"{self.user.get_full_name() or self.user.username} ({role_str})"


class ClienteRelacao(models.Model):
    """
    Relacionamento entre Cliente e Agente com força da relação.
    Compatível com RelacionamentoClienteShopper existente.
    """
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='relacoes_agente')
    agente = models.ForeignKey(Agente, on_delete=models.CASCADE, related_name='relacoes_cliente')
    
    # Força da relação (0-100)
    forca_relacao = models.DecimalField(max_digits=5, decimal_places=2, default=50.0, help_text="Força da relação (0-100)")
    
    # Status da relação
    class StatusRelacao(models.TextChoices):
        ATIVA = 'ativa', 'Ativa'
        INATIVA = 'inativa', 'Inativa'
        BLOQUEADA = 'bloqueada', 'Bloqueada'
        PENDENTE = 'pendente', 'Pendente'
    
    status = models.CharField(max_length=20, choices=StatusRelacao.choices, default=StatusRelacao.PENDENTE)
    
    # Histórico
    total_pedidos = models.PositiveIntegerField(default=0)
    valor_total_pedidos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ultimo_pedido = models.DateTimeField(null=True, blank=True)
    satisfacao_media = models.DecimalField(max_digits=3, decimal_places=2, default=5.0, help_text="Satisfação média (0-10)")
    
    # Timestamps
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Relação Cliente-Agente'
        verbose_name_plural = 'Relações Cliente-Agente'
        unique_together = ('cliente', 'agente')
        ordering = ['-forca_relacao', '-ultimo_pedido']
    
    def __str__(self):
        return f"{self.cliente.user.username} ↔ {self.agente.user.username} (Força: {self.forca_relacao})"


class EstoqueItem(models.Model):
    """
    Item de estoque gerenciado por um Agente.
    """
    agente = models.ForeignKey(Agente, on_delete=models.CASCADE, related_name='estoque')
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='estoque_items')
    
    # Estoque
    quantidade_disponivel = models.PositiveIntegerField(default=0)
    quantidade_reservada = models.PositiveIntegerField(default=0)
    
    # Localização física
    estabelecimento = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True, related_name='estoque_items', help_text="Empresa/Estabelecimento onde o estoque está localizado")
    localizacao_especifica = models.CharField(max_length=200, blank=True, help_text="Ex: Prateleira A3, Corredor 5")
    
    # Preços
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2, help_text="Preço de custo do agente")
    preco_base = models.DecimalField(max_digits=10, decimal_places=2, help_text="Preço base para a rede KMN")
    
    # Status
    ativo = models.BooleanField(default=True)
    disponivel_para_rede = models.BooleanField(default=True, help_text="Disponível para outros agentes da rede")
    
    # Timestamps
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Item de Estoque'
        verbose_name_plural = 'Itens de Estoque'
        unique_together = ('agente', 'produto')
        ordering = ['-atualizado_em']
    
    @property
    def quantidade_total(self):
        return self.quantidade_disponivel + self.quantidade_reservada
    
    def __str__(self):
        return f"{self.produto.nome} - {self.agente.user.username} ({self.quantidade_disponivel} disp.)"


class Oferta(models.Model):
    """
    Oferta de produto por um agente, com markup local.
    """
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='ofertas')
    agente_origem = models.ForeignKey(Agente, on_delete=models.CASCADE, related_name='ofertas_origem', help_text="Agente que possui o produto")
    agente_ofertante = models.ForeignKey(Agente, on_delete=models.CASCADE, related_name='ofertas_feitas', help_text="Agente que está oferecendo")
    
    # Preços
    preco_base = models.DecimalField(max_digits=10, decimal_places=2, help_text="Preço base do agente origem")
    preco_oferta = models.DecimalField(max_digits=10, decimal_places=2, help_text="Preço final da oferta")
    
    # Disponibilidade
    quantidade_disponivel = models.PositiveIntegerField(default=1)
    
    # Status
    ativo = models.BooleanField(default=True)
    exclusiva_para_clientes = models.BooleanField(default=False, help_text="Oferta apenas para clientes do agente")
    
    # Timestamps
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    valida_ate = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Oferta'
        verbose_name_plural = 'Ofertas'
        unique_together = ('produto', 'agente_ofertante')
        ordering = ['preco_oferta', '-criado_em']
    
    @property
    def markup_local(self):
        """Markup aplicado pelo agente ofertante"""
        return self.preco_oferta - self.preco_base
    
    @property
    def percentual_markup(self):
        """Percentual de markup"""
        if self.preco_base > 0:
            return (self.markup_local / self.preco_base) * 100
        return 0
    
    def __str__(self):
        markup = self.markup_local
        return f"{self.produto.nome} - {self.agente_ofertante.user.username} (R$ {self.preco_oferta}, +{markup})"


class TrustlineKeeper(models.Model):
    """
    Linha de confiança entre dois agentes da rede KMN.
    """
    agente_a = models.ForeignKey(Agente, on_delete=models.CASCADE, related_name='trustlines_como_a')
    agente_b = models.ForeignKey(Agente, on_delete=models.CASCADE, related_name='trustlines_como_b')
    
    # Níveis de confiança (0-100)
    nivel_confianca_a_para_b = models.DecimalField(max_digits=5, decimal_places=2, default=50.0)
    nivel_confianca_b_para_a = models.DecimalField(max_digits=5, decimal_places=2, default=50.0)
    
    # Percentuais de comissão
    perc_shopper = models.DecimalField(max_digits=5, decimal_places=2, default=60.0, help_text="% para o fornecedor (Shopper)")
    perc_keeper = models.DecimalField(max_digits=5, decimal_places=2, default=40.0, help_text="% para o dono do cliente (Keeper)")
    
    # Status
    class StatusTrustline(models.TextChoices):
        ATIVA = 'ativa', 'Ativa'
        PENDENTE = 'pendente', 'Pendente'
        SUSPENSA = 'suspensa', 'Suspensa'
        CANCELADA = 'cancelada', 'Encerrada'
    
    status = models.CharField(max_length=20, choices=StatusTrustline.choices, default=StatusTrustline.PENDENTE)
    
    # Direcionalidade do compartilhamento de clientes
    class TipoCompartilhamento(models.TextChoices):
        BIDIRECIONAL = 'bidirecional', 'Bidirecional (ambos compartilham)'
        UNIDIRECIONAL_A_PARA_B = 'a_para_b', 'Unidirecional (A → B: A empresta para B)'
        UNIDIRECIONAL_B_PARA_A = 'b_para_a', 'Unidirecional (B → A: B empresta para A)'
    
    tipo_compartilhamento = models.CharField(
        max_length=20,
        choices=TipoCompartilhamento.choices,
        default=TipoCompartilhamento.BIDIRECIONAL,
        help_text="Tipo de compartilhamento de carteira de clientes"
    )
    
    # Regras adicionais
    permite_indicacao = models.BooleanField(default=True)
    perc_indicacao = models.DecimalField(max_digits=5, decimal_places=2, default=5.0, help_text="% para indicação")
    
    # Timestamps
    criado_em = models.DateTimeField(auto_now_add=True)
    aceito_em = models.DateTimeField(null=True, blank=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Trustline KMN'
        verbose_name_plural = 'Trustlines KMN'
        unique_together = ('agente_a', 'agente_b')
        ordering = ['-nivel_confianca_a_para_b', '-aceito_em']
    
    def clean(self):
        if self.agente_a == self.agente_b:
            raise ValidationError("Um agente não pode ter trustline consigo mesmo")
        if self.perc_shopper + self.perc_keeper != 100:
            raise ValidationError("A soma dos percentuais deve ser 100%")
    
    @property
    def nivel_confianca_medio(self):
        """Nível médio de confiança bidirecional"""
        return (self.nivel_confianca_a_para_b + self.nivel_confianca_b_para_a) / 2
    
    def __str__(self):
        return f"{self.agente_a.user.username} ↔ {self.agente_b.user.username} (Conf: {self.nivel_confianca_medio:.1f})"


class RoleStats(models.Model):
    """
    Estatísticas de performance do agente em cada papel.
    """
    agente = models.OneToOneField(Agente, on_delete=models.CASCADE, related_name='stats')
    
    # Stats como Keeper
    pedidos_como_keeper = models.PositiveIntegerField(default=0)
    valor_total_como_keeper = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    satisfacao_media_keeper = models.DecimalField(max_digits=3, decimal_places=2, default=5.0)
    
    # Stats como Shopper
    pedidos_como_shopper = models.PositiveIntegerField(default=0)
    valor_total_como_shopper = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    satisfacao_media_shopper = models.DecimalField(max_digits=3, decimal_places=2, default=5.0)
    
    # Stats gerais
    total_clientes_atendidos = models.PositiveIntegerField(default=0)
    total_agentes_parceiros = models.PositiveIntegerField(default=0)
    
    # Timestamps
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Estatísticas de Papel'
        verbose_name_plural = 'Estatísticas de Papéis'
    
    def atualizar_scores(self):
        """Atualiza os scores do agente baseado nas estatísticas"""
        # Score Keeper baseado em satisfação e volume
        if self.pedidos_como_keeper > 0:
            volume_factor = min(self.pedidos_como_keeper / 10, 1.0)  # Max factor = 1.0 com 10+ pedidos
            self.agente.score_keeper = self.satisfacao_media_keeper * volume_factor
        
        # Score Shopper baseado em satisfação e volume
        if self.pedidos_como_shopper > 0:
            volume_factor = min(self.pedidos_como_shopper / 10, 1.0)
            self.agente.score_shopper = self.satisfacao_media_shopper * volume_factor
        
        self.agente.save()
    
    def __str__(self):
        return f"Stats {self.agente.user.username} - K:{self.pedidos_como_keeper} S:{self.pedidos_como_shopper}"


# ============================================================================
# EXTENSÃO DO MODELO PEDIDO PARA KMN
# ============================================================================

# Adicionar campos KMN ao modelo Pedido existente via migration
# Estes campos serão adicionados na migration:
# - agente_shopper (ForeignKey para Agente)
# - agente_keeper (ForeignKey para Agente) 
# - canal_entrada (ForeignKey para Agente, null=True)
# - oferta_utilizada (ForeignKey para Oferta, null=True)
# - preco_base_kmn (DecimalField)
# - preco_oferta_kmn (DecimalField)
# - markup_local_kmn (DecimalField)
# - tipo_operacao_kmn (CharField com choices)
# - comissao_shopper (DecimalField)
# - comissao_keeper (DecimalField)
# - comissao_indicacao (DecimalField, default=0)


# ============================================================================
# MODELOS OFICIAIS - PROMPT VITRINEZAP/ÉVORA/KMN
# Baseado no PROMPT OFICIAL do sistema
# ============================================================================

class CarteiraCliente(models.Model):
    """
    Carteira de clientes de um agente (Shopper ou Keeper).
    Cada agente pode ter uma ou mais carteiras de clientes.
    """
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carteiras_cliente')
    nome_exibicao = models.CharField(max_length=200, help_text="Nome para exibição da carteira")
    metadados = models.JSONField(default=dict, blank=True, help_text="Metadados adicionais da carteira")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Carteira de Clientes'
        verbose_name_plural = 'Carteiras de Clientes'
        ordering = ['-criado_em']
    
    def __str__(self):
        return f"{self.nome_exibicao} ({self.owner.username})"
    
    def total_clientes(self):
        """Retorna o total de clientes nesta carteira"""
        return self.clientes.count()


class LigacaoMesh(models.Model):
    """
    Ligação Mesh entre dois agentes (Shopper/Keeper).
    Substitui o modelo TrustlineKeeper com tipos "forte" e "fraca".
    """
    class TipoMesh(models.TextChoices):
        FORTE = 'forte', 'Mesh Forte'
        FRACA = 'fraca', 'Mesh Fraca'
    
    agente_a = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ligacoes_mesh_como_a')
    agente_b = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ligacoes_mesh_como_b')
    tipo = models.CharField(max_length=10, choices=TipoMesh.choices, default=TipoMesh.FRACA)
    ativo = models.BooleanField(default=True)
    
    # Configuração financeira em JSON
    # Formato:
    # {
    #   "taxa_evora": 0.10,
    #   "venda_clientes_shopper": {"alpha_s": 1.0},
    #   "venda_clientes_keeper": {"alpha_s": 0.60, "alpha_k": 0.40}
    # }
    config_financeira = models.JSONField(
        default=dict,
        help_text="Configuração financeira da ligação mesh"
    )
    
    # Metadados adicionais
    metadados = models.JSONField(default=dict, blank=True)
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    aceito_em = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Ligação Mesh'
        verbose_name_plural = 'Ligações Mesh'
        unique_together = ('agente_a', 'agente_b')
        ordering = ['-aceito_em', '-criado_em']
    
    def clean(self):
        if self.agente_a == self.agente_b:
            raise ValidationError("Um agente não pode ter ligação mesh consigo mesmo")
        
        # Validar config_financeira
        if not self.config_financeira:
            # Configuração padrão
            self.config_financeira = {
                "taxa_evora": 0.10,
                "venda_clientes_shopper": {"alpha_s": 1.0},
                "venda_clientes_keeper": {"alpha_s": 0.60, "alpha_k": 0.40}
            }
        else:
            # Validar estrutura
            if "taxa_evora" not in self.config_financeira:
                self.config_financeira["taxa_evora"] = 0.10
            
            if "venda_clientes_shopper" not in self.config_financeira:
                self.config_financeira["venda_clientes_shopper"] = {"alpha_s": 1.0}
            
            if "venda_clientes_keeper" not in self.config_financeira:
                self.config_financeira["venda_clientes_keeper"] = {"alpha_s": 0.60, "alpha_k": 0.40}
            
            # Validar soma dos alphas
            keeper_config = self.config_financeira.get("venda_clientes_keeper", {})
            alpha_s = keeper_config.get("alpha_s", 0.60)
            alpha_k = keeper_config.get("alpha_k", 0.40)
            if abs(alpha_s + alpha_k - 1.0) > 0.01:  # Tolerância para decimais
                raise ValidationError("A soma de alpha_s e alpha_k deve ser 1.0")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        tipo_str = "Forte" if self.tipo == self.TipoMesh.FORTE else "Fraca"
        return f"{self.agente_a.username} ↔ {self.agente_b.username} ({tipo_str})"


class LiquidacaoFinanceira(models.Model):
    """
    Liquidação financeira de um pedido.
    Calcula e armazena a distribuição de valores entre Évora, Shopper e Keeper.
    """
    pedido = models.OneToOneField('Pedido', on_delete=models.CASCADE, related_name='liquidacao')
    
    # Valores calculados
    valor_margem = models.DecimalField(max_digits=12, decimal_places=2, help_text="Margem total (P_final - P_base)")
    valor_evora = models.DecimalField(max_digits=12, decimal_places=2, help_text="Valor recebido pela Évora")
    valor_shopper = models.DecimalField(max_digits=12, decimal_places=2, help_text="Valor recebido pelo Shopper")
    valor_keeper = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Valor recebido pelo Keeper")
    
    # Detalhes do cálculo (JSON)
    detalhes = models.JSONField(
        default=dict,
        help_text="Detalhes do cálculo (taxas, percentuais, etc.)"
    )
    
    # Status
    class StatusLiquidacao(models.TextChoices):
        PENDENTE = 'pendente', 'Pendente'
        CALCULADA = 'calculada', 'Calculada'
        LIQUIDADA = 'liquidada', 'Liquidada'
        CANCELADA = 'cancelada', 'Cancelada'
    
    status = models.CharField(max_length=20, choices=StatusLiquidacao.choices, default=StatusLiquidacao.PENDENTE)
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    liquidado_em = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Liquidação Financeira'
        verbose_name_plural = 'Liquidações Financeiras'
        ordering = ['-criado_em']
    
    def __str__(self):
        return f"Liquidação Pedido #{self.pedido.id} - R$ {self.valor_margem}"


# ============================================================================
# EXTENSÕES DO USER MODEL (helpers)
# ============================================================================

# Adiciona propriedades convenientes ao User
User.add_to_class('is_cliente', property(lambda u: hasattr(u, 'cliente')))
User.add_to_class('is_shopper', property(lambda u: hasattr(u, 'personalshopper')))
User.add_to_class('is_address_keeper', property(lambda u: hasattr(u, 'address_keeper')))
User.add_to_class('is_agente', property(lambda u: hasattr(u, 'agente')))


# ============================================================================
# ÁGORA - FEED SOCIAL DO ÉVORA
# ============================================================================

class PublicacaoAgora(models.Model):
    """
    Publicação no feed Ágora (estilo TikTok/Kwai).
    Cada publicação pode conter vídeo, foto, produto vinculado, oferta, etc.
    """
    
    class TipoConteudo(models.TextChoices):
        VIDEO = 'video', 'Vídeo'
        IMAGEM = 'imagem', 'Imagem'
        PRODUTO = 'produto', 'Produto'
        TEXTO = 'texto', 'Texto'
    
    class TipoMesh(models.TextChoices):
        MALL = 'mall', 'Mall (Produto direto)'
        MESH_FORTE = 'mesh_forte', 'Mesh Forte (KMN)'
        MESH_FRACA = 'mesh_fraca', 'Mesh Fraca (KMN)'
    
    # Autor da publicação (Shopper ou Keeper)
    autor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='publicacoes_agora',
        help_text="Shopper ou Keeper que criou a publicação"
    )
    
    # Conteúdo da publicação
    tipo_conteudo = models.CharField(
        max_length=20,
        choices=TipoConteudo.choices,
        default=TipoConteudo.PRODUTO
    )
    video_url = models.URLField(blank=True, null=True, help_text="URL do vídeo")
    imagem_url = models.URLField(blank=True, null=True, help_text="URL da imagem")
    legenda = models.TextField(blank=True, help_text="Legenda/descrição da publicação")
    
    # Produto vinculado (opcional)
    produto = models.ForeignKey(
        Produto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='publicacoes_agora',
        help_text="Produto vinculado à publicação"
    )
    
    # Oferta personalizada (preço modificado pelo Shopper)
    preco_oferta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Preço personalizado da oferta (se diferente do produto)"
    )
    
    # Contexto KMN
    mesh_type = models.CharField(
        max_length=20,
        choices=TipoMesh.choices,
        default=TipoMesh.MALL,
        help_text="Tipo de mesh KMN"
    )
    
    # Evento/Campanha/Viagem vinculada
    evento = models.ForeignKey(
        Evento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='publicacoes_agora',
        help_text="Evento/Campanha/Viagem relacionada"
    )
    
    # Algoritmo de recomendação
    spark_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        help_text="SparkScore Comercial (0-100) - score de relevância"
    )
    ppa = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.0,
        help_text="PPA (Potencial Prévio de Ação) 0.0-1.0"
    )
    
    # Status
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Publicação Ágora'
        verbose_name_plural = 'Publicações Ágora'
        ordering = ['-spark_score', '-criado_em']
        indexes = [
            models.Index(fields=['-spark_score', '-criado_em']),
            models.Index(fields=['ativo', '-spark_score']),
            models.Index(fields=['evento', '-spark_score']),
        ]
    
    def __str__(self):
        autor_nome = self.autor.get_full_name() or self.autor.username
        produto_nome = self.produto.nome if self.produto else "Sem produto"
        return f"{autor_nome} - {produto_nome}"
    
    @property
    def total_views(self):
        """Total de visualizações"""
        return self.engajamentos.filter(tipo='view').count()
    
    @property
    def total_likes(self):
        """Total de likes"""
        return self.engajamentos.filter(tipo='like').count()
    
    @property
    def total_add_carrinho(self):
        """Total de adições ao carrinho"""
        return self.engajamentos.filter(tipo='add_carrinho').count()
    
    @property
    def total_compartilhar(self):
        """Total de compartilhamentos"""
        return self.engajamentos.filter(tipo='compartilhar').count()
    
    @property
    def total_view_time(self):
        """Tempo total de visualização em segundos"""
        result = self.engajamentos.filter(tipo='view').aggregate(
            total=Sum('view_time_segundos')
        )
        return result['total'] or 0


class EngajamentoAgora(models.Model):
    """
    Engajamento/interação do usuário com uma publicação do Ágora.
    """
    
    class TipoEngajamento(models.TextChoices):
        VIEW = 'view', 'Visualização'
        LIKE = 'like', 'Like'
        ADD_CARRINHO = 'add_carrinho', 'Adicionar ao Carrinho'
        COMPARTILHAR = 'compartilhar', 'Compartilhar'
        VER_DETALHES = 'ver_detalhes', 'Ver Detalhes'
    
    publicacao = models.ForeignKey(
        PublicacaoAgora,
        on_delete=models.CASCADE,
        related_name='engajamentos'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='engajamentos_agora',
        null=True,
        blank=True,
        help_text="Usuário que interagiu (null para anônimos)"
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoEngajamento.choices
    )
    
    # Para visualizações: tempo assistido
    view_time_segundos = models.IntegerField(
        default=0,
        help_text="Tempo de visualização em segundos (apenas para tipo 'view')"
    )
    
    # Metadados
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    metadados = models.JSONField(default=dict, blank=True)
    
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Engajamento Ágora'
        verbose_name_plural = 'Engajamentos Ágora'
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['publicacao', 'tipo']),
            models.Index(fields=['usuario', '-criado_em']),
        ]
    
    def __str__(self):
        usuario_str = self.usuario.username if self.usuario else "Anônimo"
        return f"{usuario_str} - {self.get_tipo_display()} - {self.publicacao}"


# ============================================================================
# MODELO PRODUTO JSON - Armazenamento em JSON (PostgreSQL JSONB)
# ============================================================================

class ProdutoJSON(models.Model):
    """
    Model para armazenar produtos completos em formato JSON (PostgreSQL JSONB ou SQLite JSON).
    Baseado nas melhorias do SinapUm para qualidade de dados e layout DJOS.
    """
    dados_json = models.JSONField(help_text="Dados completos do produto no formato modelo.json")
    nome_produto = models.CharField(max_length=500, db_index=True, help_text="Nome do produto para busca rápida")
    marca = models.CharField(max_length=200, db_index=True, null=True, blank=True)
    categoria = models.CharField(max_length=100, db_index=True, null=True, blank=True)
    codigo_barras = models.CharField(max_length=50, unique=True, null=True, blank=True, db_index=True)
    imagem_original = models.CharField(max_length=500, null=True, blank=True, help_text="Caminho do arquivo de imagem original")
    
    # Relacionamento com shopper que criou
    criado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='produtos_json_criados',
        help_text="Shopper que criou este produto"
    )
    
    # Relacionamento com grupo WhatsApp (opcional)
    grupo_whatsapp = models.ForeignKey(
        'WhatsappGroup',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='produtos_json',
        help_text="Grupo WhatsApp onde o produto foi postado"
    )
    
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Produto JSON"
        verbose_name_plural = "Produtos JSON"
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['nome_produto', 'marca']),
            models.Index(fields=['categoria']),
            models.Index(fields=['criado_por', '-criado_em']),
        ]
    
    def __str__(self):
        return f"{self.nome_produto} ({self.marca}) - {self.criado_em.strftime('%d/%m/%Y')}"
    
    def get_produto_data(self):
        """Retorna os dados do produto em formato dict"""
        if isinstance(self.dados_json, str):
            import json
            return json.loads(self.dados_json)
        return self.dados_json or {}


# ============================================================================
# SINCRONIZAÇÃO ProdutoJSON -> Produto (repositório geral)
# ============================================================================
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=ProdutoJSON)
def sync_produto_repository(sender, instance: ProdutoJSON, created, **kwargs):
    """
    Mantém o repositório geral Produto em sincronia com ProdutoJSON.
    Regra:
    - Se não existe Produto com mesmo nome, cria.
    - Se existe, preenche campos vazios/zerados com dados do JSON (IA).
    """
    try:
        dados = instance.get_produto_data() if hasattr(instance, "get_produto_data") else {}
        produto_data = dados.get("produto", {}) if isinstance(dados, dict) else {}

        nome = (instance.nome_produto or produto_data.get("nome") or "").strip()
        if not nome:
            return

        # Categoria (opcional)
        categoria_nome = instance.categoria or produto_data.get("categoria") or ""
        categoria_obj = None
        if categoria_nome:
            slug = slugify(categoria_nome) or categoria_nome.lower().replace(" ", "-")
            categoria_obj, _ = Categoria.objects.get_or_create(
                slug=slug,
                defaults={"nome": categoria_nome}
            )

        descricao = produto_data.get("descricao") or ""

        preco_valor = produto_data.get("preco")
        try:
            preco_decimal = (
                Decimal(str(preco_valor).replace(",", "."))
                if preco_valor not in [None, ""]
                else None
            )
        except Exception:
            preco_decimal = None

        # Localizar produto existente por nome
        produto_repo = Produto.objects.filter(nome__iexact=nome).first()

        if not produto_repo:
            Produto.objects.create(
                empresa=None,
                nome=nome,
                descricao=descricao,
                preco=preco_decimal or Decimal("0"),
                categoria=categoria_obj,
                criado_por=instance.criado_por if hasattr(instance, "criado_por") else None,
            )
            return

        # Atualizar campos faltantes
        updated = False
        if not produto_repo.descricao and descricao:
            produto_repo.descricao = descricao
            updated = True
        if (not produto_repo.preco or produto_repo.preco == Decimal("0")) and preco_decimal:
            produto_repo.preco = preco_decimal
            updated = True
        if not produto_repo.categoria and categoria_obj:
            produto_repo.categoria = categoria_obj
            updated = True
        if updated:
            produto_repo.save()
    except Exception:
        import logging
        logging.getLogger(__name__).warning("Falha ao sincronizar ProdutoJSON -> Produto", exc_info=True)
