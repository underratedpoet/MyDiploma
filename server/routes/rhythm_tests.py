from os import getenv
import random
from fastapi import APIRouter, Request, Depends, Form, HTTPException, Response, Body
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError
import httpx
import base64
import numpy as np

router = APIRouter()
templates = Jinja2Templates(directory="templates")

DB_API_URL = getenv("DB_API_URL", "http://db-api:8000")
FILE_API_URL = getenv("FILE_API_URL", "http://file-api:8000")
SECRET_KEY = getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = getenv("ALGORITHM", "HS256")

def get_user_id(request: Request):
    """Получает ID пользователя из сессии."""
    token = request.cookies.get("auth")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
@router.get("/tests/rhythm")
async def get_bandpass_test_page(request: Request):
    """Отображает страницу теста для bandpass."""
    return templates.TemplateResponse("rhythm_test.html", {"request": request})

@router.post("/submit-test/rhythm")
async def submit_rhythm_test(request: Request, data: dict = Body(...)):
    """Обрабатывает результат теста на ритм."""
    username = get_user_id(request)
    differences = data.get("differences")
    bpm = data.get("bpm")

    if not differences or not bpm:
        raise HTTPException(status_code=422, detail="Missing data")

    # Расчет средней разницы
    average_difference = np.mean(differences) if differences else 0

    # Расчет оценки (чем меньше разница, тем выше балл)
    max_difference = 500  # Максимальная допустимая разница (мс)
    score = max(1, 100 - (average_difference / max_difference) * 100)

    async with httpx.AsyncClient() as client:
        user_response = await client.get(f"{DB_API_URL}/users/{username}")
        if user_response.status_code != 200:
            raise HTTPException(status_code=404, detail="User not found")
        user_data = user_response.json()
        user_id = user_data["user_id"]

    async with httpx.AsyncClient() as client:
        await client.post(f"{DB_API_URL}/tests/", json={
            "user_id": user_id,
            "type_id": 6,
            "score": int(score)
        })  

    return {
        "score": int(score),
        "average_difference": int(average_difference),
        "bpm": bpm
    }