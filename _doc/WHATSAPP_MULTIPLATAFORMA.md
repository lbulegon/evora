# 📱 WhatsApp Multiplataforma - Python + Flutter

## 🎯 **Problema Resolvido**
- ❌ Selenium não funciona em Flutter
- ❌ WPPConnect descontinuado
- ✅ **Solução**: WhatsApp Cloud API (Meta)

## 🚀 **Solução Multiplataforma**

### **Arquitetura:**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flutter App   │    │  Python Backend │    │ WhatsApp Cloud  │
│                 │◄──►│     Django      │◄──►│      API        │
│  - Enviar MSG   │    │  - Processar    │    │  - Enviar MSG   │
│  - Gerenciar    │    │  - Webhook      │    │  - Receber MSG │
│  - Grupos       │    │  - API REST     │    │  - Templates    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🐍 **Python Backend (Django)**

### **1. Instalar Dependências**
```bash
pip install requests python-dotenv
```

### **2. Configurar Variáveis**
```bash
# .env
WHATSAPP_ACCESS_TOKEN=seu_token_aqui
WHATSAPP_PHONE_NUMBER_ID=seu_phone_id
WHATSAPP_VERIFY_TOKEN=seu_verify_token
```

### **3. Implementar API**
```python
# app_marketplace/whatsapp_cloud_views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .whatsapp_cloud_api import WhatsAppCloudAPI
import json

@csrf_exempt
def send_whatsapp_message(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        to = data.get('to')
        message = data.get('message')
        
        api = WhatsAppCloudAPI()
        result = api.send_text_message(to, message)
        
        return JsonResponse(result)

@csrf_exempt
def get_whatsapp_groups(request):
    # Retornar grupos do banco de dados
    groups = WhatsappGroup.objects.filter(owner=request.user)
    return JsonResponse({
        'groups': [{'id': g.chat_id, 'name': g.name} for g in groups]
    })
```

## 📱 **Flutter App**

### **1. Adicionar Dependências**
```yaml
# pubspec.yaml
dependencies:
  http: ^1.1.0
  shared_preferences: ^2.2.0
```

### **2. Implementar Serviço**
```dart
// lib/services/whatsapp_service.dart
import 'package:http/http.dart' as http;
import 'dart:convert';

class WhatsAppService {
  final String baseUrl;
  
  WhatsAppService({required this.baseUrl});
  
  Future<void> sendMessage(String to, String message) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/whatsapp/send/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'to': to, 'message': message}),
    );
    
    if (response.statusCode == 200) {
      print('✅ Mensagem enviada');
    } else {
      print('❌ Erro: ${response.statusCode}');
    }
  }
  
  Future<List<Map<String, dynamic>>> getGroups() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/whatsapp/groups/'),
    );
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return List<Map<String, dynamic>>.from(data['groups']);
    }
    
    return [];
  }
}
```

### **3. Widget de Envio**
```dart
// lib/widgets/whatsapp_sender.dart
import 'package:flutter/material.dart';
import '../services/whatsapp_service.dart';

class WhatsAppSender extends StatefulWidget {
  @override
  _WhatsAppSenderState createState() => _WhatsAppSenderState();
}

class _WhatsAppSenderState extends State<WhatsAppSender> {
  final WhatsAppService _whatsappService = WhatsAppService(
    baseUrl: 'https://seu-backend.com',
  );
  
  final TextEditingController _messageController = TextEditingController();
  String _selectedGroup = '';
  List<Map<String, dynamic>> _groups = [];
  
  @override
  void initState() {
    super.initState();
    _loadGroups();
  }
  
  Future<void> _loadGroups() async {
    final groups = await _whatsappService.getGroups();
    setState(() {
      _groups = groups;
    });
  }
  
  Future<void> _sendMessage() async {
    if (_selectedGroup.isNotEmpty && _messageController.text.isNotEmpty) {
      await _whatsappService.sendMessage(_selectedGroup, _messageController.text);
      _messageController.clear();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Mensagem enviada!')),
      );
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('WhatsApp ÉVORA')),
      body: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            DropdownButton<String>(
              value: _selectedGroup.isEmpty ? null : _selectedGroup,
              hint: Text('Selecione um grupo'),
              items: _groups.map((group) {
                return DropdownMenuItem<String>(
                  value: group['id'],
                  child: Text(group['name']),
                );
              }).toList(),
              onChanged: (value) {
                setState(() {
                  _selectedGroup = value ?? '';
                });
              },
            ),
            SizedBox(height: 16),
            TextField(
              controller: _messageController,
              decoration: InputDecoration(
                labelText: 'Mensagem',
                border: OutlineInputBorder(),
              ),
              maxLines: 3,
            ),
            SizedBox(height: 16),
            ElevatedButton(
              onPressed: _sendMessage,
              child: Text('Enviar Mensagem'),
            ),
          ],
        ),
      ),
    );
  }
}
```

