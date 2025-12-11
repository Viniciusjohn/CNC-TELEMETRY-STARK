# Relatório de Visita e Estado do Piloto Stark v1

**Data:** 06/12/2025  
**Responsável:** Cascade AI (Engenheiro de Software Sênior)  
**Contexto:** Preparação para o Piloto na Stark (Fanuc 0i-TF Plus)

---

## 1. Resumo Executivo
Após a visita técnica e as correções de arquitetura (06/12), o projeto avançou significativamente em infraestrutura e contratos de dados.
**Em uma frase:** Demo e infra de rede estão sólidos; o gargalo agora é resolver o erro de conexão FOCAS (SocketException) e fechar o ciclo de dados real (Driver → Backend).

---

## 2. O que JÁ está Implantado (Status: Sólido)

### ✅ Narrativa e Escopo
*   **Piloto Definido:** PC Windows ao lado do torno FANUC 0i-TF Plus (IP 192.168.1.1).
*   **Objetivo:** Mostrar status (RUN/IDLE/ALARM) e gerar CSV com tempos reais de ciclo (Máquina + Operador).

### ✅ Stack e Organização
*   **Estrutura Unificada:** `C:\CNC-TELEMETRY\` contendo Backend/UI (`app`) e Driver (`fanuc-driver`) separados, mas prontos para orquestração única.

### ✅ Modos de Operação (Lab vs Field)
*   **LAB:** Simulação completa (`LabSimulatedDataSource`) com dados fake para validação de UI.
*   **FIELD:** Fonte real (`FanucMqttDataSource`). Se sem dados → UI mostra "OFFLINE" (sem números falsos).

### ✅ Infraestrutura de Rede (Validada em Campo)
*   **CNC:** Fanuc 0i-TF Plus configurado (IP 192.168.1.1, Porta 8193, FOCAS2 ativo).
*   **Conectividade:** `ping` OK, `Test-NetConnection -Port 8193` OK. A rede física funciona.

### ✅ Arquitetura de Software (Correções 06/12)
*   **Ingestão MQTT:** Backend refatorado para ler JSON estruturado do driver via `FanucAdapter`.
*   **Contrato Canônico:** `TelemetrySample` implementado em todo o stack (Backend/Frontend).
*   **Configuração Única:** Backend lê configuração de máquinas diretamente do YAML do driver (SSOT).

---

## 3. O que AINDA NÃO está Funcionando (Gargalos)

### 🔴 Conexão FOCAS Real (Erro Crítico)
*   **Sintoma:** O driver Ladder99 conecta na porta 8193, mas falha ao iniciar a coleta com `SocketException` ou erro de sweep.
*   **Hipóteses:** Bloqueio de firewall no Windows, licença FOCAS na máquina faltando, ou incompatibilidade da DLL FOCAS (`fwlib32.dll`) com o Windows/CNC atual.

### 🟠 CycleTracker com Dados Reais
*   **Status:** A lógica de `CycleTracker` existe, mas só foi testada com dados simulados.
*   **Falta:** Validar se a transição de estados (RUN -> IDLE) e o incremento de `part_count` vindos do driver real disparam corretamente o cálculo de tempos no backend.

### 🟡 Pacote de Deploy "One-Click"
*   **Status:** Scripts existem (`start_lab.bat`), mas falta um `start_stark.ps1` unificado que suba Broker + Driver + Backend + Frontend e verifique a saúde do sistema automaticamente.

---

## 4. Próximos Passos (Plano de Ação Imediato)

A prioridade absoluta é **fazer o driver falar com a CNC**. Sem isso, o resto é apenas "demo bonita".

1.  **Debug FOCAS (P&D):**
    *   Isolar o teste do driver (usar ferramenta de teste FOCAS da Fanuc se disponível, ou script minimalista C#).
    *   Verificar Firewall do Windows (Porta 8193 TCP/UDP).
    *   Confirmar versão da `fwlib32.dll` no driver.

2.  **Validação de Fluxo de Dados:**
    *   Assim que o driver conectar, verificar se o JSON chega no MQTT.
    *   Verificar logs do Backend (`smoke_test_ingestion.py` já validou a lógica, agora é testar com o driver real).

3.  **Pacote de Deploy:**
    *   Criar `start_stark.ps1` para facilitar a operação pelo pessoal da fábrica.

---

**Conclusão:** A base de código está pronta e saneada. O foco agora muda de "Engenharia de Software" para "Integração de Sistemas e Redes" para resolver a conexão física com a CNC.
