import re
from datetime import datetime, timedelta
from typing import List, TypedDict
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

    @property
    def inline(self):
        """attr, title in one line"""
        return f"{self.attr}/{self.title}"[:80]

class User(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String, primary_key=True)
    
    hashed_password: Mapped[bytes] = mapped_column(LargeBinary)
    role: Mapped[str] = mapped_column(String)     # 'student', 'tutor', 'admin'


class ProblemSet(Base):
    __tablename__ = "problemsets"

    id: Mapped[str] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String)
    username: Mapped[str] = mapped_column(String)
    problem_ids: Mapped[str] = mapped_column(Text)
    open_time: Mapped[datetime] = mapped_column(DateTime)
    open_minutes: Mapped[int] = mapped_column(Integer, default=0)
    stud_filter: Mapped[str] = mapped_column(String, default='')

# --------------- problem_ids methods
    
    def get_problem_ids(self) -> List[str]:
        """return list of problem ids"""
        if not self.problem_ids:
            return []
        return self.problem_ids.split("\n")

    def set_problem_ids(self, lst: List[str] ):
        """return list of problem ids"""
        self.problem_ids = "\n".join(lst)

# --------------- time props

    @property
    def close_time(self) -> datetime: 
        if self.open_minutes == 0:
            return datetime.max
        return self.open_time + timedelta(minutes=self.open_minutes)

    @property
    def rest_time(self) -> timedelta:
        """Return remaining open time, or zero if already closed."""
        if self.open_minutes == 0:
            return timedelta.max
        remaining = self.open_time - datetime.now() + timedelta(minutes=self.open_minutes)
        return max(remaining, timedelta(0))

    @property
    def is_open(self) -> bool: 
        if self.open_minutes == 0:
            return True
        return self.open_time < datetime.now() < self.close_time;

class Ticket(Base):

    class TicketRecord(TypedDict):
        when: str
        code: str
        check: str

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

# --------------- record methods

    def add_record(self, solving, check_message):  
        RECORD_FORMAT = "~0~{0}\n~1~{1}\n~2~{2:%Y-%m-%d %H:%M:%S}\n~3~\n"
        self.records += RECORD_FORMAT.format(solving, check_message, datetime.now())
        if check_message.startswith("OK") and self.state == 0:
            self.state = 1
    
    def get_records(self) -> List[TicketRecord]:
        """ 
        Показ вирішень з тікету.
        """
        REGEX = r"~0~(.*?)~1~(.*?)~2~(.*?)~3~"
        matches = re.findall(REGEX, self.records, flags=re.S)
        return [{"when": m[2], "code":m[0].strip(), "check":m[1].strip()} for m in matches]

    def when_success(self) -> datetime :
        success_records = [r for r in self.get_records() if r["check"].startswith("OK") ]
        if len(success_records) == 0:
            return datetime.min
        when = success_records[0]["when"].strip()
        return datetime.fromisoformat(when)
       