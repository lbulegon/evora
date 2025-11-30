# 🚀 Guia de Migração - ÉVORA Connect

## 📋 Resumo das Mudanças

O sistema ÉVORA foi expandido para suportar o ecossistema completo de **Cliente / Personal Shopper / Keeper**, implementando:

### ✅ Novos Modelos Adicionados:

1. **Keeper** - Address Keepers que recebem e guardam produtos
2. **Pacote** - Volumes/pacotes gerenciados pelos Keepers
3. **MovimentoPacote** - Auditoria de movimentações dos pacotes
4. **FotoPacote** - Múltiplas fotos dos pacotes
5. **OpcaoEnvio** - Opções de envio (motoboy, correios, etc.)
6. **PagamentoIntent** - Intenções de pagamento com split
7. **PagamentoSplit** - Divisão de pagamentos entre favorecidos
8. **PedidoPacote** - Relacionamento entre Pedidos e Pacotes
9. **IntentCompra** - Captura de mensagens "QUERO" do chat-commerce

### 🔧 Correções nos Modelos Existentes:

- **ProdutoEvento.__str__()** - Corrigido para usar `evento.titulo` ao invés de `evento.nome`
- **Pedido** - Adicionado campo `cupom` para corrigir bug no método `calcular_total()`
- **Cliente.__str__()** - Adicionado fallback para `username`
- **PersonalShopper.nome** - Mudado de `TextField` para `CharField(max_length=150)`
- Todos os modelos agora usam **TextChoices** para melhor organização

### 🎨 Melhorias de Código:

- Uso de `TextChoices` para enums (mais limpo e type-safe)
- Adição de `Meta.verbose_name` e `verbose_name_plural` em todos os modelos
- Adição de `related_name` em todas as ForeignKeys
- Ordenação padrão (`ordering`) nos modelos principais
- Métodos helper adicionados ao modelo `User`:
  - `user.is_cliente` - verifica se o usuário é cliente
  - `user.is_shopper` - verifica se o usuário é shopper
  - `user.is_keeper` - verifica se o usuário é keeper

---

## 📝 Plano de Migração

### Etapa 1: Backup do Banco de Dados ⚠️

**IMPORTANTE: Faça backup antes de migrar!**

```bash
# Se estiver usando PostgreSQL local
pg_dump -U postgres -d railway > backup_evora_$(date +%Y%m%d_%H%M%S).sql

# Se estiver conectado ao Railway (produção)
# Conecte-se ao banco e faça backup via Railway CLI ou painel
```

### Etapa 2: Criar as Migrações

```bash
# Ative o ambiente virtual (se estiver usando)
# No Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Criar as migrações
python manage.py makemigrations app_marketplace

# Revisar as migrações geradas
# Verifique o arquivo em: app_marketplace/migrations/0014_*.py
```

### Etapa 3: Aplicar as Migrações

```bash
# Primeiro, verifique o que será aplicado (dry-run)
python manage.py migrate app_marketplace --plan

# Se estiver tudo OK, aplique as migrações
python manage.py migrate app_marketplace
```

### Etapa 4: Verificar a Migração

```bash
# Abra o shell do Django
python manage.py shell

# Teste os novos modelos
from app_marketplace.models import Keeper, Pacote, OpcaoEnvio
from django.contrib.auth.models import User

# Teste as propriedades helper do User
user = User.objects.first()
print(f"É cliente? {user.is_cliente}")
print(f"É shopper? {user.is_shopper}")
print(f"É keeper? {user.is_keeper}")
```

---

## 🎯 Funcionalidades Implementadas

### 1️⃣ Sistema de Keeper (Address Keeper)

```python
# Exemplo: Criar um Keeper
from django.contrib.auth.models import User
from app_marketplace.models import Keeper

user = User.objects.get(username='maria_orlando')
keeper = Keeper.objects.create(
    user=user,
    apelido_local='Vila Angélica - Sorocaba',
    cidade='Sorocaba',
    estado='SP',
    pais='Estados Unidos',
    capacidade_itens=50,
    taxa_guarda_dia=5.00,
    taxa_motoboy=15.00,
    aceita_retirada=True,
    aceita_envio=True,
    verificado=True
)
```

### 2️⃣ Sistema de Pacotes

