import os

from fastapi import FastAPI, HTTPException, Body
from typing import List
from manager import PostgresDBManager  # Подключаем ваш класс для работы с БД

from utils.shemas import User, Test, UserUpdate

app = FastAPI()

db = PostgresDBManager(
    db_name=os.getenv("POSTGRES_DB", "test_db"),
    user=os.getenv("POSTGRES_USER", "admin"),
    password=os.getenv("POSTGRES_PASSWORD", "password"),
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=int(os.getenv("POSTGRES_PORT", 5432))
)


@app.post("/users/")
def add_user(user: User):
    db.add_user(user)
    return {"message": "User added successfully"}

@app.post("/users/register")
def register_user(user: User):
    success = db.add_user(user)
    if success:
        return {"message": "User registered successfully"}
    raise HTTPException(status_code=400, detail="User already exists")

@app.post("/tests/")
def add_test(test: Test):
    db.add_test(test)
    return {"message": "Test added successfully"}


@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    db.delete_user(user_id)
    return {"message": "User deleted successfully"}

@app.put("/users/{username}")
def update_user(username: str, user: UserUpdate = Body(...)):
    """Обновляет данные пользователя (без изменения пароля)."""
    success = db.update_user(username, user)
    
    if success:
        return {"message": "User updated successfully"}
    
    raise HTTPException(status_code=400, detail="Invalid update parameters")

@app.get("/confirm_update/{token}")
async def confirm_update(token: str):
    """Подтверждает изменения, если токен действителен"""
    # Инициализация менеджера базы данных
    
    # Попытка обновить данные пользователя с помощью токена
    if db.update_user_with_token_data(token):
        return {"message": "Profile updated successfully"}
    else:
        raise HTTPException(status_code=400, detail="Invalid or expired confirmation token")

@app.post("/users/authenticate")
def authenticate_user(data: dict):
    """Проверяет соответствие хэша пароля и имени пользователя"""
    username = data.get("username")
    password_hash = data.get("password_hash")
    
    query = "SELECT * FROM users WHERE username = %s AND password_hash = %s"
    user = db.fetch_one(query, (username, password_hash))

    if user:
        return {"username": user["username"], "email": user["email"], "role": user["role"]}

    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/users/{username}")
def get_user(username: str):
    """Возвращает данные пользователя по `username`"""
    user = db.get_user_by_username(username)
    if user:
        return user
    raise HTTPException(status_code=404, detail="User not found")

@app.get("/users/get_password_hash/{username}")
def get_password_hash(username: str):
    """Возвращает хеш пароля пользователя"""
    query = "SELECT password_hash FROM users WHERE username = %s"
    db.cursor.execute(query, (username,))
    result = db.cursor.fetchone()
    print(result, username)

    if not result:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return {"password_hash": result["password_hash"]}

@app.get("/test_categories/", response_model=List[Test])
def get_all_test_categories():
    return db.get_all_test_categories()


@app.get("/test_types/", response_model=List[Test])
def get_all_test_types():
    return db.get_all_test_types()


@app.on_event("shutdown")
def shutdown():
    db.close()
