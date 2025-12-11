# Relatório Técnico: Análise de Código CNC Telemetry Stark

**Data:** 06/12/2025  
**Responsável:** Cascade AI (Engenheiro de Software Sênior)  
**Escopo:** Backend (FastAPI), Frontend (React), Driver (Fanuc/FOCAS)

---

## 1. Arquitetura Atual

O sistema opera em uma arquitetura de três camadas, desacoplada via MQTT, projetada para rodar em ambiente Windows.

*   **Frontend (React + Vite):**
    *   **Entrypoint:** `App.tsx`.
    *   **Consumo de Dados:** *Polling* HTTP a cada 2 segundos no endpoint `/demo/dashboard`.
    *   **Visualização:** Dashboard estilo "HMI Industrial" com componentes reutilizáveis (`MachinePanel`, `Charts`). Suporta visualização de múltiplas máquinas.
    *   **Contrato:** Interfaces definidas em `types.ts` (alinhadas parcialmente com o backend).

*   **Backend (FastAPI):**
    *   **Entrypoint:** `backend/main.py`.
    *   **Responsabilidade:** Orquestração e API Gateway.
    *   **Modos de Operação:**
        *   `LAB`: Usa `LabSimulatedDataSource` para gerar dados fake.
        *   `FIELD`: Usa `FanucMqttDataSource` para consumir dados reais via MQTT.
    *   **Persistência:** Em memória (caches de último estado em `FanucMqttDataSource`).

*   **Driver (l99.driver.fanuc):**
    *   **Tecnologia:** Aplicação .NET Console (binários presentes, config em YAML).
    *   **Função:** Coleta dados via FOCAS (Ethernet) e publica em broker MQTT.
    *   **Configuração:** `config.machines.yml` define IPs e estratégias de coleta.

### Fluxo de Dados (Field Mode)
1.  **CNC** (FOCAS) → **Driver** (Polling ~1s)
2.  **Driver** → **MQTT Broker** (Topic: `fanuc/{MachineID}/{VeneerClass}`)
3.  **Backend** (Subscriber) → **Cache em Memória**
4.  **Frontend** (Polling HTTP) ← **Backend**

---

## 2. Pontos Fortes

1.  **Desacoplamento via MQTT:** O uso de um broker intermediário é excelente para estabilidade. Se o backend reiniciar, o driver continua coletando. Se o driver cair, o backend mantém o último estado conhecido.
2.  **Separação de Responsabilidades:** O Frontend não sabe que existe um driver Fanuc, ele apenas consome uma API padronizada.
3.  **Frontend Moderno:** Interface bem estruturada, tipada (TypeScript) e responsiva.
4.  **Simulação Integrada:** A capacidade de rodar em modo `LAB` sem hardware físico acelera muito o desenvolvimento e testes de UI.

---

## 3. Riscos e Dívidas Técnicas (Prioridade Alta)

### 🔴 1. Incompatibilidade Crítica no Consumo MQTT (Bug Bloqueante)
O Driver e o Backend "falam" línguas diferentes no MQTT.
*   **Backend (`datasources.py`):** Espera tópicos planos/simples (ex: `fanuc/M1/status`, `fanuc/M1/rpm`) e trata o payload como valor direto.
*   **Driver (`config.machines.yml`):** Está configurado para publicar objetos JSON complexos baseados em "Veneers" (ex: `fanuc/M1/StateData` contendo `{ "execution": "ACTIVE", "mode": "MEM", ... }`).
*   **Impacto:** O backend receberá o JSON, mas tentará buscar chaves como `status` diretamente no nível superior do cache, o que falhará. **O sistema não funcionará em campo sem ajuste.**

### 🟠 2. Duplicação de Configuração
*   As máquinas são definidas em dois lugares: `backend/config.py` (`STARK_MACHINES`) e `fanuc-driver/config.machines.yml`.
*   **Risco:** Adicionar uma máquina exige editar dois arquivos em pastas diferentes. Desalinhamento de IDs causa falha silenciosa na telemetria.

### 🟡 3. Acoplamento Forte com Fanuc no Backend
*   A classe `FanucMqttDataSource` tem lógica específica de parsing (mesmo que quebrada) e normalização de estados Fanuc (`RUN` -> `ACTIVE`).
*   Para suportar Mitsubishi ou Siemens, seria necessário criar `MitsubishiDataSource` e alterar o `main.py` cheio de `if/else`.

