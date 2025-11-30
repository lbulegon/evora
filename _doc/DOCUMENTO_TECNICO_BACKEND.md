# 🔧 DOCUMENTO TÉCNICO - Backend Évora

## 📋 ESPECIFICAÇÃO TÉCNICA COMPLETA

Este documento define a implementação técnica completa do sistema Shopper/Keeper/Mesh no backend Évora.

---

## 1. ENTIDADES PRINCIPAIS

### 1.1. Usuário (User)

**Modelo Django**: `django.contrib.auth.models.User`

**Campos principais**:
- `id` - Primary Key
- `username` - Nome de usuário
- `email` - Email
- `first_name`, `last_name` - Nome completo

**Relacionamentos**:
- Pode ter múltiplas `CarteiraCliente`
- Pode ser `agente_a` ou `agente_b` em `LigacaoMesh`
- Pode ser `shopper` ou `keeper` em `Pedido`

---

### 1.2. CarteiraCliente (CustomerWallet)

**Modelo**: `app_marketplace.models.CarteiraCliente`

**Campos**:
```python
- id: BigAutoField (PK)
- owner: ForeignKey(User) - Dono da carteira
- nome_exibicao: CharField(200) - Nome para exibição
- metadados: JSONField - Metadados adicionais
- criado_em: DateTimeField (auto)
- atualizado_em: DateTimeField (auto)
```

**Relacionamentos**:
- `owner` → User (dono da carteira)
- `clientes` → Cliente (clientes desta carteira)
- `pedidos` → Pedido (pedidos desta carteira)

**Regras de Negócio**:
- Um User pode ter múltiplas CarteiraCliente
- Cada Cliente pertence a uma CarteiraCliente
- CarteiraCliente define o "dono" do cliente

---

### 1.3. Cliente (Customer)

**Modelo**: `app_marketplace.models.Cliente`

**Campos**:
```python
- id: BigAutoField (PK)
- wallet: ForeignKey(CarteiraCliente, nullable) - Carteira à qual pertence
- user: OneToOneField(User) - Usuário Django
- telefone: CharField(20) - Telefone (legado)
- contato: JSONField - Informações de contato (novo)
- metadados: JSONField - Metadados adicionais
- criado_em: DateTimeField (auto)
- atualizado_em: DateTimeField (auto)
```

**Relacionamentos**:
- `wallet` → CarteiraCliente
- `user` → User
- `pedidos` → Pedido

**Propriedades**:
- `owner_carteira` - Retorna `wallet.owner` se existir

---

### 1.4. LigacaoMesh (MeshLink)

**Modelo**: `app_marketplace.models.LigacaoMesh`

**Campos**:
```python
- id: BigAutoField (PK)
- agente_a: ForeignKey(User) - Primeiro agente
- agente_b: ForeignKey(User) - Segundo agente
- tipo: CharField - "forte" | "fraca"
- ativo: BooleanField - Se a ligação está ativa
- config_financeira: JSONField - Configuração financeira
- metadados: JSONField - Metadados adicionais
- criado_em: DateTimeField (auto)
- atualizado_em: DateTimeField (auto)
- aceito_em: DateTimeField (nullable)
```

**Relacionamentos**:
- `agente_a` → User
- `agente_b` → User

**Validações**:
- `agente_a != agente_b`
- `config_financeira["venda_clientes_keeper"]["alpha_s"] + config_financeira["venda_clientes_keeper"]["alpha_k"] = 1.0`

**Estrutura `config_financeira`**:
```json
{
  "taxa_evora": 0.20,
  "venda_clientes_shopper": {
    "alpha_s": 1.0
  },
  "venda_clientes_keeper": {
    "alpha_s": 0.60,
    "alpha_k": 0.40
  }
}
```

---

### 1.5. Produto (Product)

**Modelo**: `app_marketplace.models.Produto`

**Campos principais**:
```python
- id: BigAutoField (PK)
- criado_por: ForeignKey(User, nullable) - Shopper que criou
- nome: CharField(100)
- preco: DecimalField - Preço base (P_base)
- # ... outros campos
```

**Relacionamentos**:
- `criado_por` → User (Shopper)

---

### 1.6. Oferta (Offer)

**Modelo**: `app_marketplace.models.Oferta`

