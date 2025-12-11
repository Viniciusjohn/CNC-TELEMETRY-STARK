# Contrato de API: STARK Telemetry v1

**Versão:** 1.0
**Data:** 11/12/2025
**Status:** Congelado (Produção/Piloto)

Este documento define o contrato de dados estrito entre o Backend (Python/FastAPI) e o Frontend (React/TypeScript) para a exibição de históricos e tabelas.

## 1. Princípio de Design
O Backend é a "Fonte da Verdade". Ele deve entregar os dados já formatados e com as chaves finais em **Português (PT-BR)** para serem consumidas diretamente pela UI, sem necessidade de remapeamento ou tradução no cliente.

## 2. Endpoint de Eventos (Histórico)
**Rota:** `/demo/events` (ou `/demo/export` para CSV)
**Método:** `GET`
**Fonte:** `backend.datasources.generate_raw_events()`

### Schema do Objeto (JSON/CSV)
Cada linha do histórico deve conter obrigatoriamente as seguintes chaves:

| Chave (PT-BR) | Tipo | Descrição | Exemplo |
| :--- | :--- | :--- | :--- |
| `id` | `string` | Identificador único (pode ser o timestamp ou UUID) | `"2025-12-11 03:41:50"` |
| `data` | `string` | Timestamp ISO 8601 | `"2025-12-11T03:41:50..."` |
| `maquina_id` | `string` | ID da Máquina (Config) | `"STARK_TORNO_PILOTO"` |
| `produto` | `string` | Nome do Programa/Produto | `"O1234"` |
| `turno` | `string` | Turno calculado (1, 2, 3) | `"Turno 1"` |
| `tempo_ciclo_min` | `float` | Duração do ciclo em minutos | `4.5` |
| `pecas_boas` | `int` | Peças contabilizadas no ciclo | `1` |
| `pecas_refugo` | `int` | Peças refutadas (se houver input) | `0` |
| `parada_min` | `int` | Tempo de parada (se evento de parada) | `0` |
| `motivo_parada` | `string` | Razão da parada ou Estado | `"Cycle Complete"` / `"State: IDLE"` |

## 3. Implementação
*   **Backend:** `app/backend/datasources.py` -> `generate_raw_events`
*   **Frontend:** `app/types.ts` -> `interface TelemetryEventRow`
*   **Validação:** `verify_api_contract.py`

## 4. Regras de Evolução
1.  **Não renomeie** chaves existentes. Se precisar de inglês, adicione novas chaves, não remova as antigas.
2.  **Não mude o tipo** de dados (ex: `tempo_ciclo_min` deve ser sempre numérico, não string formatada).
3.  Qualquer alteração requer atualização simultânea em `app/types.ts` e rodar o script de verificação.
