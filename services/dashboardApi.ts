
import { DashboardData } from '../types';
import { generateSimulatedDashboardData, generateRawData } from './dataGenerator';

// Dynamic Backend URL determination
const getBackendUrl = () => {
    const hostname = window.location.hostname;
    // If running on localhost, use localhost. Otherwise use the IP/hostname that served the page.
    // This allows VPN/Remote access to work (assuming backend runs on same host)
    return `http://${hostname}:8000`;
};

const BACKEND_URL = getBackendUrl();
const MAX_RETRIES = 1; // Reduced for demo responsiveness
const RETRY_DELAY_MS = 500;
const REQUEST_TIMEOUT_MS = 2000;

const wait = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const dashboardApi = {
  /**
   * Tenta buscar os dados do Backend Python.
   */
  fetchDashboardData: async (retryCount = 0): Promise<DashboardData> => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
      const response = await fetch(`${BACKEND_URL}/demo/dashboard`, {
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data: DashboardData = await response.json();
      return data;
    } catch (error: any) {
      clearTimeout(timeoutId);
      
      if (retryCount < MAX_RETRIES) {
        // console.warn(`[Telemetry] Retrying connection...`);
        await wait(RETRY_DELAY_MS);
        return dashboardApi.fetchDashboardData(retryCount + 1);
      }

      console.warn('[Telemetry] Backend offline. Switch to Browser Simulation.');
      return generateSimulatedDashboardData();
    }
  },

  /**
   * Busca os eventos brutos do backend
   */
  fetchRawEvents: async (): Promise<any[]> => {
      try {
          const response = await fetch(`${BACKEND_URL}/demo/events`);
          if (response.ok) {
              const data = await response.json();
              // Mapeia para o formato esperado pela UI se necessário
              return data.map((d: any) => ({
                  id: Math.random().toString(36).substr(2, 9),
                  data: d.timestamp,
                  maquina_id: d.machine_id,
                  produto: d.product,
                  turno: d.shift,
                  tempo_ciclo_min: d.cycle_time,
                  pecas_boas: d.good_parts,
                  pecas_refugo: d.scrap_parts,
                  parada_min: d.stop_min,
                  motivo_parada: d.stop_reason || 'N/A'
              }));
          }
          throw new Error("Backend error");
      } catch (e) {
          console.warn("Failed to fetch raw events, using simulation");
          return generateRawData();
      }
  }
};
