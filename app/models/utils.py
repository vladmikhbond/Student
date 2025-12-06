import json
from typing import List, Tuple
from zoneinfo import ZoneInfo
from datetime import datetime
from ..models.models import Question, Ticket

#--------------------------------- time <--> str ------------------------  

FMT = "%Y-%m-%dT%H:%M"
ZONE = "Europe/Kyiv"

def time_to_str(dt: datetime) -> str:
    return dt.astimezone(ZoneInfo(ZONE)).strftime(FMT)

def str_to_time(s: str) -> datetime:
    return datetime.strptime(s, FMT) \
        .replace(tzinfo=ZoneInfo(ZONE)) \
        .astimezone(ZoneInfo("UTC"))


#---------------------------------- result of checking -----------------------

class Result:

    user_sign: list[str]
    seconds: float
    focuse_lost: int
    question: Question

    def __init__(self, db, record):                        
        """
        :param record: Один рядок з протоколу тікета, наприклад, "169;[1, 3];120;1".
        В рядку: 
            номер питання, 
            масив номерів обраних відповідей, 
            час відповіді в сек, 
            кількість втрат фокусу
        """
        quest_id, choices, seconds, focuses = Ticket.record_split(record)
        quest = db.get(Question, quest_id)
        choices = json.loads(choices)                       # choices: [1, 3]    
        self.user_sign = ['-'] * len(quest.sign)
        for i in choices:
            self.user_sign[i-1] = '+'                          #['+', '-', '+']
        self.seconds = int(seconds)
        self.focuse_lost = int(focuses)
        self.question = quest
    
    @property
    def score(self):
        return 1 if self.question.sign == self.user_sign and self.focuse_lost == 0 else 0
    

def result_from_ticket(db, ticket: Ticket) -> Tuple[float, List[Result]]:
    
    records = ticket.protocol.strip().replace("'", "").splitlines() 
    before_seconds = 0
    results = []
    for record in records[1:]:
        res = Result(db, record)
        res.seconds -= before_seconds
        before_seconds += res.seconds
        results.append(res)

    summa = sum(r.score for r in results)
    n = len(results)

    percentage = round(100 * summa / n, 0) if n > 0 else 0
    return percentage, results 



