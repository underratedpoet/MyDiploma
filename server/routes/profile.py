from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi_login import LoginManager
import httpx

SECRET = "supersecretkey"
DB_API_URL = "http://db-server:8000"  # URL сервера базы данных

manager = LoginManager(SECRET, "/login")

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/profile")
async def profile(request: Request, user=Depends(manager)):
    """Загружает профиль пользователя, получая данные с внешнего сервера БД."""
    response = httpx.get(f"{DB_API_URL}/users/{user['username']}")

    if response.status_code == 200:
        user_data = response.json()
        return templates.TemplateResponse("profile.html", {"request": request, "user": user_data})

    return RedirectResponse(url="/login", status_code=303)

@router.get("/logout")
async def logout():
    """Выход из системы — удаление cookie."""
    response = RedirectResponse(url="/")
    response.delete_cookie("auth")
    return response
