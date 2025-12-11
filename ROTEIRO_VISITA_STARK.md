# Roteiro de Visita - Piloto Stark

**Objetivo:** Provar que conseguimos extrair dados reais da máquina (via FOCAS), persistí-los e gerar inteligência básica (Histórico/CSV) em 1 turno.

---

## 🌅 Manhã: Setup & Conexão (O "Multímetro")

1.  **Chegada na Máquina:**
    *   Identificar porta Ethernet da Fanuc (PCMCIA ou Embedded).
    *   Conectar cabo de rede direto (Notebook <-> CNC).
    *   Configurar IP do Notebook: `192.168.1.100`.
    *   Ping: `ping 192.168.1.1`.

2.  **Validação FOCAS (Crítico):**
    *   Rodar: `python app/scripts/probe_focas.py 192.168.1.1`
    *   **Se der SUCESSO:** Respirar aliviado. A parte difícil acabou.
    *   **Se der ERRO:** Verificar Firewall, Cabo, IP, FOCAS Licenciado na CNC.

3.  **Subir Stack:**
    *   Iniciar Mosquitto.
    *   Iniciar Backend + Frontend (`start_stark.ps1`).
    *   Iniciar Driver (`l99.driver.fanuc.exe`).
    *   *Verificar Logs:* Driver deve mostrar "Connected to CNC" e "Connected to MQTT".

4.  **Primeiro Sinal:**
    *   Abrir Dashboard (`localhost:5173`).
    *   Card da `STARK_TORNO_PILOTO` deve sair de "OFFLINE" para "IDLE" ou "RUN".
    *   **Vitória 1:** "Estamos conectados. O sistema está lendo a máquina."

---

## ☀️ Tarde: Coleta de Dados (O "Silêncio")

1.  **Deixar Rodar:**
    *   Não fique mexendo. Deixe o operador trabalhar.
    *   O sistema vai gravar silenciosamente no `telemetry.db`.
    *   Monitore apenas se o Driver não cai (led verde no terminal).

2.  **Validar Integridade (Meio do Turno):**
    *   Baixe um CSV rápido (`/demo/export`).
    *   Confira se tem linhas novas.
    *   Confira se os estados batem com o que você viu a máquina fazer (ex: parou para almoço -> IDLE).

---

## 🌇 Fim do Dia: A Entrega de Valor

1.  **Exportar Ouro:**
    *   Baixe o CSV final do turno.
    *   Baixe os JSONs brutos (`/v1/history/events`).

2.  **O "Show" (Resumo para Gestão):**
    *   Abra o CSV no Excel (ou use a tabela da UI se estiver bonita).
    *   Filtre por `ALARM`. Mostre: "Olha, a máquina parou 3 vezes hoje, às 14:30, 15:10 e 16:00. O motivo foi X."
    *   Conte as linhas de `RUN` ou Ciclos. Mostre: "Estimamos X peças produzidas."
    *   Compare com o apontamento manual (papel) se houver. Geralmente o nosso é mais preciso nos tempos.

3.  **Próximos Passos (Venda):**
    *   "Hoje provamos que conseguimos ler. O dado está aqui."
    *   "A Fase 2 é colocar isso na nuvem/painéis históricos definitivos."

---

**Lembrete:** Se algo der errado, **seja transparente**. "O cabo soltou", "A rede oscilou". A integridade do dado (Gate Anti-Mock) te protege de mentir. Se não tem dado, é porque não veio da máquina, e não erro do software.
