# Script para limpar o banco de dados do STARK Telemetry
# Uso: right-click -> Run with PowerShell

Write-Host "=== RESETANDO DADOS DO STARK TELEMETRY ===" -ForegroundColor Cyan
Write-Host "ATENCAO: Isso apagara TODO o historico de producao e eventos." -ForegroundColor Red
$confirmation = Read-Host "Digite 'RESET' para confirmar a limpeza"

if ($confirmation -eq "RESET") {
    # Para o Backend se estiver rodando (para liberar o arquivo .db)
    Write-Host "Parando processos Python..." -ForegroundColor Yellow
    Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -like "*uvicorn*"} | Stop-Process -Force
    
    $dbPath = ".\telemetry.db"
    if (Test-Path $dbPath) {
        Remove-Item $dbPath -Force
        Write-Host "Banco de dados apagado com sucesso." -ForegroundColor Green
        Write-Host "O arquivo sera recriado limpo na proxima inicializacao do sistema."
    } else {
        Write-Host "Arquivo telemetry.db nao encontrado (ja estava limpo?)." -ForegroundColor Yellow
    }
} else {
    Write-Host "Operacao cancelada." -ForegroundColor Yellow
}

Read-Host "Pressione ENTER para sair..."
