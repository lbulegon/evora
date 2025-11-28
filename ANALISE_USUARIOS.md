# 📊 ANÁLISE COMPLETA DOS USUÁRIOS - ÉVORA/VitrineZap

## 🎯 Visão Geral

O sistema ÉVORA possui **4 tipos principais de usuários**, cada um com características, permissões e funcionalidades específicas:

1. **Cliente** - Consumidor final
2. **Personal Shopper** - Vendedor/Consultor
3. **Keeper** - Guardador de pacotes
4. **Agente KMN** - Agente unificado (Shopper/Keeper/Dual)

---

## 1️⃣ CLIENTE

### 📋 Características Básicas

**Modelo**: `Cliente`  
**Relacionamento**: `OneToOne` com `User` (Django Auth)  
**Propriedade**: `user.is_cliente` (retorna `True` se tem perfil Cliente)

### 🔑 Campos do Modelo

```python
- user: OneToOneField(User) - Usuário Django vinculado
- telefone: CharField(20) - Telefone de contato
- criado_em: DateTimeField - Data de criação
```

### 🎯 Funcionalidades

#### ✅ O que o Cliente PODE fazer:

1. **Navegação e Visualização**
   - Acessar home e catálogo de produtos
   - Ver lista de Personal Shoppers disponíveis
   - Visualizar seus próprios pedidos
   - Ver status de pacotes em guarda

2. **Relacionamentos**
   - Seguir Personal Shoppers (`RelacionamentoClienteShopper`)
   - Estabelecer relações com Agentes KMN (`ClienteRelacao`)
   - Participar de grupos WhatsApp como membro

3. **Compras**
   - Criar pedidos através de Personal Shoppers
   - Receber produtos via sistema de pacotes
   - Acompanhar status de entregas

4. **Pacotes**
   - Criar pacotes para guarda
   - Acompanhar movimentações de pacotes
   - Receber notificações de status

#### ❌ O que o Cliente NÃO pode fazer:

- ❌ Acessar dashboard administrativo
- ❌ Criar/gerenciar grupos WhatsApp (apenas participar)
- ❌ Criar produtos ou ofertas
- ❌ Gerenciar estoque
- ❌ Ver dados de outros clientes
- ❌ Acessar analytics de vendas

### 🔗 Relacionamentos

```python
# Relacionamento com Personal Shoppers
cliente.personal_shoppers()  # Retorna shoppers que o cliente segue

# Relacionamento com Pacotes
cliente.pacotes.all()  # Todos os pacotes do cliente

# Relacionamento com Pedidos
cliente.user.pedido_set.all()  # Pedidos do cliente

# Relacionamento com Agentes KMN
cliente.relacoes_agente.all()  # Relações com agentes
```

### 📊 Métodos Úteis

```python
# Obter Personal Shoppers que o cliente segue
cliente.personal_shoppers()

# Verificar se é cliente
user.is_cliente  # True/False
```

### 🎨 Interface

- **Home**: Catálogo de produtos e Personal Shoppers
- **Meus Pedidos**: Lista de pedidos realizados
- **Pacotes**: Status de pacotes em guarda
- **Personal Shoppers**: Lista de shoppers seguidos

---

## 2️⃣ PERSONAL SHOPPER

### 📋 Características Básicas

**Modelo**: `PersonalShopper`  
**Relacionamento**: `OneToOne` com `User`  
**Propriedade**: `user.is_shopper` (retorna `True` se tem perfil Shopper)

### 🔑 Campos do Modelo

```python
- user: OneToOneField(User) - Usuário Django
- nome: CharField(150) - Nome do shopper
- bio: TextField - Biografia/descrição
- facebook, tiktok, twitter, linkedin, pinterest, youtube, instagram: URLField
- empresa: ForeignKey(Empresa) - Empresa vinculada (opcional)
- ativo: BooleanField - Status ativo/inativo
- criado_em: DateTimeField - Data de criação
```

### 🎯 Funcionalidades

#### ✅ O que o Personal Shopper PODE fazer:

