# 📱 Migração WhatsApp - WPPConnect → Baileys (2024)

## ❌ **Problema: WPPConnect Descontinuado**
- WPPConnect não é mais mantido
- Quebra com atualizações do WhatsApp
- Alternativas mais estáveis disponíveis

## ✅ **Solução: Baileys (Recomendado)**

### **Por que Baileys?**
- ✅ **Ativamente mantido** (2024)
- ✅ **Mais estável** que WPPConnect
- ✅ **Comunidade ativa**
- ✅ **Funciona com WhatsApp pessoal**
- ✅ **Gratuito**

## 🚀 **Instalação e Configuração**

### **1. Instalar Node.js**
```bash
# Windows (via Chocolatey)
choco install nodejs

# Ou baixar de: https://nodejs.org/
```

### **2. Instalar Dependências**
```bash
# No diretório do projeto
npm install
```

### **3. Executar Integração**
```bash
# Listar grupos WhatsApp
npm run groups

# Enviar mensagem de teste
npm run test "120363123456789012@g.us" "Olá grupo!"
```

## 🔧 **Configuração no ÉVORA**

### **1. Atualizar requirements.txt**
```python
# Remover dependências do WPPConnect
# Adicionar suporte para Node.js
```

### **2. Criar Bridge Python ↔ Node.js**
```python
# whatsapp_bridge.py
import subprocess
import json
import os

class WhatsAppBridge:
    def __init__(self):
        self.node_script = "whatsapp_baileys_integration.js"
    
    def get_groups(self):
        """Obter grupos via Baileys"""
        try:
            result = subprocess.run([
                'node', self.node_script, 'groups'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Parsear output para extrair grupos
                return self.parse_groups_output(result.stdout)
            else:
                print(f"Erro: {result.stderr}")
                return []
        except Exception as e:
            print(f"Erro ao executar Baileys: {e}")
            return []
    
    def send_message(self, group_id, message):
        """Enviar mensagem via Baileys"""
        try:
            result = subprocess.run([
                'node', self.node_script, 'send', group_id, message
            ], capture_output=True, text=True, timeout=30)
            
            return result.returncode == 0
        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")
            return False
    
    def parse_groups_output(self, output):
        """Parsear output dos grupos"""
        groups = []
        lines = output.split('\n')
        
        current_group = {}
        for line in lines:
            if 'Chat ID:' in line:
                current_group['id'] = line.split('Chat ID: ')[1].strip()
            elif 'Participantes:' in line:
                current_group['participants'] = int(line.split('Participantes: ')[1].strip())
            elif line.strip() and not line.startswith('=') and not line.startswith('📱'):
                if current_group.get('id'):
                    current_group['name'] = line.strip()
                    groups.append(current_group.copy())
                    current_group = {}
        
        return groups
```

### **3. Atualizar Views Django**
```python
# app_marketplace/whatsapp_views.py
from .whatsapp_bridge import WhatsAppBridge

def get_whatsapp_groups(request):
    """Obter grupos WhatsApp via Baileys"""
    if not request.user.is_shopper:
        return JsonResponse({'error': 'Acesso restrito'}, status=403)
    
    bridge = WhatsAppBridge()
    groups = bridge.get_groups()
    
    return JsonResponse({
        'success': True,
        'groups': groups
    })

def send_group_message(request, group_id):
    """Enviar mensagem para grupo via Baileys"""
    if not request.user.is_shopper:
        return JsonResponse({'error': 'Acesso restrito'}, status=403)
    
    data = json.loads(request.body)
    message = data.get('message', '')
    
    bridge = WhatsAppBridge()
    success = bridge.send_message(group_id, message)
    
    return JsonResponse({
        'success': success,
        'message': 'Mensagem enviada' if success else 'Erro ao enviar'
    })
```

## 📋 **Passos da Migração**

### **1. Backup dos Dados**
```bash
# Fazer backup do banco
python manage.py dumpdata > backup_whatsapp.json
```

### **2. Remover WPPConnect**
```bash
# Remover containers Docker
docker-compose down
docker system prune -f

# Remover arquivos
rm -rf wppconnect-data/
rm docker-compose.yml
```

### **3. Instalar Baileys**
```bash
# Instalar Node.js
# Instalar dependências
npm install

# Testar conexão
npm run groups
```

### **4. Atualizar ÉVORA**
```python
# Atualizar views
# Atualizar templates
# Testar integração
```

### **5. Testar Sistema**
```bash
# Testar login
python test_marcia_login.py

# Testar grupos
npm run groups

# Testar mensagens
npm run test "CHAT_ID" "Mensagem teste"
```

## 🎯 **Vantagens da Migração**

### **Antes (WPPConnect):**
- ❌ Descontinuado
- ❌ Quebra frequentemente
- ❌ Docker obrigatório
- ❌ Configuração complexa

### **Depois (Baileys):**
- ✅ Ativamente mantido
- ✅ Mais estável
- ✅ Node.js simples
- ✅ Configuração fácil

## 🔍 **Monitoramento**

### **Logs do Baileys:**
```bash
# Ver logs em tempo real
tail -f whatsapp_auth/baileys_store.json

# Verificar conexão
ps aux | grep node
```

### **Logs do Django:**
```bash
# Ver logs do Django
python manage.py runserver --verbosity=2

# Ver logs de erro
tail -f django.log
```

## 🚨 **Troubleshooting**

### **Problema: QR Code não aparece**
```bash
# Limpar autenticação
rm -rf whatsapp_auth/
npm run groups
```

### **Problema: Grupos não carregam**
```bash
# Verificar conexão
node -e "console.log('Node.js funcionando')"

# Reinstalar dependências
rm -rf node_modules/
npm install
```

### **Problema: Mensagens não enviam**
```bash
# Verificar permissões do grupo
# Verificar se o bot está no grupo
# Testar com mensagem simples
```

## 📊 **Comparação de Performance**

| Métrica | WPPConnect | Baileys |
|---------|------------|---------|
| Estabilidade | ❌ Baixa | ✅ Alta |
| Manutenção | ❌ Parada | ✅ Ativa |
| Configuração | ❌ Complexa | ✅ Simples |
| Performance | ⚠️ Média | ✅ Boa |
| Comunidade | ❌ Pequena | ✅ Grande |

## 🎉 **Resultado Final**

Após a migração, você terá:
- ✅ **Sistema estável** de integração WhatsApp
- ✅ **Fácil manutenção** e atualizações
- ✅ **Melhor performance** e confiabilidade
- ✅ **Suporte ativo** da comunidade
- ✅ **Integração perfeita** com ÉVORA

## 📞 **Suporte**

Se encontrar problemas:
1. Verificar logs do Node.js
2. Verificar logs do Django
3. Testar conexão WhatsApp
4. Consultar documentação do Baileys
5. Abrir issue no repositório
