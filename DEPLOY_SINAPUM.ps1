# Script de Deploy Automatizado para SinapUm (PowerShell)
# Atualiza o código do OpenMind AI Server no servidor SinapUm

param(
    [string]$ServerIP = "69.169.102.84",
    [string]$ServerUser = "root",
    [string]$ServerPath = "/opt/openmind-ai"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Deploy do OpenMind AI Server para SinapUm" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""

# Verificar se estamos no diretório correto
if (-not (Test-Path "openmind-ai-server")) {
    Write-Host "❌ Erro: Execute este script da raiz do projeto (onde está a pasta openmind-ai-server)" -ForegroundColor Red
    exit 1
}

Write-Host "📁 Verificando arquivos..." -ForegroundColor Yellow

# Verificar se arquivos essenciais existem
$requiredFiles = @(
    "openmind-ai-server/app",
    "openmind-ai-server/requirements.txt",
    "openmind-ai-server/promtail-config.yml"
)

foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "❌ Erro: Arquivo não encontrado: $file" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✅ Arquivos encontrados" -ForegroundColor Green
Write-Host ""

# Perguntar confirmação
Write-Host "Servidor: $ServerUser@$ServerIP" -ForegroundColor Cyan
Write-Host "Diretório: $ServerPath" -ForegroundColor Cyan
Write-Host ""
$confirm = Read-Host "Deseja continuar? (S/N)"

if ($confirm -ne "S" -and $confirm -ne "s") {
    Write-Host "❌ Deploy cancelado" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "📤 Copiando arquivos para o servidor..." -ForegroundColor Yellow

try {
    # Copiar pasta app
    Write-Host "  - Copiando pasta app..." -ForegroundColor Gray
    scp -r "openmind-ai-server/app" "${ServerUser}@${ServerIP}:${ServerPath}/" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Erro ao copiar pasta app"
    }
    
    # Copiar requirements.txt
    Write-Host "  - Copiando requirements.txt..." -ForegroundColor Gray
    scp "openmind-ai-server/requirements.txt" "${ServerUser}@${ServerIP}:${ServerPath}/" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Erro ao copiar requirements.txt"
    }
    
    # Copiar promtail-config.yml
    Write-Host "  - Copiando promtail-config.yml..." -ForegroundColor Gray
    scp "openmind-ai-server/promtail-config.yml" "${ServerUser}@${ServerIP}:${ServerPath}/" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ⚠️  Aviso: Erro ao copiar promtail-config.yml (pode não existir ainda)" -ForegroundColor Yellow
    }
    
    Write-Host "✅ Arquivos copiados com sucesso!" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "🔧 Executando comandos no servidor..." -ForegroundColor Yellow
    
    # Comandos para executar no servidor
    $commands = @"
cd $ServerPath
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
mkdir -p /var/log/openmind-ai
chmod 755 /var/log/openmind-ai
systemctl restart openmind-ai
sleep 2
systemctl status openmind-ai --no-pager -l | head -20
"@
    
    # Executar comandos via SSH
    ssh "${ServerUser}@${ServerIP}" $commands
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Deploy concluído com sucesso!" -ForegroundColor Green
        Write-Host ""
        Write-Host "🧪 Testando servidor..." -ForegroundColor Yellow
        
        # Testar health check
        Start-Sleep -Seconds 3
        $healthCheck = Invoke-WebRequest -Uri "http://${ServerIP}:8000/health" -UseBasicParsing -ErrorAction SilentlyContinue
        
        if ($healthCheck.StatusCode -eq 200) {
            Write-Host "✅ Servidor respondendo corretamente!" -ForegroundColor Green
            Write-Host ""
            Write-Host "📊 Próximos passos:" -ForegroundColor Cyan
            Write-Host "   1. Verificar logs: ssh ${ServerUser}@${ServerIP} 'tail -f ${ServerPath}/../logs/app.log'"
            Write-Host "   2. Testar análise: python test_openmind_server.py"
            Write-Host "   3. Configurar Grafana: Ver GRAFANA_SETUP.md"
        } else {
            Write-Host "⚠️  Servidor pode não estar respondendo. Verifique os logs." -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️  Comandos executados, mas pode haver erros. Verifique os logs." -ForegroundColor Yellow
    }
    
} catch {
    Write-Host ""
    Write-Host "❌ Erro durante o deploy: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Dicas:" -ForegroundColor Yellow
    Write-Host "   - Verifique se tem acesso SSH ao servidor"
    Write-Host "   - Verifique se a senha está correta"
    Write-Host "   - Execute manualmente os passos do DEPLOY_ATUALIZACAO_SINAPUM.md"
    exit 1
}

Write-Host ""
Write-Host "🎉 Deploy finalizado!" -ForegroundColor Green



