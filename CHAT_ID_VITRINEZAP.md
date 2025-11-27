# 📱 Chat ID no VitrineZap - Guia Prático

## 🎯 **COMO ENCONTRAR CHAT ID NO VITRINEZAP**

### **1. Via Webhook (Automático)**

O VitrineZap já captura Chat IDs automaticamente via webhook:

```python
# app_marketplace/whatsapp_views.py (linha 116)
chat_id = (msg.get("chatId") or msg.get("from", "")).replace("@g.us", "").replace("@c.us", "")
```

#### **Estrutura do Webhook**
```json
{
  "data": {
    "message": {
      "chatId": "5511999999999@c.us",  // ← Chat ID aqui
      "from": "5511999999999@c.us",
      "sender": {
        "id": "5511999999999@c.us",
        "name": "João Silva"
      },
      "body": "Olá!",
      "type": "chat"
    }
  }
}
```

---

### **2. Modelos Existentes no VitrineZap**

#### **WhatsappGroup** (Grupos)
```python
# Já implementado em app_marketplace/models.py
class WhatsappGroup(models.Model):
    chat_id = models.CharField(max_length=100, unique=True)  # ← Chat ID do grupo
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    # ...
```

#### **WhatsappParticipant** (Participantes)
```python
class WhatsappParticipant(models.Model):
    phone = models.CharField(max_length=20)  # ← Número base para Chat ID
    # ...
```

---

### **3. Função de Envio Existente**

O VitrineZap já tem função para enviar mensagens:

```python
# app_marketplace/whatsapp_views.py (linha 35)
def send_message(chat_id: str, text: str) -> dict:
    """Envia mensagem para o WhatsApp via WPPConnect"""
    
    # Formata Chat ID automaticamente
    if not chat_id.endswith("@g.us") and not chat_id.endswith("@c.us"):
        if len(chat_id) > 15:  # Grupo
            chat_id = f"{chat_id}@g.us"
        else:  # Individual
            chat_id = f"{chat_id}@c.us"
    
    # Envia via WPPConnect
    url = f"{WPP_BASE}/api/{WPP_SESSION}/send-message"
    payload = {
        "phone": chat_id,
        "message": text,
        "isGroup": chat_id.endswith("@g.us")
    }
```

---

### **4. Como Descobrir Chat ID na Prática**

#### **Método 1: Via Dashboard WhatsApp**
1. Acesse: `http://127.0.0.1:8000/whatsapp/dashboard/`
2. Vá em "Grupos"
3. Os Chat IDs estão listados na coluna "Chat ID"

#### **Método 2: Via Logs do Webhook**
```python
# Adicione no webhook para debug
@csrf_exempt
def whatsapp_webhook(request):
    payload = json.loads(request.body.decode("utf-8"))
    data = payload.get("data", payload)
    msg = data.get("message", data)
    
    chat_id = msg.get("chatId") or msg.get("from", "")
    
    # LOG PARA DEBUG
    print(f"📱 Chat ID recebido: {chat_id}")
    
    # Resto da lógica...
```

#### **Método 3: Comando de Debug**
Adicione um comando especial no webhook:

```python
# No whatsapp_webhook, adicione:
if body.strip().lower() == "/meu_id":
    send_message(chat_id, f"🆔 Seu Chat ID: `{chat_id}`")
    return JsonResponse({"ok": True, "action": "sent_chat_id"})
```

---

### **5. Utilitário para Formatar Chat ID**

Crie uma função helper:

```python
# app_marketplace/utils.py
def format_chat_id(phone_or_id: str, is_group: bool = False) -> str:
    """
    Formata número/ID para Chat ID do WhatsApp
    
    Args:
        phone_or_id: Número de telefone ou ID
        is_group: Se é um grupo
    
    Returns:
        Chat ID formatado
    """
    # Remove caracteres especiais
    clean_id = re.sub(r'[^\d]', '', phone_or_id)
    
    # Se já tem sufixo, retorna como está
    if phone_or_id.endswith('@c.us') or phone_or_id.endswith('@g.us'):
        return phone_or_id
    
    # Adiciona código do país se necessário
    if len(clean_id) == 11 and clean_id.startswith('11'):  # São Paulo
        clean_id = '55' + clean_id
    elif len(clean_id) == 10:  # Sem DDD
        clean_id = '5511' + clean_id
    
    # Adiciona sufixo
    suffix = '@g.us' if is_group else '@c.us'
    return f"{clean_id}{suffix}"

# Exemplo de uso:
chat_id = format_chat_id("(11) 99999-9999")  # → "5511999999999@c.us"
```

---

### **6. View para Descobrir Chat IDs**

Adicione uma view de debug:

