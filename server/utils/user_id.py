from os import getenv
from fastapi import Request, HTTPException
from jose import jwt, JWTError

DB_API_URL = getenv("DB_API_URL", "http://db-api:8000")
FILE_API_URL = getenv("FILE_API_URL", "http://file-api:8000")
SECRET_KEY = getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = getenv("ALGORITHM", "HS256")

def get_user_id(request: Request):
    """Получает ID пользователя из сессии."""
    token = request.cookies.get("auth")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")