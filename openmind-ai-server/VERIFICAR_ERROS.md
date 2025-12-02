# 🔧 Verificação e Correção de Erros

## Problemas Identificados

1. ❌ **Erro no requirements.txt:** `python-cors==1.0.0` não existe
2. ❌ **Serviço não está respondendo:** Preciso verificar logs

---

## ✅ Correções Necessárias

### 1. Corrigir requirements.txt

O pacote `python-cors` não existe. O CORS já vem integrado no FastAPI.

**Já corrigido no arquivo requirements.txt**

### 2. Verificar se os arquivos foram transferidos

No servidor, execute:

```bash
ls -la /opt/openmind-ai/
ls -la /opt/openmind-ai/app/
```

### 3. Verificar logs do serviço

```bash
journalctl -u openmind-ai -n 50 --no-pager
systemctl status openmind-ai
```

### 4. Se os arquivos não foram transferidos

**No seu computador (PowerShell):**
```powershell
cd C:\Users\lbule\OneDrive\Documentos\Source\evora
scp -r openmind-ai-server/* root@69.169.102.84:/opt/openmind-ai/
```

### 5. Reinstalar dependências (depois de corrigir requirements.txt)

No servidor:
```bash
cd /opt/openmind-ai
source venv/bin/activate
pip install -r requirements.txt
```

### 6. Reiniciar serviço

```bash
systemctl restart openmind-ai
systemctl status openmind-ai
curl http://localhost:8000/health
```

---

## 🔍 Comandos de Diagnóstico

Execute estes comandos no servidor para ver o que está acontecendo:

```bash
# Ver logs do serviço
journalctl -u openmind-ai -n 100 --no-pager

# Ver status detalhado
systemctl status openmind-ai

# Ver se os arquivos existem
ls -la /opt/openmind-ai/app/

# Testar manualmente
cd /opt/openmind-ai
source venv/bin/activate
python3 -c "from app.main import app; print('OK')"

# Verificar porta
netstat -tlnp | grep 8000
```
