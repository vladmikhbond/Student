import os
import re, random
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
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
from pathlib import Path

root_dir = Path("шлях/до/каталогу")

@router.get("/disc/list")
async def get_disc_list(
    request: Request, 
    user: User=Depends(get_current_user)
):
    """ 
    Підпапки в папці /data/public.
    """
    path = "/data/public"
    dirs = [dir.name for dir in Path(path).iterdir() if dir.is_dir()]

    return templates.TemplateResponse("disc/list.html", {"request": request, "dirs": dirs})