```python
# app_marketplace/views.py
@login_required
def debug_chat_ids(request):
    """View para descobrir e testar Chat IDs"""
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'format_phone':
            phone = request.POST.get('phone')
            chat_id = format_chat_id(phone)
            return JsonResponse({
                'phone': phone,
                'chat_id': chat_id,
                'formatted': True
            })
        
        elif action == 'test_send':
            chat_id = request.POST.get('chat_id')
            message = request.POST.get('message', 'Teste do VitrineZap!')
            
            result = send_message(chat_id, message)
            return JsonResponse({
                'sent': 'error' not in result,
                'result': result
            })
    
    # Listar grupos existentes
    groups = WhatsappGroup.objects.all()
    
    context = {
        'groups': groups,
        'wpp_session': WPP_SESSION
    }
    
    return render(request, 'app_marketplace/debug_chat_ids.html', context)
```

---

### **7. Template de Debug**

```html
<!-- app_marketplace/templates/app_marketplace/debug_chat_ids.html -->
{% extends 'app_marketplace/base.html' %}

{% block title %}Debug Chat IDs{% endblock %}

{% block content %}
<div class="container mt-4">
    <h2>🔍 Debug Chat IDs - VitrineZap</h2>
    
    <!-- Formatar Número -->
    <div class="card mb-4">
        <div class="card-header">📱 Formatar Número para Chat ID</div>
        <div class="card-body">
            <form id="formatForm">
                <div class="input-group">
                    <input type="text" class="form-control" name="phone" 
                           placeholder="(11) 99999-9999" required>
                    <button type="submit" class="btn btn-primary">Formatar</button>
                </div>
            </form>
            <div id="formatResult" class="mt-3"></div>
        </div>
    </div>
    
    <!-- Testar Envio -->
    <div class="card mb-4">
        <div class="card-header">📤 Testar Envio</div>
        <div class="card-body">
            <form id="testForm">
                <div class="mb-3">
                    <input type="text" class="form-control" name="chat_id" 
                           placeholder="5511999999999@c.us" required>
                </div>
                <div class="mb-3">
                    <input type="text" class="form-control" name="message" 
                           placeholder="Mensagem de teste" value="🤖 Teste do VitrineZap!">
                </div>
                <button type="submit" class="btn btn-success">Enviar Teste</button>
            </form>
            <div id="testResult" class="mt-3"></div>
        </div>
    </div>
    
    <!-- Grupos Existentes -->
    <div class="card">
        <div class="card-header">👥 Grupos Cadastrados</div>
        <div class="card-body">
            {% if groups %}
                <div class="table-responsive">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Nome</th>
                                <th>Chat ID</th>
                                <th>Ações</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for group in groups %}
                            <tr>
                                <td>{{ group.name }}</td>
                                <td><code>{{ group.chat_id }}</code></td>
                                <td>
                                    <button class="btn btn-sm btn-outline-primary" 
                                            onclick="copyToClipboard('{{ group.chat_id }}')">
                                        Copiar
                                    </button>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            {% else %}
                <p class="text-muted">Nenhum grupo cadastrado ainda.</p>
            {% endif %}
        </div>
    </div>
</div>

<script>
// JavaScript para as funcionalidades
document.getElementById('formatForm').onsubmit = function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    formData.append('action', 'format_phone');
    
    fetch('', {
        method: 'POST',
        body: formData,
        headers: {'X-CSRFToken': '{{ csrf_token }}'}
    })
    .then(r => r.json())
    .then(data => {
        document.getElementById('formatResult').innerHTML = 
            `<div class="alert alert-success">
                <strong>Chat ID:</strong> <code>${data.chat_id}</code>
            </div>`;
    });
};

document.getElementById('testForm').onsubmit = function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    formData.append('action', 'test_send');
    
    fetch('', {
        method: 'POST',
        body: formData,
        headers: {'X-CSRFToken': '{{ csrf_token }}'}
    })
    .then(r => r.json())
    .then(data => {
        const alertClass = data.sent ? 'alert-success' : 'alert-danger';
        const message = data.sent ? 'Mensagem enviada!' : 'Erro ao enviar';
        
        document.getElementById('testResult').innerHTML = 
            `<div class="alert ${alertClass}">${message}</div>`;
    });
};

function copyToClipboard(text) {
    navigator.clipboard.writeText(text);
    alert('Chat ID copiado!');
}
</script>
{% endblock %}
```

---

### **8. Adicionar URL**

```python
# app_marketplace/urls.py
urlpatterns = [
    # ... URLs existentes ...
    
    # Debug Chat IDs
    path('debug/chat-ids/', views.debug_chat_ids, name='debug_chat_ids'),
]
```

---

## 🎯 **RESUMO PRÁTICO**

### **Para Descobrir Chat IDs no VitrineZap:**

1. **Automático**: Via webhook quando receber mensagens
2. **Manual**: Use a view de debug (`/debug/chat-ids/`)
3. **Comando**: Envie `/meu_id` no WhatsApp
4. **Dashboard**: Veja grupos em `/whatsapp/dashboard/`

### **Formatos:**
- **Individual**: `5511999999999@c.us`
- **Grupo**: `120363123456789012@g.us`

### **Função Pronta:**
```python
from app_marketplace.whatsapp_views import send_message

# Enviar mensagem
send_message("5511999999999@c.us", "Olá do VitrineZap!")
```

**O sistema já está preparado para capturar e usar Chat IDs automaticamente!** 🚀
