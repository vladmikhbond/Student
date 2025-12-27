import re
from datetime import datetime, timedelta
from typing import List
from sqlalchemy import ForeignKey, String, DateTime, Integer, Text, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass

class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[str] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String)
    attr: Mapped[str] = mapped_column(String)
    lang: Mapped[str] = mapped_column(String)
    cond: Mapped[str] = mapped_column(String)
    view: Mapped[str] = mapped_column(String)
    hint: Mapped[str] = mapped_column(String)
    code: Mapped[str] = mapped_column(Text)
    author: Mapped[str] = mapped_column(String)  
    timestamp: Mapped[str] = mapped_column(DateTime)
    # nav
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="problem", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String, primary_key=True)
    
    hashed_password: Mapped[bytes] = mapped_column(LargeBinary)
    role: Mapped[str] = mapped_column(String)     # 'student', 'tutor', 'admin'


class ProblemSet(Base):
    __tablename__ = "problemsets"

    title: Mapped[str] = mapped_column(String, primary_key=True)

    username: Mapped[str] = mapped_column(String)
    problem_ids: Mapped[str] = mapped_column(Text)
    open_time: Mapped[datetime] = mapped_column(DateTime)
    open_minutes: Mapped[int] = mapped_column(Integer, default=0)
    stud_filter: Mapped[str] = mapped_column(String, default='')

    def is_open(self) -> bool:
        if self.open_time is None or self.open_minutes is None:
            return False
        limit: datetime = self.open_time + timedelta(minutes=self.open_minutes)
        return limit > datetime.now()
    
    def exspire_time(self):
        return self.open_time + timedelta(minutes=self.open_minutes)
    

class Ticket(Base):
    __tablename__ = "tickets"
 
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    username: Mapped[str] = mapped_column(String)
    problem_id: Mapped[str] = mapped_column(String, ForeignKey("problems.id", ondelete="CASCADE")) 
    records: Mapped[str] = mapped_column(Text, default="")
    comment: Mapped[str] = mapped_column(String)
    expire_time: Mapped[datetime] = mapped_column(DateTime)
    state: Mapped[int] = mapped_column(Integer, default=0) # 1 - problem is solved
    #  nav
    problem: Mapped["Problem"] = relationship(back_populates="tickets")


    def do_record(self, solving, check_message):  
        RECORD_FORMAT = "~0~{0}\n~1~{1}\n~2~{2:%Y-%m-%d %H:%M:%S}\n~3~\n"
        self.records += RECORD_FORMAT.format(solving, check_message, datetime.now())
        if check_message.startswith("OK") and self.state == 0:
            self.state = 1
    
    def get_records(self) -> List[dict[str, str]]:
        """ 
        Показ вирішень з тікету.
        """
        REGEX = r"~0~(.*?)~1~(.*?)~2~(.*?)~3~"
        matches = re.findall(REGEX, self.records, flags=re.S)
        return [{"when": m[2], "code":m[0].strip(), "check":m[1].strip()} for m in matches]