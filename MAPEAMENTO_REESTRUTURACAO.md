# 🗺️ MAPEAMENTO: Estrutura Atual vs. Nova Estrutura

## 📊 COMPARAÇÃO DE MODELOS

### ✅ Modelos que JÁ EXISTEM (podem ser adaptados)

| Modelo Atual | Novo Modelo | Status | Ações Necessárias |
|--------------|-------------|--------|-------------------|
| `User` | `User` | ✅ OK | Nenhuma - já existe |
| `Produto` | `Product` | ✅ OK | Adicionar `criado_por` (FK → User) |
| `Oferta` | `Offer` | ⚠️ PARCIAL | Ajustar para usar `shopper` e `targeting` |
| `Pedido` | `Order` | ⚠️ PARCIAL | Adicionar `tipo_cliente`, `carteira_cliente` |
| `Agente` | - | ⚠️ REVISAR | Pode ser mantido como wrapper |
| `TrustlineKeeper` | `LigacaoMesh` | ❌ SUBSTITUIR | Reestruturar com tipos "forte"/"fraca" |

### ❌ Modelos que PRECISAM SER CRIADOS

| Novo Modelo | Descrição | Prioridade |
|-------------|-----------|------------|
| `CarteiraCliente` | Wallet de clientes por agente | 🔴 ALTA |
| `LiquidacaoFinanceira` | Liquidação financeira de pedidos | 🔴 ALTA |

### 🔄 Modelos que PRECISAM SER ADAPTADOS

| Modelo | Mudanças Necessárias |
|--------|---------------------|
| `Cliente` | Adicionar FK para `CarteiraCliente` |
| `PersonalShopper` | Manter, mas não é mais o foco principal |
| `Keeper` | Manter, mas não é mais o foco principal |

---

## 🔍 ANÁLISE DETALHADA

### 1. CarteiraCliente (CustomerWallet) - NOVO

**Campos necessários:**
```python
- id
- owner (FK → User)  # Agente dono da carteira
- nome_exibicao (CharField)
- metadados (JSONField)
- criado_em, atualizado_em
```

**Relacionamentos:**
- Um User pode ter múltiplas CarteiraCliente
- Cliente pertence a uma CarteiraCliente

### 2. Cliente - ADAPTAR

**Mudanças:**
```python
# ANTES
class Cliente(models.Model):
    user = OneToOneField(User)
    telefone = CharField()

# DEPOIS
class Cliente(models.Model):
    wallet = ForeignKey(CarteiraCliente)  # NOVO
    user = OneToOneField(User)  # MANTER (compatibilidade)
    contato = JSONField()  # Expandir metadados
    metadados = JSONField()  # NOVO
```

### 3. LigacaoMesh - SUBSTITUIR TrustlineKeeper

**Mudanças principais:**
```python
# ANTES: TrustlineKeeper
- agente_a, agente_b (FK → Agente)
- nivel_confianca
- perc_shopper, perc_keeper
- status

# DEPOIS: LigacaoMesh
- agente_a, agente_b (FK → User)  # Direto para User
- tipo: "forte" | "fraca"  # NOVO
- ativo: boolean
- config_financeira: JSONField  # NOVO (substitui perc_shopper/keeper)
```

**config_financeira JSON:**
```json
{
  "taxa_evora": 0.10,
  "venda_clientes_shopper": {
    "alpha_s": 1.0
  },
  "venda_clientes_keeper": {
    "alpha_s": 0.60,
    "alpha_k": 0.40
  }
}
```

### 4. Pedido - ADAPTAR

**Campos a adicionar:**
```python
- tipo_cliente: "do_shopper" | "do_keeper"  # NOVO
- carteira_cliente: FK → CarteiraCliente  # NOVO
- keeper: FK → User (nullable)  # JÁ EXISTE, ajustar lógica
```

**Lógica:**
- Se `tipo_cliente == "do_shopper"`: `keeper = null`
- Se `tipo_cliente == "do_keeper"`: `keeper = carteira_cliente.owner`

### 5. LiquidacaoFinanceira - NOVO

**Campos:**
```python
- id
- pedido: FK → Pedido (unique)
- valor_margem: DecimalField
- valor_evora: DecimalField
- valor_shopper: DecimalField
- valor_keeper: DecimalField
- detalhes: JSONField
- criado_em, atualizado_em
```

### 6. Produto - ADAPTAR

**Mudança:**
```python
# Adicionar
- criado_por: FK → User (nullable)  # Quem criou o produto
```

---

## 🔄 FLUXO DE MIGRAÇÃO

### Fase 1: Criar Novos Modelos
1. ✅ Criar `CarteiraCliente`
2. ✅ Criar `LiquidacaoFinanceira`
3. ✅ Criar `LigacaoMesh` (substituir TrustlineKeeper)

### Fase 2: Adaptar Modelos Existentes
1. ✅ Adicionar `wallet` ao `Cliente`
2. ✅ Adicionar `tipo_cliente` e `carteira_cliente` ao `Pedido`
3. ✅ Adicionar `criado_por` ao `Produto`
4. ✅ Ajustar `Oferta` para usar `shopper` e `targeting`

### Fase 3: Migração de Dados
1. ✅ Criar CarteiraCliente para cada Agente existente
2. ✅ Migrar Clientes para CarteiraCliente
3. ✅ Migrar TrustlineKeeper para LigacaoMesh
4. ✅ Atualizar Pedidos existentes

### Fase 4: Implementar Lógica
1. ✅ Algoritmo de cálculo financeiro
2. ✅ Lógica de decisão de papéis
3. ✅ Serviços de liquidação

### Fase 5: Atualizar APIs e Views
1. ✅ Serializers
2. ✅ ViewSets
3. ✅ Views Django
4. ✅ Admin

---

## ⚠️ COMPATIBILIDADE

### Manter Compatibilidade
- `PersonalShopper` e `Keeper` podem ser mantidos como wrappers
- `Agente` pode ser mantido como wrapper unificado
- Dados existentes devem ser migrados, não perdidos

### Breaking Changes
- `TrustlineKeeper` será substituído por `LigacaoMesh`
- Estrutura financeira muda completamente
- Lógica de cálculo muda

---

**Status**: 🟡 Em Análise  
**Próximo Passo**: Criar modelos base

