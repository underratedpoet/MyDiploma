from os import getenv

from fastapi import APIRouter, Request, Form, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi_login import LoginManager
from datetime import datetime, timedelta
import bcrypt
import httpx

from routes.session import *

DB_API_URL = getenv("DB_API_URL", "http://db-server:8000")

router = APIRouter()
templates = Jinja2Templates(directory="templates")

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
    print(hashed_password)
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