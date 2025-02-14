from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from models import User
from fastapi_login.exceptions import InvalidCredentialsException
from fastapi_login import LoginManager

SECRET = "supersecretkey"
manager = LoginManager(SECRET, "/login")

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/profile")
async def profile(request: Request, db: Session = Depends(get_db), user=Depends(manager)):
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("auth")
    return response
