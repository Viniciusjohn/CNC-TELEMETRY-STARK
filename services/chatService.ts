
import { GoogleGenAI, GenerateContentResponse } from "@google/genai";
import { ChatMessage, DashboardData } from "../types";
import { MITSUBISHI_ALARMS } from "../constants";

// Ensure API Key is available
const apiKey = process.env.API_KEY;
const isMockMode = !apiKey || apiKey === 'PLACEHOLDER_API_KEY';

const ai = new GoogleGenAI({ apiKey: apiKey || 'mock-key' });

const ALARM_KNOWLEDGE = MITSUBISHI_ALARMS.map(a => `- Código ${a.code}: ${a.message} (${a.description})`).join('\n');

const SYSTEM_PROMPT = `Você é o Codex, um especialista sênior em manutenção e telemetria de máquinas CNC Mitsubishi (M70/M80).
Seu objetivo é apoiar operadores e gestores de chão de fábrica.

BASE DE CONHECIMENTO TÉCNICO (ALARMES MITSUBISHI):
${ALARM_KNOWLEDGE}

DIRETRIZES DE ANÁLISE:
1. **Status UNAVAILABLE**: Significa que o MTConnect Adapter perdeu conexão. NÃO é erro da máquina, é erro de REDE ou do SERVIDOR. Sugira verificar cabos Ethernet e o serviço do Windows.
2. **Status STOPPED**: Máquina parada operacionalmente. Verifique se há alarmes associados.
3. **Alarmes**: Se houver código (ex: S01), explique o que é (Erro de Servo) e sugira resetar o drive.
4. **OEE**: Analise Disponibilidade vs Performance. Se a máquina roda muito (Active) mas produz pouco, é baixa eficiência de ciclo.

SEJA TÉCNICO E DIRETO. Fale a língua do chão de fábrica.`;

// ... helper for mock delay ...
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// ... Mock Response Logic ...
async function* mockStreamResponse(message: string, context: DashboardData | null) {
    await delay(1000); // Initial thinking time
    
    const lowerMsg = message.toLowerCase();
    let response = "";

    if (lowerMsg.includes('parada') || lowerMsg.includes('motivo')) {
        const stoppedMachine = context?.machines.find(m => m.execution_state === 'STOPPED' || m.active_alarm);
        if (stoppedMachine) {
            response = `A máquina **${stoppedMachine.machine_id}** está parada neste momento. \n\nAnálise preliminar:\n- **Estado**: ${stoppedMachine.execution_state}\n`;
            if (stoppedMachine.active_alarm) {
                response += `- **Alarme Ativo**: ${stoppedMachine.active_alarm.code} - ${stoppedMachine.active_alarm.message}.\n\nRecomendação: Verifique o manual de manutenção para o erro ${stoppedMachine.active_alarm.code}. Pode ser necessário resetar o drive.`;
            } else {
                response += `- **Nenhum alarme crítico reportado**. Pode ser uma parada programada para setup ou troca de turno.`;
            }
        } else {
            response = "No momento, todas as máquinas monitoradas parecem estar operando normalmente ou em modo de espera (IDLE/READY). Não detectei paradas críticas não planejadas.";
        }
    } else if (lowerMsg.includes('oee') || lowerMsg.includes('eficiência')) {
        const oee = context?.kpis.global_oee || 0;
        response = `O **OEE Global** da fábrica está em **${(oee * 100).toFixed(1)}%**. \n\nIsso é considerado ${oee > 0.85 ? 'excelente' : oee > 0.7 ? 'bom' : 'baixo'}. Recomendo focar na redução de micro-paradas nas máquinas M70 para melhorar este índice.`;
    } else if (lowerMsg.includes('olá') || lowerMsg.includes('oi')) {
        response = "Olá! Sou o Codex, seu assistente de chão de fábrica. Estou conectado à telemetria em tempo real. Posso ajudar com diagnósticos de alarmes, análise de OEE ou status das máquinas.";
    } else {
        response = "Entendi. Como estou em **Modo de Demonstração**, minha capacidade cognitiva está limitada a respostas pré-programadas sobre o estado atual das máquinas. \n\nPor favor, tente perguntar sobre:\n- Motivo de parada das máquinas\n- OEE atual\n- Alarmes ativos";
    }

    // Simulate streaming
    const chunks = response.split(/(?=[ \n])/); // Split by words/spaces
    for (const chunk of chunks) {
        yield chunk;
        await delay(20 + Math.random() * 30); // Random typing speed
    }
}

