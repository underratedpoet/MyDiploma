from os import getenv

from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi_login import LoginManager
import bcrypt
import httpx


SECRET = "supersecretkey"
DB_API_URL = getenv("DB_API_URL")  # URL сервера БД

manager = LoginManager(SECRET, "/login")

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@manager.user_loader
def get_user(username: str):
    """Получает пользователя по API запроса."""
    response = httpx.get(f"{DB_API_URL}/users/{username}")
    if response.status_code == 200:
        return response.json()
    return None

@router.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(...)
):
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode()
    user_data = {"username": username, "password_hash": hashed_password, "email": email}

    response = httpx.post(f"{DB_API_URL}/users/register", json=user_data)

    if response.status_code == 201:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("register.html", {"request": request, "error": "Ошибка регистрации"})

@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    response = httpx.post(f"{DB_API_URL}/users/authenticate", json={"username": username, "password": password})

    if response.status_code == 200:
        user = response.json()
        access_token = manager.create_access_token(data={"sub": user["username"]})
  
