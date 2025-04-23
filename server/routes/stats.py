import httpx
from datetime import datetime, timedelta

from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.templating import Jinja2Templates
from utils.user_id import get_user_id
from utils.user_id import DB_API_URL

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/stats")
async def stats(request: Request):
    username = get_user_id(request)

    # Получаем данные о тестах
    async with httpx.AsyncClient() as client:
        # Получаем тесты за последние 30 дней по умолчанию
        tests_response = await client.get(
            f"{DB_API_URL}/user_tests/",
            params={
                "username": username,
                "time_after": datetime.now() - timedelta(days=30)
            })
        
        if tests_response.status_code != 200:
            raise HTTPException(status_code=404, detail="User not found")
        
        tests_data = tests_response.json()
        stats_data = tests_data["tests"]
        
        # Получаем категории и типы тестов
        categories_response = await client.get(f"{DB_API_URL}/test_categories/")
        types_response = await client.get(f"{DB_API_URL}/test_types/")
        
        categories = categories_response.json()
        types = types_response.json()

    return templates.TemplateResponse(
        "stats.html",
        {
            "request": request,
            "stats": stats_data,
            "categories": categories,
            "types": types
        }
    )

@router.get("/update_stats")
async def update_stats(
    request: Request,
    time_after: datetime = Query(..., description="Временная метка (например, 2023-01-01T00:00:00)")
):
    username = get_user_id(request)  # Используйте реальное имя пользователя, не 'test_user'

    async with httpx.AsyncClient() as client:
        tests_response = await client.get(
            f"{DB_API_URL}/user_tests/",
            params={
                "username": username,  # Используйте полученное имя пользователя
                "time_after": time_after.isoformat()  # Явное преобразование в строку
            }
        )
        
        if tests_response.status_code != 200:
            raise HTTPException(status_code=tests_response.status_code, detail="Error fetching tests")
            
        tests_data = tests_response.json()
        stats_data = tests_data.get("tests", [])
        print(tests_response)
    
    return {"stats": stats_data}