```python
# Exemplo: Criar um Pacote
from app_marketplace.models import Pacote, Cliente, Keeper
from django.utils import timezone

pacote = Pacote.objects.create(
    codigo_publico='EV-2024-001',
    cliente=cliente,
    keeper=keeper,
    descricao='iPhone 15 Pro + AirPods',
    valor_declarado=8000.00,
    peso_kg=1.5,
    dimensoes_cm='30x20x15',
    status=Pacote.Status.AGUARDANDO_RECEB
)

# Confirmar recebimento
pacote.status = Pacote.Status.RECEBIDO
pacote.confirmacao_visual = Pacote.ConfirmacaoVisual.AMOR  # ❤️
pacote.recebido_em = timezone.now()
pacote.guarda_inicio = timezone.now()
pacote.save()

# Calcular custo de guarda
print(f"Dias em guarda: {pacote.dias_em_guarda()}")
print(f"Custo estimado: R$ {pacote.custo_guarda_estimado():.2f}")
```

### 3️⃣ Opções de Envio

```python
# Exemplo: Configurar opções de envio do Keeper
from app_marketplace.models import OpcaoEnvio

# Motoboy Sorocaba
OpcaoEnvio.objects.create(
    keeper=keeper,
    tipo=OpcaoEnvio.Tipo.MOTOBOY,
    cidade='Sorocaba',
    valor_base=15.00
)

# Motoboy Votorantim
OpcaoEnvio.objects.create(
    keeper=keeper,
    tipo=OpcaoEnvio.Tipo.MOTOBOY,
    cidade='Votorantim',
    valor_base=20.00
)

# Correios
OpcaoEnvio.objects.create(
    keeper=keeper,
    tipo=OpcaoEnvio.Tipo.CORREIOS,
    valor_base=50.00,
    observacoes='SEDEX com AR'
)
```

### 4️⃣ Sistema de Pagamento com Split

```python
# Exemplo: Criar pagamento parcelado com split
from app_marketplace.models import PagamentoIntent, PagamentoSplit

intent = PagamentoIntent.objects.create(
    pedido=pedido,
    metodo=PagamentoIntent.Metodo.LINK_EXTERNO,
    valor_total=500.00,
    entrada_percent=50.00,  # 50% de entrada
    gateway_ref='https://link.infinitepay.io/...',
    status=PagamentoIntent.Status.PENDENTE
)

# Split: 10% para o Shopper
PagamentoSplit.objects.create(
    intent=intent,
    favorecido=shopper.user,
    percentual=10.00,
    valor=50.00
)

# Split: 5% para o Keeper
PagamentoSplit.objects.create(
    intent=intent,
    favorecido=keeper.user,
    percentual=5.00,
    valor=25.00
)

# Split: 85% para a Empresa/ÉVORA
PagamentoSplit.objects.create(
    intent=intent,
    favorecido=empresa_user,
    percentual=85.00,
    valor=425.00
)
```

### 5️⃣ Chat-Commerce: Captura de "QUERO"

```python
# Exemplo: Processar mensagem "QUERO"
from app_marketplace.models import IntentCompra

intent = IntentCompra.objects.create(
    cliente=cliente,
    personal_shopper=shopper,
    origem_mid='whatsapp_msg_123456',
    texto_bruto='QUERO opção X',
    interpretado={'produto_id': 123, 'opcao': 'X'},
    status=IntentCompra.Status.NOVO
)

# Depois um worker pode processar e criar o pedido
if intent.status == IntentCompra.Status.NOVO:
    # Processar e criar pedido automático
    # ...
    intent.status = IntentCompra.Status.PROCESSADO
    intent.save()
```

---

## 🔗 Relacionamentos entre Modelos

```
User (Django Auth)
├── Cliente (OneToOne)
│   ├── pacotes (ForeignKey)
│   ├── pedidos (ForeignKey)
│   ├── enderecos (ForeignKey)
│   ├── intents (ForeignKey)
│   └── eventos (ManyToMany)
│
├── PersonalShopper (OneToOne)
│   ├── pacotes (ForeignKey - opcional)
│   ├── eventos (ForeignKey)
│   └── relacionamentos (ManyToMany via RelacionamentoClienteShopper)
│
└── Keeper (OneToOne)
    ├── pacotes (ForeignKey)
    └── opcoes_envio (ForeignKey)

Pacote
├── cliente (ForeignKey)
├── personal_shopper (ForeignKey - opcional)
├── keeper (ForeignKey - opcional)
├── movimentos (auditoria)
├── fotos (múltiplas)
└── pedidos_relacionados (ManyToMany via PedidoPacote)

Pedido
├── cliente (ForeignKey)
├── itens (ItemPedido)
├── pagamentos (PagamentoIntent)
│   └── splits (PagamentoSplit)
└── pacotes_relacionados (ManyToMany via PedidoPacote)
```