1. **Dashboard WhatsApp** ⭐
   - Criar e gerenciar grupos WhatsApp
   - Adicionar participantes aos grupos
   - Postar produtos nos grupos
   - Gerenciar pedidos via WhatsApp
   - Ver analytics de vendas

2. **Gestão de Produtos**
   - Criar produtos no catálogo
   - Gerenciar ofertas e promoções
   - Controlar estoque (se for Agente KMN)

3. **Relacionamentos**
   - Ter clientes que o seguem
   - Estabelecer relações com clientes
   - Participar da rede KMN como Agente

4. **Vendas**
   - Receber pedidos de clientes
   - Gerenciar pedidos e status
   - Ver relatórios de vendas

5. **Pacotes**
   - Criar pacotes para clientes
   - Associar pacotes a pedidos
   - Acompanhar envios

6. **Eventos**
   - Criar eventos (viagens, campanhas)
   - Associar produtos a eventos
   - Gerenciar catálogos por evento

#### ❌ O que o Personal Shopper NÃO pode fazer:

- ❌ Acessar dados de outros shoppers
- ❌ Ver grupos WhatsApp de outros usuários
- ❌ Modificar configurações globais do sistema
- ❌ Acessar admin Django (a menos que seja staff)

### 🔗 Relacionamentos

```python
# Clientes que seguem o shopper
shopper.clientes()  # Retorna clientes que seguem

# Produtos do shopper
shopper.user.produto_set.all()  # Via empresa

# Pedidos relacionados
shopper.pacotes.all()  # Pacotes criados pelo shopper

# Grupos WhatsApp (owner)
WhatsappGroup.objects.filter(owner=shopper.user)

# Agente KMN (se vinculado)
shopper.agente_profile  # Agente relacionado
```

### 📊 Métodos Úteis

```python
# Obter clientes que seguem
shopper.clientes()

# Verificar se é shopper
user.is_shopper  # True/False

# Acessar perfil de agente (se existir)
if user.is_shopper and hasattr(user.personalshopper, 'agente_profile'):
    agente = user.personalshopper.agente_profile
```

### 🎨 Interface

- **Dashboard WhatsApp**: Grupos, participantes, produtos, pedidos
- **Dashboard Shopper**: Analytics, vendas, clientes
- **Produtos**: Gerenciar catálogo
- **Pedidos**: Gerenciar vendas
- **Grupos WhatsApp**: Gerenciar grupos e comunicação

### 🔒 Isolamento de Dados

**IMPORTANTE**: Cada Personal Shopper é um **usuário master** com isolamento total:
- Vê apenas seus próprios grupos WhatsApp
- Vê apenas seus próprios clientes
- Vê apenas seus próprios pedidos
- Dados completamente isolados de outros shoppers

---

## 3️⃣ KEEPER

### 📋 Características Básicas

**Modelo**: `Keeper`  
**Relacionamento**: `OneToOne` com `User`  
**Propriedade**: `user.is_keeper` (retorna `True` se tem perfil Keeper)

### 🔑 Campos do Modelo

```python
# Localização
- apelido_local: CharField(100) - Ex: "Vila Angélica - Sorocaba"
- rua, numero, complemento, bairro, cidade, estado, cep, pais

# Capacidade e Taxas
- capacidade_itens: PositiveIntegerField - Capacidade (volumes)
- ocupacao_percent: DecimalField(5,2) - Ocupação calculada (%)
- taxa_guarda_dia: DecimalField(8,2) - R$/dia por volume
- taxa_motoboy: DecimalField(8,2) - Preço base motoboy (opcional)

# Opções
- aceita_retirada: BooleanField - Aceita retirada no local
- aceita_envio: BooleanField - Aceita envio via motoboy

# Status
- verificado: BooleanField - Verificado pela plataforma
- ativo: BooleanField - Status ativo/inativo
- criado_em: DateTimeField - Data de criação
```

### 🎯 Funcionalidades

#### ✅ O que o Keeper PODE fazer:

1. **Dashboard WhatsApp** ⭐
   - Criar grupos para comunicação com shoppers
   - Receber notificações de novos pacotes
   - Comunicar status de pacotes
   - Gerenciar entregas

