# Plano de Implementação - Fluxo WhatsApp Évora/VitrineZap

## 🎯 Objetivo

Implementar fluxo WhatsApp **do zero** seguindo os **Princípios Fundadores** e utilizando:
- **Django** (backend)
- **Evolution API** (comunicação WhatsApp)
- **SinapUm** (servidor de IA)
- **Agentes Ágnosticos** (arquitetura flexível)

---

## 📐 Arquitetura Proposta

### Componentes Principais

```
┌─────────────────────────────────────────────────────────────┐
│                    EVOLUTION API                             │
│              (Comunicação WhatsApp)                         │
└────────────────────┬────────────────────────────────────────┘
                      │
                      │ Webhook
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              DJANGO (Évora/VitrineZap)                      │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  WhatsApp Conversational Flow Engine              │    │
│  │  - Detecta grupo vs privado                        │    │
│  │  - Gerencia intenção social                        │    │
│  │  - Click-to-chat contextualizado                   │    │
│  │  - Carrinho invisível                              │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Agent System (Ágnostico)                          │    │
│  │  - IA-Vendedor (conversacional)                    │    │
│  │  - Processador de intenções                        │    │
│  │  - Gerenciador de fluxo                            │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  SinapUm Integration                               │    │
│  │  - Análise de imagens                              │    │
│  │  - Extração de dados de produtos                  │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  KMN Integration                                   │    │
│  │  - Gestão de entrega                               │    │
│  │  - Conexão com Address Keepers                    │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Estrutura de Implementação

### 1. Modelos Django (Novos/Atualizados)

#### 1.1 Oferta de Produto (Postagem no Grupo)
```python
class OfertaProduto(models.Model):
    """
    Oferta/postagem de produto no grupo WhatsApp
    Deve conter ID para click-to-chat
    """
    produto = models.ForeignKey(ProdutoJSON, ...)
    grupo = models.ForeignKey(WhatsappGroup, ...)
    oferta_id = models.CharField(unique=True)  # ID para click-to-chat
    mensagem_postada = models.TextField()  # Mensagem original no grupo
    imagem_url = models.URLField()
    criado_em = models.DateTimeField()
    # ... outros campos
```

#### 1.2 Intenção Social Assistida
```python
class IntencaoSocial(models.Model):
    """
    Manifestação de interesse no grupo (não é pedido!)
    """
    oferta = models.ForeignKey(OfertaProduto, ...)
    participante = models.ForeignKey(WhatsappParticipant, ...)
    tipo = models.CharField()  # 'emoji', 'texto', 'pergunta'
    conteudo = models.TextField()  # "eu quero", "❤️", "quanto custa?"
    criado_em = models.DateTimeField()
    # NÃO gera pedido, NÃO gera carrinho
```

#### 1.3 Conversa Contextualizada
```python
class ConversaContextualizada(models.Model):
    """
    Conversa privada iniciada via click-to-chat
    Já vem contextualizada com produto
    """
    oferta = models.ForeignKey(OfertaProduto, ...)  # Contexto
    participante = models.ForeignKey(WhatsappParticipant, ...)
    conversa = models.ForeignKey(WhatsappConversation, ...)
    iniciada_em = models.DateTimeField()
    status = models.CharField()  # 'aberta', 'negociando', 'fechada'
```

#### 1.4 Carrinho Invisível
```python
class CarrinhoInvisivel(models.Model):
    """
    Carrinho invisível vinculado a uma conversa privada
    Cliente não vê, sistema anota silenciosamente
    """
    conversa = models.OneToOneField(ConversaContextualizada, ...)
    itens = models.JSONField()  # [{produto_id, quantidade, preco}]
    total = models.DecimalField()
    atualizado_em = models.DateTimeField()
    # Nunca exibido como tela obrigatória
```

---

### 2. Serviços (Services)

#### 2.1 WhatsApp Flow Engine
```python
# app_marketplace/whatsapp_flow_engine.py

class WhatsAppFlowEngine:
    """
    Motor do fluxo conversacional WhatsApp
    Respeita arquitetura: GRUPO → CLICK-TO-CHAT → PRIVADO → KMN
    """
    
    def detect_chat_type(self, chat_id: str) -> str:
        """Detecta se é grupo ou privado"""
        return 'group' if '@g.us' in chat_id else 'private'
    
    def handle_group_message(self, message, group):
        """
        No grupo: apenas intenção social
        - Detecta emoji, "eu quero", perguntas
        - NÃO cria pedido
        - NÃO cria carrinho
        - Registra intenção social
        """
        pass
    
    def handle_private_message(self, message, conversation):
        """
        No privado: negociação real
        - Processa comandos /comprar, /pagar
        - Gerencia carrinho invisível
        - Permite fechamento
        """
        pass
    
    def create_click_to_chat(self, oferta, participante):
        """
        Cria conversa privada contextualizada
        Inicia já com contexto do produto
        """
        pass
