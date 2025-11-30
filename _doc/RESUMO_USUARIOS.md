# 👥 RESUMO EXECUTIVO - TIPOS DE USUÁRIOS

## 🎯 Tipos de Usuários no ÉVORA

```
┌─────────────────────────────────────────────────────────────┐
│                    USER (Django Auth)                        │
│              (Base para todos os perfis)                     │
└───────┬───────────────┬───────────────┬─────────────────────┘
        │               │               │
   ┌────▼────┐     ┌────▼──────┐  ┌───▼──────┐
   │ Cliente │     │  Shopper  │  │ Keeper  │
   └─────────┘     └─────┬──────┘  └────┬────┘
                        │              │
                        └──────┬───────┘
                               │
                          ┌────▼──────┐
                          │  Agente   │
                          │   KMN     │
                          │ (Unified) │
                          └───────────┘
```

---

## 📊 QUADRO COMPARATIVO RÁPIDO

| Característica | Cliente | Shopper | Keeper | Agente KMN |
|---------------|---------|---------|--------|------------|
| **Papel Principal** | Consumidor | Vendedor | Guardador | Ambos + Rede |
| **Dashboard** | ❌ | ✅ | ✅ | ✅ |
| **Grupos WhatsApp** | 👤 Participa | 👑 Cria | 👑 Cria | 👑 Cria |
| **Produtos** | 👀 Vê | ✏️ Cria | ❌ | ✏️ Cria |
| **Pacotes** | 📦 Cria | 📦 Cria | 📦 Recebe | 📦 Recebe |
| **Rede KMN** | ❌ | ❌ | ❌ | ✅ |
| **Isolamento** | Próprios dados | Master isolado | Master isolado | Master isolado |

---

## 1️⃣ CLIENTE 👤

**O que faz:**
- ✅ Compra produtos de Personal Shoppers
- ✅ Segue Personal Shoppers
- ✅ Cria pacotes para guarda
- ✅ Acompanha pedidos e pacotes

**O que NÃO faz:**
- ❌ Dashboard administrativo
- ❌ Criar produtos
- ❌ Gerenciar grupos WhatsApp

**Campos principais:**
- `telefone` - Contato
- Relacionamento com `PersonalShopper` via `RelacionamentoClienteShopper`

---

## 2️⃣ PERSONAL SHOPPER 🛍️

**O que faz:**
- ✅ Cria e gerencia grupos WhatsApp
- ✅ Posta produtos nos grupos
- ✅ Recebe pedidos de clientes
- ✅ Cria pacotes para envio
- ✅ Vê analytics de vendas

**O que NÃO faz:**
- ❌ Ver dados de outros shoppers
- ❌ Acessar grupos de outros usuários

**Campos principais:**
- `nome`, `bio` - Identificação
- `facebook`, `instagram`, etc. - Redes sociais
- `empresa` - Empresa vinculada
- `ativo` - Status

**Isolamento:** ✅ Master isolado (vê apenas seus dados)

---

## 3️⃣ KEEPER 📦

**O que faz:**
- ✅ Recebe pacotes para guarda
- ✅ Gerencia localização e capacidade
- ✅ Calcula taxas de guarda
- ✅ Cria grupos WhatsApp para comunicação
- ✅ Atualiza status de pacotes

**O que NÃO faz:**
- ❌ Criar produtos
- ❌ Ver dados de outros keepers

**Campos principais:**
- `apelido_local` - Nome do ponto
- `rua`, `cidade`, `estado`, `cep` - Endereço completo
- `capacidade_itens` - Capacidade máxima
- `taxa_guarda_dia` - Taxa por dia
- `taxa_motoboy` - Taxa de envio
- `aceita_retirada`, `aceita_envio` - Opções

**Isolamento:** ✅ Master isolado (vê apenas seus dados)

---

## 4️⃣ AGENTE KMN 🌐

**O que faz:**
- ✅ Atua como Shopper E/OU Keeper
- ✅ Participa da rede KMN
- ✅ Estabelece trustlines
- ✅ Cria ofertas com markup
- ✅ Gerencia estoque
- ✅ Recebe comissões

