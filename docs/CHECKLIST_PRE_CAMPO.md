# Checklist Pré-Campo: Piloto STARK

Este documento lista os requisitos e verificações necessários antes de implantar ou atualizar o sistema na máquina real (STARK).

## Documentação de Referência
*   **[RELATORIO_AUDITORIA_STARK_DEMO.md](./RELATORIO_AUDITORIA_STARK_DEMO.md)**: Detalhes da arquitetura, mapeamento de dados e estratégia de configuração.
*   **[SIMULADOR_FANUC_MQTT.md](./SIMULADOR_FANUC_MQTT.md)**: Guia para rodar o simulador em modo compatível.

## Verificações de Configuração

### 1. Configuração do Driver (Ladder99)
- [ ] Verificar arquivo `fanuc-driver/config.machines.yml`.
- [ ] Confirmar IPs das máquinas STARK (`192.168.1.X`).
- [ ] Confirmar porta FOCAS (`8193`).
- [ ] Confirmar firewall liberado para porta 8193 na rede da fábrica.

### 2. Ambiente de Execução
- [ ] Variável de ambiente `TELEMETRY_ENV` deve ser **"field"** (ou não definida).
- [ ] Verificar se o serviço MQTT (Mosquitto) está rodando na porta 1883.
- [ ] Validar conectividade com a CNC: `ping 192.168.1.1`.

### 3. Preparação (Host)
- [ ] Limpar processos antigos: `Get-Process ladder99, fanuc-driver -ErrorAction SilentlyContinue | Stop-Process -Force`
- [ ] **Limpar Dados Antigos:** Rodar `reset_stark_data.ps1` (digitar RESET) para apagar histórico de testes.
- [ ] Verificar IP da máquina host: `ipconfig` (Deve estar na mesma subnet da CNC).
- [ ] Sincronizar relógio do Windows com servidor NTP (importante para logs).

### 4. Validação de Dados (Smoke Test)
- [ ] Iniciar sistema: `start_stark.ps1`.
- [ ] Verificar logs do Backend para confirmar carregamento de `config.machines.yml`.
- [ ] Verificar logs do Driver para confirmar conexão "FOCAS Success".
- [ ] Verificar UI: Máquina deve sair do estado "OFFLINE".
- [ ] **Coleta de Evidência:** Rodar `exportar_stark_csv.ps1` e confirmar que o CSV tem dados.

## Rollback
Em caso de falha crítica na planta:
1. Parar serviços.
2. Reverter para branch `main` ou tag estável anterior.
3. Reportar logs de `fanuc-driver` para análise.