2. **Gestão de Pacotes**
   - Receber pacotes para guarda
   - Registrar recebimento de pacotes
   - Atualizar status de pacotes
   - Calcular custos de guarda
   - Gerenciar envios e retiradas

3. **Relacionamentos**
   - Trabalhar com múltiplos shoppers
   - Estabelecer trustlines na rede KMN
   - Participar da rede como Agente

4. **Financeiro**
   - Configurar taxas de guarda
   - Configurar taxas de motoboy
   - Receber comissões (via KMN)

5. **Localização**
   - Gerenciar endereço do ponto de guarda
   - Configurar capacidade
   - Controlar ocupação

#### ❌ O que o Keeper NÃO pode fazer:

- ❌ Criar produtos ou ofertas
- ❌ Acessar dados de outros keepers
- ❌ Ver grupos WhatsApp de outros usuários
- ❌ Modificar configurações globais

### 🔗 Relacionamentos

```python
# Pacotes em guarda
keeper.pacotes.all()  # Todos os pacotes do keeper

# Movimentos de pacotes
MovimentoPacote.objects.filter(pacote__keeper=keeper)

# Grupos WhatsApp (owner)
WhatsappGroup.objects.filter(owner=keeper.user)

# Agente KMN (se vinculado)
keeper.agente_profile  # Agente relacionado

# Trustlines (como keeper)
TrustlineKeeper.objects.filter(agente_b__keeper=keeper)
```

### 📊 Métodos Úteis

```python
# Verificar se é keeper
user.is_keeper  # True/False

# Calcular ocupação
keeper.ocupacao_percent  # Percentual de ocupação

# Verificar capacidade
if keeper.pacotes.filter(status='em_guarda').count() < keeper.capacidade_itens:
    print("Tem espaço disponível")
```

### 🎨 Interface

- **Dashboard WhatsApp**: Grupos de comunicação
- **Dashboard Keeper**: Pacotes em guarda, entregas
- **Pacotes**: Gerenciar recebimentos e envios
- **Localização**: Configurar endereço e capacidade

### 🔒 Isolamento de Dados

**IMPORTANTE**: Cada Keeper é um **usuário master** com isolamento total:
- Vê apenas seus próprios grupos WhatsApp
- Vê apenas seus próprios pacotes
- Dados completamente isolados de outros keepers

---

## 4️⃣ AGENTE KMN

### 📋 Características Básicas

**Modelo**: `Agente`  
**Relacionamento**: `OneToOne` com `User`  
**Propriedade**: `user.is_agente` (retorna `True` se tem perfil Agente)

### 🔑 Campos do Modelo

```python
# Vinculação
- user: OneToOneField(User)
- personal_shopper: OneToOneField(PersonalShopper, null=True)
- keeper: OneToOneField(Keeper, null=True)

# Dados do Agente
- nome_comercial: CharField(200) - Nome comercial
- bio_agente: TextField - Biografia como agente

# Scores de Reputação
- score_keeper: DecimalField(5,2) - Score como Keeper (0-10)
- score_shopper: DecimalField(5,2) - Score como Shopper (0-10)

# Status
- ativo_como_keeper: BooleanField - Ativo como Keeper
- ativo_como_shopper: BooleanField - Ativo como Shopper
- verificado_kmn: BooleanField - Verificado pela rede KMN

# Timestamps
- criado_em, atualizado_em
```

### 🎯 Funcionalidades

#### ✅ O que o Agente KMN PODE fazer:

1. **Papéis Dinâmicos** ⭐
   - Atuar como **Shopper** (vender produtos)
   - Atuar como **Keeper** (guardar pacotes)
   - Atuar como **Dual Role** (ambos simultaneamente)

2. **Rede KMN**
   - Estabelecer trustlines com outros agentes
   - Criar ofertas com markup local
   - Receber comissões de vendas cooperadas
   - Participar da resolução de conflitos de cliente

