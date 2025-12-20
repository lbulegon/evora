# Agente Ágnosto - Guia Rápido

## 🚀 Deploy Rápido

```bash
# 1. Conectar ao servidor
ssh root@69.169.102.84

# 2. Ir para o diretório
cd /opt/openmind-ai

# 3. Executar script de deploy
./SCRIPT_DEPLOY_AGENTE.sh

# 4. Verificar se está funcionando
./VERIFICAR_AGENTE.sh
```

## 📋 Checklist Rápido

- [ ] Arquivos `agnostic_agent.py` e `agent.py` estão no servidor
- [ ] `app/main.py` inclui a rota do agente
- [ ] Variável `OPENMIND_AI_API_KEY` configurada no `.env`
- [ ] Servidor reiniciado
- [ ] Endpoints testados e funcionando

## 🔗 Endpoints Principais

- `POST /api/v1/process-message` - Processar mensagem do WhatsApp
- `GET /api/v1/agent/roles` - Listar papéis disponíveis
- `GET /api/v1/agent/capabilities?role=vendedor` - Listar capacidades

## 📖 Documentação Completa

Veja `DEPLOY_AGENTE_AGNOSTO.md` para documentação detalhada.

## 🧪 Teste Rápido

```bash
curl -X GET "http://localhost:8000/api/v1/agent/roles" \
  -H "Authorization: Bearer sua-chave-api"
```

## ⚠️ Importante

- Toda a lógica de IA está no SinapUm
- Django apenas faz chamadas HTTP
- Se SinapUm não estiver disponível, Django retorna erro

