import os
from datetime import datetime

from fastapi import FastAPI, HTTPException, Body, Query
from typing import List
import psycopg2
import sys
from pydantic import BaseModel
#import bcrypt

from manager import PostgresDBManager  # Подключаем ваш класс для работы с БД
from utils.shemas import User, Test, UserUpdate, TestCategory, TestType

app = FastAPI()

def fatal_db_error(e: Exception):
    """Фатальная ошибка работы с БД — аварийное завершение приложения."""
    if isinstance(e, psycopg2.InterfaceError) or isinstance(e, psycopg2.OperationalError):
        print(f"Fatal database error detected: {str(e)}", file=sys.stderr)
        os._exit(1)

db = PostgresDBManager(
    db_name=os.getenv("POSTGRES_DB", "test_db"),
    user=os.getenv("POSTGRES_USER", "admin"),
    password=os.getenv("POSTGRES_PASSWORD", "password"),
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=int(os.getenv("POSTGRES_PORT", 5432))
)


@app.post("/users/")
def add_user(user: User):
    """Добавляет нового пользователя в БД."""
    try:
        db.add_user(user)
    except Exception as e:
        fatal_db_error(e)
    return {"message": "User added successfully"}

@app.post("/users/register")
def register_user(user: User):
    """Регистрация нового пользователя. Проверяет, существует ли пользователь с таким именем или email."""
    try:
        success = db.add_user(user)
    except Exception as e:
        fatal_db_error(e)
    if success:
        return {"message": "User registered successfully"}
    raise HTTPException(status_code=400, detail="User already exists")

class ChangePasswordRequest(BaseModel):
    username: str
    new_password: str

@app.post("/users/change_password")
async def change_password(request: ChangePasswordRequest):
    user = db.fetch_one("SELECT * FROM users WHERE username = %s", (request.username,))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_hashed_password = request.new_password#bcrypt.hashpw(request.new_password.encode("utf-8"), bcrypt.gensalt()).decode()

    try:
        db.update_password(request.username, new_hashed_password)
        return {"message": "Password updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tests/")
def add_test(test: Test):
    """Добавляет новый тест в БД."""
    try:
        db.add_test(test)
    except Exception as e:
        fatal_db_error(e)
    return {"message": "Test added successfully"}

@app.get("/user_tests/")
def get_user_tests(
    username: str = Query(..., description="Имя пользователя"),
    time_after: str = Query(..., description="Временная метка в формате ISO (например, 2023-01-01T00:00:00)")
):
    try:
        time_after_dt = datetime.fromisoformat(time_after)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format")

    try: 
        tests = db.get_tests_by_user(username=username, time_after=time_after_dt)
        #print(tests)
        return {"tests": tests or []}  # Возвращаем пустой список вместо None
    except Exception as e:
        fatal_db_error(e)



@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    """Удаляет пользователя по `user_id`."""
    try:
        db.delete_user(user_id)
    except Exception as e:
        fatal_db_error(e)
    return {"message": "User deleted successfully"}

@app.put("/users/{username}")
def update_user(username: str, user: UserUpdate = Body(...)):
    """Обновляет данные пользователя (без изменения пароля)."""
    try:
        print(user, username)
        success = db.update_user(username, user)
        print(success)
        if success:
            return {"message": "User updated successfully"}
    except Exception as e:
        print(e)
        fatal_db_error(e)
    
    raise HTTPException(status_code=400, detail="Invalid update parameters")

@app.get("/confirm_update/{token}")
async def confirm_update(token: str):
    """Подтверждает изменения, если токен действителен"""
    # Инициализация менеджера базы данных
    
    # Попытка обновить данные пользователя с помощью токена
    try:
        if db.update_user_with_token_data(token):
            return {"message": "Profile updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Invalid or expired confirmation token")
    except Exception as e:
        fatal_db_error(e)

@app.post("/users/authenticate")
def authenticate_user(data: dict):
    """Проверяет соответствие хэша пароля и имени пользователя"""
    username = data.get("username")
    password_hash = data.get("password_hash")
    
    query = "SELECT * FROM users WHERE username = %s AND password_hash = %s"
    try:
        user = db.fetch_one(query, (username, password_hash))
        if user:
            return {"username": user["username"], "email": user["email"], "role": user["role"]}
    except Exception as e:
        fatal_db_error(e)



    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/users/{username}")
def get_user(username: str):
    """Возвращает данные пользователя по `username`"""
    try:
        user = db.get_user_by_username(username)
        if user:
            return user
    except Exception as e:
        fatal_db_error(e)

    raise HTTPException(status_code=404, detail="User not found")

@app.get("/users/get_password_hash/{username}")
def get_password_hash(username: str):
    """Возвращает хеш пароля пользователя"""
    query = "SELECT password_hash FROM users WHERE username = %s"
    try:
        db.cursor.execute(query, (username,))
        result = db.cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        #print(result, username)
    except Exception as e:
        fatal_db_error(e)

    return {"password_hash": result["password_hash"]}

@app.get("/test_categories/", response_model=List[TestCategory])
def get_all_test_categories():
    """Возвращает все категории тестов."""
    try:
        return db.get_all_test_categories()
    except Exception as e:
        fatal_db_error(e)
    


@app.get("/test_types/", response_model=List[TestType])
def get_all_test_types():
    """Возвращает все типы тестов."""
    try:
        return db.get_all_test_types()
    except Exception as e:
        fatal_db_error(e)


@app.on_event("shutdown")
def shutdown():
    db.close()
