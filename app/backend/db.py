import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Caminho do banco de dados (na raiz do projeto para persistência fácil)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "telemetry.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# Engine SQLite (check_same_thread=False necessário para FastAPI + Threads MQTT)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Event(Base):
    """
    Registra transições de estado da máquina (ex: IDLE -> RUN).
    """
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    old_state = Column(String, nullable=True)
    new_state = Column(String, nullable=False) # RUN, IDLE, ALARM, OFFLINE
    reason = Column(String, nullable=True) # ex: "alarm_code", "manual_stop"

    def __repr__(self):
        return f"<Event {self.machine_id}: {self.old_state}->{self.new_state} at {self.timestamp}>"

class Cycle(Base):
    """
    Registra ciclos de produção (peças produzidas).
    """
    __tablename__ = "cycles"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String, index=True)
    
    ts_start = Column(DateTime, nullable=False)
    ts_end = Column(DateTime, nullable=False)
    duration_s = Column(Float, nullable=False)
    
    program_name = Column(String, nullable=True)
    part_count_final = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<Cycle {self.machine_id}: {self.duration_s}s at {self.ts_end}>"

# Dependência para FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
