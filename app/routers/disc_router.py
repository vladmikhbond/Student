from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from ..models.pss_models import User
from .login_router import get_current_user

# шаблони Jinja2
templates = Jinja2Templates(directory="app/templates")

router = APIRouter()

# ----------------------- list of open discs
from pathlib import Path


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
