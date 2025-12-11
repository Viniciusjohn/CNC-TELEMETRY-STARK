# Start Stark Telemetry System (Pilot v1)
# Usage: right-click -> Run with PowerShell

Write-Host "=== INICIANDO PILOTO STARK TELEMETRY v1 ===" -ForegroundColor Cyan

# 1. Configurar Ambiente
$env:TELEMETRY_ENV = "field"
Write-Host "Modo: FIELD (Conexão Real)" -ForegroundColor Yellow

# 2. Verificar Broker MQTT
# Tenta conectar na porta 1883 local para ver se tem broker rodando
$broker = Test-NetConnection -ComputerName localhost -Port 1883 -WarningAction SilentlyContinue
if (-not $broker.TcpTestSucceeded) {
    Write-Host "[ERRO] Broker MQTT não encontrado na porta 1883." -ForegroundColor Red
    Write-Host "Por favor, inicie o serviço Mosquitto antes de rodar este script."
    Read-Host "Pressione ENTER para sair..."
    exit
}
Write-Host "[OK] Broker MQTT detectado." -ForegroundColor Green

# 3. Iniciar Backend (FastAPI)
Write-Host "Iniciando Backend..."
$backendProcess = Start-Process -FilePath "python" -ArgumentList "-m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload" -WorkingDirectory ".\app" -PassThru -NoNewWindow
Write-Host "[OK] Backend rodando (PID: $($backendProcess.Id))" -ForegroundColor Green

# 4. Iniciar Driver Fanuc
Write-Host "Iniciando Driver Fanuc (Ladder99)..."
# O driver é um executável .NET ou comando?
# Assumindo que foi compilado ou está disponível como l99.driver.fanuc.exe
$driverPath = ".\fanuc-driver\fanuc.exe" # Ajustado para o nome real do binário
if (Test-Path $driverPath) {
    $driverProcess = Start-Process -FilePath $driverPath -WorkingDirectory ".\fanuc-driver" -PassThru -NoNewWindow
    Write-Host "[OK] Driver rodando (PID: $($driverProcess.Id))" -ForegroundColor Green
}
else {
    Write-Host "[AVISO] Executável do driver não encontrado em $driverPath." -ForegroundColor Yellow
    Write-Host "Se estiver rodando via 'dotnet run', inicie manualmente em outra janela."
}

# 5. Iniciar Frontend
Write-Host "Iniciando Frontend..."
$frontendProcess = Start-Process -FilePath "npm.cmd" -ArgumentList "run dev" -WorkingDirectory ".\app" -PassThru -NoNewWindow
Write-Host "[OK] Frontend iniciado." -ForegroundColor Green

Write-Host "--- SISTEMA OPERACIONAL ---" -ForegroundColor Cyan
Write-Host "Backend API: http://localhost:8000/docs"
Write-Host "Frontend UI: http://localhost:5173"
Write-Host "Pressione Ctrl+C para encerrar todos os processos..."

try {
    while ($true) {
        Start-Sleep -Seconds 1
        if ($backendProcess.HasExited) { throw "Backend encerrou inesperadamente." }
    }
}
catch {
    Write-Host "Encerrando processos..." -ForegroundColor Yellow
    Stop-Process -Id $backendProcess.Id -ErrorAction SilentlyContinue
    if ($driverProcess) { Stop-Process -Id $driverProcess.Id -ErrorAction SilentlyContinue }
    Stop-Process -Id $frontendProcess.Id -ErrorAction SilentlyContinue
    Write-Host "Desligado."
}
