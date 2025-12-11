from app.backend.db import engine, Base

def init_db():
    print("[DB] Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("[DB] Tables created successfully.")

if __name__ == "__main__":
    init_db()
