from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# ================================================================

USERS_DB = "sqlite:////data/Users.db"

engine_users = create_engine(
    USERS_DB,
    echo=True,
    connect_args={"check_same_thread": False}  # потрібно для SQLite + багатопоточного доступу
)

SessionLocalUsers = sessionmaker(
    bind=engine_users,
    class_=Session,
    expire_on_commit=False
)

def get_users_db():
    with SessionLocalUsers() as session:
        try:
            yield session
        finally:
            session.close()

# --------------------------- Attend.db ------------------------

ATTEND_DB = "sqlite:////data/Attend.db"

# Створюємо engine 
engine_attend = create_engine(
    ATTEND_DB,
    echo=True,
    connect_args={"check_same_thread": False}  # потрібно для SQLite + багатопоточного доступу
)

# Створюємо фабрику сесій
SessionLocal = sessionmaker(
    bind=engine_attend,
    class_=Session,
    expire_on_commit=False
)

# Dependency для роутерів
def get_attend_db():
    with SessionLocal() as session:
        try:
            yield session
        finally:
            session.close()


# ================================================================

# from models.models import Base
# if __name__ == "__main__":
#     Base.metadata.create_all(engine)