```

#### 2.2 IA-Vendedor Agent
```python
# app_marketplace/agents/ia_vendedor.py

class IAVendedorAgent:
    """
    Agente IA que age como vendedor humano
    Não é bot, é vendedor
    """
    
    def confirmar(self, item: str) -> str:
        """Confirma de forma natural"""
        return "Anotado! ✅"
    
    def sugerir(self, produto: dict) -> str:
        """Sugere com cuidado"""
        return f"Podemos adicionar {produto['nome']} ao seu pedido?"
    
    def fechar(self, carrinho: dict) -> str:
        """Percebe o momento de fechar"""
        return "Perfeito! Vamos finalizar?"
    
    def responder_naturalmente(self, mensagem: str, contexto: dict) -> str:
        """
        Responde como vendedor humano
        Usa linguagem natural, não robótica
        """
        pass
```

#### 2.3 Evolution API Service (Atualizado)
```python
# app_whatsapp_integration/evolution_service.py

class EvolutionAPIService:
    """
    Serviço Evolution API atualizado
    Integrado com fluxo conversacional
    """
    
    def send_message_with_context(self, to: str, message: str, context: dict):
        """
        Envia mensagem com contexto
        Permite click-to-chat com oferta_id
        """
        pass
    
    def create_click_to_chat_button(self, oferta_id: str, produto_nome: str):
        """
        Cria botão click-to-chat nas postagens
        Usa Evolution API buttons ou links
        """
        pass
```

---

### 3. Views/Handlers

#### 3.1 Webhook Evolution API (Novo)
```python
# app_whatsapp_integration/views.py

@csrf_exempt
def evolution_webhook(request):
    """
    Webhook Evolution API
    Processa mensagens recebidas
    """
    # 1. Detectar tipo de chat (grupo/privado)
    # 2. Rotear para handler apropriado
    # 3. Respeitar arquitetura conversacional
    pass
```

#### 3.2 Handler de Grupo
```python
def handle_group_message(message, group):
    """
    Processa mensagens no grupo
    - Detecta intenção social
    - NÃO cria pedido
    - NÃO cria carrinho
    - Pode sugerir click-to-chat
    """
    pass
```

#### 3.3 Handler de Privado
```python
def handle_private_message(message, conversation):
    """
    Processa mensagens no privado
    - Processa comandos /comprar, /pagar
    - Gerencia carrinho invisível
    - Permite fechamento
    """
    pass
```

#### 3.4 Click-to-Chat Handler
```python
def handle_click_to_chat(oferta_id: str, participante_phone: str):
    """
    Cria conversa privada contextualizada
    Inicia já com contexto do produto
    """
    pass
```

---

## 🔄 Fluxo Completo Implementado

### Cenário 1: Postagem no Grupo → Click-to-Chat → Compra

```
1. SHOPPER POSTA NO GRUPO:
   ┌─────────────────────────────────────┐
   │ 📦 Victoria's Secret Body Splash    │
   │ 💰 R$ 89,90                         │
   │                                     │
   │ [Falar sobre este produto] ← Click  │
   │ ID: OFT-12345                       │
   └─────────────────────────────────────┘

2. CLIENTE MANIFESTA INTERESSE (Intenção Social):
   Cliente: "❤️" ou "eu quero" ou "quanto custa?"
   Sistema: Registra intenção social (NÃO cria pedido)

3. CLIENTE CLICA "Falar sobre este produto":
   → Abre chat privado
   → Contexto: "Olá! Vi que você se interessou por Victoria's Secret Body Splash..."

4. NEGOCIAÇÃO NO PRIVADO:
   IA-Vendedor: "Podemos adicionar isso ao seu pedido?"
   Cliente: "Sim, quero 2"
   IA-Vendedor: "Anotado! ✅"
   [Carrinho invisível atualizado silenciosamente]

5. FECHAMENTO NO PRIVADO:
   Cliente: "Quero finalizar"
   IA-Vendedor: "Perfeito! Vamos finalizar?"
   [Cria pedido, processa pagamento]

6. RETORNO AO GRUPO (Prova Social):
   Sistema: "✅ [Cliente] comprou Victoria's Secret Body Splash! Obrigado!"
