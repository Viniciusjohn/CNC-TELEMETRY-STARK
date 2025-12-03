
import React, { useEffect, useRef, useState } from 'react';
import { Send, Bot, Sparkles, AlertCircle, Trash2, Cpu, XCircle, WifiOff, ShieldAlert, Lock, Globe, Clock } from 'lucide-react';
import { ChatMessage, DashboardData } from '../types';
import { chatService } from '../services/chatService';

const STORAGE_KEY = 'codexChatHistory';

interface CodexChatProps {
  dashboardData: DashboardData | null;
}

export const CodexChat: React.FC<CodexChatProps> = ({ dashboardData }) => {
  // 1. Carregar histórico do localStorage na inicialização
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) {
          return parsed;
        }
      }
    } catch (error) {
      console.error("Failed to load chat history:", error);
    }
    return [];
  });

  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  // 2. Salvar histórico no localStorage sempre que as mensagens mudarem
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    } catch (error) {
      console.error("Failed to save chat history:", error);
    }
  }, [messages]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleClearHistory = () => {
    if (confirm('Limpar histórico de conversa?')) {
      localStorage.removeItem(STORAGE_KEY);
      setMessages([]);
      setError(null);
    }
  };

  const getFriendlyErrorMessage = (error: any): string => {
    const msg = (error?.message || error?.toString() || '').toLowerCase();
    // Normaliza códigos de erro de diferentes versões da SDK ou Fetch
    const status = error?.status || error?.response?.status || error?.statusCode;

    // 1. Erros de Autenticação / API Key (401 ou mensagens específicas)
    if (status === 401 || msg.includes('api key') || msg.includes('key not valid') || msg.includes('unauthenticated')) {
      return "🔑 Autenticação Falhou: A API Key configurada está incorreta ou expirou. Verifique o arquivo .env.";
    }

    // 2. Erros de Permissão / Projeto (403)
    if (status === 403 || msg.includes('permission_denied')) {
      return "🚫 Permissão Negada: Sua chave de API não tem permissão para acessar o modelo Gemini neste projeto.";
    }

    // 3. Região não suportada (400 ou 404 específicos)
    if (msg.includes('location is not supported') || msg.includes('unsupported region')) {
      return "🌍 Região Indisponível: O acesso à API Gemini via Vertex AI/AI Studio não está disponível na sua região atual/VPN.";
    }

    // 4. Modelo não encontrado (404)
    if (status === 404 || msg.includes('not found')) {
      return "🔍 Modelo Não Encontrado: O modelo 'gemini-2.5-flash' não está disponível para sua chave. Tente usar 'gemini-pro'.";
    }

    // 5. Limites e Cota (429 - Resource Exhausted)
    if (status === 429 || msg.includes('quota') || msg.includes('resource_exhausted') || msg.includes('too many requests')) {
      return "⏳ Cota Excedida: O limite de requisições gratuitas foi atingido. Aguarde alguns instantes e tente novamente.";
    }

    // 6. Erros de Servidor do Google (500, 503)
    if (status >= 500 || msg.includes('overloaded') || msg.includes('unavailable') || msg.includes('internal')) {
      return "🔥 Erro no Servidor: Os servidores da IA estão instáveis ou sobrecarregados no momento. Tente novamente em breve.";
    }

    // 7. Filtros de Segurança (Safety Settings)
    if (msg.includes('safety') || msg.includes('blocked') || msg.includes('finishreason') || msg.includes('harmful')) {
      return "🛡️ Bloqueio de Segurança: A resposta foi bloqueada pelos filtros de conteúdo da IA (Safety Settings).";
    }

    // 8. Erros de Rede / Fetch
    if (msg.includes('fetch failed') || msg.includes('network') || msg.includes('offline') || msg.includes('failed to fetch')) {
      return "📡 Erro de Conexão: Não foi possível conectar à internet. Verifique sua rede.";
    }

    // 9. API Key não configurada (Erro local lançado pelo nosso serviço)
    if (msg.includes('api key não configurada')) {
      return "⚙️ Configuração Pendente: Nenhuma API Key foi detectada nas variáveis de ambiente.";
    }

    // Fallback genérico com detalhe técnico curto
    return `Erro Técnico: ${msg.substring(0, 100)}...`;
  };

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || isLoading) return;

    // Adiciona mensagem do usuário
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      createdAt: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setError(null);

    // Debug log to confirm context passing
    if (dashboardData) {
        console.debug("Sending message with context:", { 
            machines: dashboardData.machines.length, 
            kpis: dashboardData.kpis 
        });
    } else {
        console.debug("Sending message without context (data not ready)");
    }

    try {
      // Cria placeholder para mensagem da IA
      const assistantId = crypto.randomUUID();
      const initialAssistantMessage: ChatMessage = {
        id: assistantId,
        role: 'assistant',
        content: '',
        createdAt: new Date().toISOString(),
        isThinking: true
      };

      setMessages(prev => [...prev, initialAssistantMessage]);

      // Inicia stream
      const stream = chatService.sendMessageStream(
        [...messages, userMessage], 
        text, 
        dashboardData
      );
      
      let fullContent = '';

      for await (const chunk of stream) {
        fullContent += chunk;
        setMessages(prev => prev.map(msg => 
          msg.id === assistantId 
            ? { ...msg, content: fullContent, isThinking: false } 
            : msg
        ));
      }

    } catch (err: any) {
      console.error("Codex Chat Error:", err);
      const friendlyMsg = getFriendlyErrorMessage(err);
      setError(friendlyMsg);
      
      // Limpeza: remove mensagem de "pensando" se ela ficou vazia ou travada
      setMessages(prev => prev.filter(msg => {
        if (msg.isThinking && !msg.content) return false; // Remove placeholder vazio
        if (msg.isThinking) return { ...msg, isThinking: false }; // Mantém se já tinha conteúdo parcial
        return true;
      }));
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] bg-slate-900 border border-slate-800 rounded-lg overflow-hidden shadow-2xl">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-800 bg-slate-800/50 flex justify-between items-center backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-600/20 rounded-lg border border-indigo-500/30">
            <Cpu className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              Codex AI <span className="text-[10px] border border-emerald-500/30 text-emerald-400 px-1.5 rounded font-bold">GEMINI 2.5 FLASH</span>
            </h2>
            <p className="text-xs text-slate-400">
               {isLoading ? 'Analisando dados...' : 'Assistente de Fábrica Online'}
            </p>
          </div>
        </div>
        
        <button 
          onClick={handleClearHistory}
          className="p-2 hover:bg-slate-700/50 text-slate-500 hover:text-rose-400 rounded-lg transition-colors"
          title="Limpar Histórico"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-slate-700">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 opacity-50 select-none">
            <Sparkles className="w-12 h-12 mb-2 text-indigo-500/50" />
            <p className="text-sm font-medium">Faça perguntas sobre OEE, Alarmes ou Performance.</p>
          </div>
        )}
        
        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center flex-shrink-0 shadow-sm">
                <Bot className="w-5 h-5 text-emerald-400" />
              </div>
            )}
            
            <div className={`max-w-[85%] space-y-1 ${msg.role === 'user' ? 'items-end flex flex-col' : ''}`}>
              <div className={`
                p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap font-sans shadow-md
                ${msg.role === 'user' 
                  ? 'bg-indigo-600 text-white rounded-tr-none' 
                  : 'bg-slate-800 text-slate-200 border border-slate-700 rounded-tl-none'}
              `}>
                {msg.isThinking && !msg.content ? (
                   <span className="flex items-center gap-2 italic text-slate-400">
                     <Sparkles className="w-3 h-3 animate-pulse text-amber-400" /> Processando resposta...
                   </span>
                ) : (
                  msg.content
                )}
              </div>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Error Banner */}
      {error && (
        <div className="px-6 py-3 bg-rose-950/90 border-t border-rose-500/30 text-xs text-rose-200 flex items-center justify-between backdrop-blur-sm animate-in slide-in-from-bottom-2">
            <div className="flex items-center gap-2 font-medium">
                {error.includes('Segurança') ? <ShieldAlert className="w-4 h-4 text-rose-400" /> : 
                 error.includes('Conexão') ? <WifiOff className="w-4 h-4 text-rose-400" /> :
                 error.includes('Autenticação') ? <Lock className="w-4 h-4 text-rose-400" /> :
                 error.includes('Permissão') ? <Lock className="w-4 h-4 text-rose-400" /> :
                 error.includes('Região') ? <Globe className="w-4 h-4 text-rose-400" /> :
                 error.includes('Cota') ? <Clock className="w-4 h-4 text-rose-400" /> :
                 <AlertCircle className="w-4 h-4 text-rose-400" />}
                <span>{error}</span>
            </div>
            <button onClick={() => setError(null)} className="text-rose-400 hover:text-white transition-colors p-1 rounded hover:bg-rose-900">
                <XCircle className="w-4 h-4" />
            </button>
        </div>
      )}

      {/* Input Area */}
      <div className="p-4 bg-slate-950 border-t border-slate-800">
        <form onSubmit={handleSend} className="relative max-w-4xl mx-auto flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ex: Qual o motivo da parada da CNC-01?"
            className="flex-1 bg-slate-900 border border-slate-700 text-slate-200 text-sm rounded-lg px-4 py-3 focus:outline-none focus:border-indigo-500 transition-all placeholder:text-slate-600 disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={isLoading} 
          />
          <button 
            type="submit" 
            disabled={isLoading || !input.trim()}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white px-5 rounded-lg transition-colors shadow-lg shadow-indigo-500/20 flex items-center justify-center"
          >
            {isLoading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Send className="w-5 h-5" />}
          </button>
        </form>
      </div>
    </div>
  );
};
