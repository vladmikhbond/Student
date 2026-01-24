from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

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

