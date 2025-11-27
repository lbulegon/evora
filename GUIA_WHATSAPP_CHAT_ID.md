# 📱 GUIA: Como Encontrar Chat ID do WhatsApp

## 🎯 **MÉTODOS PARA OBTER CHAT ID**

### **1. WhatsApp Business API (Oficial)**

#### **Via Webhook**
```javascript
// Quando receber uma mensagem, o webhook retorna:
{
  "messages": [{
    "from": "5511999999999",  // ← Este é o Chat ID
    "id": "wamid.xxx",
    "timestamp": "1234567890",
    "text": {
      "body": "Olá!"
    }
  }]
}
```

#### **Via API Graph**
```bash
# Listar conversas
curl -X GET \
  "https://graph.facebook.com/v18.0/PHONE_NUMBER_ID/conversations" \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

---

### **2. WPPConnect (Biblioteca Node.js)**

#### **Método 1: Via Código**
```javascript
const wppconnect = require('@wppconnect-team/wppconnect');

wppconnect.create().then((client) => {
  // Listar todos os chats
  client.getAllChats().then((chats) => {
    chats.forEach(chat => {
      console.log(`Nome: ${chat.name}`);
      console.log(`Chat ID: ${chat.id._serialized}`); // ← Chat ID
      console.log(`Tipo: ${chat.isGroup ? 'Grupo' : 'Individual'}`);
      console.log('---');
    });
  });
});
```

#### **Método 2: Via Evento de Mensagem**
```javascript
client.onMessage((message) => {
  console.log('Chat ID:', message.chatId._serialized);
  console.log('De:', message.from);
  console.log('Mensagem:', message.body);
});
```

---

### **3. Baileys (WhatsApp Web API)**

#### **Obter Chat ID**
```javascript
const { makeWASocket } = require('@whiskeysockets/baileys');

const sock = makeWASocket({
  // configurações...
});

sock.ev.on('messages.upsert', (m) => {
  const message = m.messages[0];
  console.log('Chat ID:', message.key.remoteJid); // ← Chat ID
});

// Listar chats
const chats = await sock.store.chats.all();
chats.forEach(chat => {
  console.log(`Chat ID: ${chat.id}`);
  console.log(`Nome: ${chat.name || 'Sem nome'}`);
});
```

---

### **4. Via WhatsApp Web (Manual)**

#### **Método Browser**
1. Abra o **WhatsApp Web** (web.whatsapp.com)
2. Abra o **DevTools** (F12)
3. Vá para a aba **Console**
4. Execute este código:

```javascript
// Listar todos os chats
Store.Chat.models.forEach(chat => {
  console.log(`Nome: ${chat.name || chat.formattedTitle}`);
  console.log(`Chat ID: ${chat.id._serialized}`);
  console.log('---');
});
```

#### **Obter Chat ID Específico**
```javascript
// Chat atual aberto
const currentChat = Store.Chat.find(chat => chat.active);
console.log('Chat ID atual:', currentChat.id._serialized);
```

---

### **5. Formatos de Chat ID**

#### **Contato Individual**
```
5511999999999@c.us
```
- `5511999999999` = número com código do país + DDD
- `@c.us` = sufixo para contatos

#### **Grupo**
```
120363123456789012@g.us
```
- `120363123456789012` = ID único do grupo
- `@g.us` = sufixo para grupos

#### **Status/Stories**
```
status@broadcast
```

---

### **6. Implementação no VitrineZap**

#### **Model para Armazenar Chat IDs**
```python
# app_marketplace/models.py
class WhatsAppChat(models.Model):
    chat_id = models.CharField(max_length=100, unique=True)
    nome = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=[
        ('individual', 'Individual'),
        ('grupo', 'Grupo'),
        ('broadcast', 'Broadcast')
    ])
    ativo = models.BooleanField(default=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    agente = models.ForeignKey(Agente, on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nome} ({self.chat_id})"
```

#### **Service para Extrair Chat ID**
```python
# app_marketplace/whatsapp_service.py
class WhatsAppChatService:
    
    @staticmethod
    def extrair_chat_id_de_webhook(webhook_data):
        """Extrai Chat ID de webhook do WhatsApp"""
        try:
            if 'messages' in webhook_data:
                return webhook_data['messages'][0]['from']
            elif 'statuses' in webhook_data:
                return webhook_data['statuses'][0]['recipient_id']
        except (KeyError, IndexError):
            return None
    
    @staticmethod
    def formatar_chat_id(numero_telefone):
        """Formata número de telefone para Chat ID"""
        # Remove caracteres especiais
        numero_limpo = re.sub(r'[^\d]', '', numero_telefone)
        
        # Adiciona código do país se não tiver
        if not numero_limpo.startswith('55'):
            numero_limpo = '55' + numero_limpo
            
        return f"{numero_limpo}@c.us"
    
    @staticmethod
    def validar_chat_id(chat_id):
        """Valida formato do Chat ID"""
        patterns = [
            r'^\d+@c\.us$',      # Individual
            r'^\d+@g\.us$',      # Grupo
            r'^status@broadcast$' # Status
        ]
        return any(re.match(pattern, chat_id) for pattern in patterns)
```

---

### **7. Ferramentas Úteis**

#### **Extensão Chrome: WA Web Plus**
- Mostra Chat IDs diretamente no WhatsApp Web
- Facilita cópia dos IDs

#### **Bot de Teste**
```javascript
// Criar bot simples para descobrir IDs
client.onMessage(async (message) => {
  if (message.body === '!meuID') {
    await client.sendText(message.from, `Seu Chat ID: ${message.from}`);
  }
});
```

---

### **8. Debugging no VitrineZap**

#### **View para Testar Chat ID**
```python
# app_marketplace/views.py
@login_required
def debug_whatsapp_chat_id(request):
    if request.method == 'POST':
        numero = request.POST.get('numero')
        chat_id = WhatsAppChatService.formatar_chat_id(numero)
        
        return JsonResponse({
            'numero_original': numero,
            'chat_id_formatado': chat_id,
            'valido': WhatsAppChatService.validar_chat_id(chat_id)
        })
    
    return render(request, 'debug_chat_id.html')
```

#### **Template de Debug**
```html
<!-- templates/debug_chat_id.html -->
<form method="post">
    {% csrf_token %}
    <input type="text" name="numero" placeholder="(11) 99999-9999">
    <button type="submit">Gerar Chat ID</button>
</form>
```

---

## 🎯 **RESUMO PRÁTICO**

### **Para Desenvolvimento**
1. **Use WPPConnect** - Mais fácil para testes
2. **Capture via webhook** - Automático quando receber mensagens
3. **Store no banco** - Salve os Chat IDs descobertos

### **Para Produção**
1. **WhatsApp Business API** - Oficial e confiável
2. **Webhook configurado** - Capture automaticamente
3. **Validação rigorosa** - Sempre valide o formato

### **Formato Padrão**
```
Individual: 5511999999999@c.us
Grupo: 120363123456789012@g.us
```

**Dica**: O Chat ID é sempre retornado quando você recebe uma mensagem, então a forma mais fácil é configurar um webhook e deixar que os usuários enviem uma mensagem primeiro! 📱


