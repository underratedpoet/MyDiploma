# Используем официальный образ Python
FROM python:3.12-slim

# Установим рабочую директорию
WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    build-essential \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Установим зависимости
COPY database/requirements.txt .

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

# Скопируем исходный код
COPY database/ .
COPY utils/ ./utils/

# Открываем порт
EXPOSE 8000

# Запуск API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]