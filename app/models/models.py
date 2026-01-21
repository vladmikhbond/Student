from datetime import datetime, timedelta
from typing import List
from sqlalchemy import ForeignKey, String, DateTime, Integer, Text, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase

class Base(DeclarativeBase):
    pass


class Question(Base):
    __tablename__ = "questions"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    attr: Mapped[str] = mapped_column(String)
    kind: Mapped[str] = mapped_column(String)       # '!', '#' 
    text: Mapped[str] = mapped_column(Text)
    answers: Mapped[str] = mapped_column(Text)      # "+полуниця\n-яблуко\n+вишня\n-груша"

    @property
    def sign(self):
        """ ['+','-','-','+'] """ 
        return [x[0] for x in self.answers.splitlines()]       

    @property
    def just_answers(self):
        """ ['полуниця','яблуко','вишня','груша'] """
        return [x[1::] for x in self.answers.splitlines()]
    
    def __str__(self):
        return f"={self.attr}\n\n{self.kind } {self.text }\n\n{self.answers }"


class Seance(Base):
    __tablename__ = "seances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String)  # назва
    owner: Mapped[str] = mapped_column(String)
    question_ids: Mapped[str] = mapped_column(Text, default='')      # "11111 22222 33333"
    open_time: Mapped[datetime] = mapped_column(DateTime, default=None)
    open_minutes: Mapped[int] = mapped_column(Integer, default=0)   
    stud_filter: Mapped[str] = mapped_column(String, default='')
    defence: Mapped[str] = mapped_column(String)                     # "1, 100"

    # nav
    tickets: Mapped[List["Ticket"]] = relationship(back_populates="seance", cascade="all, delete-orphan")
    

    @property
    def number_of_questions(self) -> int:
        return len(self.ids_list)
    
    @property
    def close_time(self) -> datetime: 
        return self.open_time + timedelta(minutes=self.open_minutes)
    
    @property
    def ids_list(self) -> List[int]:
        return [int(i) for i in self.question_ids.split()]
    
    @property
    def focus(self) -> int:
        return int(self.defence.split(',')[0]) 
    
    @property
    def hole(self) -> int:
        return int(self.defence.split(',')[1]) 

class Ticket(Base):
    __tablename__ = "tickets"
 
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True) 
    seance_id: Mapped[int] = mapped_column(Integer, ForeignKey("seances.id", ondelete="CASCADE"))
    username: Mapped[str] = mapped_column(String)
    open_time: Mapped[datetime] = mapped_column(DateTime, default=None)
    close_time: Mapped[datetime] = mapped_column(DateTime, default=None)
    number_of_questions: Mapped[int] = mapped_column(Integer)
    question_counter: Mapped[int] = mapped_column(Integer) 
    question_ids: Mapped[str] = mapped_column(Text)      # "11111 22222 33333"
    protocol: Mapped[str] = mapped_column(Text)          # "quest_id;['1', '3'];seconds;focuses\n ..."
    #  nav
    seance: Mapped["Seance"] = relationship(back_populates="tickets")
    
    @property
    def next_question_id(self):
        lst = self.question_ids.split()
        if self.question_counter < len(lst):
            return int(lst[self.question_counter])
        return None
    
    def record_to_protocol(self, choice, focuses):
        seconds = (datetime.now() - self.open_time).seconds
        self.protocol += f"{self.next_question_id};{choice};{seconds};{focuses}\n"
        self.question_counter += 1
    
    @staticmethod
    def record_split(record):
        return record.split(';')
    