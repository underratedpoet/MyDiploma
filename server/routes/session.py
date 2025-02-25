from datetime import datetime, timedelta
import os

from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from fastapi_login import LoginManager
import httpx
import uuid
import smtplib
from email.mime.text import MIMEText
import jwt


SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8080")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

#def generate_confirmation_token(user_data: dict) -> str:
#    # Настроим токен, который будет содержать информацию о данных пользователя, которые необходимо обновить
#    expiration = datetime.utcnow() + timedelta(hours=1)  # Токен истекает через 1 час
#    payload = {
#        "exp": expiration,
#        "iat": datetime.utcnow(),
#        "user_data": user_data
#    }
#    # Генерация токена с секретным ключом
#    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
#    return token
#
#async def send_confirmation_email(username: str, confirmation_token: str):
#    """Отправляет письмо с подтверждением обновлений."""
#    to_email = f"{username}@example.com"  # Пример email, берется из username (или можно использовать email из базы данных)
#
#    subject = "Please confirm your profile update"
#    body = f"To confirm your profile update, please click the link below:\n\nhttp://frontend/confirm_update/{confirmation_token}"
#
#    # Формируем сообщение
#    msg = MIMEMultipart()
#    msg['From'] = "your_email@example.com"
#    msg['To'] = to_email
#    msg['Subject'] = subject
#    msg.attach(MIMEText(body, 'plain'))
#
#    # Отправляем через MailHog (SMTP сервер)
#    with smtplib.SMTP("mailhog", 1025) as server:
#        server.sendmail("your_email@example.com", to_email, msg.as_string())
#
#    return {"status_code": 200, "message": "Email sent"}
#
#def send_email(subject, body, to_email):
#    msg = MIMEText(body)
#    msg["Subject"] = subject
#    msg["From"] = "your_email@example.com"
#    msg["To"] = to_email
#
#    # Настроим MailHog как SMTP сервер
#    with smtplib.SMTP("mailhog", 1025) as server:
#        server.sendmail("your_email@example.com", to_email, msg.as_string())