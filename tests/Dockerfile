# Используем официальный Python образ
FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем зависимости
COPY tests/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --timeout=240 -r /app/requirements.txt

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем приложение и тесты
COPY tests .
COPY files_storage files_storage



# Указываем команду для запуска pytest
CMD ["pytest", "--log-cli-level=INFO"]

#CMD [ "find", "."]
