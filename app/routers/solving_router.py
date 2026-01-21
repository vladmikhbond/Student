import httpx, re
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy import and_
from sqlalchemy.orm import Session

from .login_router import get_current_user, JUDGE
from ..models.schemas import AnswerSchema
from ..dal import get_pss_db  # Функція для отримання сесії БД
from ..models.pss_models import Problem, ProblemSet, Ticket, User

# шаблони Jinja2
templates = Jinja2Templates(directory="app/templates")

router = APIRouter()

# логування
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------------ list

@router.get("/solving")
async def get_solving_list(
    request: Request,
    db: Session = Depends(get_pss_db),
    user: User=Depends(get_current_user)
):
    """
    Показує сторінку з задачами, розподіленими по задачникам.
    Враховуються лише відкриті та доступні поточному юзеру задачники.
    """
    problemsets: list[ProblemSet] = db.query(ProblemSet).all()
    open_problemsets = [ps for ps in problemsets if ps.is_open and re.match(ps.stud_filter, user.username)]

    token = request.cookies["access_token"]

    if token == "":
        # redirect to login page
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "No token"
        })

    psets = []
    for problemset in open_problemsets:
        ids = problemset.get_problem_ids()
        problems = db.query(Problem).filter(Problem.id.in_(ids)).all()
    
        psets.append({
            "id": problemset.id,
            "title": problemset.title,
            "username": problemset.username,
            "rest": problemset.rest_time,
            "problems": problems})

    return templates.TemplateResponse("solving/list.html", {"request": request, "psets": psets})

# ---------------------------- open 

@router.get("/solving/problem/{problem_id}/{pset_id}")  
async def get_solving_problem(
    problem_id: str,
    pset_id: str,
    request: Request,
    db: Session = Depends(get_pss_db),
    user: User=Depends(get_current_user)
):
    """
    Відкриває вікно для вирішення задачі.
    Створює тікет і зберігає його в базі даних, якщо це вже не зроблене раніше.
    """  
    problem = db.get(Problem, problem_id)

    # get user's ticket
    ticket = db.query(Ticket) \
        .filter(and_(Ticket.username == user.username, Ticket.problem_id == problem_id)) \
        .first()

    # create a new ticket
    if ticket is None:
        problemset:ProblemSet = db.get(ProblemSet, pset_id) 
        ticket = Ticket(
            username=user.username, 
            problem_id=problem_id, 
            records="",
            comment="",
            expire_time=problemset.close_time,            
        )
        ticket.add_record("Вперше побачив задачу.", "User saw the task for the first time.");

        try:
            db.add(ticket)
            db.commit()
        except Exception as e:
            db.rollback()
            err_mes = f"Error during a ticket creating: {e}"
            logger(err_mes)

    # show the ticket solving
    else:
        records = ticket.get_records()
        if len(records) > 1:
            problem.view = records[len(records)-1]["code"]

    # open a problem window
    dict = {"py": "python", "js": "javascript", "cs": "csharp"}
    problem.lang = dict[problem.lang] 

    return templates.TemplateResponse("solving/problem.html", {"request": request, "problem": problem})

#-------------- check (AJAX)

@router.post("/check")
async def post_check(
    answer: AnswerSchema,
    db: Session = Depends(get_pss_db),
    user: User=Depends(get_current_user)
) -> str:
    """
    Відправляє рішення задачі на перевірку до judje і повертає відповідь .
    Додає в тіскет рішення і відповідь. 
    Приймає JSON у тілі у форматі AnswerSchema.
    """

    problem_id = answer.problem_id
    solving = answer.solving

    # get a ticket
    ticket = db.query(Ticket) \
        .filter(and_(Ticket.username == user.username, Ticket.problem_id == problem_id)) \
        .first()
                              
    if ticket is None:
        raise RuntimeError("не знайдений тікет")
    if ticket.expire_time < datetime.now():
        return "Your time is over."

    problem = ticket.problem
    
    # Replace author's solving with user's one
    regex = regex_helper(problem.lang);
    if regex == None:
       return "Wrong Language" 
    newCode = re.sub(regex, solving, problem.code, count=1, flags=re.DOTALL)

    # Check user's solving
    payload = {"code": newCode, "timeout": 2000}
    url = JUDGE[problem.lang]
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
        check_message = response.text
    except Exception as e:
        return f"Error. Is url '{url}' responding?"
  
    # Write solving to the ticket
    ticket.add_record(solving, check_message)
    db.commit()
    return check_message


def regex_helper(lang:str):
    if lang == 'js' or lang == 'cs':
        return r"//BEGIN.*//END"
    elif lang == 'py':
        return r"#BEGIN.*#END"
    else:
        return None
