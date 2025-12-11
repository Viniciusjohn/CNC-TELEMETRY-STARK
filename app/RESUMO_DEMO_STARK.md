# Resumo da Demo: Stark Telemetry | CNC Monitor

Este documento resume a arquitetura e o roteiro da demonstração preparada para a Stark Brasil.

## 1. Arquitetura da Demo

O sistema roda em modo **Híbrido/Offline**, garantindo estabilidade durante a visita mesmo sem internet.

### Backend (Python/FastAPI)
Responsável pela simulação de dados e geração de arquivos.
*   **Localização**: `/backend`
*   **Porta**: `8000`
*   **Rotas Principais**:
    *   `GET /healthz`: Verifica se o backend está vivo.
    *   `GET /demo/dashboard`: Retorna o "snapshot" atual de todas as máquinas (KPIs, status, alertas) para a tela principal.
    *   `GET /demo/events`: Retorna o histórico de eventos brutos (para a aba DATA).
    *   `GET /demo/export`: Gera e baixa o arquivo CSV (`telemetry_demo_YYYYMMDD.csv`) com headers corretos.

### Frontend (React/Vite)
Interface HMI moderna para visualização.
*   **Localização**: `/src`, `/components`
*   **Porta**: `5173`
*   **Abas**:
    1.  **MONITOR**: Visão geral das máquinas (Grid). Mostra Status (RUN/IDLE/ALARM), RPM, Carga e Programa.
    2.  **ANALYTICS**: Gráficos de tendência de OEE e Pareto de paradas.
    3.  **DATA**: Tabela de eventos brutos + Botão **"Export Log"** (integração com backend).
    4.  **CODEX AI**: Assistente virtual industrial.

### Codex AI (Modo Demo)
O assistente possui um sistema de **Fallback Automático**:
*   Se houver API Key válida (`.env`): Conecta ao Google Gemini 2.5 Flash.
*   **Se estiver Offline/Sem Key (Padrão Demo)**: Ativa o **Modo Mock**, respondendo perguntas pré-programadas sobre:
    *   Motivo de paradas (lê o estado simulado da máquina).
    *   OEE atual da fábrica.
    *   Saudações e explicações sobre o sistema.

---

## 2. Roteiro de Apresentação

Siga estes passos para uma demonstração fluida:

### Passo 1: Inicialização
1.  Abra o **PowerShell** na pasta do projeto.
2.  Execute: `.\scripts\start_telemetry_demo.ps1`
    *   *O script abrirá o Backend em uma nova janela e manterá o Frontend na janela atual.*
    *   *Aguarde o navegador abrir automaticamente em `http://localhost:5173`.*

### Passo 2: Monitoramento em Tempo Real
1.  Mostre a tela **MONITOR**.
2.  Destaque a atualização em tempo real (RPM e Carga variando).
3.  Explique os status visuais:
    *   **Verde/Pulsando**: Em Produção.
    *   **Vermelho/Pulsando**: Alarme/Erro Crítico.
    *   **Cinza**: Offline/Sem Rede.

### Passo 3: Dados e Relatórios
1.  Vá para a aba **DATA**.
2.  Mostre a tabela de eventos.
3.  Clique em **"Export Log"**.
4.  Abra o arquivo CSV baixado no Excel para provar que os dados são exportáveis.

### Passo 4: Inteligência Artificial (Codex)
1.  Vá para a aba **CODEX AI**.
2.  Pergunte: *"Qual o motivo da parada?"* ou *"Como está o OEE?"*.
3.  Mostre a resposta técnica gerada (mesmo sem internet), provando o valor da análise automática.

---

## 3. Pontos de Atenção

*   **Não feche a janela do PowerShell**: Ela mantém o servidor Frontend rodando.
*   **Backend Minimizado**: O backend roda em uma janela separada. Se precisar reiniciar, feche ambas e rode o script novamente.
*   **Resolução**: O layout é responsivo, mas funciona melhor em tela cheia (F11) no notebook.
