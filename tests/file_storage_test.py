import os
from pathlib import Path
from fastapi.testclient import TestClient
from files_storage.main import app, STORAGE_DIR, TESTING_TRACKS_DIR
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = TestClient(app)

# Настройка тестовой среды
def setup_module(module):
    """Создание базовых директорий и тестовых файлов перед запуском тестов."""
    Path(STORAGE_DIR).mkdir(parents=True, exist_ok=True)
    Path(TESTING_TRACKS_DIR).mkdir(parents=True, exist_ok=True)

    # Создание тестовых файлов
    for i in range(1, 6):
        with open(Path(TESTING_TRACKS_DIR) / f"track_{i}.wav", "wb") as f:
            f.write(os.urandom(1024))  # Генерация случайного содержимого


def teardown_files():
    """Удаление файлов, созданных во время тестов."""
    for file in Path(TESTING_TRACKS_DIR).iterdir():
        file.unlink()


# Тесты для метода get_file
def test_get_file():
    """Тест успешного получения файла."""
    filename = "track_1.wav"
    response = client.get(f"/file/?directory=testing_tracks&filename={filename}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert "content-disposition" in response.headers
    assert filename in response.headers["content-disposition"]


def test_get_file_not_found():
    """Тест получения несуществующего файла."""
    response = client.get("/file/?directory=testing_tracks&filename=nonexistent.wav")
    logger.info(f"response: {response.json()["detail"]}")
    assert response.status_code == 404
    assert response.json()["detail"] == "File not found"


# Тесты для метода get_random_file
def test_get_random_file():
    """Тест успешного получения случайного файла."""
    response = client.get("/random-file/?directory=testing_tracks")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"


def test_get_random_file_no_files():
    """Тест получения случайного файла из пустой папки."""
    # Удаляем все файлы
    teardown_files()

    response = client.get("/random-file/?directory=testing_tracks")
    logger.info(f"response: {response.json()["detail"]}")
    assert response.status_code == 404
    assert response.json()["detail"] == "No files in directory"

    # Восстанавливаем тестовые файлы
    setup_module(None)


# Тесты для метода send_tracks
def test_send_tracks():
    """Тест успешной отправки случайных треков."""
    response = client.get("/send-tracks/?count=3")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"


def test_send_tracks_with_filter():
    """Тест отправки треков с фильтром."""
    response = client.get("/send-tracks/?count=2&filter=track_1")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"


def test_send_tracks_filter_no_match():
    """Тест отправки треков с фильтром, который не совпадает."""
    response = client.get("/send-tracks/?count=2&filter=nonexistent")
    logger.info(f"response: {response.json()["detail"]}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Треки, начинающиеся с 'nonexistent', не найдены."


def test_send_tracks_more_than_available():
    """Тест отправки большего числа треков, чем доступно."""
    response = client.get("/send-tracks/?count=10")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"


def test_send_tracks_no_files():
    """Тест отправки треков из пустой папки."""
    # Удаляем все файлы
    teardown_files()

    response = client.get("/send-tracks/?count=3")
    logger.info(f"response: {response.json()["detail"]}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Треки не найдены."

    # Восстанавливаем тестовые файлы
    setup_module(None)
