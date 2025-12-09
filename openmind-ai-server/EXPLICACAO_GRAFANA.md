# 🔍 Explicação: Grafana e Sistema de Logging

## 📍 Onde está cada coisa?

### **No Servidor SinapUm** (69.169.102.84):
- ✅ **Grafana** - Já instalado e rodando
- ❓ **Loki** - Precisa estar instalado (ou instalar)
- ❓ **Promtail** - Precisa estar instalado (ou instalar)
- ✅ **OpenMind AI Server** - Rodando em `/opt/openmind-ai`

### **No Projeto ÉVORA** (GitHub/local):
- ✅ **Código do OpenMind AI Server** - Gera logs estruturados
- ✅ **promtail-config.yml** - Configuração para copiar para SinapUm
- ✅ **GRAFANA_SETUP.md** - Instruções para configurar no SinapUm

---

## 🔄 Como funciona o fluxo:

```
┌─────────────────────────┐
│  OpenMind AI Server     │
│  (SinapUm:8000)         │
│                         │
│  logging_grafana.py     │──┐
│  Gera logs em JSON      │  │
│  Salva em:              │  │
│  /var/log/openmind-ai/  │  │
└─────────────────────────┘  │
                             │
                             │ Lê arquivos
                             │
┌─────────────────────────┐  │
│  Promtail               │◄─┘
│  (SinapUm)              │
│                         │
│  Lê:                    │
│  /var/log/openmind-ai/*.log│
│                         │
│  Envia para:            │──┐
└─────────────────────────┘  │
                             │
                             │ Recebe logs
                             │
┌─────────────────────────┐  │
│  Loki                   │◄─┘
│  (SinapUm:3100)         │
│                         │
│  Armazena logs          │
└─────────────────────────┘
          │
          │ Consulta logs
          │
┌─────────────────────────┐
│  Grafana                │
│  (SinapUm - já existe!) │
│                         │
│  Visualiza logs do Loki │
│  Dashboards, queries    │
└─────────────────────────┘
```

---

## 📦 O que está no Projeto ÉVORA?

### Arquivos que fazem parte do código:
- `app/core/logging_grafana.py` - Sistema de logging (vai para SinapUm com o deploy)
- `app/main.py` - Integra o sistema de logging
- `app/core/config.py` - Configurações de logging

**Estes arquivos precisam ser deployados no SinapUm** (fazem parte do servidor OpenMind AI)

### Arquivos de configuração/documentação:
- `promtail-config.yml` - Configuração do Promtail
  - **Precisa ser copiado para**: `/etc/promtail/promtail-config.yml` no SinapUm
  
- `GRAFANA_SETUP.md` - Documentação
  - **Instruções para configurar no SinapUm** (não precisa estar no servidor)

---

## ✅ O que fazer agora?

### 1. **Deploy do código no SinapUm** (Opção 1 do deploy)
Isso atualiza o OpenMind AI Server para gerar logs estruturados:
- Copiar `app/` para `/opt/openmind-ai/app/`
- O servidor passa a gerar logs em `/var/log/openmind-ai/`

### 2. **Configurar Promtail no SinapUm** (se ainda não estiver)
- Copiar `promtail-config.yml` para `/etc/promtail/promtail-config.yml`
- Instalar e iniciar Promtail
- Ver `GRAFANA_SETUP.md` para instruções detalhadas

### 3. **Configurar Loki no SinapUm** (se ainda não estiver)
- Instalar Loki
- Configurar Loki
- Ver `GRAFANA_SETUP.md` para instruções detalhadas

### 4. **Configurar Grafana no SinapUm** (se ainda não estiver configurado)
- Adicionar Loki como data source no Grafana
- Criar dashboards para visualizar logs
- Ver `GRAFANA_SETUP.md` para instruções detalhadas

---

## 🎯 Resumo:

- **Código no ÉVORA** → Deploy para SinapUm → Servidor gera logs
- **Config no ÉVORA** → Copiar para SinapUm → Promtail lê logs
- **Grafana no SinapUm** → Já existe → Só precisa configurar data source

**O Grafana está no SinapUm, não no projeto ÉVORA!** ✅

Os arquivos no projeto ÉVORA são apenas:
1. Código fonte do servidor (que gera logs)
2. Configurações para copiar ao SinapUm
3. Documentação de como configurar

