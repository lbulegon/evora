# 🎯 Modelo TalkRobo - Análise e Melhorias para ÉVORA

## 📊 Visão Geral

O **TalkRobo** é uma plataforma profissional para organização e gestão de WhatsApp. Este documento analisa suas funcionalidades e propõe melhorias para o sistema ÉVORA baseadas nesse modelo.

**Referência:** https://app.talkrobo.com.br/tickets

---

## 🔍 Funcionalidades do TalkRobo (Modelo)

### 1. **Sistema de Tickets/Conversas Organizadas**
- ✅ Conversas centralizadas em uma caixa de entrada unificada
- ✅ Tickets para cada cliente/conversa
- ✅ Status de conversa (aberto, em atendimento, resolvido, fechado)
- ✅ Atribuição de conversas para agentes
- ✅ Histórico completo de interações

### 2. **Interface de Chat Unificada**
- ✅ Visualização de todas as conversas em um só lugar
- ✅ Preview de mensagens não lidas
- ✅ Indicadores de status (online, digitando, etc.)
- ✅ Filtros e busca avançada

### 3. **Automação e Chatbot**
- ✅ Respostas automáticas
- ✅ Mensagens de boas-vindas
- ✅ Respostas para perguntas frequentes
- ✅ Fluxos conversacionais

### 4. **Gestão Multi-Agente**
- ✅ Vários agentes podem atender
- ✅ Transferência de conversas
- ✅ Status de ocupação dos agentes
- ✅ Balanceamento de carga

### 5. **Análise e Relatórios**
- ✅ Métricas de atendimento
- ✅ Tempo médio de resposta
- ✅ Taxa de resolução
- ✅ Dashboard analítico

---

## 📋 Estado Atual do ÉVORA

### ✅ O que já existe:

1. **Grupos WhatsApp**
   - Modelo `WhatsappGroup` vinculado a shoppers/keepers
   - Chat ID único por grupo
   - Participantes do grupo (`WhatsappParticipant`)

2. **Mensagens**
   - Modelo `WhatsappMessage` armazena mensagens
   - Tipos: texto, imagem, vídeo, áudio, documento
   - Vinculadas a grupos

3. **Produtos**
   - `WhatsappProduct` vinculado a grupos e mensagens
   - Criados pelos shoppers
   - Disponíveis para clientes

4. **Pedidos**
   - `WhatsappOrder` para pedidos via WhatsApp
   - Status: pending, confirmed, paid, etc.

5. **Dashboard**
   - Interface web para gerenciar grupos
   - Visualização de produtos e pedidos
   - Estatísticas básicas

6. **Comandos WhatsApp**
   - Parser de comandos (`whatsapp_integration.py`)
   - Handlers para /comprar, /pagar, /status, etc.
   - Webhook para receber mensagens

### ❌ O que falta (baseado no TalkRobo):

1. **Sistema de Conversas/Tickets Organizados**
   - Não há modelo de "conversa" ou "ticket"
   - Mensagens ficam apenas vinculadas ao grupo
   - Não há threads de conversa individuais

2. **Interface de Chat Unificada**
   - Não há caixa de entrada centralizada
   - Visualização fragmentada por grupos
   - Sem preview de conversas não lidas

3. **Gestão de Status de Conversa**
   - Não há status de atendimento
   - Sem atribuição de conversas
   - Sem histórico organizado por cliente

4. **Automação Avançada**
   - Comandos básicos existem, mas sem chatbot completo
   - Sem fluxos conversacionais
   - Sem mensagens automáticas contextuais

5. **Multi-Agente**
   - Não há sistema de múltiplos atendentes
   - Sem transferência de conversas
   - Sem gestão de ocupação

---

## 🚀 Propostas de Melhorias

### 1. **Sistema de Conversas/Tickets** (PRIORIDADE ALTA)

#### Modelo de Dados

```python
class WhatsappConversation(models.Model):
    """Conversa/ticket individual com cliente"""
    STATUS_CHOICES = [
        ('new', 'Nova'),
        ('open', 'Aberta'),
        ('waiting', 'Aguardando Cliente'),
        ('pending', 'Pendente'),
        ('resolved', 'Resolvida'),
        ('closed', 'Fechada'),
    ]
    
    # Identificação
    conversation_id = models.CharField(max_length=50, unique=True)
    group = models.ForeignKey(WhatsappGroup, on_delete=models.CASCADE, related_name='conversations')
    participant = models.ForeignKey(WhatsappParticipant, on_delete=models.CASCADE, related_name='conversations')
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status e atribuição
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_conversations')
    
    # Metadados
    tags = models.JSONField(default=list, help_text="Tags para categorizar a conversa")
    priority = models.IntegerField(default=5, help_text="Prioridade 1-10")
    last_message_at = models.DateTimeField(auto_now=True)
    first_message_at = models.DateTimeField(auto_now_add=True)
    
    # Estatísticas
    message_count = models.IntegerField(default=0)
    response_time_avg = models.DurationField(null=True, blank=True)
    first_response_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-last_message_at']
        indexes = [
            models.Index(fields=['status', 'assigned_to']),
            models.Index(fields=['group', 'participant']),
        ]
    
    def __str__(self):
        return f"Conversa #{self.conversation_id} - {self.participant.name}"
    
    @property
    def is_unread(self):
        """Verifica se há mensagens não lidas"""
        return self.messages.filter(read=False).exists()
    
    @property
    def unread_count(self):
        """Conta mensagens não lidas"""
        return self.messages.filter(read=False).count()
```