**Campos principais**:
```python
- id: BigAutoField (PK)
- produto: ForeignKey(Produto)
- agente_ofertante: ForeignKey(Agente) - Shopper que oferece
- preco_oferta: DecimalField - Preço final (P_final)
- # ... outros campos
```

**Nota**: Pode ter `targeting` para carteira específica (futuro)

---

### 1.7. Pedido (Order)

**Modelo**: `app_marketplace.models.Pedido`

**Campos principais**:
```python
- id: BigAutoField (PK)
- cliente: ForeignKey(Cliente)
- carteira_cliente: ForeignKey(CarteiraCliente, nullable)
- tipo_cliente: CharField - "do_shopper" | "do_keeper"
- shopper: ForeignKey(User, nullable) - Quem vendeu
- keeper: ForeignKey(User, nullable) - Quem entrega
- preco_base: DecimalField - P_base
- preco_final: DecimalField - P_final
- valor_total: DecimalField - Total do pedido
- status: CharField - Status do pedido
- # ... outros campos
```

**Métodos**:
- `determinar_tipo_cliente(shopper_user)` - Determina tipo e keeper
- `atualizar_precos()` - Atualiza preco_base e preco_final

**Regras de Negócio**:
- Se `tipo_cliente == "do_shopper"`: `keeper = null`
- Se `tipo_cliente == "do_keeper"`: `keeper = carteira_cliente.owner`
- **OBRIGATÓRIO**: LigacaoMesh ativa para vender para cliente do Keeper

---

### 1.8. LiquidacaoFinanceira (Settlement)

**Modelo**: `app_marketplace.models.LiquidacaoFinanceira`

**Campos**:
```python
- id: BigAutoField (PK)
- pedido: OneToOneField(Pedido) - Pedido liquidado
- valor_margem: DecimalField - M (margem total)
- valor_evora: DecimalField - M_E
- valor_shopper: DecimalField - Receita do Shopper
- valor_keeper: DecimalField - Receita do Keeper
- detalhes: JSONField - Detalhes do cálculo
- status: CharField - "pendente" | "calculada" | "liquidada" | "cancelada"
- criado_em: DateTimeField (auto)
- atualizado_em: DateTimeField (auto)
- liquidado_em: DateTimeField (nullable)
```

**Relacionamentos**:
- `pedido` → Pedido (OneToOne)

---

## 2. LÓGICA DE DECISÃO DOS PAPÉIS

### 2.1. Algoritmo de Decisão

```python
def determinar_tipo_cliente(pedido, shopper_user):
    """
    Determina tipo_cliente e keeper baseado na carteira e mesh.
    """
    # 1. Obter carteira do cliente
    carteira = pedido.cliente.wallet or pedido.carteira_cliente
    if not carteira:
        # Sem carteira = cliente do shopper
        return {
            "tipo_cliente": "do_shopper",
            "keeper": None
        }
    
    # 2. Verificar owner da carteira
    wallet_owner = carteira.owner
    
    if wallet_owner == shopper_user:
        # Cliente do Shopper
        return {
            "tipo_cliente": "do_shopper",
            "keeper": None
        }
    else:
        # Cliente do Keeper - VERIFICAR MESH
        mesh = LigacaoMesh.objects.filter(
            ativo=True
        ).filter(
            (Q(agente_a=shopper_user, agente_b=wallet_owner)) |
            (Q(agente_a=wallet_owner, agente_b=shopper_user))
        ).first()
        
        if not mesh:
            raise ValidationError(
                "LigacaoMesh ativa obrigatória para vender para cliente do Keeper"
            )
        
        return {
            "tipo_cliente": "do_keeper",
            "keeper": wallet_owner
        }
```

### 2.2. Validações Obrigatórias

1. **Para vender para cliente do Keeper**:
   - ✅ Deve existir `LigacaoMesh` ativa
   - ✅ `LigacaoMesh.ativo == True`
   - ✅ `LigacaoMesh` deve conectar `shopper` e `keeper`

2. **Para vender para cliente do Shopper**:
   - ✅ Não requer mesh
   - ✅ `keeper = null`

---

## 3. LÓGICA DE CÁLCULO FINANCEIRO

### 3.1. Algoritmo Completo

