from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routes import home, auth, profile

app = FastAPI()

# Подключаем маршруты
app.include_router(home.router)
app.include_router(auth.router)
app.include_router(profile.router)

# Подключаем статику (CSS, JS)
app.mount('/static', StaticFiles(directory='static'), 'static')

