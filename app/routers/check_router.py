import re, random
import itertools as it
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..models.pss_models import User
from ..models.utils import result_from_ticket
from ..models.models import Seance, Ticket, Question
from ..dal import get_duro_db  # Функція для отримання сесії БД

from .login_router import get_current_user

# шаблони Jinja2
templates = Jinja2Templates(directory="app/templates")

router = APIRouter()

# ----------------------- list of open seances

@router.get("/check/open_list")
async def get_check_open_list(
    request: Request, 
    db: Session = Depends(get_duro_db),
    user: User=Depends(get_current_user)
):
    """ 
    Усі відкриті сеанси, доступні поточному юзеру (студенту).
    """
    all = db.query(Seance).all()
    seances = []
    for s in all:
        not_expired = s.open_time + timedelta(minutes=s.open_minutes) > datetime.now()
        matched = re.match(s.stud_filter, user.username) 
        if not_expired and matched:
            tickets = list(filter(lambda t: t.username == user.username, s.tickets))
            s.color = "black" if len(tickets) == 0 else "gray"
            seances.append(s)

    return templates.TemplateResponse("check/list.html", {"request": request, "seances": seances})

# --------------------------- run 

@router.get("/check/run/{seance_id}")
async def get_check_run(
    seance_id: int,
    request: Request, 
    db: Session = Depends(get_duro_db),
    user: User=Depends(get_current_user) 
):
    seance = db.get(Seance, seance_id)
    # тікети поточного юзера - в нормі лише 1
    tickets = [t for t in seance.tickets if t.username == user.username]

    if len(tickets) > 0:
        # --- ticket exists
        ticket: Ticket = tickets[0]
        # чи не прострочений тікет
        if ticket.close_time < datetime.now():
            return stopTemplateResponse(db, user.role, request, ticket, "Час сплив.")     
        # чи не скінчилися питанняя тесту
        if ticket.next_question_id is None:
            return stopTemplateResponse(db, user.role, request, ticket, "Тест завершений.")
    else:
        # --- new ticket
        seconds_from_seance_start = (datetime.now() - seance.open_time).seconds
        ticket = Ticket(
            seance_id = seance.id,
            username = user.username,
            open_time = datetime.now(),
            close_time = seance.close_time,
            number_of_questions = seance.number_of_questions,
            question_counter = 0,
            question_ids = seance.question_ids,
            protocol =f"{seconds_from_seance_start}\n",
            #
            seance = seance
        )
        db.add(ticket)
        db.commit()

    # обрати чергове питання і надисати сторінку
    return runTemplateResponse(db, user.role, request, ticket)


@router.post("/check/run/{seance_id}")
async def post_check_run(
    seance_id: int,
    request: Request, 
    db: Session = Depends(get_duro_db),
    user: User = Depends(get_current_user) 
):
    seance = db.get(Seance, seance_id)
    # тікети поточного юзера (в нормі точно 1)
    tickets = [t for t in seance.tickets if t.username == user.username]
    # чи не видалив студента викладач
    if len(tickets) == 0:
        return RedirectResponse("/check/open_list")
    ticket = tickets[0]   
    # чи не прострочений тікет
    if ticket.close_time < datetime.now():
        return stopTemplateResponse(db, user.role, request, ticket, "Час сплив.")     
    # чи не скінчилися питанняя тесту
    if ticket.next_question_id is None:
        return stopTemplateResponse(db, user.role, request, ticket, "Тест завершений.")
  
    # Зібрати дані з форми
    form = await request.form()
    choice = form.getlist('choice')      #  "['1', '4', '3']"
    focuse_lost = form.get('focusCounter', '0')

    # Зберегти відповідь
    ticket.record_to_protocol(choice, focuse_lost)
    db.commit()

    return runTemplateResponse(db, user.role, request, ticket)


@staticmethod
def stopTemplateResponse(db, role, request, ticket, reason):
    vm = {"title": f"{ticket.seance.title}", 
        "percentage": result_from_ticket(db, ticket)[0],
        "reason": reason }
    url = "check/stop.html" if role == "tutor" else "check/stop.html"
    return templates.TemplateResponse(url, {"request": request, "vm":vm})    


@staticmethod
def runTemplateResponse(db, role, request: Request, ticket: Ticket):
    question_id = ticket.next_question_id
    if question_id is None:
        return stopTemplateResponse(db, role, request, ticket, "Тест завершений.")
    
    question = db.get(Question, question_id)
    shuffled_answers = list(enumerate(question.answers.splitlines(), start=1))
    random.shuffle(shuffled_answers)
    vm = {
        "question": question,
        "answers": shuffled_answers,
        "seance_title": ticket.seance.title,
        "question_counter": ticket.question_counter + 1,
        "number_of_questions": ticket.number_of_questions,
        "rest_seconds": (ticket.close_time - datetime.now()).seconds
    }
    no_cache_headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0"
    }

    return templates.TemplateResponse("check/run.html", 
        {"request": request,  "vm": vm}, headers=no_cache_headers)        