```python
def calcular_liquidacao(pedido: Pedido, mesh_link: LigacaoMesh):
    """
    Calcula liquidação financeira conforme modelo matemático oficial.
    """
    # 1. Obter preços
    P_base = pedido.preco_base
    P_final = pedido.preco_final
    M = P_final - P_base  # Margem bruta
    
    # 2. Obter configuração
    conf = mesh_link.config_financeira
    taxa_evora = conf["taxa_evora"]
    
    # 3. Calcular valores da Évora
    M_evora = taxa_evora * M
    M_liquida = M - M_evora
    
    # 4. Determinar valores por tipo
    if pedido.tipo_cliente == "do_shopper":
        alpha_s = conf["venda_clientes_shopper"]["alpha_s"]
        valor_shopper = alpha_s * M_liquida
        valor_keeper = 0.0
    elif pedido.tipo_cliente == "do_keeper":
        alpha_s = conf["venda_clientes_keeper"]["alpha_s"]
        alpha_k = conf["venda_clientes_keeper"]["alpha_k"]
        valor_shopper = alpha_s * M_liquida
        valor_keeper = alpha_k * M_liquida
    
    return {
        "valor_margem": M,
        "valor_evora": M_evora,
        "valor_shopper": valor_shopper,
        "valor_keeper": valor_keeper,
    }
```

### 3.2. Validações do Cálculo

1. **Soma dos alphas**:
   ```python
   assert alpha_s(B) + alpha_k(B) == 1.0
   ```

2. **Soma total**:
   ```python
   assert valor_shopper + valor_keeper + valor_evora == M
   ```

---

## 4. FLUXO DE CRIAÇÃO DE PEDIDO

### 4.1. Passo a Passo

```python
# 1. Criar pedido base
pedido = Pedido.objects.create(
    cliente=cliente,
    shopper=shopper_user,
    # ... outros campos
)

# 2. Determinar carteira
if cliente.wallet:
    pedido.carteira_cliente = cliente.wallet

# 3. Determinar tipo_cliente e keeper
pedido.determinar_tipo_cliente(shopper_user)

# 4. Atualizar preços
pedido.atualizar_precos()

# 5. Salvar
pedido.save()

# 6. Processar liquidação (quando pedido for pago)
from app_marketplace.services_financeiro import servico_liquidacao
liquidacao = servico_liquidacao.processar_liquidacao_pedido(pedido)
```

### 4.2. Tratamento de Erros

```python
try:
    pedido.determinar_tipo_cliente(shopper_user)
except ValidationError as e:
    # Sem mesh ativa para cliente do Keeper
    return {
        "erro": str(e),
        "sugestao": "Estabeleça uma LigacaoMesh com o Keeper primeiro"
    }
```

---

## 5. ESTRUTURA JSON - LigacaoMesh.config_financeira

### 5.1. Formato Padrão

```json
{
  "taxa_evora": 0.20,
  "venda_clientes_shopper": {
    "alpha_s": 1.0
  },
  "venda_clientes_keeper": {
    "alpha_s": 0.60,
    "alpha_k": 0.40
  }
}
```

### 5.2. Validação

```python
def validar_config_financeira(config):
    """
    Valida estrutura da config_financeira.
    """
    # 1. Verificar campos obrigatórios
    assert "taxa_evora" in config
    assert "venda_clientes_shopper" in config
    assert "venda_clientes_keeper" in config
    
    # 2. Validar taxa_evora
    assert 0 <= config["taxa_evora"] <= 1
    
    # 3. Validar alphas do shopper
    assert "alpha_s" in config["venda_clientes_shopper"]
    assert config["venda_clientes_shopper"]["alpha_s"] == 1.0
    
    # 4. Validar alphas do keeper
    keeper_config = config["venda_clientes_keeper"]
    assert "alpha_s" in keeper_config
    assert "alpha_k" in keeper_config
    assert abs(keeper_config["alpha_s"] + keeper_config["alpha_k"] - 1.0) < 0.01
```

---

## 6. ENDPOINTS RECOMENDADOS

### 6.1. CarteiraCliente

