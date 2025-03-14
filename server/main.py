from os import getenv
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
#from aioredis import Redis, from_url
from uuid import uuid4
  
from routes import home, auth, profile, timbre_tests, harmonic_tests, rhythm_tests, select_mode

#@asynccontextmanager
#async def lifespan(app: FastAPI):
#    # Подключение к Redis при запуске
#    redis_url = getenv("REDIS_URL", "redis://localhost:6379")
#    app.state.redis = await from_url(redis_url)
#    print("Redis подключен")
#
#    yield  # Приложение работает

    # Отключение Redis при завершении
#    await app.state.redis.close()
#    print("Redis отключен")

# Создаем FastAPI приложение с lifespan
app = FastAPI()#lifespan=lifespan

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

# Зависимость для получения Redis
#async def get_redis(request: Request) -> Redis:
#    return request.app.state.redis

# Подключаем маршруты
app.include_router(home.router)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(timbre_tests.router)
app.include_router(harmonic_tests.router)
app.include_router(rhythm_tests.router)
app.include_router(select_mode.router)

# Подключаем статику (CSS, JS)
app.mount('/static', StaticFiles(directory='static'), 'static')

