import os
from tkinter import Tk, filedialog
from pydub import AudioSegment

def process_wav_files(output_dir, target_dBFS=-14.0, duration=15 * 1000):
    """
    Нормализует громкость, обрезает до 15 секунд и добавляет fade in/out к группе WAV-файлов.
    Сохраняет обработанные файлы в указанную папку.

    :param output_dir: Папка для сохранения обработанных файлов.
    :param target_dBFS: Целевой уровень громкости (по умолчанию -14 дБ).
    :param duration: Длительность в миллисекундах (по умолчанию 15 секунд).
    """
    # Открыть файловый диалог для выбора файлов
    Tk().withdraw()  # Отключить главное окно Tkinter
    file_paths = filedialog.askopenfilenames(
        title="Выберите WAV-файлы для обработки",
        filetypes=[("WAV файлы", "*.wav")]
    )

    if not file_paths:
        print("Файлы не выбраны. Завершение работы.")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for file_path in file_paths:
        try:
            print(f"Обработка файла: {file_path}")
            audio = AudioSegment.from_file(file_path)

            # Нормализация громкости
            change_in_dBFS = target_dBFS - audio.dBFS
            normalized_audio = audio.apply_gain(change_in_dBFS)

            # Обрезка до 15 секунд
            trimmed_audio = normalized_audio[:duration]

            # Применение fade in и fade out
            processed_audio = trimmed_audio.fade_in(500).fade_out(500)

            # Сохранение файла
            base_name = os.path.basename(file_path)
            output_path = os.path.join(output_dir, base_name)
            processed_audio.export(output_path, format="wav")
            print(f"Сохранён обработанный файл: {output_path}")

        except Exception as e:
            print(f"Ошибка при обработке файла {file_path}: {e}")

if __name__ == "__main__":
    # Укажите папку для сохранения обработанных файлов
    output_directory = "D:/Универ/ДИПЛОМ/Project/fs/testing_tracks"

    # Запуск обработки файлов
    process_wav_files(output_dir=output_directory)