**O que NÃO faz:**
- ❌ Acessar dados sem trustline

**Campos principais:**
- `personal_shopper` - Vinculado a Shopper (opcional)
- `keeper` - Vinculado a Keeper (opcional)
- `score_keeper`, `score_shopper` - Scores (0-10)
- `ativo_como_keeper`, `ativo_como_shopper` - Status por papel
- `verificado_kmn` - Verificação da rede

**Propriedades especiais:**
- `dual_role_score` - Score combinado
- `is_dual_role` - Atua como ambos

**Isolamento:** ✅ Master isolado + acesso via trustlines

---

## 🔗 RELACIONAMENTOS ENTRE USUÁRIOS

```
Cliente ──[segue]──> Personal Shopper
   │                    │
   │                    │
   └──[pedido]──────────┘
         │
         │
         ▼
      Pacote ──[guarda]──> Keeper
         │
         │
         ▼
    Entrega
```

```
Cliente (Márcia) ──[relação]──> Agente (Márcia/Keeper)
                                      │
                                      │ [trustline]
                                      ▼
                              Agente (Júnior/Shopper)
                                      │
                                      │ [oferta]
                                      ▼
                              Cliente vê produto
                                      │
                                      │ [pedido]
                                      ▼
                              Venda Cooperada
                                      │
                                      │ [comissões]
                                      ▼
                              Ambos recebem
```

---

## 🔐 VERIFICAÇÕES RÁPIDAS

```python
# Verificar tipo de usuário
user.is_cliente   # True/False
user.is_shopper   # True/False
user.is_keeper    # True/False
user.is_agente    # True/False

# Acessar perfis
user.cliente           # Cliente
user.personalshopper   # PersonalShopper
user.keeper            # Keeper
user.agente            # Agente

# Verificar dual role
if user.is_agente:
    agente = user.agente
    if agente.is_dual_role:
        print("Atua como Shopper E Keeper")
```

---

## 📈 MÉTRICAS POR TIPO

### Cliente
- Total de pedidos
- Valor gasto
- Shoppers seguidos

### Shopper
- Total de clientes
- Total de vendas
- Receita
- Grupos ativos

### Keeper
- Pacotes recebidos
- Capacidade (%)
- Receita de guarda

### Agente KMN
- Score Keeper (0-10)
- Score Shopper (0-10)
- Trustlines ativas
- Ofertas criadas
- Vendas cooperadas

---

## 🎯 CASOS DE USO PRINCIPAIS

### 1. Cliente Compra
```
Cliente → Segue Shopper → Vê produtos → Faz pedido → 
Shopper cria pacote → Keeper recebe → Cliente recebe
```

### 2. Venda Cooperada (KMN)
```
Cliente (Keeper) → Vê oferta (Shopper) → Faz pedido → 
Ambos recebem comissão
```

### 3. Agente Dual
```
Agente → Vende (Shopper) → Guarda (Keeper) → 
Gerencia tudo em um lugar
```

---

## ⚠️ REGRAS IMPORTANTES

1. **Isolamento Total**
   - Cada Shopper/Keeper vê apenas seus dados
   - Impossível acessar dados de outros

2. **Multi-perfil**
   - Um User pode ter múltiplos perfis
   - Ex: Cliente + Shopper, Shopper + Keeper

3. **KMN**
   - Apenas Agentes participam
   - Requer trustlines para colaboração
   - Sistema de comissões automático

4. **WhatsApp**
   - Apenas Shoppers e Keepers criam grupos
   - Cada grupo tem um `owner` (master)
   - Clientes apenas participam

---

## 📚 DOCUMENTAÇÃO RELACIONADA

- `ANALISE_USUARIOS.md` - Análise completa e detalhada
- `KMN_SYSTEM_README.md` - Sistema KMN completo
- `WHATSAPP_ISOLATION_GUIDE.md` - Isolamento WhatsApp
- `RESUMO_EVOLUCAO_EVORA.md` - Evolução do sistema

---

**Versão**: 1.0  
**Data**: 2025-01-27  
**Sistema**: ÉVORA/VitrineZap

