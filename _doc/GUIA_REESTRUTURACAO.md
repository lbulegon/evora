# 📚 GUIA COMPLETO - REESTRUTURAÇÃO OFICIAL

## ✅ O QUE FOI IMPLEMENTADO

### 1. Modelos Criados ✅

- **CarteiraCliente** - Carteira de clientes por agente
- **LigacaoMesh** - Ligações mesh (forte/fraca) entre agentes
- **LiquidacaoFinanceira** - Liquidação financeira de pedidos

### 2. Modelos Adaptados ✅

- **Cliente** - Adicionado `wallet`, `contato`, `metadados`
- **Pedido** - Adicionado `carteira_cliente`, `tipo_cliente`, `shopper`, `keeper`, `preco_base`, `preco_final`
- **Produto** - Adicionado `criado_por`

### 3. Serviços ✅

- **ServicoLiquidacaoFinanceira** - Algoritmo oficial de cálculo financeiro

### 4. Migrations ✅

- Migration `0018_reestruturacao_oficial.py` criada

### 5. Admin Django ✅

- Todos os novos modelos registrados
- Admin atualizado para Cliente e Pedido

### 6. Script de Migração ✅

- `scripts/migrar_dados_reestruturacao.py` criado

---

## 🚀 COMO APLICAR A REESTRUTURAÇÃO

### Passo 1: Aplicar Migrations

```bash
# Aplicar a migration
python manage.py migrate app_marketplace

# Verificar se aplicou corretamente
python manage.py showmigrations app_marketplace
```

### Passo 2: Executar Script de Migração de Dados

```bash
# Opção 1: Via shell do Django
python manage.py shell < scripts/migrar_dados_reestruturacao.py

# Opção 2: Executar diretamente
python scripts/migrar_dados_reestruturacao.py
```

O script irá:
1. ✅ Criar CarteiraCliente para cada Agente/User
2. ✅ Migrar Clientes para CarteiraCliente
3. ✅ Migrar TrustlineKeeper para LigacaoMesh
4. ✅ Atualizar Pedidos com novos campos

### Passo 3: Verificar no Admin

Acesse `http://localhost:8000/admin/` e verifique:
- ✅ Carteiras de Clientes
- ✅ Ligações Mesh
- ✅ Liquidações Financeiras
- ✅ Clientes com wallet
- ✅ Pedidos com tipo_cliente

---

## 📊 ESTRUTURA DE DADOS

### CarteiraCliente

```python
carteira = CarteiraCliente.objects.create(
    owner=user,
    nome_exibicao="Minha Carteira",
    metadados={"tipo": "agente_kmn"}
)
```

### LigacaoMesh

```python
mesh = LigacaoMesh.objects.create(
    agente_a=user_a,
    agente_b=user_b,
    tipo=LigacaoMesh.TipoMesh.FORTE,  # ou FRACA
    config_financeira={
        "taxa_evora": 0.10,
        "venda_clientes_shopper": {"alpha_s": 1.0},
        "venda_clientes_keeper": {"alpha_s": 0.60, "alpha_k": 0.40}
    }
)
```

### LiquidacaoFinanceira

```python
from app_marketplace.services_financeiro import servico_liquidacao

# Processar liquidação de um pedido
liquidacao = servico_liquidacao.processar_liquidacao_pedido(pedido)
```

---

## 🧮 USO DO SERVIÇO DE LIQUIDAÇÃO

### Exemplo Básico

```python
from app_marketplace.services_financeiro import servico_liquidacao
from app_marketplace.models import Pedido, LigacaoMesh

# Obter pedido
pedido = Pedido.objects.get(id=1)

# Processar liquidação (busca mesh_link automaticamente)
liquidacao = servico_liquidacao.processar_liquidacao_pedido(pedido)

# Valores calculados
print(f"Margem: R$ {liquidacao.valor_margem}")
print(f"Évora: R$ {liquidacao.valor_evora}")
print(f"Shopper: R$ {liquidacao.valor_shopper}")
print(f"Keeper: R$ {liquidacao.valor_keeper}")
```

### Exemplo com Mesh Link Específico

```python
mesh_link = LigacaoMesh.objects.get(agente_a=shopper, agente_b=keeper)
liquidacao = servico_liquidacao.criar_liquidacao(pedido, mesh_link)
```

---

## 🔄 FLUXO DE PEDIDO

### 1. Criar Pedido

```python
pedido = Pedido.objects.create(
    cliente=cliente,
    shopper=shopper_user,
    # ... outros campos
)

# Determinar tipo_cliente automaticamente
pedido.determinar_tipo_cliente(shopper_user)

# Atualizar preços
pedido.atualizar_precos()
pedido.save()
```

### 2. Processar Liquidação

```python
# Após pedido ser pago/confirmado
liquidacao = servico_liquidacao.processar_liquidacao_pedido(pedido)
```

---

## ⚠️ PONTOS IMPORTANTES

1. **Compatibilidade**: Modelos antigos mantidos para compatibilidade
2. **Migração**: Execute o script de migração ANTES de usar em produção
3. **Validação**: LigacaoMesh valida automaticamente soma de alphas = 1.0
4. **Preços**: `preco_base` e `preco_final` devem ser preenchidos para cálculo correto

---

## 📝 PRÓXIMOS PASSOS

- [ ] Atualizar APIs REST
- [ ] Atualizar serializers
- [ ] Integrar no fluxo de criação de pedidos
- [ ] Criar views para gerenciar CarteiraCliente
- [ ] Criar views para gerenciar LigacaoMesh
- [ ] Documentar APIs

---

**Status**: ✅ Reestruturação Base Completa  
**Data**: 2025-01-27  
**Versão**: 1.0

