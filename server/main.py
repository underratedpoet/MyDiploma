from os import getenv

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
  
from routes import home, auth, profile, timbre_tests

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=getenv("SECRET_KEY", "super"))

# Middleware для обработки 401 и 400 ошибок
class RedirectOnAuthErrorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Если получен статус 401 (Unauthorized) или 400 (Bad Request), перенаправляем на /login
        if response.status_code == 401 or response.status_code == 400:
            return RedirectResponse(url="/login")
        
        return response

# Добавляем middleware в приложение
app.add_middleware(RedirectOnAuthErrorMiddleware)

# Подключаем маршруты
app.include_router(home.router)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(timbre_tests.router)

# Подключаем статику (CSS, JS)
app.mount('/static', StaticFiles(directory='static'), 'static')

