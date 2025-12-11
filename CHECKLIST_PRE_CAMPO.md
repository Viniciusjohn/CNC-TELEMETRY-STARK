# Checklist de Prontidão - Piloto Stark (Pré-Campo)

**Objetivo:** Garantir que o Notebook está preparado para validar o FOCAS (Missão 1) e subir o sistema (Missão 2).

**Ação Imediata (Admin):**
Abra o PowerShell como Admin e rode:
`Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`
*(Isso evita que o Windows bloqueie o script start_stark.ps1 na hora H)*

---

## 🛑 FASE 1: MISSÃO CRÍTICA (FOCAS PROBE)
*Se esta fase falhar, a visita termina aqui. Prioridade total.*

### 1.1. Ambiente Python & DLL (O "Multímetro")
- [ ] **Visual C++ Redistributable (x64)**
    *   *Crítico:* Sem isso, a `Fwlib64.dll` falha silenciosamente ou dá erro genérico.
    *   *Link:* [vc_redist.x64.exe](https://aka.ms/vs/17/release/vc_redist.x64.exe)
- [ ] **Python 3.10+ (64-bit)**
    *   *Check:* `python -c "import struct; print(struct.calcsize('P') * 8)"` -> **DEVE retornar 64**.
    *   *Risco:* Se der 32, o probe não carrega a DLL 64-bit.
- [ ] **Arquivos Presentes:**
    *   `C:\CNC-TELEMETRY\fanuc-driver\Fwlib64.dll`
    *   `C:\CNC-TELEMETRY\app\scripts\probe_focas.py`

### 1.2. Ensaio de Probe (Rodar em Casa)
No PowerShell: `python C:\CNC-TELEMETRY\app\scripts\probe_focas.py 127.0.0.1`

*   **Resultado Esperado (Sucesso no Ensaio):**
    *   `Python Architecture: 64bit`
    *   `Loading DLL: ...Fwlib64.dll`
    *   `Connection failed: EW_SOCKET` (ou `EW_HANDLE`)
    *   *Interpretação:* O ambiente está perfeito. Falhou porque não tem CNC em casa. Pode ir pro campo.
*   **Resultado Ruim (Corrigir AGORA):**
    *   `ImportError / OSError`: Falta VC++ ou DLL corrompida.
    *   `EW_DLL`: Erro de arquitetura (Python 32 vs DLL 64).

### 1.3. Rede (Configurar APENAS na Fábrica)
- [ ] **IP Fixo:** 192.168.1.100 / Máscara 255.255.255.0.
- [ ] **Ping:** `ping 192.168.1.1` (Deve responder).
- [ ] **Porta:** `Test-NetConnection 192.168.1.1 -Port 8193` (TcpTestSucceeded: True).

---

## 🚀 FASE 2: STACK COMPLETO (TELEMETRY)
*Só faz sentido se a Fase 1 passar.*

### 2.1. Dependências da Aplicação
- [ ] **Node.js (LTS)** (Para o painel React).
- [ ] **.NET Runtime 6.0+** (Para o driver Ladder99).
- [ ] **Mosquitto MQTT**
    *   *Check:* `Test-NetConnection localhost -Port 1883`.
    *   *Nota:* Se falhar, inicie o serviço "Mosquitto Broker".

### 2.2. Ensaio de Start (Rodar em Casa)
No PowerShell: `C:\CNC-TELEMETRY\start_stark.ps1`

*   **Resultado Esperado:**
    *   Scripts iniciam sem erro de "File not found".
    *   Janelas do Backend, Frontend e Driver abrem.
    *   *Interpretação:* O "canivete suíço" está afiado.

---

## 🧪 TESTE DE FUMAÇA AUTOMATIZADO
Copie e cole este bloco inteiro no PowerShell do notebook **AGORA**:

```powershell
Clear-Host
Write-Host "--- 1. CHECK PERMISSÃO ---" -ForegroundColor Cyan
Get-ExecutionPolicy

Write-Host "`n--- 2. CHECK AMBIENTE PYTHON (MISSÃO 1) ---" -ForegroundColor Cyan
python --version
python -c "import struct; print(f'Arquitetura Python: {struct.calcsize(''P'') * 8} bits')"
Write-Host "Testando Probe Local (esperado: EW_SOCKET)..."
python C:\CNC-TELEMETRY\app\scripts\probe_focas.py 127.0.0.1

Write-Host "`n--- 3. CHECK STACK (MISSÃO 2) ---" -ForegroundColor Cyan
node --version
dotnet --list-runtimes
$mqtt = Test-NetConnection localhost -Port 1883 -InformationLevel Quiet -WarningAction SilentlyContinue
Write-Host "MQTT Local (Mosquitto): $(if($mqtt){'OK'}else{'FALHA/PARADO'})" -ForegroundColor $(if($mqtt){'Green'}else{'Red'})

Write-Host "`n--- FIM DO CHECKLIST ---" -ForegroundColor Cyan
```

---

## 🛡️ FASE 3: INTEGRIDADE DE DADOS (GATE ANTI-MOCK)
*Garante que o sistema não está inventando dados.*

### 3.1. Teste "Sem Sinal, Sem Dados"
1. **Pare todos os processos** (Backend, Simulador).
2. Delete o banco para zerar (opcional): `rm telemetry.db`.
3. Inicie **apenas o Backend**: `python -m backend.main` (ou via `start_stark.ps1`).
4. Acesse: `http://localhost:8000/demo/export`.
   * **Esperado:** Arquivo CSV contendo "No data" ou apenas cabeçalho.
   * **Erro Crítico:** Se vierem linhas de dados sem o simulador/máquina, existe código "fake" ativo.

### 3.2. Teste "Com Sinal"
1. Inicie o **Simulador MQTT** (ou conecte na máquina real).
2. Aguarde 30 segundos para gerar ciclos.
3. Acesse: `http://localhost:8000/demo/export`.
   * **Esperado:** CSV com linhas recentes da máquina `STARK_TORNO_PILOTO` (Status RUN/IDLE/ALARM).

---

## 🎭 FASE 4: ENSAIOS FINAIS (EM CASA)
*Validação de fluxo completo antes de embarcar.*

### 4.1. Ensaio "Carga 3 Máquinas"
1. Configurar `sim_config.json` com 3 IDs (ex: `STARK_TORNO_PILOTO`, `STARK_TORNO_02`, `STARK_CENTRO_01`).
2. Subir pilha completa (Mosquitto + Backend + Simulador).
3. Deixar rodar por 15 min.
4. Baixar CSV: `http://localhost:8000/demo/export`.
   * **Check:** [ ] Linhas presentes para todas as 3 máquinas?
   * **Check:** [ ] Estados variando (RUN/IDLE/ALARM)?
   * **Check:** [ ] Timestamps coerentes (sem buracos gigantes)?

### 4.2. Ensaio "Reboot Cold-Start"
1. Derrube tudo (`taskkill` ou feche terminais).
2. Suba na ordem real: 
   1. Broker (Mosquitto).
   2. Backend (`start_stark.ps1`).
   3. Driver (no caso, Simulador).
3. Observe a UI:
   * **Check:** [ ] Backend sobe sem erro de import/DB.
   * **Check:** [ ] UI mostra máquinas "OFFLINE" ou "Aguardando".
   * **Check:** [ ] Assim que o Simulador entra, máquinas ficam "ONLINE" e dados fluem.

---