3. **Estoque**
   - Gerenciar estoque de produtos
   - Disponibilizar produtos para a rede
   - Controlar preços e disponibilidade

4. **Ofertas**
   - Criar ofertas com markup local
   - Oferecer produtos para clientes de outros agentes
   - Gerenciar ofertas exclusivas

5. **Relacionamentos**
   - Estabelecer relações com clientes (`ClienteRelacao`)
   - Controlar força da relação (0-100)
   - Acompanhar histórico de pedidos

6. **Estatísticas**
   - Ver `RoleStats` (estatísticas por papel)
   - Acompanhar scores de reputação
   - Ver performance como Shopper/Keeper

#### ❌ O que o Agente NÃO pode fazer:

- ❌ Acessar dados de outros agentes (exceto via trustlines)
- ❌ Modificar trustlines sem aprovação
- ❌ Ver ofertas exclusivas de outros agentes

### 🔗 Relacionamentos

```python
# Relações com Clientes
agente.relacoes_cliente.all()  # ClienteRelacao

# Estoque
agente.estoque.all()  # EstoqueItem

# Ofertas
agente.ofertas_origem.all()  # Ofertas onde é origem
agente.ofertas_feitas.all()  # Ofertas que fez

# Trustlines
agente.trustlines_como_a.all()  # Trustlines como agente A
agente.trustlines_como_b.all()  # Trustlines como agente B

# Estatísticas
agente.stats  # RoleStats

# Perfis vinculados
agente.personal_shopper  # Se for shopper
agente.keeper  # Se for keeper
```

### 📊 Propriedades e Métodos

```python
# Verificar se é agente
user.is_agente  # True/False

# Score dual (média harmônica)
agente.dual_role_score  # Score combinado

# Verificar se é dual role
agente.is_dual_role  # True se atua como ambos

# Atualizar scores
agente.stats.atualizar_scores()  # Atualiza scores baseado em stats
```

### 🎨 Interface

- **Dashboard KMN**: Visão geral da rede
- **Rede**: Trustlines, ofertas, agentes parceiros
- **Estoque**: Gerenciar produtos
- **Ofertas**: Criar e gerenciar ofertas
- **Estatísticas**: Performance e scores

### 🔄 Compatibilidade

O modelo `Agente` é **compatível** com os modelos existentes:
- Um `PersonalShopper` pode ter um `Agente` vinculado
- Um `Keeper` pode ter um `Agente` vinculado
- Um `Agente` pode ser criado sem perfil Shopper/Keeper (futuro)

---

## 🔄 COMPARAÇÃO ENTRE TIPOS

### Matriz de Permissões

| Funcionalidade | Cliente | Shopper | Keeper | Agente |
|----------------|---------|---------|--------|--------|
| Ver produtos | ✅ | ✅ | ✅ | ✅ |
| Criar produtos | ❌ | ✅ | ❌ | ✅ (se shopper) |
| Criar grupos WhatsApp | ❌ | ✅ | ✅ | ✅ (se shopper/keeper) |
| Gerenciar pacotes | ✅ (próprios) | ✅ (criar) | ✅ (receber) | ✅ (se keeper) |
| Ver dashboard | ❌ | ✅ | ✅ | ✅ |
| Ver analytics | ❌ | ✅ | ✅ | ✅ |
| Participar KMN | ❌ | ❌ | ❌ | ✅ |
| Criar ofertas | ❌ | ❌ | ❌ | ✅ |
| Estabelecer trustlines | ❌ | ❌ | ❌ | ✅ |
| Gerenciar estoque | ❌ | ❌ | ❌ | ✅ |

### Matriz de Acesso a Dados

| Tipo de Dado | Cliente | Shopper | Keeper | Agente |
|--------------|---------|---------|--------|--------|
| Próprios dados | ✅ | ✅ | ✅ | ✅ |
| Dados de outros | ❌ | ❌ | ❌ | ❌ |
| Dados via trustline | ❌ | ❌ | ❌ | ✅ |
| Dados globais | ❌ | ❌ | ❌ | ❌ |

---

## 🔐 SISTEMA DE PERMISSÕES

