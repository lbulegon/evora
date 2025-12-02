# 🚀 Executar Configuração no Servidor SinapUm

## Opção 1: Executar Script Automático (Recomendado)

### Do seu computador local:

```bash
# 1. Navegar até a pasta do projeto
cd C:\Users\lbule\OneDrive\Documentos\Source\evora

# 2. Executar o script via SSH
ssh root@69.169.102.84 'bash -s' < openmind-ai-server/CONFIGURAR_VARIAVEIS_AGORA.sh
```

O script irá:
- ✅ Fazer backup do .env atual
- ✅ Adicionar as variáveis necessárias
- ✅ Testar se as variáveis foram lidas corretamente
- ✅ Reiniciar o serviço
- ✅ Mostrar o status

---

## Opção 2: Configuração Manual

### Passo 1: Conectar ao Servidor

```bash
ssh root@69.169.102.84
```

### Passo 2: Ir para o Diretório

```bash
cd /opt/openmind-ai
```

### Passo 3: Fazer Backup

```bash
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
```

### Passo 4: Editar o Arquivo

```bash
nano .env
```

### Passo 5: Adicionar Estas Linhas

```bash
# Autenticação do próprio servidor
OPENMIND_AI_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1

# OpenMind.org - LLM principal (você já pagou!)
OPENMIND_ORG_API_KEY=om1_live_7d4102a1bf72cc497d7651beb6a98292764b1f77df947c82d086506038ea6b9921efb9d9833045d1
OPENMIND_ORG_BASE_URL=https://api.openmind.org/api/core/openai
OPENMIND_ORG_MODEL=qwen2.5-vl-72b-instruct
```

### Passo 6: Salvar

- `Ctrl + O` (salvar)
- `Enter` (confirmar)
- `Ctrl + X` (sair)

### Passo 7: Reiniciar o Serviço

```bash
systemctl restart openmind-ai
systemctl status openmind-ai
```

---

## ✅ Verificar se Funcionou

### 1. Verificar Variáveis

```bash
cd /opt/openmind-ai
python3 -c "from app.core.config import settings; print('API Key:', '✅' if settings.OPENMIND_ORG_API_KEY else '❌'); print('Base URL:', settings.OPENMIND_ORG_BASE_URL)"
```

### 2. Ver Logs

```bash
journalctl -u openmind-ai -f
```

### 3. Testar Análise

Faça upload de uma imagem no Railway. Agora deve retornar dados reais!

---

## 🎯 Resultado Esperado

**Antes (Fallback):**
```json
{
  "nome_produto": "Produto identificado",
  "categoria": "Não identificada",
  "descricao": "Análise de imagem em desenvolvimento"
}
```

**Depois (Dados Reais):**
```json
{
  "nome_produto": "Nome real do produto",
  "categoria": "Categoria real",
  "descricao": "Descrição detalhada baseada na imagem",
  "caracteristicas": {
    "marca": "Marca real",
    ...
  }
}
```

---

## 🆘 Problemas Comuns

### Variáveis não estão sendo lidas

```bash
# Verificar se o arquivo .env existe
ls -la /opt/openmind-ai/.env

# Verificar conteúdo
cat /opt/openmind-ai/.env | grep OPENMIND
```

### Serviço não inicia

```bash
# Ver logs de erro
journalctl -u openmind-ai -n 50 --no-pager

# Verificar se o Python consegue importar
cd /opt/openmind-ai
python3 -c "from app.core.config import settings; print(settings.OPENMIND_ORG_BASE_URL)"
```

### Serviço não usa o .env

```bash
# Verificar se o serviço está configurado para usar .env
systemctl cat openmind-ai | grep -i env
```

---

## 📞 Precisa de Ajuda?

Se algo não funcionar, compartilhe:
1. A saída do comando de verificação
2. Os logs do serviço
3. Qualquer mensagem de erro