```

---

## 📝 Checklist de Implementação

### FASE 1: Estrutura Base (Semana 1)

#### Modelos
- [ ] Criar `OfertaProduto` com `oferta_id`
- [ ] Criar `IntencaoSocial` (não gera pedido)
- [ ] Criar `ConversaContextualizada`
- [ ] Criar `CarrinhoInvisivel`
- [ ] Migrations

#### Serviços Base
- [ ] `WhatsAppFlowEngine` - detectar grupo/privado
- [ ] `EvolutionAPIService` - atualizar para suportar contexto
- [ ] Integração com Evolution API webhook

---

### FASE 2: Fluxo Grupo (Semana 2)

#### Intenção Social
- [ ] Detectar emoji, "eu quero", perguntas no grupo
- [ ] Registrar `IntencaoSocial` (não criar pedido)
- [ ] Reagir com emoji (prova social)

#### Click-to-Chat
- [ ] Gerar `oferta_id` único em postagens
- [ ] Criar botão/link nas postagens do grupo
- [ ] Handler `handle_click_to_chat()`
- [ ] Criar conversa privada contextualizada

---

### FASE 3: Fluxo Privado (Semana 3)

#### Carrinho Invisível
- [ ] Criar `CarrinhoInvisivel` vinculado à conversa
- [ ] Processar comandos `/comprar` no privado
- [ ] Atualizar carrinho silenciosamente
- [ ] Confirmar naturalmente: "Anotado! ✅"

#### IA-Vendedor
- [ ] Implementar `IAVendedorAgent`
- [ ] Reescrever mensagens para linguagem humana
- [ ] Implementar frase-canônica
- [ ] Detectar momento de fechar

#### Fechamento
- [ ] Validar que `/pagar` só funciona no privado
- [ ] Processar pagamento
- [ ] Criar pedido a partir do carrinho invisível

---

### FASE 4: Integração KMN (Semana 4)

#### KMN Integration
- [ ] Ativar KMN após fechamento
- [ ] Conectar com Address Keepers
- [ ] Gestão de entrega

#### Retorno ao Grupo
- [ ] Mensagem de prova social após compra
- [ ] Mensagem após entrega
- [ ] Reaquecimento do ciclo

---

## 🔧 Arquivos a Criar/Modificar

### Novos Arquivos
```
app_marketplace/
├── whatsapp_flow_engine.py          # Motor do fluxo conversacional
├── agents/
│   ├── __init__.py
│   └── ia_vendedor.py               # Agente IA-Vendedor
├── models/
│   └── whatsapp_conversational.py   # Novos modelos (OfertaProduto, etc.)
└── services/
    └── conversational_cart.py       # Carrinho invisível
```

### Arquivos a Modificar
```
app_whatsapp_integration/
├── evolution_service.py            # Adicionar suporte a contexto
└── views.py                         # Novo webhook Evolution API

app_marketplace/
├── whatsapp_views.py                # Refatorar handlers
└── models.py                        # Adicionar novos modelos
```

---

## 🎯 Princípios Implementados

✅ **1. Comprar = Iniciar Conversa**
- Click-to-chat é o ato inicial
- Chat é interface principal

✅ **2. Click-to-Chat Contextualizado**
- Postagens têm `oferta_id`
- Chat inicia com contexto

✅ **3. Intenção Social Assistida**
- Grupo: apenas intenção (não pedido)
- Registrado mas não vinculante

✅ **4. Pedido em Estado Social**
- Grupo: desejo
- Privado: compromisso

✅ **5. Conversa Privada = Negociação**
- Toda negociação no privado
- Carrinho invisível

✅ **6. Carrinho Invisível**
- Nunca exibido
- Sistema anota silenciosamente

✅ **7. IA-Vendedor (não IA-Bot)**
- Linguagem humana
- Confirma naturalmente
- Frase-canônica

✅ **8. Fechamento Individual**
- Sempre no privado
- Nunca no grupo

✅ **9. KMN Integration**
- Conecta conversa → operação
- Entrega e confiança

✅ **10. Arquitetura Respeitada**
- GRUPO → CLICK-TO-CHAT → PRIVADO → KMN → RETORNO

---

## ❓ Próximos Passos

**Posso começar a implementação?**

1. **Criar modelos** (OfertaProduto, IntencaoSocial, etc.)
2. **Implementar WhatsAppFlowEngine**
3. **Criar IA-Vendedor Agent**
4. **Integrar com Evolution API**

**Aguardando confirmação para iniciar!**

