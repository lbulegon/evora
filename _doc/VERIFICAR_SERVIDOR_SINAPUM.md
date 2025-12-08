# ⚠️ Servidor SinapUm Não Acessível

## 🔍 Problema

O servidor em `http://69.169.102.84:8000` não está respondendo.

---

## ✅ Checklist para Verificar

### 1. Verificar se o Serviço Está Rodando

Conecte via SSH e verifique:

```bash
ssh root@69.169.102.84
systemctl status openmind-ai
```

**Esperado:** Status "active (running)"

### 2. Se o Serviço Não Estiver Rodando

```bash
# Verificar logs de erro
journalctl -u openmind-ai -n 50

# Tentar iniciar
systemctl start openmind-ai

# Verificar status novamente
systemctl status openmind-ai
```

### 3. Verificar se a Porta Está Aberta

```bash
# Verificar se a porta 8000 está escutando
netstat -tlnp | grep 8000
# ou
ss -tlnp | grep 8000
```

**Esperado:** Porta 8000 escutando

### 4. Verificar Firewall

```bash
# Verificar regras do firewall
ufw status
# ou
iptables -L -n | grep 8000
```

Se necessário, abrir a porta:
```bash
ufw allow 8000/tcp
```

---

## 🧪 Testar Health Check Localmente no Servidor

```bash
# No servidor SinapUm
curl http://localhost:8000/health
```

**Esperado:** `{"status": "healthy", "service": "OpenMind AI Server"}`

---

## 🔧 Possíveis Soluções

### Problema: Serviço não inicia

**Verificar:**
1. Arquivo `.env` existe em `/opt/openmind-ai/`?
2. Variáveis configuradas corretamente?
3. Dependências instaladas?

**Solução:**
```bash
cd /opt/openmind-ai
cat .env  # Verificar variáveis
pip install -r requirements.txt  # Reinstalar dependências
systemctl restart openmind-ai
```

### Problema: Porta bloqueada

**Solução:**
```bash
# Verificar firewall
ufw allow 8000/tcp
```

---

## ✅ Próximos Passos

1. Conecte ao servidor SinapUm via SSH
2. Verifique o status do serviço
3. Verifique os logs de erro
4. Me informe o resultado!

**Vamos verificar juntos?** 🔍
