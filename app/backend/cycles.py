from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Dict
from backend.persistence import persist_state_transition, persist_cycle

@dataclass
class CycleState:
    machine_id: str
    last_run_start: Optional[datetime] = None
    last_run_end: Optional[datetime] = None
    last_piece_timestamp: Optional[datetime] = None
    last_part_count: Optional[int] = None
    last_cycle_machine_s: Optional[float] = None
    last_cycle_total_s: Optional[float] = None
    current_program: Optional[str] = None

class CycleTracker:
    def __init__(self):
        self._state: Dict[str, CycleState] = {}

    def _get_state(self, machine_id: str) -> CycleState:
        if machine_id not in self._state:
            self._state[machine_id] = CycleState(machine_id=machine_id)
        return self._state[machine_id]

    def get_state(self, machine_id: str) -> Optional[CycleState]:
        """Retorna o estado atual da máquina, se existir."""
        return self._state.get(machine_id)

    def update(
        self,
        machine_id: str,
        *,
        now: datetime,
        state: Optional[str],        # "RUN", "IDLE", "ALARM", etc.
        part_count: Optional[int] = None,   # contador de peças lido da FANUC
        program_name: Optional[str] = None
    ) -> CycleState:
        if not state:
            return self._get_state(machine_id)

        cycle_state = self._get_state(machine_id)
        normalized_state = state.upper()
        
        # Retrieve previous state (stored dynamically)
        previous_state = getattr(cycle_state, 'current_state', None)

        # --- PERSISTENCE: State Transitions ---
        if previous_state and normalized_state != previous_state:
            # Detect change
            persist_state_transition(
                machine_id=machine_id,
                old_state=previous_state,
                new_state=normalized_state,
                timestamp=now,
                reason=None # TODO: Pass reason if available (e.g. alarm code)
            )

        # Update current program if provided
        if program_name:
            cycle_state.current_program = program_name

        # --- Logic: Cycle Detection ---
        
        # 1. Part Count Strategy (Priority)
        if part_count is not None:
            if cycle_state.last_part_count is None:
                # Init
                cycle_state.last_part_count = part_count
                cycle_state.last_piece_timestamp = now
            elif part_count > cycle_state.last_part_count:
                # Part finished
                if cycle_state.last_piece_timestamp:
                    cycle_total = (now - cycle_state.last_piece_timestamp).total_seconds()
                    # Filter crazy values (e.g. < 1s)
                    if cycle_total > 1.0:
                        cycle_state.last_cycle_total_s = cycle_total
                        
                        # PERSISTENCE: Cycle Finished
                        persist_cycle(
                            machine_id=machine_id,
                            ts_start=cycle_state.last_piece_timestamp,
                            ts_end=now,
                            duration_s=cycle_total,
                            program_name=cycle_state.current_program,
                            part_count_final=part_count
                        )
                
                cycle_state.last_piece_timestamp = now
                cycle_state.last_part_count = part_count
        
        # 2. Machine Cycle Tracking (RUN duration)
        is_running = (normalized_state == "RUN" or normalized_state == "ACTIVE")
        was_running = (previous_state == "RUN" or previous_state == "ACTIVE")
        
        if is_running and not was_running:
            # Start of RUN
            cycle_state.last_run_start = now
            
        elif not is_running and was_running:
            # End of RUN
            if cycle_state.last_run_start:
                cycle_state.last_run_end = now
                machine_cycle = (now - cycle_state.last_run_start).total_seconds()
                if machine_cycle > 1.0:
                    cycle_state.last_cycle_machine_s = machine_cycle
                    # Note: We usually prefer persisting cycles based on Part Count.
                    # Persisting run-time blocks is possible but might spam if user pauses/starts often.
                    # For now, we stick to persisting "Parts Produced".

        # Update internal state tracking
        setattr(cycle_state, 'current_state', normalized_state)
        
        return cycle_state


# Global Instance
cycle_tracker = CycleTracker()
