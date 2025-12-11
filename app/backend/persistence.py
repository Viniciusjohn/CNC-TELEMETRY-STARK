from datetime import datetime
from typing import Optional
import logging
from backend.db import SessionLocal, Event, Cycle

logger = logging.getLogger(__name__)

def persist_state_transition(
    machine_id: str,
    old_state: str,
    new_state: str,
    timestamp: datetime,
    reason: Optional[str] = None
):
    """
    Grava uma transição de estado no banco de dados.
    Cria uma sessão nova e fecha imediatamente.
    """
    db = SessionLocal()
    try:
        event = Event(
            machine_id=machine_id,
            timestamp=timestamp,
            old_state=old_state,
            new_state=new_state,
            reason=reason
        )
        db.add(event)
        db.commit()
        logger.debug(f"[DB] Saved Event: {machine_id} {old_state}->{new_state}")
    except Exception as e:
        logger.error(f"[DB] Failed to save event: {e}")
    finally:
        db.close()

def persist_cycle(
    machine_id: str,
    ts_start: datetime,
    ts_end: datetime,
    duration_s: float,
    program_name: Optional[str] = None,
    part_count_final: Optional[int] = None
):
    """
    Grava um ciclo de produção finalizado.
    """
    # Validação básica para evitar lixo
    if duration_s < 0.5:
        return

    db = SessionLocal()
    try:
        cycle = Cycle(
            machine_id=machine_id,
            ts_start=ts_start,
            ts_end=ts_end,
            duration_s=duration_s,
            program_name=program_name,
            part_count_final=part_count_final
        )
        db.add(cycle)
        db.commit()
        logger.info(f"[DB] Saved Cycle: {machine_id} {duration_s}s")
    except Exception as e:
        logger.error(f"[DB] Failed to save cycle: {e}")
    finally:
        db.close()
