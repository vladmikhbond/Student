from fastapi import FastAPI
# from starlette.middleware.sessions import SessionMiddleware
from .routers import \
login_router, check_router
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(login_router.router, tags=["login"])

app.include_router(check_router.router, tags=["check"])