const formatContext = (data: DashboardData | null): string => {
  if (!data) return "Status: Aguardando sincronização de dados.";

  // Group machines by status for better summary
  const activeMachines = data.machines.filter(m => m.execution_state === 'ACTIVE' && m.availability === 'AVAILABLE');
  const stoppedMachines = data.machines.filter(m => m.execution_state !== 'ACTIVE' && m.availability === 'AVAILABLE');
  const offlineMachines = data.machines.filter(m => m.availability === 'UNAVAILABLE');
  
  // Format detailed machine info with explicit status mapping
  const machinesInfo = data.machines.map(m => {
    let status = 'Unknown';
    let alarmDetails = 'No Alarms';

    // Determinar Status Macroscópico para o Contexto da IA
    if (m.availability === 'UNAVAILABLE') {
        status = 'OFFLINE (FALHA DE REDE/ADAPTER)';
    } else if (m.active_alarm) {
        status = 'ERRO CRÍTICO';
        alarmDetails = `ALARM CODE: ${m.active_alarm.code} (${m.active_alarm.message})`;
    } else if (m.execution_state === 'ACTIVE') {
        status = 'EM PRODUÇÃO';
    } else if (m.execution_state === 'STOPPED') {
        status = 'PARADA';
    } else if (m.execution_state === 'FEED_HOLD' || m.execution_state === 'READY') {
        status = 'SETUP/AGUARDANDO';
    }

    const load = m.availability === 'AVAILABLE' ? `Load:${m.spindle_load.toFixed(0)}%` : 'Load:--';
    const prog = m.program_name ? `Prg:${m.program_name}` : 'Prg:--';
    
    return `> ${m.machine_id} (${m.controller_type}): ${status} | ${alarmDetails} | ${load} | ${prog}`;
  }).join('\n');

  return `
  [SNAPSHOT TELEMETRIA - ${new Date().toLocaleTimeString()}]
  
  RESUMO OPERACIONAL:
  - OEE Global: ${(data.kpis.global_oee * 100).toFixed(1)}%
  - Produção Total: ${data.kpis.total_production} peças
  - Status Máquinas: ${activeMachines.length} Rodando, ${stoppedMachines.length} Paradas, ${offlineMachines.length} Sem Conexão

  DETALHE POR MÁQUINA (Contexto Rico):
  ${machinesInfo}
  `;
};

export const chatService = {
  checkConnection: async (): Promise<boolean> => {
    if (isMockMode) return true; // Mock mode is always connected
    try {
      await ai.models.generateContent({
        model: "gemini-2.5-flash",
        contents: "ping",
      });
      return true;
    } catch (e) {
      console.error("Gemini connection check failed:", e);
      return false;
    }
  },

  sendMessageStream: async function* (
    history: ChatMessage[], 
    newMessage: string,
    context: DashboardData | null
  ) {
    if (isMockMode) {
        yield* mockStreamResponse(newMessage, context);
        return;
    }

    const previousHistory = history.slice(0, -1).map(msg => ({
      role: msg.role === 'assistant' ? 'model' : 'user',
      parts: [{ text: msg.content }]
    }));

    // Inject formatted dashboard data into the system prompt
    const fullSystemInstruction = `${SYSTEM_PROMPT}\n\n${formatContext(context)}`;

    const chat = ai.chats.create({
      model: 'gemini-2.5-flash', 
      history: previousHistory,
      config: {
        systemInstruction: fullSystemInstruction,
      },
    });

    const resultStream = await chat.sendMessageStream({ message: newMessage });

    for await (const chunk of resultStream) {
      const c = chunk as GenerateContentResponse;
      if (c.text) {
        yield c.text;
      }
    }
  }
};
