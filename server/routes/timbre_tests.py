from os import getenv
import random
from fastapi import APIRouter, Request, Depends, Form, HTTPException, Response
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError
import httpx
import base64

from utils.fx_processor import one_band_eq

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

@router.get("/tests/bandpass-gain")
async def get_test_page(request: Request):
    """Отображает страницу теста."""
    return templates.TemplateResponse("bandpass_gain_test.html", {"request": request})

@router.get("/generate-test/bandpass-gain")
async def generate_test(request: Request, difficulty: str = "medium"):
    """Генерирует испытание."""
    username = get_user_id(request)
    
    async with httpx.AsyncClient() as client:
        file_response = await client.get(f"{FILE_API_URL}/random-file/", params={"directory": "testing_tracks"})
        if file_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to retrieve test file")
        original_audio = file_response.content

    async with httpx.AsyncClient() as client:
        user_response = await client.get(f"{DB_API_URL}/users/{username}")
        if user_response.status_code != 200:
            raise HTTPException(status_code=404, detail="User not found")
        user_data = user_response.json()
        print(user_data)
        user_id = user_data["user_id"]
        
    # Определяем параметры фильтра в зависимости от сложности
    filter_width = random.uniform(200, 1000) if difficulty == "easy" else random.uniform(100, 500) if difficulty == "medium" else random.uniform(50, 200)
    filter_freq = random.uniform(300, 15000)
    gain = 15 if difficulty == "easy" else 10 if difficulty == "medium" else 5
    
    processed_audio = one_band_eq(original_audio, filter_width, filter_freq, gain)

    original_audio_base64 = base64.b64encode(original_audio).decode('utf-8')
    processed_audio_base64 = base64.b64encode(processed_audio).decode('utf-8')
    
    request.session["test_data"] = {
        "user_id": user_id,
        "filter_freq": filter_freq,
        "filter_width": filter_width
    }
    print(user_id)
    
    return {
        "original_audio": original_audio_base64,
        "processed_audio": processed_audio_base64,
        "filter_width": filter_width,
        "filter_freq": filter_freq,
    }

@router.post("/submit-test/bandpass-gain")
async def submit_test(request: Request, selected_freq: float = Form(...)):
    """Обрабатывает результат теста и сохраняет его."""
    test_data = request.session.get("test_data")
    if not test_data:
        raise HTTPException(status_code=400, detail="No active test session")
    
    real_freq = test_data["filter_freq"]
    error = abs(selected_freq - real_freq)
    error_percentage = (error / real_freq) * 100
    score = max(100 - (error_percentage / 0.75), 1)  # Линейное уменьшение до 0 при ошибке 80%
    
    async with httpx.AsyncClient() as client:
        await client.post(f"{DB_API_URL}/tests/", json={
            "user_id": test_data["user_id"],
            "type_id": 1,
            "score": int(score)
        })
    
    return {"score": int(score), "real_freq": real_freq, "selected_freq": selected_freq}
