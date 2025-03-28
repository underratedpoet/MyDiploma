from fastapi import APIRouter, Request, Depends, Form, HTTPException, Response, Body
from fastapi.templating import Jinja2Templates
import httpx
import base64
import numpy as np

from utils.user_id import get_user_id, DB_API_URL
from utils.mongo import get_user_difficulty

router = APIRouter()
templates = Jinja2Templates(directory="templates")
    
@router.get("/tests/rhythm")
async def get_bandpass_test_page(request: Request):
    """Отображает страницу теста для bandpass."""
    return templates.TemplateResponse("rhythm_test.html", {"request": request})

@router.post("/submit-test/rhythm")
async def submit_rhythm_test(request: Request, data: dict = Body(...)):
    """Обрабатывает результат теста на ритм."""
    username = get_user_id(request)   
    difficulty = await get_user_difficulty(username)
    differences = data.get("differences")
    bpm = data.get("bpm")

    if not differences or not bpm:
        raise HTTPException(status_code=422, detail="Missing data")

    # Расчет средней разницы
    average_difference = np.mean(differences) if differences else 0

    # Расчет оценки (чем меньше разница, тем выше балл)
    max_difference = 500  # Максимальная допустимая разница (мс)
    score = max(1, 100 - (average_difference / max_difference) * 100)
    if difficulty == "hard":
        score *= 1.2
    elif difficulty == "easy":
        score *= 0.8

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
            "score": int(score),
            "difficulty": difficulty
        })  

    return {
        "score": int(score),
        "average_difference": int(average_difference),
        "bpm": bpm
    }

@router.get("/tests/bpm")
async def get_bandpass_test_page(request: Request):
    """Отображает страницу теста для bandpass."""
    return templates.TemplateResponse("bpm_test.html", {"request": request})

@router.post("/submit-test/bpm")
async def submit_bpm_test(request: Request, data: dict = Body(...)):
    """Обрабатывает результат теста на угадывание BPM."""
    username = get_user_id(request)
    difficulty = await get_user_difficulty(username)
    user_bpm = data.get("user_bpm")
    real_bpm = data.get("real_bpm")

    if not user_bpm or not real_bpm:
        raise HTTPException(status_code=422, detail="Missing data")

    # Расчет разницы
    difference = abs(user_bpm - real_bpm)

    # Расчет оценки (чем меньше разница, тем выше балл)
    max_difference = 50  # Максимальная допустимая разница
    score = max(0, 100 - (difference / max_difference) * 100)
    if difficulty == "hard":
        score *= 1.2
    elif difficulty == "easy":
        score *= 0.8

    async with httpx.AsyncClient() as client:
        user_response = await client.get(f"{DB_API_URL}/users/{username}")
        if user_response.status_code != 200:
            raise HTTPException(status_code=404, detail="User not found")
        user_data = user_response.json()
        user_id = user_data["user_id"]

    async with httpx.AsyncClient() as client:
        await client.post(f"{DB_API_URL}/tests/", json={
            "user_id": user_id,
            "type_id": 7,
            "score": int(score),
            "difficulty": difficulty
        })  

    return {
        "score": int(score),
        "user_bpm": user_bpm,
        "real_bpm": real_bpm
    }

