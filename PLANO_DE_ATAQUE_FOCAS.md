# Plano de Ataque: Desbloqueio FOCAS e Integração Real

**Data:** 06/12/2025
**Status:** Crítico / Imediato
**Contexto:** Pós-visita Stark. Infraestrutura de rede validada. Stack de software pronto.

---

## 1. Diagnóstico Preciso
O piloto está travado na **camada de aplicação FOCAS**, não na infraestrutura de rede.

*   **Rede (Layer 3/4):** ✅ VALIDADA.
    *   Ping 192.168.1.1 OK.
    *   Porta 8193 TCP aberta e acessível (Test-NetConnection OK).
    *   CNC mostra FOCAS2 ativo na tela.
*   **Software (Stack):** ✅ PRONTO.
    *   Backend refatorado para aceitar JSON do driver.
    *   Contratos de dados (`TelemetrySample`) definidos.
    *   Frontend pronto para exibir dados reais.
*   **Bloqueio Atual:** ❌ DRIVER FOCAS (Aplicação).
    *   O driver inicia, conecta no socket, cria coletores, mas falha ao tentar ler dados (Sweep/SocketException).
    *   O backend, apesar de pronto, não recebe dados porque o driver não publica.

---

## 2. Missão Técnica Única
**Objetivo:** Fazer o circuito completo funcionar: CNC -> Driver -> MQTT -> Backend -> UI.

### Etapa 1: Estabilizar Driver FOCAS (Ainda não resolvido)
Fazer o `fanuc-driver` (Ladder99) ler com sucesso pelo menos **Status (RUN/IDLE)** e **Contador de Peças** da Fanuc 0i-TF Plus.

**Roteiro de Validação (Missão 1):**
1.  **Check de Rede:**
    *   `ping 192.168.1.1`
    *   `Test-NetConnection 192.168.1.1 -Port 8193`
2.  **Rodar Probe Isolado:**
    *   `cd C:\CNC-TELEMETRY\app`
    *   `python scripts/probe_focas.py 192.168.1.1`
    *   **Sucesso (0):** FOCAS está OK. O problema é no Ladder99.
    *   **Erro (-16/Socket):** Firewall ou Porta fechada.
    *   **Erro (-15/DLL):** DLL errada ou caminho.
3.  **Se Probe OK:**
    *   Rodar Ladder99 e verificar logs.

**Hipóteses de Erro e Ações de Debug:**
1.  **Firewall do Windows (PC Piloto):**
    *   *Ação:* Verificar se o executável do driver ou a porta de retorno estão bloqueados. (Teste rápido: desativar firewall temporariamente).
2.  **Versão da DLL FOCAS (`fwlib32.dll`):**
    *   *Ação:* A DLL embarcada no driver pode ser antiga para o controlador 0i-TF **Plus**. Verificar se há versão mais nova da DLL FOCAS disponível e substituir na pasta do driver.
3.  **Parâmetros FOCAS na CNC:**
    *   *Ação:* Confirmar se a porta FOCAS está habilitada para *escrita/leitura* ou se requer senha (parâmetros de segurança da Fanuc).
4.  **Timeout/Latência:**
    *   *Ação:* Aumentar `timeout_s` no `config.machines.yml` de 3 para 10 segundos.

### Etapa 2: Integração Backend (JÁ IMPLEMENTADA ✅)
*   O código do backend (`datasources.py` + `adapters.py`) já foi ajustado para ler o JSON que o driver vai gerar.
*   *Ação:* Assim que o driver publicar no MQTT, verificar logs do backend (`[FanucAdapter] Ingested...`).

---

## 3. Narrativa para Stakeholders (Centelha/Adriano)
"A infraestrutura de rede e o ambiente Windows foram validados com sucesso em campo. O sistema já conecta à porta de gerenciamento da máquina. O foco atual é um ajuste fino na biblioteca de comunicação (driver FOCAS) para compatibilidade com o modelo específico '0i-TF Plus', seguido da validação do fluxo de dados até o painel."

---

## 4. Próximos Passos Imediatos (Hands-on)
1.  Obter acesso ao PC Piloto (ou simular ambiente similar).
2.  Executar `fanuc-driver` com log verboso.
3.  Testar substituição da `fwlib32.dll`.
4.  Validar se o tópico MQTT `fanuc/STARK_TORNO_PILOTO/StateData` começa a chegar.
