from os import getenv
import random
from fastapi import APIRouter, Request, Depends, Form, HTTPException, Response
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError
import httpx
import base64

from utils.fx_processor import one_band_eq, apply_random_effect
from utils.user_id import get_user_id, FILE_API_URL, DB_API_URL
from utils.mongo import get_user_difficulty
from routes.session import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

async def generate_eq_test(request: Request, difficulty: str = "medium", filter_type: int = 1):
    """Общие действия для генерации тестов: bandpass-gain и bandstop."""
    username = get_user_id(request)
    difficulty = await get_user_difficulty(username)
    
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
        user_id = user_data["user_id"]
        
    # Определяем параметры фильтра в зависимости от сложности
    filter_width = random.uniform(1500, 1000) if difficulty == "easy" else random.uniform(700, 1000) if difficulty == "medium" else random.uniform(200, 500)
    filter_freq = random.uniform(1600, 18000)
    gain = 15 if difficulty == "easy" else 10 if difficulty == "medium" else 5
    
    # Обрабатываем фильтр в зависимости от типа (bandpass или bandstop)
    processed_audio = one_band_eq(original_audio, filter_width, filter_freq, gain if filter_type == 1 else -1)

    original_audio_base64 = base64.b64encode(original_audio).decode('utf-8')
    processed_audio_base64 = base64.b64encode(processed_audio).decode('utf-8')
    
    request.session["test_data"] = {
        "user_id": user_id,
        "filter_freq": filter_freq,
        "filter_width": filter_width
    }
    
    return {
        "original_audio": original_audio_base64,
        "processed_audio": processed_audio_base64,
        "filter_width": filter_width,
        "filter_freq": filter_freq,
    }

async def do_generate_effects_test(request: Request, difficulty: str = "medium"):
    username = get_user_id(request)
    difficulty = await get_user_difficulty(username)

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
        user_id = user_data["user_id"] 

    processed_audio, effect_type = apply_random_effect(audio_bytes=original_audio, difficulty=difficulty) 

    original_audio_base64 = base64.b64encode(original_audio).decode('utf-8')
    processed_audio_base64 = base64.b64encode(processed_audio).decode('utf-8')

    request.session["test_data"] = {
        "user_id": user_id,
        "effect": effect_type,
    }    

    return {
        "original_audio": original_audio_base64,
        "processed_audio": processed_audio_base64,
        "effect": effect_type
    }    


@router.get("/tests/bandpass-gain")
async def get_bandpass_test_page(request: Request, username: str = Depends(get_current_user)):
    """Отображает страницу теста для bandpass."""
    return templates.TemplateResponse("bandpass_gain_test.html", {"request": request})

@router.get("/generate-test/bandpass-gain")
async def generate_bandpass_test(request: Request, difficulty: str = "medium", username: str = Depends(get_current_user)):
    """Генерирует испытание для bandpass-gain."""
    return await generate_eq_test(request, difficulty, filter_type=1)

@router.get("/tests/effects")
async def get_effects_test_page(request: Request, username: str = Depends(get_current_user)):
    """Отображает страницу теста для effects."""
    return templates.TemplateResponse("effects_test.html", {"request": request})

@router.get("/generate-test/effects")
async def generate_effects_test(request: Request, difficulty: str = "medium", username: str = Depends(get_current_user)):
    """Генерирует испытание для effects."""
    return await do_generate_effects_test(request, difficulty)

@router.get("/tests/bandstop")
async def get_bandstop_test_page(request: Request, username: str = Depends(get_current_user)):
    """Отображает страницу теста для bandstop."""
    return templates.TemplateResponse("bandstop_test.html", {"request": request})

@router.get("/generate-test/bandstop")
async def generate_bandstop_test(request: Request, difficulty: str = "medium", username: str = Depends(get_current_user)):
    """Генерирует испытание для bandstop."""
    return await generate_eq_test(request, difficulty, filter_type=2)

@router.post("/submit-test/bandpass-gain")
async def submit_bandpass_test(request: Request, selected_freq: float = Form(...), username: str = Depends(get_current_user)):
    """Обрабатывает результат теста bandpass-gain и сохраняет его."""
    return await do_submit_eq_test(request, selected_freq, filter_type=1)

@router.post("/submit-test/bandstop")
async def submit_bandstop_test(request: Request, selected_freq: float = Form(...), username: str = Depends(get_current_user)):
    """Обрабатывает результат теста bandstop и сохраняет его."""
    return await do_submit_eq_test(request, selected_freq, filter_type=2)

@router.post("/submit-test/effects")
async def submit_effects_test(request: Request, selected_effect: str = Form(...), username: str = Depends(get_current_user)):
    """Обрабатывает результат теста bandstop и сохраняет его."""
    return await do_submit_effects_test(request, selected_effect)

async def do_submit_effects_test(request: Request, selected_effect: str):
    """Обрабатывает результат теста и сохраняет его (для обоих типов фильтров)."""
    username = get_user_id(request)
    difficulty = await get_user_difficulty(username)
    test_data = request.session.get("test_data")
    if not test_data:
        raise HTTPException(status_code=400, detail="No active test session")

    real_effect = test_data["effect"]
    score = 100 if real_effect == selected_effect else 1

    async with httpx.AsyncClient() as client:
        await client.post(f"{DB_API_URL}/tests/", json={
            "user_id": test_data["user_id"],
            "type_id": 3,  # В зависимости от типа фильтра
            "score": int(score),
            "difficulty": difficulty
        })    

    return {"score": int(score), "real_effect": real_effect, "selected_effect": selected_effect}    

async def do_submit_eq_test(request: Request, selected_freq: float, filter_type: int):
    """Обрабатывает результат теста и сохраняет его (для обоих типов фильтров)."""
    username = get_user_id(request)
    difficulty = await get_user_difficulty(username)    
    test_data = request.session.get("test_data")
    if not test_data:
        raise HTTPException(status_code=400, detail="No active test session")
    
    real_freq = test_data["filter_freq"]
    error = abs(selected_freq - real_freq)
    error_percentage = (error / real_freq) * 100
    score = max(100 - (error_percentage / 0.75), 1)  # Линейное уменьшение до 1 при ошибке 80%
    
    async with httpx.AsyncClient() as client:
        await client.post(f"{DB_API_URL}/tests/", json={
            "user_id": test_data["user_id"],
            "type_id": filter_type,  # В зависимости от типа фильтра
            "score": int(score),
            "difficulty": difficulty
        })
    
    return {"score": int(score), "real_freq": real_freq, "selected_freq": selected_freq}
