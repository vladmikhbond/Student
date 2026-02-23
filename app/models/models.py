import datetime as dt
from sqlalchemy import ForeignKey, String, DateTime, Integer, Text, LargeBinary, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass

class Log(Base):
    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String)
    when: Mapped[dt.datetime] = mapped_column(DateTime)
    body: Mapped[str] = mapped_column(Text)
   