#### Atualizar Modelo de Mensagem

```python
class WhatsappMessage(models.Model):
    # ... campos existentes ...
    
    # NOVOS CAMPOS
    conversation = models.ForeignKey(
        'WhatsappConversation', 
        on_delete=models.CASCADE, 
        related_name='messages',
        null=True, 
        blank=True,
        help_text="Conversa/ticket a que pertence esta mensagem"
    )
    read = models.BooleanField(default=False, help_text="Mensagem foi lida")
    read_at = models.DateTimeField(null=True, blank=True)
    is_from_customer = models.BooleanField(default=True, help_text="Mensagem veio do cliente")
```

#### Funcionalidades

- **Criar conversa automaticamente** quando cliente envia primeira mensagem
- **Agrupar mensagens** do mesmo participante em uma conversa
- **Tags** para categorizar (vendas, suporte, pedido, etc.)
- **Prioridade** baseada em palavras-chave ou status do pedido
- **Status** para rastrear ciclo de vida da conversa

---

### 2. **Caixa de Entrada Unificada** (PRIORIDADE ALTA)

#### Nova View: `conversations_inbox`

```python
@login_required
def conversations_inbox(request):
    """Caixa de entrada unificada - estilo TalkRobo"""
    
    # Filtros
    status = request.GET.get('status', 'open')
    assigned = request.GET.get('assigned', '')
    tag = request.GET.get('tag', '')
    search = request.GET.get('search', '')
    
    # Base queryset - conversas dos grupos do usuário
    conversations = WhatsappConversation.objects.filter(
        group__owner=request.user
    )
    
    # Aplicar filtros
    if status:
        conversations = conversations.filter(status=status)
    if assigned == 'me':
        conversations = conversations.filter(assigned_to=request.user)
    elif assigned == 'unassigned':
        conversations = conversations.filter(assigned_to__isnull=True)
    if tag:
        conversations = conversations.filter(tags__contains=[tag])
    if search:
        conversations = conversations.filter(
            Q(participant__name__icontains=search) |
            Q(participant__phone__icontains=search) |
            Q(messages__content__icontains=search)
        ).distinct()
    
    # Ordenar por não lidas primeiro, depois por última mensagem
    conversations = conversations.order_by(
        '-last_message_at',
        '-priority'
    )
    
    # Estatísticas da sidebar
    stats = {
        'total': conversations.count(),
        'unread': conversations.filter(status='new').count(),
        'open': conversations.filter(status='open').count(),
        'waiting': conversations.filter(status='waiting').count(),
        'resolved': conversations.filter(status='resolved').count(),
    }
    
    context = {
        'conversations': conversations[:50],  # Paginação
        'stats': stats,
        'current_filter': status,
        'filters': {
            'status': status,
            'assigned': assigned,
            'tag': tag,
            'search': search,
        }
    }
    
    return render(request, 'app_marketplace/conversations_inbox.html', context)
```

#### Template: Interface tipo TalkRobo

```
┌─────────────────────────────────────────────────────────┐
│  Caixa de Entrada WhatsApp                    [Buscar]  │
├──────────────┬──────────────────────────────────────────┤
│              │  📧 Conversas                              │
│  FILTROS     ├──────────────────────────────────────────┤
│              │  🆕 Novas (3)                             │
│  Status:     │  📂 Abertas (12)                          │
│  ☑ Novas     │  ⏳ Aguardando (5)                        │
│  ☐ Abertas   │  ✅ Resolvidas (8)                        │
│  ☐ Fechadas  │                                           │
│              │  ┌──────────────────────────────────────┐ │
│  Atribuídas: │  │ 👤 Maria Silva                    🆕 │ │
│  ☑ Minhas    │  │ Olá, quero comprar VS Body Splash   │ │
│  ☐ Sem       │  │ há 2 min                            │ │
│              │  └──────────────────────────────────────┘ │
│  Tags:       │  ┌──────────────────────────────────────┐ │
│  #vendas     │  │ 👤 João Santos                       │ │
│  #suporte    │  │ Quando chega meu pedido?            │ │
│              │  │ há 5 min                            │ │
│              │  └──────────────────────────────────────┘ │
└──────────────┴──────────────────────────────────────────┘
```

