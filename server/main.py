from os import getenv
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, ExpiredSignatureError, jwt
import logging

from routes.session import SECRET_KEY, ALGORITHM

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedirectOnAuthErrorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = request.cookies.get("auth")
        is_authenticated = False
        token_expired = False

        # Проверка токена, если он есть
        if token:
            try:
                jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                is_authenticated = True
            except ExpiredSignatureError:
                logger.warning("JWT истёк — удаляем cookie")
                token_expired = True
            except JWTError:
                logger.warning("JWT недействителен")

        # Если токен истёк — делаем logout + redirect
        if token_expired:
            response = RedirectResponse(url="/login")
            response.delete_cookie("auth")
            return response

        # Продолжаем обычную обработку
        response = await call_next(request)
        current_path = request.url.path
        logger.info(f"Request to {current_path} returned status code {response.status_code}")

        # Ошибки авторизации — если не авторизован
        if response.status_code in {401, 400, 422, 500} and not is_authenticated:
            logger.warning(f"Redirecting to /login due to status code {response.status_code}")
            return RedirectResponse(url="/login")

        # Ошибка 404 — редиректим на /profile только если есть токен
        if response.status_code == 404 and is_authenticated:
            logger.warning(f"Redirecting to /profile due to status code 404")
            return RedirectResponse(url="/profile")

        return response

# Создаем FastAPI приложение
app = FastAPI()

# Добавляем middleware
app.add_middleware(SessionMiddleware, secret_key=getenv("SECRET_KEY", "super"))
app.add_middleware(RedirectOnAuthErrorMiddleware)

# Подключаем маршруты
from routes import home, auth, profile, timbre_tests, harmonic_tests, rhythm_tests, select_mode, references, stats
app.include_router(home.router)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(timbre_tests.router)
app.include_router(harmonic_tests.router)
app.include_router(rhythm_tests.router)
app.include_router(select_mode.router)
app.include_router(references.router)
app.include_router(stats.router)

# Подключаем статику (CSS, JS)
app.mount('/static', StaticFiles(directory='static'), 'static')