---

## 🎨 Próximos Passos

### 1. Atualizar o Admin do Django

Crie/atualize `app_marketplace/admin.py`:

```python
from django.contrib import admin
from .models import (
    Keeper, Pacote, MovimentoPacote, FotoPacote,
    OpcaoEnvio, PagamentoIntent, PagamentoSplit,
    IntentCompra, PedidoPacote
)

@admin.register(Keeper)
class KeeperAdmin(admin.ModelAdmin):
    list_display = ['user', 'cidade', 'pais', 'verificado', 'ativo']
    list_filter = ['verificado', 'ativo', 'pais']
    search_fields = ['user__username', 'cidade', 'apelido_local']

@admin.register(Pacote)
class PacoteAdmin(admin.ModelAdmin):
    list_display = ['codigo_publico', 'cliente', 'keeper', 'status', 'confirmacao_visual']
    list_filter = ['status', 'confirmacao_visual']
    search_fields = ['codigo_publico', 'descricao']
    readonly_fields = ['criado_em', 'atualizado_em']

# ... adicione os demais
```

### 2. Criar Views e URLs

- View para listar Keepers disponíveis
- View para criar/gerenciar Pacotes
- View para acompanhar status do Pacote (timeline)
- API endpoints para integração com chat (WhatsApp)

### 3. Templates

- Dashboard do Keeper (gerenciar pacotes)
- Dashboard do Cliente (acompanhar pacotes)
- Dashboard do Shopper (gerenciar compras)
- Timeline de Pacote (com fotos e movimentos)

### 4. Testes

Crie testes para os novos modelos:

```python
from django.test import TestCase
from app_marketplace.models import Keeper, Pacote

class KeeperTestCase(TestCase):
    def test_criar_keeper(self):
        # ...
```

---

## 📚 Documentação dos Insights Implementados

Com base nos diálogos do WhatsApp, implementamos:

### ✅ Confirmação Visual (❤️ / 👍)
- Campo `confirmacao_visual` no modelo `Pacote`
- Enum com opções: `NENHUMA`, `APROVADO` (👍), `AMOR` (❤️)

### ✅ Pagamento Fracionado
- Modelo `PagamentoIntent` com campo `entrada_percent`
- Suporta links externos (InfinitePay, etc.)
- Sistema de `PagamentoSplit` para divisão automática

### ✅ Opções de Logística Local
- Modelo `OpcaoEnvio` com tipos: motoboy, correios, retirada, etc.
- Valores por cidade (Sorocaba R$15, Votorantim R$20)

### ✅ Gestão de Estoque Visual
- Campo `foto_recebimento` no `Pacote`
- Modelo `FotoPacote` para múltiplas fotos
- Campos `peso_kg` e `dimensoes_cm` para controle de espaço

### ✅ Timeline e Prazos
- Modelo `MovimentoPacote` para auditoria
- Campos `guarda_inicio` e `guarda_fim`
- Método `dias_em_guarda()` para calcular tempo

### ✅ Chat-Commerce
- Modelo `IntentCompra` para capturar "QUERO"
- Campo `interpretado` (JSON) para parsing automático
- Status: novo → processado

---

## ⚠️ Avisos Importantes

1. **Produção**: Teste todas as migrações em ambiente local antes de aplicar em produção
2. **Backup**: Sempre faça backup antes de migrar
3. **Dados Existentes**: As migrações são aditivas (não removem dados existentes)
4. **Performance**: Considere criar índices para campos muito consultados:
   ```python
   class Meta:
       indexes = [
           models.Index(fields=['status', 'criado_em']),
       ]
   ```

---

## 🤝 Suporte

Para dúvidas ou problemas durante a migração, consulte:
- Documentação Django: https://docs.djangoproject.com/
- Railway Docs: https://docs.railway.app/

---

**ÉVORA Connect** - *Minimalist, Sophisticated Style*