---

### 3. **Interface de Chat Individual** (PRIORIDADE ALTA)

#### Nova View: `conversation_detail`

```python
@login_required
def conversation_detail(request, conversation_id):
    """Visualização detalhada de uma conversa - estilo chat"""
    
    conversation = get_object_or_404(
        WhatsappConversation,
        conversation_id=conversation_id,
        group__owner=request.user
    )
    
    # Mensagens da conversa
    messages = conversation.messages.all().order_by('timestamp')
    
    # Marcar como lidas
    messages.filter(is_from_customer=True, read=False).update(
        read=True,
        read_at=timezone.now()
    )
    
    # Informações do cliente
    cliente_info = {
        'name': conversation.participant.name,
        'phone': conversation.participant.phone,
        'cliente': conversation.cliente,
        'pedidos': conversation.cliente.whatsapp_orders.all() if conversation.cliente else [],
        'total_pedidos': conversation.cliente.whatsapp_orders.count() if conversation.cliente else 0,
    }
    
    context = {
        'conversation': conversation,
        'messages': messages,
        'cliente_info': cliente_info,
    }
    
    return render(request, 'app_marketplace/conversation_detail.html', context)
```

#### Funcionalidades do Chat

- **Envio de mensagens** diretamente pela interface web
- **Preview de produtos** relacionados à conversa
- **Ações rápidas**: criar pedido, adicionar tag, atribuir
- **Histórico completo** de mensagens
- **Status em tempo real** (digitando, online, etc.)

---

### 4. **Sistema de Tags e Priorização** (PRIORIDADE MÉDIA)

#### Tags Sugeridas

- `#vendas` - Conversa sobre venda
- `#suporte` - Suporte ao cliente
- `#pedido` - Relacionado a pedido existente
- `#urgente` - Requer atenção imediata
- `#followup` - Acompanhamento necessário
- `#cancelamento` - Pedido cancelado
- `#reclamação` - Reclamação do cliente

#### Priorização Automática

```python
def calculate_priority(conversation):
    """Calcula prioridade baseada em fatores"""
    priority = 5  # Padrão
    
    # Tags
    if '#urgente' in conversation.tags:
        priority = 9
    if '#reclamação' in conversation.tags:
        priority = 8
    
    # Tempo sem resposta
    if conversation.last_message_at:
        hours_since_last = (timezone.now() - conversation.last_message_at).total_seconds() / 3600
        if hours_since_last > 24:
            priority += 2
    
    # Cliente VIP
    if conversation.cliente and conversation.cliente.total_pedidos > 10:
        priority += 1
    
    return min(priority, 10)
```

---

### 5. **Automação Avançada** (PRIORIDADE MÉDIA)

#### Mensagens Automáticas

```python
AUTO_MESSAGES = {
    'welcome': """
    👋 Olá! Bem-vindo ao ÉVORA!
    
    Sou o assistente virtual. Como posso ajudar?
    
    📦 Ver produtos: /produtos
    🛒 Fazer pedido: /comprar
    📊 Status do pedido: /status
    """,
    
    'first_message': """
    👋 Oi! Vi que você está interessado.
    
    Posso ajudar com:
    • Informações sobre produtos
    • Criação de pedidos
    • Acompanhamento de entregas
    
    O que você precisa?
    """,
    
    'after_order': """
    ✅ Pedido criado com sucesso!
    
    Número: {order_number}
    Total: {total}
    
    Agora use /pagar para finalizar o pagamento.
    """,
}
```

#### Chatbot Inteligente

```python
def handle_auto_response(conversation, message):
    """Responde automaticamente se possível"""
    
    # Perguntas frequentes
    faq_patterns = {
        r'(tempo|quando|chega|entrega)': 'delivery_time',
        r'(preço|valor|custo|quanto)': 'price_info',
        r'(produto|item|tem|disponível)': 'product_availability',
        r'(pedido|status|onde|rastrear)': 'order_status',
    }
    
    content_lower = message.content.lower()
    
    for pattern, response_type in faq_patterns.items():
        if re.search(pattern, content_lower):
            return get_faq_response(response_type, conversation)
    
    # Se não encontrar, marcar para atendimento humano
    conversation.status = 'open'
    conversation.assigned_to = None  # Ficar disponível para qualquer agente
    conversation.save()
    
    return None
```

---

### 6. **Multi-Agente e Atribuição** (PRIORIDADE BAIXA)

#### Atribuição de Conversas

