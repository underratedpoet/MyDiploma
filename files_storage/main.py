from fastapi import FastAPI, UploadFile, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from pathlib import Path
import random
import os

app = FastAPI()

STORAGE_DIR = "fs"  # Базовая директория для файлового хранилища
TESTING_TRACKS_DIR = "fs/testing_tracks"  # Директория для тестовых треков

# Создаём базовые директории, если их нет
Path(STORAGE_DIR).mkdir(parents=True, exist_ok=True)
Path(TESTING_TRACKS_DIR).mkdir(parents=True, exist_ok=True)



@app.post("/upload/")
async def upload_file(directory: str, file: UploadFile):
    """
    Загружает файл в указанную директорию.
    В папке avatars файл перезаписывается,
    в других папках создается уникальное имя при необходимости.
    """
    dir_path = Path(STORAGE_DIR) / directory
    dir_path.mkdir(parents=True, exist_ok=True)  # Создание директории, если отсутствует

    file_path = dir_path / file.filename
    base_name, ext = os.path.splitext(file.filename)
    counter = 1

    if directory == "avatars":
        # В avatars всегда перезаписываем
        pass
    else:
        # Генерация уникального имени файла
        while file_path.exists():
            file_path = dir_path / f"{base_name}_{counter}{ext}"
            counter += 1

    # Сохраняем файл
    content = await file.read()
    with file_path.open("wb") as f:
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

    return FileResponse(file_path, media_type="application/octet-stream", filename=filename)


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
    return FileResponse(random_file, media_type="application/octet-stream", filename=random_file.name)

@app.get("/send-tracks/")
def send_tracks(
    count: int = Query(1, ge=1, le=10),
    filter: str = Query(None, description="Фильтр для названия файла (например, 'bass')")
):
    """
    Отправляет от 1 до 10 треков из папки `testing_tracks`.
    Если указан фильтр, выбираются только файлы, название которых начинается с указанного фильтра.
    """
    try:
        # Получаем список всех файлов в папке
        files = list(Path(TESTING_TRACKS_DIR).iterdir())
        if not files:
            raise HTTPException(status_code=404, detail="Треки не найдены.")

        # Если указан фильтр, выбираем только файлы, начинающиеся с фильтра
        if filter:
            files = [file for file in files if file.name.startswith(filter)]
            if not files:
                raise HTTPException(status_code=404, detail=f"Треки, начинающиеся с '{filter}', не найдены.")

        # Если файлов меньше, чем запрашивается, возвращаем их все
        count = min(count, len(files))

        # Выбираем случайные файлы
        selected_files = random.sample(files, count)

        # Создаём поток для передачи нескольких файлов
        def file_stream():
            for file in selected_files:
                yield file.read_bytes()

        # Возвращаем поток как ответ
        return StreamingResponse(file_stream(), media_type="application/octet-stream")

    except HTTPException as http_exc:
        # Обрабатываем исключения HTTP с кодами ошибок, например, 404
        raise http_exc
    except Exception as e:
        # Обрабатываем другие ошибки, отправляя код 500
        print(f"Ошибка: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при отправке треков: {e}")