# 🚀 Deploy de Atualização - OpenMind AI no SinapUm

Guia rápido para atualizar o código do servidor OpenMind AI no SinapUm com as novas funcionalidades (sistema de logging Grafana/Loki).

---

## 📋 Opções de Deploy

### **Opção 1: Via SCP (Recomendado - Mais Rápido)**

Atualiza apenas os arquivos que mudaram diretamente do seu computador.

#### No seu computador Windows (PowerShell):

```powershell
# 1. Navegar para a pasta do projeto
cd C:\Users\lbule\OneDrive\Documentos\Source\evora

# 2. Copiar arquivos atualizados para o servidor
scp -r openmind-ai-server/app root@69.169.102.84:/opt/openmind-ai/
scp openmind-ai-server/promtail-config.yml root@69.169.102.84:/opt/openmind-ai/
scp openmind-ai-server/requirements.txt root@69.169.102.84:/opt/openmind-ai/

# 3. Conectar ao servidor para finalizar
ssh root@69.169.102.84
```

#### No servidor SinapUm:

```bash
cd /opt/openmind-ai

# 1. Fazer backup do código atual (opcional mas recomendado)
cp -r app app.backup.$(date +%Y%m%d_%H%M%S)

# 2. Ativar ambiente virtual
source venv/bin/activate

# 3. Atualizar dependências (se necessário)
pip install --upgrade pip
pip install -r requirements.txt

# 4. Criar diretório de logs
mkdir -p /var/log/openmind-ai
chmod 755 /var/log/openmind-ai

# 5. Reiniciar serviço
systemctl restart openmind-ai

# 6. Verificar status
systemctl status openmind-ai
tail -f /var/log/openmind-ai/app.log
```

---

### **Opção 2: Via Git (Se você usa repositório)**

#### No servidor SinapUm:

```bash
cd /opt/openmind-ai

# 1. Parar serviço temporariamente
systemctl stop openmind-ai

# 2. Fazer backup
cp -r app app.backup.$(date +%Y%m%d_%H%M%S)

# 3. Atualizar código
git pull origin main  # ou sua branch

# 4. Ativar ambiente virtual
source venv/bin/activate

# 5. Atualizar dependências
pip install --upgrade pip
pip install -r requirements.txt

# 6. Criar diretório de logs
mkdir -p /var/log/openmind-ai
chmod 755 /var/log/openmind-ai

# 7. Reiniciar serviço
systemctl start openmind-ai
systemctl status openmind-ai
```

---

### **Opção 3: Atualização Manual (Copiar arquivos específicos)**

Para atualizar apenas os arquivos que mudaram:

#### No servidor SinapUm:

```bash
cd /opt/openmind-ai

# 1. Parar serviço
systemctl stop openmind-ai

# 2. Fazer backup
cp -r app app.backup.$(date +%Y%m%d_%H%M%S)

# 3. Ativar ambiente virtual
source venv/bin/activate

# 4. Criar/atualizar arquivos manualmente via nano ou vim
# (ou copiar via scp conforme Opção 1)
```

---

## 🔧 Arquivos que Foram Atualizados

Os seguintes arquivos foram modificados/criados e precisam ser atualizados:

### Novos Arquivos:
- ✅ `app/core/logging_grafana.py` - Sistema de logging estruturado
- ✅ `promtail-config.yml` - Configuração do Promtail para Grafana

### Arquivos Modificados:
- ✅ `app/main.py` - Adicionado middleware de logging e sistema Grafana
- ✅ `app/api/v1/endpoints/analyze.py` - Logs estruturados nas análises
- ✅ `app/core/image_analyzer.py` - Logs estruturados
- ✅ `app/core/config.py` - Novas configurações de logging
- ✅ `ENV_EXAMPLE.txt` - Novas variáveis de ambiente

---

## 📝 Checklist de Deploy

Execute estes passos na ordem:

- [ ] **1. Fazer backup do código atual**
  ```bash
  cp -r /opt/openmind-ai/app /opt/openmind-ai/app.backup.$(date +%Y%m%d_%H%M%S)
  ```

- [ ] **2. Transferir arquivos atualizados** (via SCP, Git ou manual)

- [ ] **3. Atualizar dependências Python**
  ```bash
  cd /opt/openmind-ai
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
  ```

- [ ] **4. Criar diretório de logs**
  ```bash
  mkdir -p /var/log/openmind-ai
  chmod 755 /var/log/openmind-ai
  ```

- [ ] **5. Verificar variáveis de ambiente** (se necessário adicionar novas)
  ```bash
  cd /opt/openmind-ai
  cat .env | grep LOG
  ```

  Se não existir, adicionar (opcional - já tem valores padrão):
  ```bash
  echo "LOG_FORMAT=json" >> .env
  echo "LOG_DIR=/var/log/openmind-ai" >> .env
  echo "LOKI_ENABLED=true" >> .env
  ```

- [ ] **6. Testar importações**
  ```bash
  cd /opt/openmind-ai
  source venv/bin/activate
  python3 -c "from app.main import app; print('✅ Importações OK')"
  ```

- [ ] **7. Reiniciar serviço**
  ```bash
  systemctl restart openmind-ai
  ```

- [ ] **8. Verificar status**
  ```bash
  systemctl status openmind-ai
  journalctl -u openmind-ai -n 50 --no-pager
  ```

- [ ] **9. Verificar logs**
  ```bash
  ls -la /var/log/openmind-ai/
  tail -f /var/log/openmind-ai/app.log
  ```

- [ ] **10. Testar servidor**
  ```bash
  curl http://localhost:8000/health
  ```

---

## 🐛 Troubleshooting

### Erro ao importar módulos

```bash
# Verificar se está no ambiente virtual
source venv/bin/activate
which python3  # Deve mostrar /opt/openmind-ai/venv/bin/python3

# Reinstalar dependências
pip install -r requirements.txt
```

### Serviço não inicia

```bash
# Ver logs detalhados
journalctl -u openmind-ai -n 100 --no-pager

# Verificar se há erros de sintaxe
cd /opt/openmind-ai
source venv/bin/activate
python3 -m app.main
```

### Erro de permissões nos logs

```bash
# Criar diretório e ajustar permissões
sudo mkdir -p /var/log/openmind-ai
sudo chown -R root:root /var/log/openmind-ai
sudo chmod -R 755 /var/log/openmind-ai
```

### Porta 8000 já em uso

```bash
# Verificar processo
lsof -i :8000

# Matar processo antigo (se necessário)
kill -9 <PID>

# Reiniciar serviço
systemctl restart openmind-ai
```

---

## ✅ Verificação Pós-Deploy

Execute estes testes para confirmar que tudo está funcionando:

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Verificar logs sendo gerados
ls -lh /var/log/openmind-ai/

# 3. Ver últimos logs
tail -20 /var/log/openmind-ai/app.log

# 4. Verificar formato JSON dos logs
tail -1 /var/log/openmind-ai/app.log | python3 -m json.tool

# 5. Teste completo (do seu computador)
python test_openmind_server.py
```

---

## 📊 Próximos Passos (Opcional)

Após o deploy bem-sucedido, você pode:

1. **Configurar Grafana/Loki** - Ver `GRAFANA_SETUP.md`
2. **Configurar Promtail** - Ver `GRAFANA_SETUP.md`
3. **Criar Dashboards** - Importar dashboard no Grafana

---

## 🆘 Rollback

Se algo der errado, você pode reverter:

```bash
cd /opt/openmind-ai

# Parar serviço
systemctl stop openmind-ai

# Restaurar backup
rm -rf app
mv app.backup.* app  # Use o backup mais recente

# Reiniciar serviço
systemctl start openmind-ai
```

---

**Pronto!** Seu servidor está atualizado com o novo sistema de logging! 🎉

