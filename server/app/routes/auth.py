from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models import User
import bcrypt
from fastapi.responses import RedirectResponse
from fastapi_login import LoginManager

SECRET = "supersecretkey"
manager = LoginManager(SECRET, "/login")

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@manager.user_loader
def get_user(username: str, db: Session = next(get_db())):
    return db.query(User).filter(User.username == username).first()

@router.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode()
    new_user = User(username=username, password_hash=hashed_password, email=email)
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/login", status_code=303)

@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if user and bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
        access_token = manager.create_access_token(data={"sub": user.username})
        response = RedirectResponse(url="/profile", status_code=303)
        response.set_cookie("auth", access_token)
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Неверные данные"})
