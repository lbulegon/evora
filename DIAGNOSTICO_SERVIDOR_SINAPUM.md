# 🔍 Diagnóstico Completo - Servidor SinapUm Não Acessível

## ⚠️ Problema

Não consegue conectar ao servidor `http://69.169.102.84:8000`

---

## 🔍 Checklist de Diagnóstico

### 1. Serviço Está Rodando?

```bash
ssh root@69.169.102.84
systemctl status openmind-ai
```

**Esperado:** `Active: active (running)`

**Se não estiver rodando:**
```bash
# Ver logs de erro
journalctl -u openmind-ai -n 50

# Tentar iniciar
systemctl start openmind-ai
```

---

### 2. Porta Está Escutando LOCALMENTE?

```bash
# No servidor SinapUm
netstat -tlnp | grep 8000
# ou
ss -tlnp | grep 8000
# ou
lsof -i :8000
```

**Esperado:** Ver algo como `0.0.0.0:8000` ou `*:8000`

**Se não estiver escutando:**
- Serviço não iniciou corretamente
- Verificar logs: `journalctl -u openmind-ai -n 50`

---

### 3. Health Check Local Funciona?

```bash
# No servidor SinapUm
curl http://localhost:8000/health
```

**Esperado:** `{"status": "healthy", "service": "OpenMind AI Server"}`

**Se não funcionar:**
- Problema no código/configuração do servidor
- Verificar logs e variáveis

---

### 4. Firewall Está Bloqueando?

```bash
# Verificar firewall
ufw status
# ou
iptables -L -n | grep 8000

# Se necessário, abrir porta
ufw allow 8000/tcp
# ou
iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
```

---

### 5. Servidor Escutando no IP Correto?

O servidor deve escutar em `0.0.0.0:8000` (todas as interfaces), não apenas `127.0.0.1:8000`

**Verificar no config.py:**
```python
OPENMIND_AI_HOST: str = "0.0.0.0"  # Deve ser 0.0.0.0, não 127.0.0.1
```

---

## 🔧 Correções Comuns

### Problema: Serviço não inicia

**Verificar:**
1. Arquivo `.env` existe e tem variáveis corretas
2. Sem variáveis extras causando erro do Pydantic
3. Dependências instaladas

**Solução:**
```bash
cd /opt/openmind-ai
cat .env  # Verificar variáveis
pip install -r requirements.txt  # Reinstalar dependências
systemctl restart openmind-ai
```

---

### Problema: Porta bloqueada no firewall

**Solução:**
```bash
ufw allow 8000/tcp
systemctl restart ufw  # Se necessário
```

---

### Problema: Servidor escutando apenas localhost

**Solução:**
- Verificar `OPENMIND_AI_HOST=0.0.0.0` no `.env` ou config.py
- Reiniciar serviço

---

## ✅ Comandos de Diagnóstico Completo

Execute estes comandos no servidor SinapUm:

```bash
ssh root@69.169.102.84

# 1. Status do serviço
systemctl status openmind-ai

# 2. Porta escutando
netstat -tlnp | grep 8000

# 3. Health check local
curl http://localhost:8000/health

# 4. Logs recentes
journalctl -u openmind-ai -n 30

# 5. Firewall
ufw status

# 6. Variáveis do .env
cd /opt/openmind-ai
cat .env
```

---

## 📋 Enviar Resultados

Execute os comandos acima e me envie os resultados para eu ajudar a identificar o problema específico!

**Vamos diagnosticar juntos?** 🔍
