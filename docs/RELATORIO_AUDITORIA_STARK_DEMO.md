# Relatório de Auditoria Forense: Piloto STARK e Estratégia DEMO

**Data:** 11/12/2025
**Projeto:** CNC-TELEMETRY
**Contexto:** Auditoria técnica para validação do piloto em máquina real e alinhamento do ambiente de demonstração.

## 1. Resumo Executivo
O sistema CNC-Telemetry opera em produção utilizando **eventos reais** oriundos do chão de fábrica, sem geradores de dados simulados ("fakers") no código de backend. A arquitetura validada é:
`Ladder99 (Driver) → MQTT → FastAPI (Backend) → SQLite (Persistência) → UI (Frontend)`

O ambiente **DEMO** foi reestruturado para ser um espelho fiel do ambiente de campo (STARK), diferenciando-se apenas pelo endereçamento de rede (Localhost vs. IP Real), garantindo que a demonstração técnica reflita exatamente a capacidade do produto final.

## 2. Configuração de Campo (STARK)
A "Single Source of Truth" para configuração de máquinas é o driver Ladder99. O backend lê dinamicamente este arquivo.

**Arquivo:** `fanuc-driver/config.machines.yml`

| Machine ID | IP (Campo) | Porta | Coletores Ativos |
| :--- | :--- | :--- | :--- |
| **STARK_TORNO_PILOTO** | `192.168.1.1` | 8193 | `StateData`, `ProductionData`, `SpindleData`, `Alarms` |
| **STARK_TORNO_02** | `192.168.1.2` | 8193 | (Idem) |
| **STARK_CENTRO_01** | `192.168.1.3` | 8193 | (Idem) |

## 3. Fluxo de Dados e Mapeamento

### 3.1 Pipeline de Ingestão
O backend (`FanucMqttDataSource`) assina o tópico `fanuc/#` e processa mensagens via `FanucAdapter`.

| Tópico MQTT | Dado Bruto (Ladder99) | Dado Normalizado (Telemetry) | Aplicação |
| :--- | :--- | :--- | :--- |
| `fanuc/{id}/state` | `execution: RUN/IDLE` | `state` | Cálculo de OEE e Status UI |
| `fanuc/{id}/production` | `pieces.produced` | `part_count` | Detecção de Ciclos e Contagem |
| `fanuc/{id}/spindle` | `speed` | `spindle_speed` | Gauge de RPM em Tempo Real |
| `fanuc/{id}/alarms` | `active: true` | `alarms` | Bloqueio de Estado / Log de Erro |

### 3.2 Persistência e Rastreabilidade
A lógica de negócio reside em `CycleTracker` e persiste em SQLite (`telemetry.db`).

*   **Eventos (`Event`):** Gravados a cada mudança de estado (ex: RUN -> IDLE).
*   **Ciclos (`Cycle`):** Gravados a cada incremento de `part_count`.
    *   `duration_s`: Calculado via `now - last_piece_timestamp`.
    *   `program`: Rastreia qual programa CNC gerou a peça.

## 4. Estratégia DEMO (Espelho de Campo)
Para garantir simetria entre DEV e PROD:

1.  **Configuração Espelho:** `fanuc-driver/config.machines.demo.yml`
    *   Cópia exata da estrutura de campo.
    *   IPs alterados para `127.0.0.1` (Simulador Local).
2.  **Seleção de Ambiente:** Variável `TELEMETRY_ENV` em `app/backend/config.py`.
    *   `TELEMETRY_ENV=lab` → Carrega `config.machines.demo.yml`.
    *   `TELEMETRY_ENV=field` (ou nulo) → Carrega `config.machines.yml`.

## 5. Validação (Smoke Tests)

### Teste A: Modo DEMO
1.  Setar `$env:TELEMETRY_ENV = "lab"`.
2.  Iniciar Backend.
3.  Verificar Log: Deve carregar `config.machines.demo.yml`.
4.  Subir Simulador com ID `STARK_TORNO_PILOTO`.
5.  **Resultado:** UI exibe dados fluindo, CSV exporta dados do simulador.

### Teste B: Modo CAMPO
1.  Setar `$env:TELEMETRY_ENV = "field"`.
2.  Iniciar Backend.
3.  Verificar Log: Deve carregar `config.machines.yml`.
4.  **Resultado:** Backend tenta conexão com `192.168.1.1` (Timeout esperado se fora da fábrica).

---
*Este documento serve como evidência técnica da arquitetura do piloto STARK.*
