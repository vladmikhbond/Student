from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from sqlalchemy import event
from sqlalchemy.engine import Engine

# Підтримка foreign keys для SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# ================================================================
DURO_DB = "sqlite:////data/Durometer.db"


# Створюємо engine 
engine = create_engine(
    DURO_DB,
    echo=True,
    connect_args={"check_same_thread": False}  # потрібно для SQLite + багатопоточного доступу
)

# Створюємо фабрику сесій
SessionLocalDuro = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency для роутерів
def get_duro_db():
    db: Session = SessionLocalDuro()
    try:
        yield db
    finally:
        db.close()
        
# ================================================================
PSS_DB = "sqlite:////data/PSS.db"

# Створюємо engine 
engine = create_engine(
    PSS_DB,
    echo=True,
    connect_args={"check_same_thread": False}  # потрібно для SQLite + багатопоточного доступу
)

# Створюємо фабрику сесій
SessionLocalPss = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency для роутерів
def get_pss_db():
    db: Session = SessionLocalPss()
    try:
        yield db
    finally:
        db.close()

# ================================================================
USERS_DB = "sqlite:////data/Users.db"

engine_users = create_engine(
    USERS_DB,
    echo=True,
    connect_args={"check_same_thread": False}  # потрібно для SQLite + багатопоточного доступу
)

SessionLocalUsers = sessionmaker(autocommit=False, autoflush=False, bind=engine_users)

def get_users_db():
    db: Session = SessionLocalUsers()
    try:
        yield db
    finally:
        db.close()

# ================================================================

# from models.models import Base
# if __name__ == "__main__":
#     Base.metadata.create_all(engine)

