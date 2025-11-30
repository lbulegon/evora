# 📱 Integração WhatsApp - Alternativas 2024

## ❌ **WPPConnect - DESCONTINUADO**
- **Status**: Não mantido desde 2024
- **Problema**: Quebra com atualizações do WhatsApp
- **Recomendação**: **NÃO USAR**

## ✅ **Alternativas Atuais**

### **1. WhatsApp Business API (Oficial) - RECOMENDADO**

#### **Vantagens:**
- ✅ Oficial do Meta/Facebook
- ✅ Estável e confiável
- ✅ Suporte completo
- ✅ Sem risco de bloqueio

#### **Desvantagens:**
- ❌ Requer aprovação do Meta
- ❌ Pode ter custos
- ❌ Processo de verificação

#### **Implementação:**
```python
# requirements.txt
requests==2.31.0
python-dotenv==1.0.0

# .env
WHATSAPP_ACCESS_TOKEN=seu_token_aqui
WHATSAPP_PHONE_NUMBER_ID=seu_phone_id
WHATSAPP_VERIFY_TOKEN=seu_verify_token
```

```python
# whatsapp_business_api.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

class WhatsAppBusinessAPI:
    def __init__(self):
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.base_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}"
    
    def send_message(self, to, message):
        """Enviar mensagem via WhatsApp Business API"""
        url = f"{self.base_url}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }
        
        response = requests.post(url, headers=headers, json=data)
        return response.json()
    
    def send_to_group(self, group_id, message):
        """Enviar mensagem para grupo"""
        return self.send_message(group_id, message)
```

### **2. Baileys (Node.js) - Alternativa Não-Oficial**

#### **Vantagens:**
- ✅ Gratuito
- ✅ Não precisa de aprovação
- ✅ Funciona com WhatsApp pessoal
- ✅ Mais estável que WPPConnect

#### **Desvantagens:**
- ❌ Pode ser bloqueado pelo WhatsApp
- ❌ Requer Node.js
- ❌ Não oficial

#### **Implementação:**
```javascript
// package.json
{
  "dependencies": {
    "@whiskeysockets/baileys": "^6.6.0"
  }
}

// baileys_integration.js
const { default: makeWASocket, DisconnectReason } = require('@whiskeysockets/baileys');
const fs = require('fs');

class WhatsAppBaileys {
    constructor() {
        this.sock = null;
        this.state = null;
    }
    
    async connect() {
        this.sock = makeWASocket({
            printQRInTerminal: true,
            auth: this.state,
            browser: ['ÉVORA', 'Chrome', '1.0.0']
        });
        
        this.sock.ev.on('connection.update', (update) => {
            const { connection, lastDisconnect } = update;
            if (connection === 'close') {
                const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
                if (shouldReconnect) {
                    this.connect();
                }
            }
        });
    }
    
    async getGroups() {
        const groups = await this.sock.groupFetchAllParticipating();
        return Object.values(groups).map(group => ({
            id: group.id,
            name: group.subject,
            participants: group.participants.length
        }));
    }
    
    async sendMessage(groupId, message) {
        await this.sock.sendMessage(groupId, { text: message });
    }
}

module.exports = WhatsAppBaileys;
```

### **3. Venom-Bot - Alternativa Simples**

#### **Vantagens:**
- ✅ Muito simples de usar
- ✅ Documentação boa
- ✅ Comunidade ativa

#### **Desvantagens:**
- ❌ Pode ser bloqueado
- ❌ Não oficial

#### **Implementação:**
```javascript
// venom_integration.js
const venom = require('venom-bot');

class WhatsAppVenom {
    constructor() {
        this.client = null;
    }
    
    async connect() {
        this.client = await venom.create({
            session: 'evora-session',
            multidevice: true
        });
    }
    
    async getGroups() {
        const groups = await this.client.getAllGroups();
        return groups.map(group => ({
            id: group.id,
            name: group.name,
            participants: group.participants.length
        }));
    }
    
    async sendMessage(groupId, message) {
        await this.client.sendText(groupId, message);
    }
}

module.exports = WhatsAppVenom;
```

## 🎯 **Recomendação para ÉVORA**

### **Para Produção:**
1. **WhatsApp Business API** (oficial)
2. **Baileys** (se não conseguir aprovação)

### **Para Desenvolvimento/Teste:**
1. **Baileys** (mais fácil de configurar)
2. **Venom-Bot** (mais simples)

## 🚀 **Implementação no ÉVORA**

Vou criar um sistema híbrido que suporte múltiplas integrações:

```python
# whatsapp_integrations.py
from abc import ABC, abstractmethod

class WhatsAppIntegration(ABC):
    @abstractmethod
    def send_message(self, to, message):
        pass
    
    @abstractmethod
    def get_groups(self):
        pass

class WhatsAppBusinessAPI(WhatsAppIntegration):
    # Implementação da API oficial
    pass

class WhatsAppBaileys(WhatsAppIntegration):
    # Implementação do Baileys
    pass

class WhatsAppVenom(WhatsAppIntegration):
    # Implementação do Venom
    pass
```

## 📋 **Próximos Passos**

1. **Escolher integração** baseada nas necessidades
2. **Configurar ambiente** de desenvolvimento
3. **Implementar no ÉVORA**
4. **Testar com grupos reais**
5. **Deploy em produção**

## 🔗 **Links Úteis**

- [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)
- [Baileys GitHub](https://github.com/WhiskeySockets/Baileys)
- [Venom-Bot GitHub](https://github.com/orkestral/venom)
- [WhatsApp Business Platform](https://business.whatsapp.com/)
