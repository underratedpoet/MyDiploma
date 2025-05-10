from os import getenv

from fastapi import APIRouter, Request, Form, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi_login import LoginManager
from datetime import datetime, timedelta
import bcrypt
import httpx

from routes.session import create_access_token
from utils.mails import send_email, generate_code, store_code, verify_code

DB_API_URL = getenv("DB_API_URL", "http://db-server:8000")

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
async def register(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    ):
    # Генерация кода
    code = await generate_code()
    await store_code(username, code)
    # Отправка письма
    send_email(
        to_email=email,
        subject="Код подтверждения изменения данных",
        body=f"Ваш код подтверждения: {code}\n\nДействует 5 минут."
    )

@router.post("/end_registration")
async def end_registration(
    request: Request, 
    username: str = Form(...), 
    password: str = Form(...), 
    email: str = Form(...), 
    verification_code: str = Form(...)
    ):
    # Проверка кода
    if not await verify_code(username, verification_code):
        return JSONResponse({"detail": "Invalid or expired verification code"}, status_code=400)
        
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode()
    user_data = {"username": username, "password_hash": hashed_password, "email": email}

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{DB_API_URL}/users/register", json=user_data)

    if response.status_code == 200:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("register.html", {"request": request, "error": "Ошибка регистрации"})

@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)):
    # Параметры пользователя
    db_response = httpx.get(f"{DB_API_URL}/users/get_password_hash/{username}")

    if db_response.status_code != 200:
        return JSONResponse({"detail": "Invalid credentials"}, status_code=400)

    password_hash = db_response.json().get("password_hash")
    
    if not password_hash or not bcrypt.checkpw(password.encode(), password_hash.encode()):
        return JSONResponse({"detail": "Invalid credentials"}, status_code=400)

    # Генерация токена
    access_token = create_access_token(data={"sub": username})
    response = RedirectResponse(url="/profile", status_code=303)
    response.set_cookie("auth", access_token, httponly=True, secure=False, samesite="Lax")

    return response