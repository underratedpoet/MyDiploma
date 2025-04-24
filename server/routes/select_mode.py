from fastapi import APIRouter, Request, Depends, HTTPException, Form, Response, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import random
from utils.mongo import get_user_data, update_user_data, add_score, update_test_index
from utils.user_id import get_user_id

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Определяем типы тестов и их количество в зависимости от режима
TEST_TYPES = {
    "bandpass-gain": 1,
    "bandstop": 2,
    "effects": 3,
    "interval": 4,
    "chords": 5,
    "rhythm": 6,
    "bpm": 7,
}

MODES = {
    "exam": {"bandpass-gain": 5, "bandstop": 5, "effects": 5, "interval": 5, "chords": 5, "rhythm": 5, "bpm": 5},
    "quick_check": {"bandpass-gain": 1, "bandstop": 1, "effects": 1, "interval": 1, "chords": 1, "rhythm": 1, "bpm": 1},
    "timbre": {"bandpass-gain": 3, "bandstop": 3, "effects": 3},
    "harmonic": {"interval": 3, "chords": 3},
    "rhythm": {"rhythm": 3, "bpm": 3},
}

@router.get("/select-mode")
async def select_mode(request: Request):
    """Страница выбора режима тестирования."""
    return templates.TemplateResponse("select_mode.html", {"request": request})

@router.post("/start-test")
async def start_test(
    req: Request,
    response: Response,
    mode: str = Form(...),  # Принимаем данные из формы
    difficulty: str = Form(...)  # Принимаем данные из формы
):
    """Начинает тестирование в выбранном режиме и сложности."""
    if mode not in MODES:
        raise HTTPException(status_code=400, detail="Invalid mode")
    
    if difficulty not in ["easy", "medium", "hard"]:
        raise HTTPException(status_code=400, detail="Invalid difficulty")

    # Получаем user_id из кук или генерируем новый
    user_id = get_user_id(req)
    
    # Формируем последовательность тестов
    test_sequence = []
    for test_type, count in MODES[mode].items():
        test_sequence.extend([test_type] * count)
    
    # Перемешиваем тесты, если это не режим "Тембральный слух", "Гармонический слух" или "Ритм"
    if mode not in ["timbre", "harmonic", "rhythm"]:
        random.shuffle(test_sequence)
    
    # Сохраняем данные пользователя в MongoDB
    user_data = {
        "test_sequence": test_sequence,
        "current_test_index": 0,
        "difficulty": difficulty,
        "scores": [],
    }

    await update_user_data(user_id, user_data)
    
    next_test_type = test_sequence[0]
    return RedirectResponse(url=f"/tests/{next_test_type}", status_code=303)

@router.post("/next-test")
async def next_test(request: Request, score: int = Form(None)):
    """Переход к следующему тесту."""
    user_id = get_user_id(request)

    user_data = await get_user_data(user_id)
    print(user_data)
    
    if not user_data:
        raise HTTPException(status_code=400, detail="No active test session")

    if score is not None:
        await add_score(user_id, score)

    test_sequence = user_data["test_sequence"]
    current_test_index = user_data["current_test_index"]
    
    # Увеличиваем индекс и сохраняем в MongoDB
    new_index = current_test_index + 1
    await update_test_index(user_id, new_index)
    
    if current_test_index >= len(test_sequence) - 1:
        # Все тесты пройдены, возвращаем результаты
        scores = user_data["scores"]
        average_score = sum(scores) / len(scores) if scores else 0
        return RedirectResponse(url="/test-results", status_code=303)
    
    # Получаем следующий тест
    next_test_type = test_sequence[new_index]
    print(f"Next test type: {next_test_type}")
    
    return RedirectResponse(url=f"/tests/{next_test_type}", status_code=303)

@router.get("/test-results")
async def test_results(request: Request):
    """Отображает результаты тестирования."""
    user_id = get_user_id(request)
    user_data = await get_user_data(user_id)
    
    if not user_data:
        raise HTTPException(status_code=400, detail="No active test session")
    
    scores = user_data["scores"]
    average_score = sum(scores) / len(scores) if scores else 0
    
    return templates.TemplateResponse("test_results.html", {"request": request, "average_score": average_score})
