# Roadmap Estratégico: CNC Telemetry Stark (Pós-Campo)

Este documento consolida o plano de ação técnica para superar os desafios encontrados no piloto da Stark Brasil (FANUC 0i-TF Plus) e estabilizar o produto.

## 1. Arquitetura de Integração (Mudança de Rota)
**Problema:** Assumimos que o driver da Ladder99 expunha uma API HTTP simples, mas ele é nativo MQTT/SHDR. A integração atual via HTTP (`httpx.get`) não vai funcionar.

- [ ] **Decisão de Protocolo:**
  - Adotar **MQTT** como padrão de troca de mensagens (Padrão Indústria 4.0).
  - Instalar um Broker MQTT leve no PC Windows (Eclipse Mosquitto).
  - Configurar driver Ladder99 para publicar em `tcp://localhost:1883`.
- [ ] **Refatoração do Backend (Python):**
  - Substituir `FanucDataSource` (HTTP) por um cliente MQTT (`paho-mqtt`).
  - Assinar tópicos como `fanuc/STARK_TORNO_PILOTO/status`, `.../rpm`, `.../part_count`.
  - Atualizar `CycleTracker` em tempo real a cada mensagem recebida.

## 2. Estabilização do Driver FOCAS
**Problema:** Erro `SocketException (0xFFFFFFFFF0)` na coleta de dados, indicando falha na biblioteca FOCAS ou bloqueio na CNC.

- [ ] **Diagnóstico Fino:**
  - Testar driver "mínimo": Configurar `config.machines.yml` para ler APENAS status (RUN/IDLE), removendo eixos, PMC e macros complexas.
  - Validar versão da DLL `fwlib32.dll`: Garantir compatibilidade com Series 0i-TF Plus (Type A/B).
- [ ] **Plano B (Alternativa):**
  - Se o driver Ladder99 persistir no erro, implementar um **Wrapper FOCAS Python** direto (`pyfocas` ou `ctypes`) dentro do próprio backend, eliminando a camada intermediária.

## 3. Expansão Multi-Máquina
**Cenário:** 3 máquinas na rede (0i-TF Plus, 0i-TF, 0i-MD).

- [ ] **Configuração de Rede:**
  - Definir IPs fixos para todas: `.101` (Piloto), `.102` (Torno 2), `.103` (Centro).
  - Testar cabeamento e switch para garantir visibilidade simultânea.
- [ ] **Dashboard Paralelo:**
  - O backend já suporta `asyncio.gather`, mas precisa ser testado com 3 conexões MQTT simultâneas.

## 4. Métricas e Valor para o Cliente (Centelha)
**Meta:** Gerar o CSV de prova de valor.

- [ ] **Validação do Part Counter:** Confirmar qual variável FOCAS representa a contagem real de peças (frequentemente é um parâmetro PMC ou variável macro customizada).
- [ ] **Cálculo de OEE Simplificado:**
  - Disponibilidade = Tempo em RUN / Tempo Total.
  - Performance = (Ciclo Ideal * Peças) / Tempo em RUN.
  - Qualidade = (Total - Refugo) / Total.
- [ ] **Exportação:** Melhorar o endpoint `/demo/export` para gerar relatório por turno/dia real.

## Cronograma Sugerido

| Fase | Ação Principal | Meta |
| :--- | :--- | :--- |
| **Semana 1** | Integração MQTT + Fix Driver | Ler 1 variável real na tela (sem erro de socket). |
| **Semana 2** | Part Counter + CycleTracker | Ter ciclos reais sendo calculados automaticamente. |
| **Semana 3** | Expansão Multi-Máquina | Conectar as 3 máquinas no switch e validar dashboard completo. |
| **Semana 4** | Relatórios & Entrega | Gerar CSVs de produção para o Adriano validar o Centelha. |
