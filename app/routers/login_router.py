import os

from fastapi.security import OAuth2PasswordRequestForm
import httpx

from fastapi import APIRouter, Depends, HTTPException, Request, Form, Response, Security
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import APIKeyCookie

from jose import jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..dal import get_users_db  # Функція для отримання сесії БД
from ..models.pss_models import User
import bcrypt

SECRET_KEY = "super-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180


# шаблони Jinja2
templates = Jinja2Templates(directory="app/templates")

router = APIRouter()

# ----------------------- login

@router.get("/", response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse("login/login.html", {"request": request})

# Вставляє JWT у HttpOnly cookie
@router.post("/")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db_users: Session = Depends(get_users_db),
):
    user = get_authenticated_user(form_data.username, form_data.password, db_users)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Створення токену
    expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    claims = {"sub": user.username, "role": user.role, "exp": datetime.now() + expires_delta}
    access_token = jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM) 

    redirect = RedirectResponse("/check/open_list", status_code=302)

    # Встановлюємо cookie у відповідь
    redirect.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,        # ❗ Забороняє доступ з JS
        # secure=True,        # ❗ Передавати лише по HTTPS
        samesite="lax",       # ❗ Захист від CSRF
        # max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # in seconds 
    )
    return redirect    
    

@router.get("/logout")
def logout(response: Response):
    response.delete_cookie(
        key="access_token"
    )
    return {"message": "Session ended"}    
# --------------------------------


def get_authenticated_user(username: str, password: str, db: Session):
    """
    Перевірка користувача
    """
    user = db.get(User, username)
    if user is None:
        return None

    ### на той випадок, якщо в базу вставляли юзера вручну
    hashed_password = user.hashed_password.encode('utf-8') \
        if isinstance(user.hashed_password, str) \
        else user.hashed_password
     
    try:
        if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
            return user
    except Exception:
        return None

    return None


# описуємо джерело токена (cookie)
cookie_scheme = APIKeyCookie(name="access_token")

def get_current_user(token: str = Security(cookie_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return User(username=payload.get("sub"), role=payload.get("role"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

