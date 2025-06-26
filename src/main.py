# main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from api import router
from utils.config import settings
from utils.logging import configure_logging

SECRET_KEY = settings.SECRET_KEY

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="sessionid",
    https_only=False,
    same_site="lax",
)

app.mount("/static", StaticFiles(directory="src/api/static"), name="static")

app.include_router(router)

configure_logging()
