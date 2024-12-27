from fastapi import FastAPI, UploadFile, HTTPException
from pathlib import Path
import os
import random
from typing import List

app = FastAPI()

STORAGE_DIR = "file_storage"  # Базовая директория для файлового хранилища


@app.post("/upload/")
async def upload_file(directory: str, file: UploadFile):
    """
    Загружает файл в указанную директорию.
    Если файл с таким именем существует, добавляется порядковый номер.
    """
    dir_path = Path(STORAGE_DIR) / directory
    dir_path.mkdir(parents=True, exist_ok=True)  # Создаем директорию, если ее нет

    file_path = dir_path / file.filename
    base_name, ext = os.path.splitext(file.filename)
    counter = 1

    # Генерируем уникальное имя файла, если он уже существует
    while file_path.exists():
        file_path = dir_path / f"{base_name}_{counter}{ext}"
        counter += 1

    with file_path.open("wb") as f:
        content = await file.read()
        f.write(content)

    return {"message": "File uploaded successfully", "path": str(file_path)}


@app.get("/file/")
def get_file(directory: str, filename: str):
    """
    Отправляет конкретный файл из указанной директории.
    """
    file_path = Path(STORAGE_DIR) / directory / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return {
        "filename": filename,
        "content": file_path.read_bytes()
    }


@app.get("/random-file/")
def get_random_file(directory: str):
    """
    Отправляет случайный файл из указанной директории.
    """
    dir_path = Path(STORAGE_DIR) / directory
    if not dir_path.exists() or not dir_path.is_dir():
        raise HTTPException(status_code=404, detail="Directory not found")

    files = list(dir_path.iterdir())
    if not files:
        raise HTTPException(status_code=404, detail="No files in directory")

    random_file = random.choice(files)
    return {
        "filename": random_file.name,
        "content": random_file.read_bytes()
    }


@app.get("/list-files/")
def list_files(directory: str) -> List[str]:
    """
    Возвращает список всех файлов в указанной директории.
    """
    dir_path = Path(STORAGE_DIR) / directory
    if not dir_path.exists() or not dir_path.is_dir():
        raise HTTPException(status_code=404, detail="Directory not found")

    return [f.name for f in dir_path.iterdir()]
