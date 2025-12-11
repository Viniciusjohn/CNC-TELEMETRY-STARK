# Script de Coleta de CSV - STARK Telemetry
# Uso: ./exportar_stark_csv.ps1

$ErrorActionPreference = "Stop"

# Configuração
$BackendUrl = "http://localhost:8000"
$Endpoint = "/demo/export"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmm"
$OutputDir = ".\dados_coletados"
$OutputFile = "$OutputDir\stark_telemetry_$Timestamp.csv"

# Verifica se o backend está rodando
Write-Host "Conectando ao Backend STARK em $BackendUrl..." -ForegroundColor Cyan

try {
    $response = Invoke-WebRequest -Uri "$BackendUrl/healthz" -UseBasicParsing -TimeoutSec 5
    Write-Host "[OK] Backend Online ($($response.Content))" -ForegroundColor Green
}
catch {
    Write-Host "[ERRO] Backend não respondeu. Verifique se o sistema está rodando." -ForegroundColor Red
    exit 1
}

# Cria diretório se não existir
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

# Baixa o CSV
Write-Host "Baixando histórico de produção..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri "$BackendUrl$Endpoint" -OutFile $OutputFile
    
    # Verifica se o arquivo tem conteúdo
    if ((Get-Item $OutputFile).Length -gt 0) {
        Write-Host "[SUCESSO] Dados salvos em: $OutputFile" -ForegroundColor Green
        # Mostra as primeiras linhas
        Get-Content $OutputFile -TotalCount 5
    }
    else {
        Write-Host "[AVISO] Arquivo gerado está vazio. Verifique se há dados no banco." -ForegroundColor Yellow
    }
}
catch {
    Write-Host "[ERRO] Falha ao baixar CSV: $_" -ForegroundColor Red
    exit 1
}
