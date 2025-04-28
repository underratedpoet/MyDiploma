import time
from utils.mongo import db
from datetime import datetime, timedelta
from random import randint
import smtplib
from email.mime.text import MIMEText

# Настройки SMTP сервера
SMTP_SERVER = "smtp.yandex.ru" 
SMTP_PORT = 465
SMTP_USER = "danielmaksimencko@yandex.ru"  
SMTP_PASSWORD = "obmpfbykvmzmdyqn"

verification_codes_collection = db["verification_codes"]

async def generate_code() -> str:
    """Генерирует 6-значный код."""
    return str(randint(100000, 999999))

async def store_code(username: str, code: str, expiration_seconds: int = 300):
    """Сохраняет код подтверждения в MongoDB с истечением."""
    expires_at = datetime.utcnow() + timedelta(seconds=expiration_seconds)
    await verification_codes_collection.update_one(
        {"username": username},
        {"$set": {
            "code": code,
            "expires_at": expires_at
        }},
        upsert=True
    )

async def verify_code(username: str, code: str) -> bool:
    """Проверяет код и срок его действия."""
    record = await verification_codes_collection.find_one({"username": username})
    if not record:
        return False

    if record["code"] != code:
        return False

    if datetime.utcnow() > record["expires_at"]:
        await verification_codes_collection.delete_one({"username": username})
        return False

    # Успешная проверка, удаляем код
    await verification_codes_collection.delete_one({"username": username})
    return True

def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:  # SMTP_SSL для порта 465
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
