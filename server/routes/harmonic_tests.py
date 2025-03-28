from fastapi import APIRouter, Request, Depends, Form, HTTPException, Response, Body
from fastapi.templating import Jinja2Templates
import httpx
import base64

from utils.harmonic_processor import get_notes_wav, get_chords_wav
from utils.structures import Chord, Note, generate_chord_progression, generate_random_interval
from utils.user_id import get_user_id, DB_API_URL
from utils.mongo import get_user_difficulty

router = APIRouter()
templates = Jinja2Templates(directory="templates")
    
async def do_generate_interval_test(request: Request, difficulty: str = "medium"):
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

async def do_generate_chords_test(request: Request, difficulty: str = "medium"):
    """Общие действия для генерации тестов: bandpass-gain и bandstop."""
    username = get_user_id(request)
    difficulty = await get_user_difficulty(username)

    async with httpx.AsyncClient() as client:
        user_response = await client.get(f"{DB_API_URL}/users/{username}")
        if user_response.status_code != 200:
            raise HTTPException(status_code=404, detail="User not found")
        user_data = user_response.json()
        user_id = user_data["user_id"]
    
    # Обрабатываем фильтр в зависимости от типа (bandpass или bandstop)
    chords, steps = generate_chord_progression(3 if difficulty=='easy' else 4 if difficulty=='medium' else 5)
    chords_audio = get_chords_wav(chords)

    chords_audio_base64 = base64.b64encode(chords_audio).decode('utf-8')
    
    request.session["test_data"] = {
        "user_id": user_id,
        "steps": steps
    }
    
    return {
        "chords_audio": chords_audio_base64,
        "steps": steps
    }

@router.get("/tests/interval")
async def get_interval_test_page(request: Request):
    """Отображает страницу теста для bandpass."""
    return templates.TemplateResponse("intervals_test.html", {"request": request})

@router.get("/tests/chords")
async def get_chords_test_page(request: Request):
    """Отображает страницу теста для bandpass."""
    return templates.TemplateResponse("chords_test.html", {"request": request})

@router.get("/generate-test/interval")
async def generate_interval_test(request: Request, difficulty: str = "medium"):
    """Генерирует испытание для bandpass-gain."""
    return await do_generate_interval_test(request, difficulty)

@router.get("/generate-test/chords")
async def generate_chords_test(request: Request, difficulty: str = "medium"):
    """Генерирует испытание для bandpass-gain."""
    return await do_generate_chords_test(request, difficulty)

@router.post("/submit-test/interval")
async def submit_interval_test(request: Request, selected_interval: int = Form(...)):
    """Обрабатывает результат теста bandstop и сохраняет его."""
    return await do_submit_interval_test(request, selected_interval)

@router.post("/submit-test/chords")
async def submit_chords_test(request: Request, data: dict = Body(...)):
    """Обрабатывает результат теста bandstop и сохраняет его."""
    selected_steps = data.get("selected_steps")
    if not selected_steps:
        raise HTTPException(status_code=422, detail="selected_steps is required")

    return await do_submit_chords_test(request, selected_steps)

async def do_submit_interval_test(request: Request, selected_interval: int):
    """Обрабатывает результат теста и сохраняет его (для обоих типов фильтров)."""
    username = get_user_id(request)
    difficulty = await get_user_difficulty(username)
    test_data = request.session.get("test_data")
    if not test_data:
        raise HTTPException(status_code=400, detail="No active test session")
    
    real_interval = test_data["interval"]
    

    score = max(1, 100 - (abs(real_interval - selected_interval) / 24) * 100)
    if difficulty == "hard":
        score *= 1.2
    elif difficulty == "easy":
        score *= 0.8
    
    async with httpx.AsyncClient() as client:
        await client.post(f"{DB_API_URL}/tests/", json={
            "user_id": test_data["user_id"],
            "type_id": 4,  # В зависимости от типа фильтра
            "score": int(score),
            "difficulty": difficulty
        })
    
    return {"score": int(score), "real_interval": real_interval, "selected_interval": selected_interval}

async def do_submit_chords_test(request: Request, selected_steps: list[int]):
    """Обрабатывает результат теста и сохраняет его (для обоих типов фильтров)."""
    username = get_user_id(request)
    difficulty = await get_user_difficulty(username)
    test_data = request.session.get("test_data")
    if not test_data:
        raise HTTPException(status_code=400, detail="No active test session")
    
    real_steps = test_data.get("steps")
    if not real_steps:
        raise HTTPException(status_code=400, detail="No steps data in session")
    
    # Убираем первый и последний элементы из real_steps и selected_steps
    real_steps = real_steps[1:-1]  # Исключаем первый и последний элементы
    selected_steps = selected_steps[1:-1]  # Исключаем первый и последний элементы

    # Подсчет количества совпадений
    correct_count = sum(1 for real, selected in zip(real_steps, selected_steps) if real == selected)
    total_steps = len(real_steps)

    # Расчет балла
    if correct_count == total_steps:  # Все правильно
        score = 100
    elif correct_count == 0:  # Ни одного правильного
        score = 1
    else:  # Пропорциональный расчет
        score = int((correct_count / total_steps) * 100)

    print(f"Real steps: {real_steps}, Selected steps: {selected_steps}, Correct: {correct_count}/{total_steps}, Score: {score}")
    
    # Отправляем результат в базу данных
    async with httpx.AsyncClient() as client:
        await client.post(f"{DB_API_URL}/tests/", json={
            "user_id": test_data["user_id"],
            "type_id": 5,  # В зависимости от типа фильтра
            "score": int(score),
            "difficulty": difficulty
        })
    
    # Возвращаем результат
    return {
        "score": int(score),
        "real_steps": real_steps,
        "selected_steps": selected_steps,
        "correct_count": correct_count,
        "total_steps": total_steps
    }
