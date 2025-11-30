# 📊 MODELO MATEMÁTICO FINAL DOS PERCENTUAIS

## 1. VARIÁVEIS BÁSICAS DA VENDA

### Definições

```
P_base = preço base / custo de aquisição do produto
P_final = preço pago pelo cliente
```

### Margem Bruta

```
M = P_final - P_base
```

### Taxa da ÉVORA

```
τ_E = percentual da margem destinado à ÉVORA (plataforma)
0 ≤ τ_E ≤ 1
```

### Parte da Évora

```
M_E = τ_E · M
```

### Margem Líquida (para agentes)

```
M* = M - M_E = (1 - τ_E) · M
```

---

## 2. DOIS CENÁRIOS DE VENDA

### 2.1. Cenário A – Venda para Clientes do Shopper

**Fluxo**:
- Shopper cria a vitrine
- Shopper recebe o pedido
- Shopper entrega para seus próprios clientes
- **Keeper não participa**

**Definição**:

```
α_S(A) = percentual da margem líquida que vai para o Shopper
         (normalmente α_S(A) = 1, isto é, 100% da parte dos agentes)
```

**Cálculo**:

```
Receita_Shopper(A) = α_S(A) · M*
Receita_Keeper(A) = 0
```

**Exemplo**:
- Se `α_S(A) = 1.0` (100%)
- `Receita_Shopper = M*`
- `Receita_Keeper = 0`

---

### 2.2. Cenário B – Venda para Clientes do Keeper

**Fluxo**:
- Shopper cria a vitrine
- Shopper vende ativamente
- Shopper gera o pedido
- **Keeper recebe os pedidos**
- **Keeper faz a entrega física** para seus clientes

**Definição**:

```
α_S(B) = percentual da margem líquida para o Shopper (vendedor ativo)
α_K(B) = percentual da margem líquida para o Keeper (vendedor passivo + logística)
```

**Regra Fundamental**:

```
α_S(B) + α_K(B) = 1
```

**Cálculo**:

```
Receita_Shopper(B) = α_S(B) · M*
Receita_Keeper(B) = α_K(B) · M*
```

**Exemplo Padrão**:
- `α_S(B) = 0.60` (60% para Shopper - vendedor ativo)
- `α_K(B) = 0.40` (40% para Keeper - vendedor passivo + logística)

---

## 3. FUNÇÃO GERAL POR VENDA

### Indicador

```
I_K = 1  se a venda é para cliente do Keeper
I_K = 0  se a venda é para cliente do Shopper
```

### Receita do Shopper

```
Receita_Shopper = {
    α_S(A) · M*,    se I_K = 0
    α_S(B) · M*,    se I_K = 1
}
```

### Receita do Keeper

```
Receita_Keeper = {
    0,              se I_K = 0
    α_K(B) · M*,    se I_K = 1
}
```

### Receita da Évora (sempre)

```
Receita_Évora = M_E = τ_E · M
```

---

## 4. EXEMPLO NUMÉRICO COMPLETO

### Dados de Entrada

```
P_base = R$ 100,00
P_final = R$ 180,00
τ_E = 0.20 (20% da margem)
```

### Cálculo da Margem

```
M = 180 - 100 = R$ 80,00
M_E = 0.20 · 80 = R$ 16,00
M* = 80 - 16 = R$ 64,00
```

### Caso 1: Cliente do Shopper (I_K = 0)

**Configuração**:
```
α_S(A) = 1.0
```

**Resultado**:
```
Receita_Shopper = 1.0 · 64 = R$ 64,00
Receita_Keeper = R$ 0,00
Receita_Évora = R$ 16,00
```

**Total**: R$ 80,00 (confere com M)

---

### Caso 2: Cliente do Keeper (I_K = 1)

**Configuração**:
```
α_S(B) = 0.60 (60%)
α_K(B) = 0.40 (40%)
```

**Resultado**:
```
Receita_Shopper = 0.60 · 64 = R$ 38,40
Receita_Keeper = 0.40 · 64 = R$ 25,60
Receita_Évora = R$ 16,00
```

**Total**: R$ 80,00 (confere com M)

---

## 5. FÓRMULAS CONSOLIDADAS

### Para Qualquer Venda

```
M = P_final - P_base
M_E = τ_E · M
M* = (1 - τ_E) · M
```

### Se I_K = 0 (Cliente do Shopper)

```
Receita_Shopper = α_S(A) · M*
Receita_Keeper = 0
```

### Se I_K = 1 (Cliente do Keeper)

```
Receita_Shopper = α_S(B) · M*
Receita_Keeper = α_K(B) · M*
```

**Sempre**:
```
Receita_Évora = M_E = τ_E · M
```

---

## 6. VALIDAÇÕES

### Validação 1: Soma dos Percentuais

```
α_S(B) + α_K(B) = 1
```

**Exemplo válido**:
- `α_S(B) = 0.60`, `α_K(B) = 0.40` → 0.60 + 0.40 = 1.0 ✅

**Exemplo inválido**:
- `α_S(B) = 0.70`, `α_K(B) = 0.40` → 0.70 + 0.40 = 1.1 ❌

### Validação 2: Soma Total das Receitas

```
Receita_Shopper + Receita_Keeper + Receita_Évora = M
```

**Sempre deve ser verdadeiro** para qualquer cenário.

---

## 7. CONFIGURAÇÃO PADRÃO RECOMENDADA

### Taxa da Évora

```
τ_E = 0.10 a 0.20 (10% a 20% da margem)
```

### Venda para Clientes do Shopper

```
α_S(A) = 1.0 (100% da margem líquida)
```

### Venda para Clientes do Keeper

```
α_S(B) = 0.60 (60% - vendedor ativo)
α_K(B) = 0.40 (40% - vendedor passivo + logística)
```

**Justificativa**:
- Shopper faz trabalho ativo (vitrine, negociação, venda)
- Keeper faz trabalho passivo (empresta carteira) + logística (entrega)
- Divisão 60/40 reflete essa diferença de esforço

---

## 8. IMPLEMENTAÇÃO NO CÓDIGO

### Estrutura JSON (LigacaoMesh.config_financeira)

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

### Algoritmo (Python)

```python
def calcular_liquidacao(pedido, mesh_link):
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

**Versão**: 1.0 - Modelo Final  
**Data**: 2025-01-27  
**Status**: ✅ Oficial e Validado

