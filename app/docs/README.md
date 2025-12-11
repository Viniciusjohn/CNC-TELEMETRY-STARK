# Telemetry UI v0 - Factory Dashboard

Dashboard de telemetria industrial projetado para monitoramento de CNCs Mitsubishi (M70/M80) via MTConnect.

## 🚀 Status Atual
- **Interface:** React + Tailwind (Dark Industrial Theme).
- **Gráficos:** Recharts (OEE, Sparklines de Carga, Pareto de Paradas).
- **Dados:** Atualmente operando em modo **SIMULAÇÃO** (gerador interno).
- **AI:** Chatbot "Codex" integrado com Google Gemini 2.5 Flash.

---

## 🛠️ Roteiro de Integração (Próximos Passos)

Para conectar este Frontend ao seu Backend existente (Python/C++), siga este fluxo:

### Passo 1: Extração de Conhecimento
1. Abra o arquivo `prompt_extracao.md` neste projeto.
2. Copie o conteúdo.
3. Cole no chat/interface onde você tem acesso ao código fonte do seu projeto atual.
4. **Objetivo:** Obter um JSON descrevendo a arquitetura e o formato dos dados.

### Passo 2: Adaptação do Contrato de Dados
1. Cole o JSON gerado no Passo 1 aqui no chat.
2. Atualizaremos o arquivo `types.ts` para espelhar exatamente os campos do seu banco de dados/API.
3. Atualizaremos o `services/dashboardApi.ts` para consumir sua API real (ex: `http://localhost:8000/api/v1/...`).

### Passo 3: Validação em Chão de Fábrica
1. Rodar o comando de build: `npm run build`.
2. Servir os arquivos estáticos junto com seu servidor Python.
3. Testar a latência dos gráficos de Carga (Sparklines) com a máquina operando.

---

## 🔧 Configuração Local

### Instalação
```bash
npm install
```

### Rodar Desenvolvimento
```bash
npm run dev
```
O app abrirá em `http://localhost:5173`.

### Variáveis de Ambiente (.env)
```bash
# Chave da API do Google Gemini (para o Chatbot)
API_KEY=sua_chave_aqui
```

## 📂 Estrutura Principal
- `src/components/Charts.tsx`: Configuração dos gráficos (Sparklines, Barras).
- `src/services/dataGenerator.ts`: Lógica da simulação (será substituída pela API real).
- `src/services/chatService.ts`: Integração com LLM (Gemini).
