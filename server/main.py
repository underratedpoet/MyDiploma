from os import getenv

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
  
from routes import home, auth, profile, timbre_tests

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=getenv("SECRET_KEY", "super"))


# Подключаем маршруты
app.include_router(home.router)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(timbre_tests.router)

# Подключаем статику (CSS, JS)
app.mount('/static', StaticFiles(directory='static'), 'static')

