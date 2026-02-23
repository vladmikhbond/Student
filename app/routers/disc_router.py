import json
import datetime as dt
from pathlib import Path
from fastapi import APIRouter, Depends, Request, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.models.models import Log

from ..dal import get_attend_db
from ..models.users_models import User
from .login_router import get_current_user

# шаблони Jinja2
templates = Jinja2Templates(directory="app/templates")

router = APIRouter()

# ----------------------- list of open discs

@router.get("/disc/list")
async def get_disc_list(
    request: Request, 
    user: User=Depends(get_current_user)
):
    """ 
    Досліджує папку /data/public.
    """
    path = "/data/public"
    dirs = [dir.name for dir in Path(path).iterdir() if dir.is_dir()]
    return templates.TemplateResponse("disc/list.html", {"request": request, "dirs": dirs})


# ------------------- Лог перегляду лекцій (JSON)

@router.post("/disc/log")
async def post_disc_log (
    request: Request,
    user: User=Depends(get_current_user),
    db: Session = Depends(get_attend_db),
):
    body = await request.body()
    log = Log(username=user.username,
              when=dt.datetime.now(),
              body=body.decode('utf-8'))
    db.add(log)
    db.commit()

    print(log)
    return Response(status_code=204)


# from urllib.parse import unquote

# url = "1.05_%D0%A4%D1%83%D0%BD%D0%BA%D1%86%D1%96%D1%97__2_.html"
# decoded = unquote(url, encoding="utf-8")

# print(decoded)