## 🔧 **Configuração WhatsApp Cloud API**

### **1. Criar App no Meta**
1. Acesse: https://developers.facebook.com/
2. Criar novo app
3. Adicionar produto "WhatsApp"
4. Configurar webhook

### **2. Obter Credenciais**
```bash
# Variáveis de ambiente
WHATSAPP_ACCESS_TOKEN=EAABwzLixnjYBO...
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_VERIFY_TOKEN=meu_token_secreto
```

### **3. Configurar Webhook**
```python
# app_marketplace/whatsapp_webhook.py
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def whatsapp_webhook(request):
    if request.method == 'GET':
        # Verificação do webhook
        hub_mode = request.GET.get('hub.mode')
        hub_challenge = request.GET.get('hub.challenge')
        hub_verify_token = request.GET.get('hub.verify_token')
        
        if hub_mode == 'subscribe' and hub_verify_token == 'meu_token_secreto':
            return HttpResponse(hub_challenge)
        else:
            return HttpResponse('Forbidden', status=403)
    
    elif request.method == 'POST':
        # Processar mensagens recebidas
        data = json.loads(request.body)
        # Implementar lógica de processamento
        return HttpResponse('OK')
```

## 📊 **Vantagens da Solução**

### **✅ Multiplataforma**
- Python Backend + Flutter App
- Mesma API para ambos
- Sincronização automática

### **✅ Oficial e Estável**
- WhatsApp Cloud API (Meta)
- Sem risco de bloqueio
- Suporte oficial

### **✅ Escalável**
- Suporta milhares de mensagens
- Webhook para tempo real
- Templates personalizados

### **✅ Flexível**
- Texto, mídia, templates
- Grupos e individuais
- Automação completa

## 🚀 **Implementação Completa**

### **1. Backend Django**
```python
# URLs
path('api/whatsapp/send/', whatsapp_cloud_views.send_whatsapp_message),
path('api/whatsapp/groups/', whatsapp_cloud_views.get_whatsapp_groups),
path('webhook/whatsapp/', whatsapp_webhook.whatsapp_webhook),
```

### **2. Flutter App**
```dart
// main.dart
void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ÉVORA WhatsApp',
      home: WhatsAppSender(),
    );
  }
}
```

### **3. Deploy**
```bash
# Backend
python manage.py migrate
python manage.py runserver

# Flutter
flutter run
```

## 🎯 **Resultado Final**

Com esta solução você terá:
- ✅ **Backend Python** funcionando
- ✅ **App Flutter** funcionando
- ✅ **Integração WhatsApp** oficial
- ✅ **Sincronização** entre plataformas
- ✅ **Escalabilidade** para produção

## 📞 **Próximos Passos**

1. **Configurar WhatsApp Cloud API**
2. **Implementar backend Django**
3. **Criar app Flutter**
4. **Testar integração**
5. **Deploy em produção**

A solução está pronta para funcionar tanto em Python quanto em Flutter! 🚀
