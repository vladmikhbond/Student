from fastapi import FastAPI
from .routers import login_router, disc_router
from fastapi.staticfiles import StaticFiles
from .dal import engine_attend, engine_users
from .models.models import Base as AttendBase
from .models.users_models import Base as UsersBase

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/public", StaticFiles(directory="/data/public"), name="public")

app.include_router(login_router.router, tags=["login"])
app.include_router(disc_router.router, tags=["disc"])

# Create tables on startup
AttendBase.metadata.create_all(bind=engine_attend)
UsersBase.metadata.create_all(bind=engine_users)
