# Planejamento de Integração: Telemetria CNC Mitsubishi (M70/M80)

## 1. Entendimento do Cenário Atual
Você possui um sistema estruturado que extrai dados de máquinas com comandos Mitsubishi (M70/M80) via protocolo **MTConnect**. Isso implica que:
1.  Existe um **Adapter** rodando (provavelmente na IHM da máquina ou em um gateway externo) que traduz os sinais da Mitsubishi (via bibliotecas como EZSocket ou FOCAS-like da Mitsubishi) para o padrão SHDR.
2.  Existe um **Agent** MTConnect servindo XML via HTTP.
3.  Você já possui uma camada que lê esses dados e os estrutura (Backend/Coletor).

## 2. Melhor Forma de Compartilhar o Projeto
Como sou uma IA baseada em texto e processamento de contexto, **não consigo baixar ZIPs, clonar repositórios privados do GitHub ou acessar sua rede local**.

A forma mais eficiente e precisa (o método "TED" que você mencionou) é você compilar um **Prompt de Contexto** contendo os artefatos de dados, em vez do código fonte do driver C++/C#.

### O que você deve me mandar no próximo prompt:

Não preciso do código que conecta na máquina, preciso da **saída** desse código que o Front-end vai consumir. Por favor, forneça:

#### A. O "Contrato de Dados" (JSON Final)
O Dashboard precisa saber exatamente o que chega para ele. Copie e cole um exemplo de JSON real ou a definição da classe/interface de dados do seu sistema.
*Exemplo:*
```json
{
  "timestamp": "2023-10-27T10:00:00Z",
  "machine_id": "CNC-01",
  "controller": "M80",
  "status": "ACTIVE",
  "program": "O1234",
  "spindle_load": 45.5,
  "feed_rate_override": 100,
  "current_tool": 12,
  "alarms": []
}
```

#### B. Mapeamento de Estados (Business Rules)
Como você traduz os estados do MTConnect para o negócio?
*   *Exemplo:* `EXECUTION=ACTIVE` + `SpindleLoad > 0` = **Produzindo**?
*   *Exemplo:* `EXECUTION=STOPPED` + `Alarm != null` = **Parada por Erro**?
Essas regras são vitais para calcularmos o OEE corretamente no Dashboard.

#### C. Estrutura de Arquivos (Tree)
Se você quiser que eu mantenha a arquitetura do seu projeto, mande a árvore de pastas atual (apenas texto):
```text
/src
  /backend (Python/C#?)
  /frontend (React?)
  /models
```

## 3. Roteiro para o Próximo Passo

No próximo prompt, você pode colar o seguinte (preenchendo os colchetes):

> "Aqui está a estrutura de dados JSON que meu sistema MTConnect gera a cada segundo:
> [COLAR JSON AQUI]
>
> As regras para considerar a máquina 'Parada' são:
> [EXPLICAR REGRA]
>
> Eu quero que você substitua a simulação atual do `AutoData Dashboard` para consumir esse formato exato. Mantenha os gráficos de OEE, mas adicione um gráfico de 'Carga do Spindle' em tempo real."

**Resumo:** Não envie ZIP. Copie e cole a **estrutura de dados (JSON)** e as **regras de negócio**. Isso é o suficiente para eu recriar o dashboard perfeito para o seu cenário.