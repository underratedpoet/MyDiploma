FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости для FluidSynth, TiMidity++ и FFmpeg
RUN apt-get update && apt-get install -y \
    fluidsynth \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Python-библиотеки
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем файлы проекта в контейнер
COPY . .

# Указываем путь к SoundFont
ENV SF2_PATH="/app/FluidR3_GM.sf2"

# Указываем команду по умолчанию (можно запустить контейнер с bash)
CMD ["python"]
