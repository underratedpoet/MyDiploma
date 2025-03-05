from os import getenv
import random
from fastapi import APIRouter, Request, Depends, Form, HTTPException, Response
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError
import httpx
import base64

from utils.harmonic_processor import get_notes_wav, get_chords_wav
from utils.structures import Chord, Note, generate_chord_progression, generate_random_interval

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
    
async def generate_interval_test(request: Request, difficulty: str = "medium"):
    """Общие действия для генерации тестов: bandpass-gain и bandstop."""
    username = get_user_id(request)

    async with httpx.AsyncClient() as client:
        user_response = await client.get(f"{DB_API_URL}/users/{username}")
        if user_response.status_code != 200:
            raise HTTPException(status_code=404, detail="User not found")
        user_data = user_response.json()
        user_id = user_data["user_id"]
    
    # Обрабатываем фильтр в зависимости от типа (bandpass или bandstop)
    notes, interval = generate_random_interval()
    interval_audio = get_notes_wav(notes)

    interval_audio_base64 = base64.b64encode(interval_audio).decode('utf-8')
    
    request.session["test_data"] = {
        "user_id": user_id,
        "interval": interval
    }
    
    return {
        "interval_audio": interval_audio_base64,
        "interval": interval
    }

@router.get("/tests/interval")
async def get_bandpass_test_page(request: Request):
    """Отображает страницу теста для bandpass."""
    return templates.TemplateResponse("intervals_test.html", {"request": request})

@router.get("/generate-test/interval")
async def generate_bandpass_test(request: Request, difficulty: str = "medium"):
    """Генерирует испытание для bandpass-gain."""
    return await generate_interval_test(request, difficulty)

@router.post("/submit-test/interval")
async def submit_bandstop_test(request: Request, selected_interval: int = Form(...)):
    """Обрабатывает результат теста bandstop и сохраняет его."""
    return await submit_interval_test(request, selected_interval)

async def submit_interval_test(request: Request, selected_interval: int):
    """Обрабатывает результат теста и сохраняет его (для обоих типов фильтров)."""
    test_data = request.session.get("test_data")
    if not test_data:
        raise HTTPException(status_code=400, detail="No active test session")
    
    real_interval = test_data["interval"]
    

    score = 100 if real_interval == selected_interval else 1
    print(real_interval, selected_interval, score)
    
    async with httpx.AsyncClient() as client:
        await client.post(f"{DB_API_URL}/tests/", json={
            "user_id": test_data["user_id"],
            "type_id": 4,  # В зависимости от типа фильтра
            "score": int(score)
        })
    
    return {"score": int(score), "real_interval": real_interval, "selected_interval": selected_interval}
