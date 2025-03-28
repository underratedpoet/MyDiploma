from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, Any

# Подключение к MongoDB
MONGO_URI = "mongodb://mongo:27017"  # Используйте переменную окружения в реальном приложении
MONGO_DB = "test_db"

client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB]
users_collection = db["users"]

# Функция для получения данных пользователя по user_id
async def get_user_data(user_id: str) -> Dict[str, Any]:
    user_data = await users_collection.find_one({"_id": user_id})
    return user_data

# Функция для обновления данных пользователя
async def update_user_data(user_id: str, data: Dict[str, Any]) -> None:
    await users_collection.update_one(
        {"_id": user_id},
        {"$set": data},
        upsert=True
    )

# Функция для добавления оценки в массив scores
async def add_score(user_id: str, score: int) -> None:
    await users_collection.update_one(
        {"_id": user_id},
        {"$push": {"scores": score}}  # Добавляем оценку в массив
    )

# Функция для обновления текущего индекса теста
async def update_test_index(user_id: str, new_index: int) -> None:
    await users_collection.update_one(
        {"_id": user_id},
        {"$set": {"current_test_index": new_index}}
    )

# Функция для получения сложности пользователя
async def get_user_difficulty(user_id: str) -> str:
    user_data = await get_user_data(user_id)  # Получаем данные пользователя
    if not user_data:
        raise ValueError("User data not found")  # Если данных пользователя нет, выбрасываем ошибку
    return user_data.get("difficulty", "medium")  # Возвращаем значение сложности, по умолчанию 'medium'