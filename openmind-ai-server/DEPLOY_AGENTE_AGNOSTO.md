# Deploy do Agente Ágnosto - Servidor SinapUm

## 📋 Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Estrutura de Arquivos](#estrutura-de-arquivos)
3. [Instalação](#instalação)
4. [Configuração](#configuração)
5. [Deploy](#deploy)
6. [Testes](#testes)
7. [Integração com Django](#integração-com-django)
8. [Monitoramento](#monitoramento)
9. [Troubleshooting](#troubleshooting)

---

## 🔧 Pré-requisitos

- Servidor SinapUm acessível (69.169.102.84)
- Python 3.8+ instalado
- Acesso SSH ao servidor
- FastAPI já configurado no servidor
- Variáveis de ambiente configuradas

---

## 📁 Estrutura de Arquivos

Os arquivos do agente ágnosto devem estar na seguinte estrutura:

```
openmind-ai-server/
├── app/
│   ├── core/
│   │   └── agnostic_agent.py          # ✅ NOVO - Core do agente
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── agent.py           # ✅ NOVO - Endpoint do agente
│   └── main.py                         # ⚠️ ATUALIZAR - Adicionar rota
├── requirements.txt                    # ⚠️ VERIFICAR - Dependências
└── .env                                # ⚠️ ATUALIZAR - Variáveis
```

---

## 📦 Instalação

### 1. Conectar ao Servidor

```bash
ssh root@69.169.102.84
```

### 2. Navegar para o Diretório do Projeto

```bash
cd /opt/openmind-ai
# ou
cd /caminho/para/openmind-ai-server
```

### 3. Ativar Ambiente Virtual

```bash
source venv/bin/activate
```

### 4. Verificar Dependências

O agente ágnosto usa apenas bibliotecas padrão do Python. Verifique se `requirements.txt` contém:

```txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
python-multipart>=0.0.6
```

Se necessário, instale:

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuração

### 1. Arquivo: `app/core/agnostic_agent.py`

Este arquivo já deve estar criado. Verifique se contém:

- `AgnosticAgent` (classe base)
- `VendedorAgent` (implementação do vendedor)
- `AgentFactory` (factory para criar agentes)
- `AgentContext` e `AgentResponse` (estruturas de dados)

### 2. Arquivo: `app/api/v1/endpoints/agent.py`

Este arquivo já deve estar criado. Verifique se contém:

- `POST /api/v1/process-message` (processar mensagem)
- `GET /api/v1/agent/capabilities` (listar capacidades)
- `GET /api/v1/agent/roles` (listar papéis)

### 3. Arquivo: `app/main.py`

**ATUALIZAR** para incluir a rota do agente:

```python
from app.api.v1.endpoints import analyze, agent

# ... código existente ...

# Registrar rotas
app.include_router(
    analyze.router,
    prefix="/api/v1",
    tags=["Análise"]
)

# ✅ ADICIONAR ESTA LINHA
app.include_router(
    agent.router,
    prefix="/api/v1",
    tags=["Agente"]
)
```

### 4. Variáveis de Ambiente (`.env`)

Verifique se as seguintes variáveis estão configuradas:

```bash
# API Key para autenticação
OPENMIND_AI_API_KEY=sua-chave-secreta-aqui

# Host e Porta
OPENMIND_AI_HOST=0.0.0.0
OPENMIND_AI_PORT=8000

# CORS (se necessário)
CORS_ORIGINS=http://localhost:8000,https://seu-dominio.com
```

---

## 🚀 Deploy

### Opção 1: Deploy Manual

#### 1. Copiar Arquivos

Se os arquivos estão no repositório local, copie para o servidor:

```bash
# No servidor, criar diretórios se não existirem
mkdir -p app/core
mkdir -p app/api/v1/endpoints

# Copiar arquivos (via scp do seu computador)
scp app/core/agnostic_agent.py root@69.169.102.84:/opt/openmind-ai/app/core/
scp app/api/v1/endpoints/agent.py root@69.169.102.84:/opt/openmind-ai/app/api/v1/endpoints/
```

#### 2. Atualizar `app/main.py`

Edite o arquivo no servidor:

```bash
nano app/main.py
```

Adicione as importações e rotas conforme mostrado na seção de Configuração.

#### 3. Reiniciar Servidor

Se estiver usando systemd:

```bash
systemctl restart openmind-ai
systemctl status openmind-ai
```

Ou se estiver rodando manualmente:

```bash
# Parar processo atual (Ctrl+C ou kill)
# Iniciar novamente
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Opção 2: Deploy via Git

Se o código está no Git:

```bash
cd /opt/openmind-ai
git pull origin main  # ou branch apropriada
source venv/bin/activate
pip install -r requirements.txt
systemctl restart openmind-ai
```

---

## 🧪 Testes

### 1. Teste de Health Check

```bash
curl http://localhost:8000/health
```

Deve retornar:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "OpenMind AI Server"
}
```

### 2. Teste de Listar Papéis

```bash
curl -X GET "http://localhost:8000/api/v1/agent/roles" \
  -H "Authorization: Bearer sua-chave-api"
```

Deve retornar:
```json
{
  "success": true,
  "roles": ["vendedor", "atendente", "assistente", "analista"]
}
```

### 3. Teste de Capacidades

```bash
curl -X GET "http://localhost:8000/api/v1/agent/capabilities?role=vendedor" \
  -H "Authorization: Bearer sua-chave-api"
```

Deve retornar:
```json
{
  "success": true,
  "role": "vendedor",
  "capabilities": [
    "add_to_cart",
    "ask_price",
    "ask_delivery",
    "finalize_order",
    "set_quantity",
    "general_conversation"
  ]
}
```

### 4. Teste de Processar Mensagem

```bash
curl -X POST "http://localhost:8000/api/v1/process-message" \
  -H "Authorization: Bearer sua-chave-api" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Quero adicionar 2 unidades",
    "conversation_id": "PRIV-5511999999999-1234567890",
    "user_phone": "+5511999999999",
    "user_name": "João",
    "is_group": false,
    "offer_id": "OFT-12345",
    "language": "pt-BR",
    "agent_role": "vendedor",
    "metadata": {
      "produto_id": 1,
      "produto_nome": "Produto Exemplo",
      "preco": "89.90",
      "moeda": "BRL"
    }
  }'
```

Deve retornar:
```json
{
  "success": true,
  "message": "Perfeito! Anotei 2 unidade(s) no seu pedido. ✅\n\nQuer adicionar mais alguma coisa ou podemos fechar o pedido?",
  "action": "add_to_cart",
  "data": {
    "quantity": 2
  },
  "should_continue": true,
  "agent_role": "vendedor",
  "capabilities": [...]
}
```

### 5. Teste de Documentação Swagger

Acesse no navegador:
```
http://69.169.102.84:8000/docs
```

Você deve ver a documentação interativa com os novos endpoints do agente.

---

## 🔗 Integração com Django

### 1. Configurar Variáveis no Django

No arquivo `settings.py` do Django:

```python
# URL do agente SinapUm
SINAPUM_AGENT_URL = "http://69.169.102.84:8000/api/v1/process-message"

# API Key (mesma do SinapUm)
SINAPUM_API_KEY = "sua-chave-secreta-aqui"
# ou usar a mesma do OpenMind AI
# SINAPUM_API_KEY = OPENMIND_AI_API_KEY
```

### 2. Testar Integração

No Django, o `WhatsAppFlowEngine` já está configurado para chamar o SinapUm. Teste enviando uma mensagem via WhatsApp e verifique os logs:

```bash
# No servidor Django
tail -f logs/django.log | grep FLOW_ENGINE
```

Você deve ver:
```
[FLOW_ENGINE] Chamando agente SinapUm: http://69.169.102.84:8000/api/v1/process-message
[FLOW_ENGINE] Resposta do SinapUm: add_to_cart
```

---

## 📊 Monitoramento

### 1. Logs do Servidor

```bash
# Se usando systemd
journalctl -u openmind-ai -f

# Se rodando manualmente
tail -f logs/app.log
```

### 2. Verificar Processo

```bash
ps aux | grep uvicorn
```

### 3. Verificar Porta

```bash
netstat -tulpn | grep 8000
# ou
ss -tulpn | grep 8000
```

### 4. Teste de Carga (Opcional)

```bash
# Instalar apache bench
apt install apache2-utils

# Teste básico
ab -n 100 -c 10 -H "Authorization: Bearer sua-chave" \
  http://localhost:8000/api/v1/agent/roles
```

---

## 🔍 Troubleshooting

### Problema: Endpoint não encontrado (404)

**Solução:**
1. Verifique se `app/main.py` inclui a rota do agente
2. Verifique se o servidor foi reiniciado após as mudanças
3. Verifique se o arquivo `agent.py` está no caminho correto

### Problema: Erro 401 (Unauthorized)

**Solução:**
1. Verifique se a API key está correta no header `Authorization: Bearer ...`
2. Verifique se `OPENMIND_AI_API_KEY` está configurada no `.env`
3. Verifique se o middleware de autenticação está funcionando

### Problema: Erro 500 (Internal Server Error)

**Solução:**
1. Verifique os logs do servidor: `journalctl -u openmind-ai -n 50`
2. Verifique se todas as dependências estão instaladas
3. Verifique se há erros de sintaxe nos arquivos Python

### Problema: Timeout ao chamar do Django

**Solução:**
1. Verifique conectividade de rede entre Django e SinapUm
2. Verifique firewall: `ufw status` ou `iptables -L`
3. Aumente timeout no Django se necessário (padrão: 10s)

### Problema: Agente não processa corretamente

**Solução:**
1. Verifique se o `VendedorAgent` está implementado corretamente
2. Teste diretamente via curl primeiro
3. Verifique logs do SinapUm para ver o que está sendo recebido

---

## 📝 Checklist de Deploy

- [ ] Arquivos copiados para o servidor
- [ ] `app/main.py` atualizado com rota do agente
- [ ] Variáveis de ambiente configuradas
- [ ] Dependências instaladas
- [ ] Servidor reiniciado
- [ ] Health check funcionando
- [ ] Endpoint `/api/v1/agent/roles` funcionando
- [ ] Endpoint `/api/v1/agent/capabilities` funcionando
- [ ] Endpoint `/api/v1/process-message` funcionando
- [ ] Integração com Django testada
- [ ] Logs sendo gerados corretamente
- [ ] Documentação Swagger acessível

---

## 🎯 Próximos Passos

Após o deploy bem-sucedido:

1. **Monitorar Performance**: Acompanhe tempo de resposta e uso de recursos
2. **Adicionar Mais Agentes**: Implemente outros tipos de agentes (atendente, analista)
3. **Melhorar Detecção de Intenções**: Integre NLP mais avançado
4. **Adicionar Memória**: Implemente memória de conversa
5. **Métricas**: Configure métricas e alertas

---

## 📞 Suporte

Em caso de problemas:

1. Verifique os logs primeiro
2. Teste endpoints individualmente
3. Verifique configuração de rede
4. Consulte documentação do FastAPI: https://fastapi.tiangolo.com/

---

**Última atualização:** 2025-01-XX
**Versão:** 1.0.0