### Propriedades do User

```python
# Verificações rápidas
user.is_cliente   # True se tem perfil Cliente
user.is_shopper   # True se tem perfil PersonalShopper
user.is_keeper    # True se tem perfil Keeper
user.is_agente    # True se tem perfil Agente

# Acessar perfis
user.cliente           # Cliente (se existir)
user.personalshopper   # PersonalShopper (se existir)
user.keeper            # Keeper (se existir)
user.agente            # Agente (se existir)
```

### Verificações em Views

```python
# Exemplo: Dashboard WhatsApp
@login_required
def whatsapp_dashboard(request):
    if not (request.user.is_shopper or request.user.is_keeper):
        messages.error(request, "Acesso restrito")
        return redirect('home')
    # ...
```

### Isolamento de Dados

**Regra de Ouro**: Sempre filtrar por `owner=request.user` ou relacionamento direto:

```python
# ✅ CORRETO - Isolado
groups = WhatsappGroup.objects.filter(owner=request.user)
pacotes = Pacote.objects.filter(cliente__user=request.user)

# ❌ ERRADO - Expõe dados de outros
groups = WhatsappGroup.objects.all()
pacotes = Pacote.objects.all()
```

---

## 📈 ESTATÍSTICAS E MÉTRICAS

### Por Tipo de Usuário

#### Cliente
- Total de pedidos
- Valor total gasto
- Personal Shoppers seguidos
- Pacotes em guarda

#### Personal Shopper
- Total de clientes
- Total de vendas
- Receita total
- Produtos no catálogo
- Grupos WhatsApp ativos

#### Keeper
- Total de pacotes recebidos
- Capacidade utilizada (%)
- Receita de guarda
- Taxa média de guarda

#### Agente KMN
- Score Keeper (0-10)
- Score Shopper (0-10)
- Total de trustlines
- Ofertas criadas
- Vendas cooperadas
- Comissões recebidas

---

## 🚀 CASOS DE USO

### 1. Cliente Compra de Personal Shopper

```
Cliente → Segue Personal Shopper → Vê produtos → Faz pedido → 
Personal Shopper cria pacote → Keeper recebe → Cliente recebe
```

### 2. Venda Cooperada (KMN)

```
Cliente (da Márcia/Keeper) → Vê oferta do Júnior (Shopper) → 
Faz pedido → Márcia recebe comissão → Júnior recebe comissão
```

### 3. Agente Dual Role

```
Agente (Ana) → Atua como Shopper (vende) → Atua como Keeper (guarda) → 
Gerencia tudo em um só lugar → Scores combinados
```

---

## 📝 NOTAS IMPORTANTES

1. **Um usuário pode ter múltiplos perfis?**
   - ✅ Sim! Um `User` pode ter `Cliente` + `PersonalShopper`
   - ✅ Um `User` pode ter `PersonalShopper` + `Keeper`
   - ✅ Um `Agente` pode estar vinculado a `PersonalShopper` e/ou `Keeper`

2. **Isolamento de Dados**
   - Cada usuário master (Shopper/Keeper) vê apenas seus dados
   - Sistema multi-tenant com isolamento total
   - Impossível acessar dados de outros usuários

3. **KMN (Keeper Mesh Network)**
   - Sistema avançado de colaboração entre agentes
   - Permite vendas cooperadas
   - Sistema de trustlines e comissões
   - Resolução automática de conflitos

4. **WhatsApp Integration**
   - Shoppers e Keepers podem criar grupos
   - Cada grupo tem um `owner` (usuário master)
   - Isolamento total por owner

---

## 🔄 PRÓXIMOS PASSOS

1. **Análise de Performance**: Verificar queries e índices
2. **Testes de Permissões**: Validar isolamento de dados
3. **Documentação de APIs**: Documentar endpoints por tipo de usuário
4. **Guias de Uso**: Criar guias específicos para cada tipo

---

**Documento gerado em**: {{ data_atual }}  
**Versão do Sistema**: ÉVORA/VitrineZap v2.0  
**Última atualização**: Análise completa dos modelos de usuário

