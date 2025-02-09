import os

from fastapi import FastAPI, HTTPException, Depends
from typing import List
from manager import PostgresDBManager  # Подключаем ваш класс для работы с БД

from utils.shemas import User, Test

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


@app.post("/tests/")
def add_test(test: Test):
    db.add_test(test)
    return {"message": "Test added successfully"}


@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    db.delete_user(user_id)
    return {"message": "User deleted successfully"}


@app.put("/users/{user_id}")
def update_user(user_id: int, user: User):
    success = db.update_user(user_id, **user.dict(exclude_unset=True))
    if success:
        return {"message": "User updated successfully"}
    raise HTTPException(status_code=400, detail="Invalid update parameters")


@app.get("/users/verify")
def verify_user_credentials(username: str, password_hash: str):
    if db.verify_user_credentials(username, password_hash):
        return {"message": "Credentials are valid"}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.get("/test_categories/", response_model=List[Test])
def get_all_test_categories():
    return db.get_all_test_categories()


@app.get("/test_types/", response_model=List[Test])
def get_all_test_types():
    return db.get_all_test_types()


@app.on_event("shutdown")
def shutdown():
    db.close()
