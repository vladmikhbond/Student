from fastapi import FastAPI
from .routers import \
login_router, check_router, solving_router
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(login_router.router, tags=["login"])
app.include_router(check_router.router, tags=["check"])
app.include_router(solving_router.router, tags=["solving"])
