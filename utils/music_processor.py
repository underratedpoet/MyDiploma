import random
from googleapiclient.discovery import build
from yt_dlp import YoutubeDL
import os

# Ваш YouTube Data API ключ
API_KEY = os.getenv("API_KEY")

def get_random_video(query="instrumental music"):
    """Ищет случайное видео на YouTube по запросу."""
    try:
        # Инициализация YouTube API
        youtube = build("youtube", "v3", developerKey=API_KEY)

        # Поиск видео
        request = youtube.search().list(
            q=query,
            part="snippet",
            type="video",
            videoLicense="creativeCommon",
            maxResults=50,  # Максимум 50 результатов
            videoDuration='short',
        )
        response = request.execute()

        # Проверяем, есть ли результаты
        if "items" not in response or not response["items"]:
            print("Видео не найдены.")
            return None

        # Случайный выбор видео
        video = random.choice(response["items"])
        video_id = video["id"]["videoId"]
        video_title = video["snippet"]["title"]
        print(f"Найдено видео: {video_title} (https://www.youtube.com/watch?v={video_id})")
        return video_id

    except Exception as e:
        print(f"Ошибка при поиске видео: {e}")
        return None

def download_audio(video_id):
    """Скачивает аудио с YouTube."""
    try:
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            'format': 'bestaudio/best',  # Скачивает только аудио
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': '%(title)s.%(ext)s',  # Формат имени файла
            'cookiefile': 'cookies.txt',
        }

        with YoutubeDL(ydl_opts) as ydl:
            print(f"Скачивание: {video_url}")
            ydl.download([video_url])
            print("Загрузка завершена.")
    except Exception as e:
        print(f"Ошибка при скачивании: {e}")

# Основной процесс
query = "instrumental music"
video_id = get_random_video(query)
if video_id:
    download_audio(video_id)
