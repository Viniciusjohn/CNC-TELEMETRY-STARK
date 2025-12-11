# Dossiê Técnico STARK v1 - Piloto CNC-Telemetry

**Versão:** 1.0 (Marco 0.9 Produto)
**Data:** 11/12/2025
**Status:** Validado em Campo (Ambiente Real)

## 1. Resumo da Conquista
O sistema CNC-Telemetry atingiu o marco de **operação real em chão de fábrica** (Piloto STARK). A arquitetura provou-se robusta e capaz de ler dados de máquinas FANUC via rede industrial sem interferir na operação (leitura passiva).

O ambiente de demonstração (Demo/Lab) foi tecnicamente alinhado para ser um **espelho exato** do ambiente de campo, garantindo que apresentações para investidores (Centelha) e clientes reflitam a realidade técnica do produto.

## 2. Arquitetura Validada
O pipeline de dados confirmado em operação é:
1.  **Driver (Ladder99):** Coleta dados via FOCAS (Ethernet) da CNC.
2.  **Transporte (MQTT):** Publica tópicos normalizados (`fanuc/STARK_...`).
3.  **Backend (FastAPI):** Ingestão reativa, processamento de regras de negócio (Ciclos, Estados).
4.  **Persistência (SQLite):** Armazenamento de Eventos e Histórico de Produção.
5.  **Frontend (React):** Visualização em Tempo Real e KPIs de OEE.

**Documentação Técnica de Suporte:**
*   [Relatório de Auditoria e Arquitetura (RELATORIO_AUDITORIA_STARK_DEMO.md)](./RELATORIO_AUDITORIA_STARK_DEMO.md)
*   [Checklist Pré-Campo (CHECKLIST_PRE_CAMPO.md)](./CHECKLIST_PRE_CAMPO.md)

## 3. Status Funcional (O que já roda)
O sistema entrega hoje:
*   **Monitoramento de Estado:** Detecção automática de RUN, IDLE, ALARM e STOPPED.
*   **Contagem de Produção:** Rastreamento de peças produzidas com timestamp exato.
*   **Telemetria de Processo:** RPM do Spindle e Override de Avanço em tempo real.
*   **Histórico:** Tabela de produção e exportação CSV fiéis ao banco de dados.

## 4. Evidências de Campo
*(Insira aqui os prints da UI com dados da STARK_TORNO_PILOTO)*
*   [Print 1: Dashboard com Máquina em RUN e RPM variando]
*   [Print 2: Tabela de Histórico populada com ciclos reais]
*   *(Link para vídeo da máquina operando sincronizada com o dashboard)*

## 5. Próximos Passos (Roadmap Pós-CAM)
Com a base de telemetria consolidada, o foco evolui para:
1.  **Integração Bidirecional:** Envio de programas/receitas para a máquina (DNC).
2.  **Análise Avançada:** Correlação de alarmes com paradas de produção.
3.  **Escala:** Deploy para múltiplas máquinas simultâneas.
