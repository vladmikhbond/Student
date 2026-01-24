from sqlalchemy import String, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase


class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String, primary_key=True)
    
    hashed_password: Mapped[bytes] = mapped_column(LargeBinary)
    role: Mapped[str] = mapped_column(String)     # 'student', 'tutor', 'admin'