### 🟡 4. Tratamento de Erros e Resiliência
*   O Backend armazena estado apenas em memória (`self.cache`). Um restart do serviço backend perde todo o histórico de contagem de peças do dia até chegar nova mensagem MQTT.
*   `datasources.py` captura exceções genéricas no loop MQTT (`try/except Exception`), o que pode mascarar erros de parsing ou conexão.

---

## 4. Sugestões de Refatoração e Escalabilidade

Para suportar múltiplos controladores (Fanuc, Mitsubishi, Siemens) sem reescrever o sistema:

### A. Corrigir a Camada de Ingestão (Imediato)
Refatorar `FanucMqttDataSource` para interpretar corretamente os JSONs do driver l99.
*   **Ação:** Criar parsers específicos para os "Veneers" (`StateData`, `ProductionData`) dentro do `datasources.py`.
*   **Exemplo:** Ao receber `StateData`, decodificar o JSON e atualizar `status`, `mode`, `spindle_load` no modelo interno unificado.

### B. Introduzir "Machine Adapter Pattern" (Curto Prazo)
Abstrair a lógica de conversão de dados brutos para o modelo de domínio (`CncMachineData`).
*   Criar uma interface `IMachineAdapter` no Python.
*   Implementar `FanucAdapter`, `MitsubishiAdapter`.
*   O `MqttDataSource` passa a ser genérico: ele assina tópicos e delega o parsing para o Adapter correto com base no ID da máquina (configurado no `config.py`).

### C. Unificar Configuração (Médio Prazo)
Centralizar a lista de máquinas em um arquivo `machines.json` ou banco de dados leve (SQLite).
*   O Backend lê essa lista para saber quais máquinas monitorar.
*   Scripts de deploy podem gerar o `config.machines.yml` do driver Fanuc automaticamente a partir dessa fonte única.

### D. Persistência Leve
Implementar persistência local (ex: SQLite ou Append-only Log) para contadores de produção e histórico de 20 pontos. Isso evita "zerar" o dashboard se o serviço FastAPI reiniciar.

### Perfil de Controlador Sugerido
Para escalar, o Backend deve ignorar detalhes de hardware.
*   **Perfil Padrão:** `GENERIC_CNC` (Status, RPM, Load, Parts).
*   Adapters (Drivers) devem mapear seus dados específicos para esse perfil.
*   **Mitsubishi:** Se usar protocolo MTConnect (comum em M70/M80 novos), pode-se usar um driver MTConnect -> MQTT e criar um `MTConnectAdapter` no backend, reutilizando quase toda a estrutura.

---

## 5. Correções Aplicadas – 06/12/2025

Seguindo as recomendações deste relatório, as seguintes correções foram aplicadas para estabilizar o piloto Stark:

### 1. Camada de Ingestão Refatorada
*   **Problema:** Incompatibilidade entre JSON do Driver e expectativa de string plana do Backend.
*   **Solução:**
    *   Criado `backend/adapters.py` com `FanucAdapter`.
    *   Refatorado `backend/datasources.py` (`FanucMqttDataSource`) para usar o adapter.
    *   O Adapter agora processa os Veneers complexos (`StateData`, `ProductionData`, `SpindleData`) e os normaliza para um modelo interno.

### 2. Contrato Canônico `TelemetrySample`
*   **Solução:** Definido modelo `TelemetrySample` em `backend/models.py` e interface equivalente em `app/types.ts`.
*   **Benefício:** Frontend e Backend agora falam a mesma língua. Campos opcionais são tratados explicitamente.

### 3. Unificação de Configuração
*   **Problema:** IDs de máquinas duplicados entre Python e YAML.
*   **Solução:** `backend/config.py` agora lê dinamicamente o arquivo `../fanuc-driver/config.machines.yml`.
*   **Fonte de Verdade:** O arquivo YAML do driver é a única fonte de verdade para IDs e IPs de máquinas.

### 4. Ajustes no Driver
*   **Arquivo:** `fanuc-driver/config.machines.yml`
*   **Mudança:** Alterado `publish_model` para `true` (garantindo JSON estruturado) e adicionados coletores de `Alarms` e `SpindleData` para a máquina `STARK_TORNO_PILOTO`.

### Próximos Passos (Futuro)
*   Implementar persistência em disco (SQLite) para histórico de produção.
*   Adicionar suporte a outros drivers (Mitsubishi) criando novos Adapters (`MitsubishiAdapter`).
