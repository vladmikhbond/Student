import os
import bcrypt

from fastapi.security import APIKeyCookie
import httpx
import jwt

from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, HTTPException, Request, Form, Response, Security
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.dal import get_users_db

from ..models.pss_models import User

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
TOKEN_LIFETIME = int(os.getenv("TOKEN_LIFETIME"))
TOKEN_URL = os.getenv("TOKEN_URL")

JUDGE = {"cs": "http://judge_cs_cont:7010/verify",
         "py": "http://judge_py_cont:7011/verify",
         "js": "http://judge_js_cont:7012/verify"}

# шаблони Jinja2
templates = Jinja2Templates(directory="app/templates")

router = APIRouter()

# ----------------------- login

@router.get("/")
async def get_login(request: Request):
    return templates.TemplateResponse("login/login.html", {"request": request})


@router.post("/")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    client = httpx.AsyncClient()
    try:
        client_response = await client.post(
                TOKEN_URL, data={"username": username, "password": password})
    except httpx.RequestError as e:
        raise HTTPException(500, e)
    finally:
        await client.aclose()

    if client_response.is_success:
        token = client_response.json()
    else: 
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": f"Invalid credentials. Response status_code: {client_response.status_code}"
        })

    redirect = RedirectResponse("/solving", status_code=302)

    # Встановлюємо cookie у відповідь
    redirect.set_cookie(
        key="access_token",
        value=token,
        httponly=True,        # ❗ Забороняє доступ з JS
        # secure=True,        # ❗ Передавати лише по HTTPS
        samesite="lax",       # ❗ Захист від CSRF
        max_age=TOKEN_LIFETIME * 60,  # in seconds 
    )
    return redirect

# ----------------------------------- logout

@router.get("/login/logout")
async def logout(request: Request):
    resp = templates.TemplateResponse("login/login.html", {"request": request})
    resp.delete_cookie("access_token", path="/")
    return resp


# --------------------------- aux

# описуємо джерело токена (cookie)
cookie_scheme = APIKeyCookie(name="access_token")

def get_current_user(token: str = Security(cookie_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    else:
        return User(username=payload.get("sub"), role=payload.get("role"))

# ----------------------- password

@router.get("/pass")
async def get_pass(
    request: Request, 
    user: User = Depends(get_current_user) 
):
    return templates.TemplateResponse("login/pass.html", {"request": request})

@router.post("/pass")
async def post_pass (
    request: Request,
    password: str = Form(...),
    db: Session = Depends(get_users_db),
    current_user: User = Depends(get_current_user) 
):
    user = db.get(User, current_user.username);
    if not user:
        raise HTTPException(400)
    user.hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    try:
        db.commit()
    except:
        error = "Не вдалося змінити пароль"
        return templates.TemplateResponse("login/pass.html", {"request": request, "error": error}) 
     
    return templates.TemplateResponse("login/login.html", {"request": request})


