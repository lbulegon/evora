# Configuração do Grafana/Loki para OpenMind AI Server

Este guia explica como configurar o sistema de logging estruturado do OpenMind AI Server para visualização no Grafana.

## 📋 Pré-requisitos

- Grafana instalado no servidor SinapUm
- Loki instalado (se não estiver, veja instruções abaixo)
- Promtail instalado (se não estiver, veja instruções abaixo)

## 🔧 Instalação dos Componentes

### 1. Instalar Loki

```bash
# Download do Loki
wget https://github.com/grafana/loki/releases/download/v2.9.2/loki-linux-amd64.zip
unzip loki-linux-amd64.zip
sudo mv loki-linux-amd64 /usr/local/bin/loki
sudo chmod +x /usr/local/bin/loki

# Criar diretório de configuração
sudo mkdir -p /etc/loki
sudo mkdir -p /var/lib/loki

# Criar arquivo de configuração do Loki
sudo nano /etc/loki/loki-config.yml
```

Conteúdo do `loki-config.yml`:
```yaml
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

common:
  instance_addr: 127.0.0.1
  path_prefix: /var/lib/loki
  storage:
    filesystem:
      chunks_directory: /var/lib/loki/chunks
      rules_directory: /var/lib/loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2024-01-01
      store: tsdb
      object_store: filesystem
      schema: v13
      index:
        prefix: index_
        period: 24h

ruler:
  alertmanager_url: http://localhost:9093
```

### 2. Instalar Promtail

```bash
# Download do Promtail
wget https://github.com/grafana/loki/releases/download/v2.9.2/promtail-linux-amd64.zip
unzip promtail-linux-amd64.zip
sudo mv promtail-linux-amd64 /usr/local/bin/promtail
sudo chmod +x /usr/local/bin/promtail

# Criar diretório de configuração
sudo mkdir -p /etc/promtail

# Copiar arquivo de configuração do projeto
sudo cp /opt/openmind-ai/promtail-config.yml /etc/promtail/promtail-config.yml
```

### 3. Criar serviços systemd

#### Serviço do Loki

```bash
sudo nano /etc/systemd/system/loki.service
```

```ini
[Unit]
Description=Loki service
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/loki -config.file /etc/loki/loki-config.yml
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

#### Serviço do Promtail

```bash
sudo nano /etc/systemd/system/promtail.service
```

```ini
[Unit]
Description=Promtail service
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/promtail -config.file /etc/promtail/promtail-config.yml
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### 4. Iniciar serviços

```bash
sudo systemctl daemon-reload
sudo systemctl enable loki promtail
sudo systemctl start loki promtail
sudo systemctl status loki promtail
```

## 📊 Configurar Grafana

### 1. Adicionar Loki como Data Source

1. Acesse o Grafana (geralmente em `http://seu-servidor:3000`)
2. Vá em **Configuration > Data Sources**
3. Clique em **Add data source**
4. Selecione **Loki**
5. Configure:
   - **URL**: `http://localhost:3100`
   - Clique em **Save & Test**

### 2. Criar Dashboards

#### Dashboard Básico de Logs

Use estas queries no Grafana:

**Últimos Logs (Stream):**
```logql
{job="openmind-ai"} | json
```

**Logs de Erros:**
```logql
{job="openmind-ai", log_type="error"} | json
```

**Requests por Endpoint:**
```logql
sum by (endpoint) (count_over_time({job="openmind-ai", log_type="access"}[5m]))
```

**Tempo de Processamento Médio:**
```logql
avg_over_time({job="openmind-ai", log_type="analysis"} | json | unwrap processing_time_ms [5m])
```

**Análises por API Provider:**
```logql
sum by (api_provider) (count_over_time({job="openmind-ai", log_type="analysis"} | json [5m]))
```

**Taxa de Sucesso:**
```logql
sum by (success) (count_over_time({job="openmind-ai", log_type="analysis"} | json [5m]))
```

**Status Codes HTTP:**
```logql
sum by (status_code) (count_over_time({job="openmind-ai", log_type="access"}[5m]))
```

## 🔍 Queries Úteis

### Filtrar por Request ID
```logql
{job="openmind-ai"} | json | request_id="<request-id>"
```

### Logs de uma análise específica
```logql
{job="openmind-ai", log_type="analysis"} | json | image_filename=~".*\.jpg$"
```

### Erros nos últimos 30 minutos
```logql
{job="openmind-ai", log_type="error"} | json | timestamp > now() - 30m
```

### Análises mais lentas
```logql
{job="openmind-ai", log_type="analysis"} | json | processing_time_ms > 5000
```

## 📁 Estrutura de Logs

Os logs são salvos em `/var/log/openmind-ai/`:

- `app.log` - Logs gerais da aplicação
- `errors.log` - Apenas erros (ERROR e CRITICAL)
- `access.log` - Logs de requisições HTTP
- `analysis.log` - Logs de análise de imagens
- `metrics.log` - Logs de métricas

## 🔐 Permissões

Certifique-se de que os diretórios têm as permissões corretas:

```bash
sudo chown -R root:root /var/log/openmind-ai
sudo chmod -R 755 /var/log/openmind-ai
```

## ✅ Verificação

Teste se tudo está funcionando:

```bash
# Verificar se o Loki está rodando
curl http://localhost:3100/ready

# Verificar se o Promtail está rodando
curl http://localhost:9080/ready

# Verificar logs do OpenMind AI
tail -f /var/log/openmind-ai/app.log

# Verificar logs do Promtail
sudo journalctl -u promtail -f

# Verificar logs do Loki
sudo journalctl -u loki -f
```

## 🎨 Dashboard de Exemplo

Você pode importar este dashboard JSON no Grafana para visualizar todos os logs estruturados do OpenMind AI Server.

```json
{
  "dashboard": {
    "title": "OpenMind AI Server - Logs",
    "panels": [
      {
        "title": "Últimos Logs",
        "targets": [
          {
            "expr": "{job=\"openmind-ai\"} | json"
          }
        ]
      },
      {
        "title": "Erros",
        "targets": [
          {
            "expr": "{job=\"openmind-ai\", log_type=\"error\"} | json"
          }
        ]
      },
      {
        "title": "Taxa de Requisições",
        "targets": [
          {
            "expr": "rate({job=\"openmind-ai\", log_type=\"access\"}[5m])"
          }
        ]
      }
    ]
  }
}
```

## 🐛 Troubleshooting

### Promtail não está coletando logs

1. Verifique se o arquivo de log existe: `ls -la /var/log/openmind-ai/`
2. Verifique permissões: `sudo chmod 644 /var/log/openmind-ai/*.log`
3. Verifique configuração do Promtail: `sudo promtail -config.file /etc/promtail/promtail-config.yml -dry-run`

### Loki não está recebendo logs

1. Verifique se o Loki está rodando: `sudo systemctl status loki`
2. Verifique conectividade: `curl http://localhost:3100/ready`
3. Verifique logs do Loki: `sudo journalctl -u loki -f`

### Grafana não mostra dados

1. Verifique se o data source está configurado corretamente
2. Teste a conexão no Grafana: **Data Sources > Loki > Save & Test**
3. Verifique se há dados no Loki: `curl http://localhost:3100/loki/api/v1/query_range`



