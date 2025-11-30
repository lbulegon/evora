# 🔄 REESTRUTURAÇÃO COMPLETA - VitrineZap/Évora/KMN

## 📋 ANÁLISE DO PROMPT OFICIAL

Este documento define a reestruturação completa do sistema baseada no **PROMPT OFICIAL** fornecido.

---

## 🎯 CONCEITOS FUNDAMENTAIS

### 1. Pessoa Évora
- Usuário humano do sistema
- Pode assumir dois papéis contextuais:
  - **Shopper** (vendedor ativo)
  - **Keeper** (vendedor passivo + logística)

### 2. Papéis Oficiais

#### 2.1. Shopper (Vendedor Ativo)
- Monta vitrines
- Fotografa produtos
- Ativa campanhas
- Compartilha ofertas
- Negocia
- Gera pedidos
- Recebe pagamentos
- **Entrega para seus próprios clientes**

#### 2.2. Keeper (Vendedor Passivo + Logística)
- Empresta carteira de clientes ao Shopper
- **NÃO vende ativamente**
- **NÃO cria vitrine**
- **NÃO negocia**
- Recebe pedidos que o Shopper gera para seus clientes
- Faz entrega local para sua própria carteira
- **Ganha dinheiro passivamente**

---

## 🔗 LIGAÇÕES MESH (KMN)

### 3.1. Mesh Forte (Strong Link)
- Totalmente recíproca
- Ambos podem atuar como Shopper e Keeper
- Papéis trocam conforme o fluxo
- Carteiras parcialmente compartilhadas
- Alta confiança
- Rede de alta densidade

**Regra**: Em Mesh Forte, você é Shopper para seus clientes e Keeper para os clientes do outro.

### 3.2. Mesh Fraca (Weak Link)
- Assimétrica
- Cada agente escolhe seu papel (somente Shopper OU somente Keeper)
- Sem reciprocidade obrigatória
- Ideal para relações iniciais
- Exige menos confiança

---

## 💰 MODELO FINANCEIRO OFICIAL

### Fórmulas Base

```
P_base = preço base (custo)
P_final = valor pago pelo cliente
M = P_final - P_base (Margem)

τ_E = % da margem da ÉVORA
M_E = τ_E · M (Évora recebe)
M* = (1 - τ_E) · M (Margem líquida dos agentes)
```

### 5.1. Venda para Clientes do Shopper

```
α_S(A) = 1.0
Receita_Shopper = M*
Receita_Keeper = 0
```

### 5.2. Venda para Clientes do Keeper

```
α_S(B) + α_K(B) = 1
Receita_Shopper = α_S(B) · M*
Receita_Keeper = α_K(B) · M*
```

---

## 📊 MODELO DE DADOS OFICIAL

### Entidades Principais

1. **User** (Usuário)
   - id, nome, email, atributos gerais

2. **CarteiraCliente** (CustomerWallet)
   - id, owner (FK → User), nome_exibicao, metadados

3. **Cliente** (Customer)
   - id, wallet (FK → CarteiraCliente), contato, metadados (JSON)

4. **LigacaoMesh** (MeshLink)
   - id, agente_a (User), agente_b (User)
   - tipo: "forte" | "fraca"
   - ativo: boolean
   - config_financeira (JSON)

5. **Produto** (Product)
   - id, criado_por (User/Shopper), dados_base, preco_base

6. **Oferta** (Offer)
   - id, produto, shopper, preco_final
   - targeting opcional (wallet específica)

7. **Pedido** (Order)
   - id, oferta, cliente, carteira_cliente
   - tipo_cliente: "do_shopper" | "do_keeper"
   - shopper (FK → User)
   - keeper (FK → User ou null)
   - preco_base, preco_final, status

8. **LiquidacaoFinanceira** (Settlement)
   - id, pedido
   - valor_margem, valor_evora, valor_shopper, valor_keeper
   - detalhes (JSON)

---

## 🔄 LÓGICA DE DECISÃO

### Regra de Papéis por Venda

```
Se cliente pertence à carteira do Shopper:
  tipo_cliente = "do_shopper"
  keeper = null

Se cliente pertence à carteira do Keeper:
  tipo_cliente = "do_keeper"
  keeper = wallet.owner
```

---

## 🧮 ALGORITMO DE CÁLCULO FINANCEIRO

```python
def calcular_liquidacao(pedido: Order, mesh_link: MeshLink):
    P_base = pedido.preco_base
    P_final = pedido.preco_final
    M = P_final - P_base

    conf = mesh_link.config_financeira
    taxa_evora = conf["taxa_evora"]

    M_evora = taxa_evora * M
    M_liquida = M - M_evora

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

---

## 📝 PLANO DE IMPLEMENTAÇÃO

### Fase 1: Análise e Mapeamento
- [x] Documentar prompt oficial
- [ ] Mapear modelos atuais vs. novos
- [ ] Identificar diferenças e gaps

### Fase 2: Modelos de Dados
- [ ] Criar/adaptar CarteiraCliente
- [ ] Reestruturar LigacaoMesh (tipos forte/fraca)
- [ ] Adaptar Cliente para usar CarteiraCliente
- [ ] Reestruturar Pedido com tipo_cliente
- [ ] Criar LiquidacaoFinanceira

### Fase 3: Lógica de Negócio
- [ ] Implementar algoritmo de cálculo financeiro
- [ ] Implementar lógica de decisão de papéis
- [ ] Atualizar fluxos de venda
- [ ] Configurar percentuais padrão

### Fase 4: Migrations e Dados
- [ ] Criar migrations
- [ ] Script de migração de dados existentes
- [ ] Validação de integridade

### Fase 5: APIs e Endpoints
- [ ] Atualizar serializers
- [ ] Atualizar views/viewsets
- [ ] Atualizar URLs
- [ ] Documentação de APIs

### Fase 6: Admin e Interface
- [ ] Atualizar admin Django
- [ ] Ajustar templates se necessário
- [ ] Documentação de uso

---

## ⚠️ PONTOS DE ATENÇÃO

1. **Compatibilidade**: Manter compatibilidade com dados existentes
2. **Migração**: Criar script de migração de dados
3. **Validação**: Garantir integridade referencial
4. **Testes**: Testar todos os fluxos
5. **Documentação**: Atualizar toda documentação

---

**Status**: 🟡 Em Análise  
**Data Início**: 2025-01-27  
**Versão**: 1.0

