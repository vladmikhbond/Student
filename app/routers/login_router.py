import os

from fastapi.security import APIKeyCookie
import httpx
import jwt

from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, HTTPException, Request, Form, Response, Security
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from ..models.pss_models import User

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
TOKEN_LIFETIME = int(os.getenv("TOKEN_LIFETIME"))
PSS_HOST = os.getenv("PSS_HOST")

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
    url = f"{PSS_HOST}/token"
    data = {"username": username, "password": password}

    client = httpx.AsyncClient()
    try:
        pss_response = await client.post(url, data=data)
    except httpx.RequestError as e:
        raise HTTPException(500, f"{e}\nА чи працює pss_cont на :7000 у мережі докера mynet?")
    finally:
        await client.aclose()

    if pss_response.is_success:
        answer_json = pss_response.json()
        token = answer_json["access_token"]
    else: 
        return templates.TemplateResponse("login/login.html", {
            "request": request, 
            "error": f"Invalid credentials. Response status_code: {pss_response.status_code}"
        })

    redirect = RedirectResponse("/check/open_list", status_code=302)

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

@router.get("/logout")
async def logout(response: Response):
    response.delete_cookie(
        key="access_token"
    )
    return {"message": "Session ended"}   

# =================================================================

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


# def get_current_tutor(token: str = Security(cookie_scheme)):
#     user = get_current_user(token)
#     if user.role != "tutor":
#         raise HTTPException(status_code=403, detail="Permission denied: tutors only.")
#     return user
