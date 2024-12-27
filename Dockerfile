# Используем официальный образ Python
FROM python:3.12-slim

# Установим рабочую директорию
WORKDIR /app

# Установим необходимые зависимости
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Установим нужные Python библиотеки
RUN pip install --no-cache-dir google-api-python-client yt-dlp

# Скопируем скрипт в контейнер
COPY ./utils/music_processor.py music_processor.py
COPY ./cookies.txt cookies.txt

# Запустим скрипт
#CMD [ "find", "." ]
ENTRYPOINT ["python"]
CMD ["utils/music_processor.py"]
