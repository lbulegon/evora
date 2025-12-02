# 🚀 Quick Start - OpenMind AI Server

Guia rápido para iniciar o servidor OpenMind AI no SinapUm.

---

## ⚡ Início Rápido (5 minutos)

### 1. Transferir Arquivos para o Servidor

```bash
# No seu computador local (do diretório evora/)
scp -r openmind-ai-server/* root@69.169.102.84:/opt/openmind-ai/
```

### 2. No Servidor SinapUm

```bash
# Conectar
ssh root@69.169.102.84

# Ir para o diretório
cd /opt/openmind-ai

# Instalar Python e dependências do sistema
apt update && apt install -y python3 python3-pip python3-venv

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# Configurar .env
nano .env
# Cole o conteúdo do ENV_EXAMPLE.txt e configure:
# - OPENMIND_AI_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
# - OPENAI_API_KEY (se usar OpenAI como backend)

# Dar permissão ao script
chmod +x run.sh

# Iniciar servidor
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Testar

```bash
# Health check
curl http://localhost:8000/health

# Testar análise (precisa de uma imagem de produto)
curl -X POST http://localhost:8000/api/v1/analyze-product-image \
  -H "Authorization: Bearer SUA_API_KEY" \
  -F "image=@/caminho/para/imagem.jpg"
```

### 4. Configurar no ÉVORA

No arquivo `.env` do ÉVORA:
```bash
AI_SERVICE=openmind
OPENMIND_AI_URL=http://69.169.102.84:8000/api/v1
OPENMIND_AI_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
```

---

## ✅ Pronto!

O servidor OpenMind AI está rodando e pronto para receber requisições do ÉVORA!

**Documentação da API:** http://69.169.102.84:8000/docs

---

## 🔧 Próximos Passos (Opcional)

- [ ] Configurar como serviço systemd (ver DEPLOY_SINAPUM.md)
- [ ] Configurar Nginx como reverse proxy
- [ ] Configurar SSL/HTTPS
- [ ] Implementar modelo de IA próprio (substituir OpenAI)
