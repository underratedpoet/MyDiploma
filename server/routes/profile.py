from os import getenv

from fastapi import APIRouter, Request, Form, UploadFile, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse, Response
from fastapi_login import LoginManager
from jose import JWTError, jwt
import httpx
import bcrypt
 
from routes.session import *
from utils.mails import send_email, generate_code, store_code, verify_code

DB_API_URL = getenv("DB_API_URL", "http://db-api:8000")
FILE_API_URL = getenv("FILE_API_URL", "http://file-api:8000")

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/profile")
async def profile(request: Request):
    """Отображение профиля пользователя."""
    token = request.cookies.get("auth")
    if not token:
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise JWTError
        
        # Запрос данных пользователя
        user_response = httpx.get(f"{DB_API_URL}/users/{username}")
        if user_response.status_code != 200:
            return JSONResponse({"detail": "User not found"}, status_code=404)
        
        user_data = user_response.json()

        # Новый путь, через который FastAPI отдаст файл
        avatar_url = f"/avatar/{username}"

    except JWTError:
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user_data,
        "avatar_url": avatar_url
    })

@router.get("/avatar/{username}")
async def proxy_avatar(username: str):
    """Проксирование запроса к файловому серверу."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{FILE_API_URL}/file/", params={"directory": "avatars", "filename": f"{username}.jpg"})
    
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    return Response(content=response.content, media_type="image/jpeg")

@router.post("/update_profile")
async def update_profile(
    request: Request,
    first_name: str = Form(None),
    last_name: str = Form(None),
    email: str = Form(None),
    phone_number: str = Form(None)
):
    """Обновляет профиль пользователя"""
    token = request.cookies.get("auth")
    if not token:
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise JWTError
        
        user_data = {key: value for key, value in {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone_number": phone_number
        }.items() if value is not None}

        response = httpx.put(f"{DB_API_URL}/users/{username}", json=user_data)

        if response.status_code == 200:
            return {"message": "Profile updated successfully"}
        return JSONResponse({"detail": "Update failed"}, status_code=400)

    except JWTError:
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)


@router.post("/upload_avatar")
async def upload_avatar(request: Request, file: UploadFile):
    """Загружает новый аватар пользователя."""
    token = request.cookies.get("auth")
    if not token:
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise JWTError

        files = {"file": (f"{username}.jpg", await file.read(), file.content_type)}
        response = httpx.post(f"{FILE_API_URL}/upload/", params={"directory": "avatars"}, files=files)

        if response.status_code == 200:
            return {"message": "Avatar uploaded successfully"}
        return JSONResponse({"detail": "Upload failed"}, status_code=400)

    except JWTError:
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)


@router.post("/request_email_verification")
async def request_email_verification(request: Request):
    """Запросить код подтверждения для изменения данных."""
    token = request.cookies.get("auth")
    if not token:
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise JWTError

        # Получение email пользователя
        user_response = httpx.get(f"{DB_API_URL}/users/{username}")
        if user_response.status_code != 200:
            return JSONResponse({"detail": "User not found"}, status_code=404)

        email = user_response.json().get("email")
        if not email:
            return JSONResponse({"detail": "Email not found"}, status_code=404)

        # Генерация кода
        code = await generate_code()
        await store_code(username, code)

        # Отправка письма
        send_email(
            to_email=email,
            subject="Код подтверждения изменения данных",
            body=f"Ваш код подтверждения: {code}\n\nДействует 5 минут."
        )

        return {"message": "Verification code sent"}

    except JWTError:
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)

@router.post("/confirm_change_password")
async def confirm_change_password(
    request: Request,
    new_password: str = Form(...),
    verification_code: str = Form(...)
):
    """Подтвердить изменение пароля с кодом."""
    token = request.cookies.get("auth")
    if not token:
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise JWTError

        # Проверка кода
        if not await verify_code(username, verification_code):
            return JSONResponse({"detail": "Invalid or expired verification code"}, status_code=400)

        # Отправка запроса на смену пароля в API БД
        response = httpx.post(f"{DB_API_URL}/users/change_password", json={
            "username": username,
            "new_password": bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode()
        })

        if response.status_code == 200:
            return {"message": "Password changed successfully"}
        else:
            return JSONResponse({"detail": "Password change failed"}, status_code=400)

    except JWTError:
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)

@router.get("/logout")
async def logout():
    """Выход из системы — удаление cookie."""
    response = RedirectResponse(url="/")
    response.delete_cookie("auth")
    return response
