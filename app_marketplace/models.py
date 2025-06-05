from django.db import models
from django.contrib.auth.models import User

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
    evento  = models.ForeignKey('Evento', on_delete=models.CASCADE, related_name='produto_eventos')
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='produto_eventos')
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
    personal_shopper = models.ForeignKey(
        PersonalShopper,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clientes'
    )
    criado_em     = models.DateTimeField(auto_now_add=True)


    def personal_shoppers(self):
        return PersonalShopper.objects.filter(
            relacionamento_clienteshopper__cliente=self,
            relacionamento_clienteshopper__status='seguindo'
        )


    def __str__(self):
        return self.user.get_full_name()


class RelacionamentoClienteShopper(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    personal_shopper = models.ForeignKey('PersonalShopper', on_delete=models.CASCADE)

    STATUS_CHOICES = [
        ('solicitado', 'Solicitado'),
        ('seguindo', 'Seguindo'),
        ('recusado', 'Recusado'),
        ('bloqueado', 'Bloqueado'),
    ]
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
        verbose_name = 'Endereço de Entrega'
        verbose_name_plural = 'Endereços de Entrega'

    def __str__(self):
        return f"{self.apelido or 'Endereço'} - {self.rua}, {self.numero}, {self.cidade}/{self.estado}"


class Pedido(models.Model):
    cliente          = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    endereco_entrega = models.ForeignKey(EnderecoEntrega, on_delete=models.CASCADE)
    criado_em        = models.DateTimeField(auto_now_add=True)
    status           = models.CharField(
        max_length=20,
        choices=[
            ('pendente', 'Pendente'),
            ('pago', 'Pago'),
            ('enviado', 'Enviado'),
            ('entregue', 'Entregue'),
            ('cancelado', 'Cancelado'),
        ],
        default='pendente'
    )

    def __str__(self):
        return f"Pedido #{self.id} - {self.cliente.user.username}"

class ItemPedido(models.Model):
    pedido         = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='itens')
    produto        = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade     = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.quantidade * self.preco_unitario

    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome}"


class Evento(models.Model):
    personal_shopper = models.ForeignKey(PersonalShopper, on_delete=models.CASCADE, related_name='eventos')
    nome             = models.CharField(max_length=100)
    descricao        = models.TextField(blank=True)
    data_inicio      = models.DateTimeField()
    data_fim         = models.DateTimeField()
    clientes         = models.ManyToManyField('Cliente', related_name='eventos')
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

    @property
    def produtos(self):
        return Produto.objects.filter(produto_eventos__evento=self)


    def __str__(self):
        return f"{self.nome} - {self.personal_shopper.user.get_full_name()}"
