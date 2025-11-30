# 📘 DEFINIÇÃO OFICIAL DO KEEPER - VitrineZap/Évora/KMN

## ✅ O QUE É O KEEPER (DEFINIÇÃO DEFINITIVA)

### 🎯 Definição Completa

O **Keeper** é um **vendedor passivo** que:

1. **Empresta sua carteira de clientes** ao Shopper
2. **Recebe pedidos** que o Shopper gerar para os clientes da sua carteira
3. **Faz a entrega local** dos produtos para seus próprios clientes
4. **Ganha passivamente** quando o Shopper vende para seus clientes

### ❌ O QUE O KEEPER NÃO É

- ❌ **NÃO vende ativamente**
- ❌ **NÃO cria vitrine**
- ❌ **NÃO negocia**
- ❌ **NÃO faz curadoria**
- ❌ **NÃO precisa fazer prospecção**

---

## 🔄 COMO FUNCIONA NA PRÁTICA

### Cenário A: Venda para Clientes do Shopper

```
Shopper → Cria vitrine → Vende → Entrega para seus próprios clientes
```

**Participação do Keeper**: ❌ NENHUMA
- Keeper não participa
- Keeper não ganha nada
- Keeper não tem papel ativo

### Cenário B: Venda para Clientes do Keeper

```
Shopper → Cria vitrine → Vende → Gera pedidos
                ↓
         [Lista de pedidos]
                ↓
Keeper → Recebe pedidos → Entrega para seus próprios clientes
```

**Participação do Keeper**: ✅ TOTAL
- Keeper entra na jogada
- Keeper recebe os pedidos
- Keeper faz a entrega final
- Keeper dá suporte logístico
- Keeper representa fisicamente a ponta do Shopper
- **Keeper ganha** (divisão financeira)

---

## 💰 MODELO FINANCEIRO

### Venda para Clientes do Shopper

```
Receita_Shopper = 100% da margem líquida (M*)
Receita_Keeper = 0
Receita_Évora = τ_E · M
```

### Venda para Clientes do Keeper

```
Receita_Shopper = α_S(B) · M*  (vendedor ativo)
Receita_Keeper = α_K(B) · M*   (vendedor passivo + logística)
Receita_Évora = τ_E · M

Onde: α_S(B) + α_K(B) = 1
```

**Exemplo padrão**:
- `α_S(B) = 0.60` (60% para Shopper)
- `α_K(B) = 0.40` (40% para Keeper)

---

## 🕸️ PAPÉIS SÃO FLUÍDOS (MESH)

Na **Keeper Mesh Network (KMN)**, os papéis são contextuais:

- Em relação à **carteira A**, você pode ser **Keeper**
- Em relação à **carteira B**, você pode ser **Shopper**
- Tudo isso pode acontecer no mesmo dia

**Porque cada carteira define seu papel.**

Essa é a genialidade da Mesh.

---

## 🔐 REGRA FUNDAMENTAL

### Para Vender para Cliente do Keeper:

**É OBRIGATÓRIO** ter uma **LigacaoMesh ativa** entre:
- O Shopper (quem vende)
- O Keeper (dono da carteira)

**Sem LigacaoMesh = Não pode vender para cliente do Keeper**

---

## 📊 IMPLEMENTAÇÃO TÉCNICA

### Validação no Modelo Pedido

```python
def determinar_tipo_cliente(self, shopper_user):
    """
    Determina tipo_cliente baseado na carteira E na existência de LigacaoMesh.
    """
    wallet_owner = self.carteira_cliente.owner
    
    if wallet_owner == shopper_user:
        # Cliente do Shopper
        self.tipo_cliente = "do_shopper"
        self.keeper = None
    else:
        # Cliente do Keeper - VERIFICAR MESH
        mesh = LigacaoMesh.objects.filter(
            ativo=True,
            (Q(agente_a=shopper_user, agente_b=wallet_owner) |
             Q(agente_a=wallet_owner, agente_b=shopper_user))
        ).first()
        
        if mesh:
            self.tipo_cliente = "do_keeper"
            self.keeper = wallet_owner
        else:
            raise ValidationError("LigacaoMesh ativa obrigatória")
```

---

## 🎯 VALOR DO KEEPER NA REDE

O Keeper se torna uma espécie de:

- **"Franquia passiva"** ou
- **"Representante territorial passivo"**

Ele não precisa trabalhar vendendo, mas mesmo assim ganha sempre que:
- O Shopper usa a carteira dele
- E gera vendas para os seus clientes

---

## 📝 RESUMO EXECUTIVO

> **O Keeper é um agente que não cria vitrines e não vende ativamente. Ele disponibiliza sua carteira de clientes para o Shopper usar em suas ofertas.**
>
> **Em troca, o Keeper se responsabiliza por entregar os produtos comprados pelos clientes da sua carteira quando as vendas forem geradas pelo Shopper.**
>
> **O Shopper entrega apenas para os próprios clientes; o Keeper entrega para os clientes dele.**
>
> **Assim, o Keeper ganha como um "vendedor passivo + distribuidor local", enquanto o Shopper ganha como "curador + vendedor ativo".**

---

**Versão**: 1.0 - Definição Definitiva  
**Data**: 2025-01-27  
**Status**: ✅ Oficial

