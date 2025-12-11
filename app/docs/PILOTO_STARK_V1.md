# PILOTO STARK TELEMETRY V1

> **Objetivo:** Validar a captura de dados de ciclo real (Homem + Máquina) em ambiente industrial, utilizando o Telemetry Stark.

## 1. Escopo do Piloto

*   **Data Alvo:** Até 14/12/2025.
*   **Duração:** 1 turno (ou janela de 4-6 horas contínuas).
*   **Máquina Alvo:** Torno CNC FANUC Series 0i-TF Plus (3 Eixos).
*   **Setup:**
    *   Notebook Windows rodando o sistema `CNC-TELEMETRY-STARK` localmente.
    *   Conexão de rede (cabo ethernet) com a máquina (se Plano A).
    *   Posicionamento ao lado do operador (para Plano B).

## 2. Estratégia de Medição

O sistema operará com redundância de métodos para garantir a coleta de dados:

### Plano Principal (B) - Manual / Garantido
*   **Método:** Operador ou responsável técnico pressiona um botão "Registrar Peça" na interface do Telemetry a cada ciclo concluído.
*   **Métrica:** `cycle_time_total_s` = tempo decorrido entre dois acionamentos do botão.
*   **Independência:** Não requer integração com CNC, licenças FOCAS ou configuração de rede complexa.

### Plano Bônus (A) - FOCAS / Automático
*   **Método:** Leitura automática via protocolo FANUC FOCAS 2 (Ethernet).
*   **Métrica:** Leitura direta dos timers internos (`cnc_rdtimer`) para Ciclo e Corte.
*   **Requisito:** Porta Ethernet habilitada e FOCAS disponível na CNC.

## 3. Entregáveis (Material Centelha)

Ao final do piloto, deve-se gerar:

1.  **Arquivo CSV Validado:** Contendo colunas para:
    *   Timestamp
    *   Estado (RUN/IDLE/ALARM)
    *   Tempo Ciclo Máquina (Estimado/Lido)
    *   Tempo Ciclo Total (Real/Homem+Máquina)
2.  **Relatório Fotográfico:**
    *   Tela do sistema rodando ao lado da máquina.
    *   Gráficos de produção do dia.
3.  **Métricas Chave:**
    *   Eficiência Real vs Teórica.
    *   Dissecção do tempo de ciclo (quanto foi máquina vs quanto foi manuseio).

## 4. Checklist de Sucesso (Gate)

- [ ] Sistema roda estável por 4h+ sem reiniciar.
- [ ] Operador entende e interage com o botão de registro sem erros.
- [ ] CSV gerado abre no Excel e reflete a realidade observada.
