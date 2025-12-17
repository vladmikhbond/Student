import httpx, re
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy import and_
from sqlalchemy.orm import Session

from .login_router import get_current_user, PSS_HOST
from ..models.schemas import ProblemHeaderSchema, AnswerSchema
from ..dal import get_pss_db  # Функція для отримання сесії БД
from ..models.pss_models import Problem, ProblemSet, Ticket, User

# шаблони Jinja2
templates = Jinja2Templates(directory="app/templates")

router = APIRouter()

# логування
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.get("/solving")
async def get_solveing(
    request: Request,
    db: Session = Depends(get_pss_db),
    user: User=Depends(get_current_user)
):
    """
    Показує сторінку з задачами, розподіленими по задачникам.
    Враховуються лише відкриті та доступні поточному юзеру задачники.
    """
    problemsets: list[ProblemSet] = db.query(ProblemSet).all()
    open_problemsets = [ps for ps in problemsets if ps.is_open() and re.match(ps.stud_filter, user.username)]

    token = request.cookies["access_token"]

    if token == "":
        # redirect to login page
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "No token"
        })

    headers = {"Authorization": f"Bearer {token}"}
    psets = []
    for problemset in open_problemsets:
        pheaders = []
        for id in problemset.problem_ids.split():
            api_url = f"{PSS_HOST}/api/problems/{id}"
            async with httpx.AsyncClient() as client:
                response = await client.get(api_url, headers=headers)
                if response.is_success:
                    json = response.json()                    

                    problem_header = ProblemHeaderSchema(
                        id=json["id"], 
                        title=json["title"], 
                        attr=json["attr"])
                    pheaders.append(problem_header)

        rest_time: timedelta = problemset.open_time - \
            datetime.now() + timedelta(minutes=problemset.open_minutes)
        psets.append({
            "title": problemset.title,         #TODO  encode
            "username": problemset.username,
            "t": rest_time,
            "headers": pheaders})

    return templates.TemplateResponse("solving/list.html", {"request": request, "psets": psets})


@router.get("/solving/problem/{problem_id}/{pset_title}")  
async def get_solveing_problem(
    problem_id: str,
    pset_title: str,
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
        problemset:ProblemSet = db.query(ProblemSet).get(pset_title)
        ticket = Ticket(
            username=user.username, 
            problem_id=problem_id, 
            records="",
            comment="",
            expire_time=problemset.exspire_time(),            
        )
        ticket.do_record("Вперше побачив задачу.", "User saw the task for the first time.");

        try:
            db.add(ticket)
            db.commit()
        except Exception as e:
            db.rollback()
            err_mes = f"Error during a ticket creating: {e}"
            logger(err_mes)
    # show last solving
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
    Відправляє рішення задачі на перевірку до PSS і повертає відповідь від PSS.
    Додає в тіскет рішення і відповідь. 
    """
    
    # get a ticket
    ticket = db.query(Ticket) \
        .filter(and_(Ticket.username == user.username, Ticket.problem_id == answer.problem_id)) \
        .first()
                              
    if ticket is None:
        raise RuntimeError("не знайдений тікет")
    if ticket.expire_time < datetime.now():
        return "Your time is over."

    api_url = f"{PSS_HOST}/api/check"
    data = {"id": answer.problem_id, "solving": answer.solving}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=data)
        check_message: str = response.json()
    except Exception as e:
        err_message = f"Error during a check solving: {e}"
        print(err_message)
        return err_message
  
    # write solving to the ticket
    ticket.do_record(answer.solving, check_message)
    db.commit()
    return check_message