```python
def assign_conversation(conversation, agent):
    """Atribui conversa para um agente"""
    conversation.assigned_to = agent
    conversation.status = 'open'
    conversation.save()
    
    # Notificar agente
    send_notification(agent, f"Nova conversa atribuída: {conversation}")
```

#### Balanceamento Automático

```python
def auto_assign_conversation(conversation):
    """Atribui automaticamente para o agente com menos conversas"""
    agents = User.objects.filter(
        is_shopper=True,
        is_active=True
    )
    
    # Contar conversas abertas por agente
    agent_loads = {}
    for agent in agents:
        agent_loads[agent] = WhatsappConversation.objects.filter(
            assigned_to=agent,
            status__in=['new', 'open', 'waiting']
        ).count()
    
    # Atribuir para o menos ocupado
    if agent_loads:
        best_agent = min(agent_loads.items(), key=lambda x: x[1])[0]
        assign_conversation(conversation, best_agent)
```

---

## 📊 Melhorias de Interface

### 1. **Dashboard de Conversas**

```
┌──────────────────────────────────────────────────────────┐
│  Dashboard WhatsApp                       [Período: 7d]  │
├──────────────────┬───────────────────────────────────────┤
│                  │  📊 Estatísticas                       │
│  📈 Gráficos     │  ┌─────────────────────────────────┐  │
│                  │  │ Conversas Abertas: 45           │  │
│  [Gráfico]       │  │ Tempo Médio Resposta: 5m        │  │
│                  │  │ Taxa Resolução: 87%             │  │
│                  │  └─────────────────────────────────┘  │
│                  │                                        │
│                  │  🏆 Top Agentes                       │
│                  │  1. Maria - 23 conversas              │
│                  │  2. João - 18 conversas               │
│                  │                                        │
└──────────────────┴───────────────────────────────────────┘
```

### 2. **Sidebar de Conversas (Estilo TalkRobo)**

- Lista de conversas com preview
- Badge de não lidas
- Filtros rápidos
- Busca instantânea
- Tags visuais

### 3. **Interface de Chat**

- Bubbles de mensagem (estilo WhatsApp)
- Indicadores de leitura
- Timestamps
- Ações rápidas (emoji, responder, arquivar)
- Botão de criar pedido inline

---

## 🎯 Priorização de Implementação

### Fase 1 - Fundação (2-3 semanas)
1. ✅ Modelo `WhatsappConversation`
2. ✅ Atualizar `WhatsappMessage` com campo `conversation`
3. ✅ View básica de caixa de entrada
4. ✅ Criação automática de conversas

### Fase 2 - Interface (2 semanas)
5. ✅ Template de caixa de entrada estilo TalkRobo
6. ✅ Visualização de conversa individual (chat)
7. ✅ Envio de mensagens pela interface web
8. ✅ Sistema de tags básico

### Fase 3 - Automação (1-2 semanas)
9. ✅ Mensagens automáticas de boas-vindas
10. ✅ Respostas para perguntas frequentes
11. ✅ Status automático baseado em tempo

### Fase 4 - Avançado (2-3 semanas)
12. ✅ Sistema de priorização
13. ✅ Multi-agente e atribuição
14. ✅ Dashboard analítico
15. ✅ Relatórios e métricas

---

## 📝 Checklist de Implementação

### Backend
- [ ] Criar migration para `WhatsappConversation`
- [ ] Adicionar campo `conversation` em `WhatsappMessage`
- [ ] Criar signal para criar conversa automaticamente
- [ ] Implementar views de caixa de entrada
- [ ] API para enviar mensagens via web
- [ ] Sistema de tags
- [ ] Priorização automática

### Frontend
- [ ] Template de caixa de entrada
- [ ] Interface de chat individual
- [ ] Componente de lista de conversas
- [ ] Busca e filtros
- [ ] Dashboard de estatísticas
- [ ] Sidebar de ações rápidas

### Automação
- [ ] Mensagens automáticas de boas-vindas
- [ ] Parser de perguntas frequentes
- [ ] Respostas automáticas
- [ ] Atualização de status

### Testes
- [ ] Testes de criação de conversa
- [ ] Testes de atribuição
- [ ] Testes de automação
- [ ] Testes de interface

---

## 🚀 Próximos Passos

1. **Criar modelo `WhatsappConversation`**
2. **Desenvolver migration**
3. **Implementar view básica de caixa de entrada**
4. **Criar template inicial**
5. **Testar criação automática de conversas**

---

**Referências:**
- TalkRobo: https://app.talkrobo.com.br/tickets
- Documentação WhatsApp Integration: `_doc/WHATSAPP_INTEGRATION.md`

---

**ÉVORA Connect** - *Where form becomes community. Where trust becomes network.* ✨