```
GET    /api/carteiras/              - Listar carteiras
POST   /api/carteiras/              - Criar carteira
GET    /api/carteiras/{id}/         - Detalhes da carteira
PUT    /api/carteiras/{id}/         - Atualizar carteira
DELETE /api/carteiras/{id}/         - Deletar carteira
GET    /api/carteiras/{id}/clientes/ - Clientes da carteira
```

### 6.2. LigacaoMesh

```
GET    /api/mesh/                   - Listar ligações mesh
POST   /api/mesh/                   - Criar ligação mesh
GET    /api/mesh/{id}/              - Detalhes da ligação
PUT    /api/mesh/{id}/              - Atualizar ligação
DELETE /api/mesh/{id}/              - Deletar ligação
POST   /api/mesh/{id}/aceitar/      - Aceitar ligação
```

### 6.3. Pedido

```
POST   /api/pedidos/                - Criar pedido
GET    /api/pedidos/{id}/           - Detalhes do pedido
POST   /api/pedidos/{id}/liquidar/   - Processar liquidação
GET    /api/pedidos/{id}/liquidacao/ - Ver liquidação
```

---

## 7. TESTES RECOMENDADOS

### 7.1. Teste de Decisão de Papéis

```python
def test_determinar_tipo_cliente_shopper():
    """Testa venda para cliente do Shopper"""
    # Criar carteira do shopper
    # Criar cliente na carteira
    # Criar pedido
    # Verificar: tipo_cliente == "do_shopper", keeper == None

def test_determinar_tipo_cliente_keeper():
    """Testa venda para cliente do Keeper"""
    # Criar mesh entre shopper e keeper
    # Criar carteira do keeper
    # Criar cliente na carteira
    # Criar pedido
    # Verificar: tipo_cliente == "do_keeper", keeper == wallet.owner

def test_determinar_tipo_cliente_sem_mesh():
    """Testa erro quando não há mesh"""
    # Criar carteira do keeper (sem mesh)
    # Criar cliente na carteira
    # Tentar criar pedido
    # Verificar: ValidationError levantado
```

### 7.2. Teste de Cálculo Financeiro

```python
def test_calculo_liquidacao_shopper():
    """Testa cálculo para cliente do Shopper"""
    # P_base = 100, P_final = 180
    # M = 80, M_E = 16 (20%), M* = 64
    # Verificar: valor_shopper = 64, valor_keeper = 0

def test_calculo_liquidacao_keeper():
    """Testa cálculo para cliente do Keeper"""
    # P_base = 100, P_final = 180
    # M = 80, M_E = 16 (20%), M* = 64
    # alpha_s = 0.60, alpha_k = 0.40
    # Verificar: valor_shopper = 38.40, valor_keeper = 25.60
```

---

## 8. MIGRAÇÃO DE DADOS

### 8.1. Script de Migração

Ver: `scripts/migrar_dados_reestruturacao.py`

### 8.2. Passos

1. Criar CarteiraCliente para cada Agente/User
2. Migrar Clientes para CarteiraCliente
3. Migrar TrustlineKeeper para LigacaoMesh
4. Atualizar Pedidos com novos campos

---

## 9. SEGURANÇA E VALIDAÇÕES

### 9.1. Validações Obrigatórias

1. **LigacaoMesh**: Não pode ter mesh consigo mesmo
2. **Config Financeira**: Alphas devem somar 1.0
3. **Pedido**: Não pode vender para cliente do Keeper sem mesh
4. **CarteiraCliente**: Owner deve ser User válido

### 9.2. Permissões

- Apenas owner pode modificar sua CarteiraCliente
- Apenas agentes envolvidos podem modificar LigacaoMesh
- Apenas shopper pode criar pedidos

---

## 10. PERFORMANCE

### 10.1. Índices Recomendados

```python
# CarteiraCliente
indexes = [
    models.Index(fields=['owner']),
]

# LigacaoMesh
indexes = [
    models.Index(fields=['agente_a', 'agente_b']),
    models.Index(fields=['ativo']),
]

# Pedido
indexes = [
    models.Index(fields=['tipo_cliente']),
    models.Index(fields=['shopper', 'keeper']),
    models.Index(fields=['carteira_cliente']),
]
```

---

**Versão**: 1.0 - Documento Técnico Completo  
**Data**: 2025-01-27  
**Status**: ✅ Especificação Oficial

