# Используем официальный образ Python
FROM python:3.12-slim

# Установим рабочую директорию
WORKDIR /app

# Установим зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Скопируем исходный код
COPY . .

# Открываем порт
EXPOSE 8000

# Запуск API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
