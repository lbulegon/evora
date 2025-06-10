from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Empresa(models.Model):
    nome      = models.CharField(max_length=100)
    cnpj      = models.CharField(max_length=18, unique=True)
    email     = models.EmailField()
    telefone  = models.CharField(max_length=20, blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome
class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.nome

class Produto(models.Model):
    empresa      = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome         = models.CharField(max_length=100)
    descricao    = models.TextField()
    preco        = models.DecimalField(max_digits=10, decimal_places=2)
    categoria    = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    imagem       = models.ImageField(upload_to='produtos/', blank=True, null=True)
    criado_em    = models.DateTimeField(auto_now_add=True)
    ativo        = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

class ProdutoEvento(models.Model):
    evento       = models.ForeignKey('Evento', on_delete=models.CASCADE, related_name='produto_eventos')
    produto      = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='produto_eventos')
    importado_de = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='importacoes')

    class Meta:
        unique_together = ('evento', 'produto')

    def __str__(self):
        return f"{self.produto.nome} no evento {self.evento.nome}"

class PersonalShopper(models.Model):
    user         = models.OneToOneField(User, on_delete=models.CASCADE)
    nome         = models.TextField(blank=True)
    bio          = models.TextField(blank=True)
    # Redes sociais
    facebook     = models.URLField(blank=True)
    tiktok       = models.URLField(blank=True)
    twitter      = models.URLField(blank=True)
    linkedin     = models.URLField(blank=True)
    pinterest    = models.URLField(blank=True)
    youtube      = models.URLField(blank=True)
    instagram    = models.URLField(blank=True)
    empresa      = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True)
    ativo        = models.BooleanField(default=True)
    criado_em    = models.DateTimeField(auto_now_add=True)

    def clientes(self):
        return Cliente.objects.filter(
            relacionamento_clienteshopper__personal_shopper=self,
            relacionamento_clienteshopper__status='seguindo'
        )

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Cliente(models.Model):
    user             = models.OneToOneField(User, on_delete=models.CASCADE)
    telefone         = models.CharField(max_length=20, blank=True)
    criado_em        = models.DateTimeField(auto_now_add=True)

    def personal_shoppers(self):
        return PersonalShopper.objects.filter(
            relacionamento_clienteshopper__cliente=self,
            relacionamento_clienteshopper__status='seguindo'
        )

    def __str__(self):
        return self.user.get_full_name()

class RelacionamentoClienteShopper(models.Model):
    STATUS_CHOICES = [
        ('solicitado', 'Solicitado'),
        ('seguindo', 'Seguindo'),
        ('recusado', 'Recusado'),
        ('bloqueado', 'Bloqueado'),
    ]

    cliente          = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    personal_shopper = models.ForeignKey('PersonalShopper', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='solicitado')
    data_criacao = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('cliente', 'personal_shopper')

    def __str__(self):
        return f"{self.cliente.user.username} ↔ {self.personal_shopper.user.username} ({self.status})"

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
        verbose_name        = 'Endereço de Entrega'
        verbose_name_plural = 'Endereços de Entrega'

    def __str__(self):
        return f"{self.apelido or 'Endereço'} - {self.rua}, {self.numero}, {self.cidade}/{self.estado}"


class Pedido(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
        ('em_preparacao', 'Em preparação'),
        ('enviado', 'Enviado'),
        ('entregue', 'Entregue'),
        ('cancelado', 'Cancelado'),
    ]

    METODO_PAGAMENTO_CHOICES = [
        ('pix', 'PIX'),
        ('cartao_credito', 'Cartão de Crédito'),
        ('cartao_debito', 'Cartão de Débito'),
        ('boleto', 'Boleto'),
        ('dinheiro', 'Dinheiro'),
    ]

    cliente             = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    endereco_entrega    = models.ForeignKey(EnderecoEntrega, on_delete=models.CASCADE)
    criado_em           = models.DateTimeField(auto_now_add=True)
    atualizado_em       = models.DateTimeField(auto_now=True)
    status              = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    metodo_pagamento    = models.CharField(max_length=20, choices=METODO_PAGAMENTO_CHOICES, blank=True, null=True)
    valor_total         = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    observacoes         = models.TextField(blank=True)
    codigo_rastreamento = models.CharField(max_length=100, blank=True, null=True)
    is_revisado         = models.BooleanField(default=False)
    is_prioritario      = models.BooleanField(default=False)


    def calcular_total(self):
        total = sum(item.subtotal() for item in self.itens.all())
        if self.cupom and self.cupom.ativo:
            total -= total * (self.cupom.desconto_percentual / 100)
        self.valor_total = total
        return total


    def salvar_com_total(self):
        self.valor_total = self.calcular_total()
        self.save()

    def __str__(self):
        return f"Pedido #{self.id} - {self.cliente.user.username} - {self.get_status_display()}"
class CupomDesconto(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    descricao = models.TextField(blank=True)
    desconto_percentual = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # Ex: 10.00 = 10%
    ativo = models.BooleanField(default=True)
    valido_ate = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.codigo} - {self.desconto_percentual}%"


class ItemPedido(models.Model):
    pedido         = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='itens')
    produto        = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade     = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    cupom          = models.ForeignKey(CupomDesconto, null=True, blank=True, on_delete=models.SET_NULL)

    def subtotal(self):
        return self.quantidade * self.preco_unitario

    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome}"

class Estabelecimento(models.Model):
    nome        = models.CharField(max_length=150)
    endereco    = models.CharField(max_length=300, blank=True)
    telefone    = models.CharField(max_length=20, blank=True)
    email       = models.EmailField(blank=True)
    descricao   = models.TextField(blank=True)
    criado_em   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

class Evento(models.Model):
    personal_shopper = models.ForeignKey(PersonalShopper, on_delete=models.CASCADE, related_name='eventos')
    titulo           = models.CharField(max_length=100)
    descricao        = models.TextField(blank=True)
    data_inicio      = models.DateTimeField()
    data_fim         = models.DateTimeField()
    clientes         = models.ManyToManyField(Cliente, related_name='eventos')
    estabelecimentos = models.ManyToManyField(Estabelecimento, related_name='eventos', blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('ativo', 'Ativo'),
            ('encerrado', 'Encerrado'),
            ('privado', 'Privado'),
        ],
        default='ativo'
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} - {self.personal_shopper.user.get_full_name()}"

class OpenAIKey(models.Model):
    nome              = models.CharField(max_length=100)
    chave_secreta     = models.CharField(max_length=255)
    criado            = models.DateTimeField(auto_now_add=True)
    usado_ultima_vez  = models.DateTimeField(null=True, blank=True)
    criado_por        = models.CharField(max_length=100)
    permissoes        = models.TextField(blank=True)  # Pode ser um campo JSONField dependendo do banco de dados

    def __str__(self):
        return self.nome