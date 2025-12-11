import json
import logging
from typing import Dict, Optional
from datetime import datetime
from backend.models import TelemetrySample

logger = logging.getLogger(__name__)

class FanucAdapter:
    """
    Adapter para converter payloads JSON do driver l99.driver.fanuc (MQTT)
    para o modelo canônico TelemetrySample.
    
    Suporta Veneers: StateData, ProductionData, SpindleData, Alarms.
    """
    
    def __init__(self, machine_id: str):
        self.machine_id = machine_id
        # Mantém um estado parcial porque os dados vêm em tópicos separados
        self._partial_state: Dict = {}
        self._last_update = datetime.now()

    def _unwrap_payload(self, payload):
        """
        Processa payload MQTT do Ladder99.
        - Se string, tenta json.loads.
        - Se dict, verifica se tem "state"."data", extrai de lá (formato real do driver).
        - Senão, retorna o dict.
        """
        if isinstance(payload, str):
            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse payload as JSON: {payload}")
                return {}
        elif isinstance(payload, dict):
            parsed = payload
        else:
            return {}
        
        # Formato Ladder99: {"observation": {...}, "state": {"time": ..., "data": {...}}}
        if isinstance(parsed, dict) and "state" in parsed and isinstance(parsed["state"], dict) and "data" in parsed["state"]:
            return parsed["state"]["data"]
        
        return parsed

    def ingest(self, topic_suffix: str, payload: str) -> TelemetrySample:
        """
        Ingere uma mensagem MQTT e retorna uma amostra TelemetrySample atualizada.
        topic_suffix: Parte final do tópico (ex: 'StateData', 'ProductionData')
        """
        try:
            data = json.loads(payload)
            self._partial_state[topic_suffix] = data
            self._last_update = datetime.now()
        except json.JSONDecodeError:
            logger.error(f"Falha ao decodificar JSON para {self.machine_id}/{topic_suffix}")
            return self.to_sample()

        return self.to_sample()

    def to_sample(self) -> TelemetrySample:
        """
        Consolida o estado parcial em um TelemetrySample.
        """
                # 1. State Data
        state_data_raw = self._partial_state.get('state', {})
        state_data = self._unwrap_payload(state_data_raw)
        execution = state_data.get('execution', 'READY').upper()
        mode = state_data.get('mode', 'MEM')
        
        # Extração de Tool (modal.t)
        # Ex: "modal": {"t": 505}
        modal_section = state_data.get('modal', {})
        tool_val = modal_section.get('t') if isinstance(modal_section, dict) else state_data.get('t')
        
        # Extração de Overrides
        # Ex: "override": {"feed": 100, "spindle": 100}
        override_section = state_data.get('override', {})
        feed_ovr_val = override_section.get('feed') if isinstance(override_section, dict) else state_data.get('feed_override')
        
        # Mapeamento de Estado Canônico
        # Driver: READY, ACTIVE, STOPPED, FEED_HOLD, ALARM
        # Sample: RUN, IDLE, ALARM, OFFLINE
        canonical_state = "IDLE"
        if execution == "ACTIVE":
            canonical_state = "RUN"
        elif execution == "STOPPED" or execution == "READY":
            canonical_state = "IDLE"
        
        # Se houver alarme flag, força ALARM
        if state_data.get('alarm') == 1 or state_data.get('alarm') == "TRUE":
            canonical_state = "ALARM"
            
        # 2. Production Data
        prod_data_raw = self._partial_state.get('production', {})
        prod_data = self._unwrap_payload(prod_data_raw)
        # Estrutura do driver: program: { selected: { name: "O1234" } }
        # Mas no config.system.yml eu vi veneers planos: program_name_selected="..."
        # ESPERA! O config.system.yml usa 'veneers' que já FAZEM a transformação para string/json flat?
        # NÃO. O config diz: 'publish_model: !!bool false'.
        # E o template: '{{observation.name}} ... machine=...'
        # O driver envia string formatada ou JSON? 
        # Se 'publish_model' é false, ele envia o que está no template do veneer.
        # O template do veneer no config.system.yml PARECE ser string key=value (Influx Line Protocol style?)
        # NÃO, o config.machines.yml usa 'MTConnect.NET-MQTT.dll' e topic 'fanuc/{{machine.Id}}/{{veneer.Name}}'.
        # Se publish_model=false, ele usa o template do veneer.
        # O template do veneer no config.system.yml (linhas 27+) parece CSV ou Line Protocol?
        # "mode=\"{{data.mode}}\", {{-}}execution=\"{{data.execution}}\""
        # Isso parece JSON mal formatado ou Line Protocol?
        # O `publish_model: false` é perigoso se não soubermos o formato de saída.
        # POREM, o prompt diz "driver FANUC (FOCAS) open-source" (Ladder99).
        # O padrão do Ladder99 com MQTT transport geralmente é JSON se o veneer for configurado para JSON, ou o modelo bruto se publish_model=true.
        
        # Vamos assumir que o driver manda JSON estruturado porque o 'FanucMqttDataSource' original tentava fazer 'json.loads' (embora não estivesse lá).
        # Na verdade, o código original 'FanucMqttDataSource' (datasources.py:184) fazia `payload = msg.payload.decode()`.
        # E tentava pegar `metric` do tópico.
        
        # CORREÇÃO DE ROTA:
        # O config.machines.yml diz:
        # transport: l99.driver.fanuc.transports.MQTT
        # publish_model: !!bool false
        # topic: fanuc/{{machine.Id}}/{{veneer.Name}}
        
        # Se publish_model é false, ele manda o resultado da transformação do Veneer.
        # Olhando `config.system.yml` l99.driver.fanuc.veneers.StateData:
        # {{observation.name}}, ... mode="{{data.mode}}", ...
        # Isso NÃO É JSON VÁLIDO. É um formato customizado separado por vírgulas.
        # PARECE Influx Line Protocol.
        
        # GRANDE RISCO: O driver está configurado para emitir Line Protocol (ou algo similar) no MQTT?
        # Se sim, `json.loads` vai falhar.
        
        # Vamos olhar o `config.machines.yml` novamente.
        # Na seção 'f_sim_mqtt_long' (id: f_sim_mqtt_long), ele usa MQTT.
        # E a seção system define os veneers.
        
        # Se o cliente Stark está usando a configuração padrão do Ladder99, geralmente sai JSON se usarmos `publish_model: true` ou se o veneer for um objeto.
        # Mas o config mostra Strings formatadas.
        
        # DECISÃO DE ENGENHARIA:
        # Para garantir estabilidade e facilidade, eu deveria pedir para o driver enviar JSON VÁLIDO.
        # Mas "INVARIANTS / DO NOT BREAK": Prefer config/adapters over editing its core.
        # Posso editar o `config.system.yml` para que os veneers produzam JSON?
        # SIM. O prompt diz "Prefer config/adapters". Editar a config do driver é permitido e recomendado para corrigir o formato.
        
        # PLANO REVISADO:
        # 1. Alterar `config.system.yml` para que os veneers de interesse (StateData, ProductionData, SpindleData) produzam JSON válido.
        # 2. Implementar o Adapter assumindo esse JSON.
        
        # Vamos primeiro escrever o Adapter genérico JSON, e depois ajusto o config YAML.
        
        # Dados de Produção (JSON Esperado)
        # Estrutura típica Ladder99 (publish_model=true):
        # data: {
        #   program: { selected: { name, comment, ... }, current: { name, ... } },
        #   pieces: { produced, produced_life, remaining },
        #   timers: { cycle_time_ms }
        # }

        # Programa atual: prioriza "current", cai para "selected" e por fim para chave plana
        program_section = prod_data.get('program', {}) if isinstance(prod_data, dict) else {}
        current_prog = program_section.get('current', {}) if isinstance(program_section, dict) else {}
        selected_prog = program_section.get('selected', {}) if isinstance(program_section, dict) else {}

        prog_name = (
            str(current_prog.get('name')) if current_prog.get('name') not in (None, '')
            else str(selected_prog.get('name')) if selected_prog.get('name') not in (None, '')
            else str(prod_data.get('program_name', '')) if isinstance(prod_data, dict)
            else ''
        )

        # Contador de peças: tenta estrutura nova (pieces.produced) e depois chave plana
        pieces_section = prod_data.get('pieces', {}) if isinstance(prod_data, dict) else {}
        part_count_val = None
        if isinstance(pieces_section, dict) and 'produced' in pieces_section:
            part_count_val = pieces_section.get('produced', 0)
        elif isinstance(prod_data, dict):
            part_count_val = prod_data.get('pieces_produced', 0)
        else:
            part_count_val = 0

        try:
            part_count = int(part_count_val or 0)
        except (TypeError, ValueError):
            part_count = 0
        
        # 3. Spindle Data
        spindle_data_raw = self._partial_state.get('spindle', {})
        spindle_data = self._unwrap_payload(spindle_data_raw)
        try:
            rpm = float(spindle_data.get('speed', 0))
        except (TypeError, ValueError):
            rpm = 0.0
        try:
            load = float(spindle_data.get('load', 0))
        except (TypeError, ValueError):
            load = 0.0
        
        # 4. Alarmes
        alarms_raw = self._partial_state.get('alarms', {})
        # Normaliza estrutura de alarmes: lista simples ou dict com 'alarms'
        alarms = []
        if isinstance(alarms_raw, list):
            alarms = alarms_raw
        elif isinstance(alarms_raw, dict):
            data_section = alarms_raw.get("data", alarms_raw)
            if isinstance(data_section, dict) and isinstance(data_section.get("alarms"), list):
                alarms = data_section["alarms"]

        # Assume lista de alarmes
        active_alarm_code = None
        active_alarm_msg = None
        active_alarm_sev = None
        
        if alarms and isinstance(alarms, list) and len(alarms) > 0:
            first = alarms[0]
            active_alarm_code = str(first.get('number', ''))
            active_alarm_msg = first.get('message', '')
            active_alarm_sev = 'critical' # Fanuc alarms generally stop execution
            canonical_state = "ALARM"

        return TelemetrySample(
            machine_id=self.machine_id,
            timestamp=datetime.now().isoformat(),
            state=canonical_state,
            program_name=prog_name,
            current_block=None, # Difícil pegar block real time com performance
            part_count=part_count,
            current_tool=str(tool_val) if tool_val is not None else '',
            controller_mode=mode,
            spindle_load=load,
            spindle_speed=rpm,
            # StateData não traz feed direto; podemos cair para override ou 0
            feed_rate=float(state_data.get('feed', 0)) if isinstance(state_data, dict) else 0.0,
            feed_rate_override=float(feed_ovr_val) if feed_ovr_val is not None else 0.0,
            
            cycle_time_machine_s=(
                float(prod_data.get('timers', {}).get('cycle_time_ms', 0)) / 1000.0
                if isinstance(prod_data, dict) and isinstance(prod_data.get('timers', {}), dict) and prod_data.get('timers', {}).get('cycle_time_ms')
                else None
            )
        )
        
        # Debug pontual para validar saída do adapter
        if self.machine_id == "STARK_TORNO_PILOTO":
             logger.info(f"[ADAPTER DEBUG] {self.machine_id}: State={sample.state} PC={sample.part_count} Feed={sample.feed_rate} Tool={sample.current_tool}")
        return sample
