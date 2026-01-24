from fastapi import FastAPI
from .routers import login_router, disc_router
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/public", StaticFiles(directory="/data/public"), name="public")

app.include_router(login_router.router, tags=["login"])
app.include_router(disc_router.router, tags=["disc"])
