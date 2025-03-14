import io
import numpy as np
from scipy.signal import butter, lfilter
from pydub import AudioSegment, effects
import wave
import numpy as np
import scipy.signal as signal
import soundfile as sf
import random

def one_band_eq(wav_bytes: bytes, filter_width: float, filter_freq: float, gain: float) -> bytes:
    """
    Применяет полосовой фильтр или усиливает частоты в WAV-файле.

    :param wav_bytes: Байтовая строка исходного WAV-файла.
    :param filter_width: Ширина полосового фильтра (в Гц).
    :param filter_freq: Центральная частота фильтра (в Гц).
    :param gain: Усиление/ослабление.
    :return: Обработанный WAV-файл в виде байтовой строки.
    """
    # Чтение WAV-файла
    with wave.open(io.BytesIO(wav_bytes), 'rb') as wav_in:
        params = wav_in.getparams()
        nchannels, sampwidth, framerate, nframes = params[:4]

        # Проверяем, что ширина сэмпла совпадает с ожиданиями (4 байта = 32 бита)
        if sampwidth != 4:
            raise ValueError("Эта функция поддерживает только 32-битные WAV файлы.")

        # Читаем аудиоданные в numpy массив
        audio_data = np.frombuffer(wav_in.readframes(nframes), dtype=np.int32)

        # Если стерео, делаем reshape для разделения каналов
        if nchannels == 2:
            audio_data = audio_data.reshape(-1, 2)
    if gain > 0:
        processed_data = bandpass_gain(audio_data, filter_freq, filter_width, gain, framerate)
    else:
        processed_data = bandstop_filter(audio_data, filter_freq, filter_width, framerate)
    # Преобразуем массив обратно в WAV-байты
    output_io = io.BytesIO()
    with wave.open(output_io, 'wb') as wav_out:
        wav_out.setparams(params)
        # Уплощаем массив для записи, если он многоканальный
        wav_out.writeframes(processed_data.astype(np.int32).tobytes())  # Преобразуем обратно в int32 перед записью

    return output_io.getvalue()

def bandpass_gain(audio_data: np.ndarray, central_freq: float, bandwidth: float, gain_dB: float, samp_rate: int) -> np.ndarray:
    """
    Усиливает указанную полосу частот в аудиосигнале, как в эквалайзере.
    
    :param audio_data: numpy массив с аудиоданными (int32, двухканальный сигнал).
    :param central_freq: Центральная частота полосы пропускания в Гц.
    :param bandwidth: Ширина полосы частот в Гц.
    :param gain_dB: Усиление/ослабление в децибелах (положительное для усиления, отрицательное для ослабления).
    :param samp_rate: Частота дискретизации (samples per second) аудиофайла.
    :return: numpy массив с обработанным аудиосигналом (с измененной полосой частот).
    """
    # Проектируем фильтр Баттерворта для полосы пропускания
    lowcut = central_freq - bandwidth / 2
    highcut = central_freq + bandwidth / 2

    # Создаем фильтр Баттерворта
    b, a = butter(3, [lowcut / (0.5 * samp_rate), highcut / (0.5 * samp_rate)], btype='bandpass')
    
    # Применяем фильтр к аудиоданным (по оси 0, так как каналы могут быть разные)
    filtered_audio = lfilter(b, a, audio_data, axis=0)

    # Преобразуем усиление из децибел в линейный коэффициент
    gain = 10 ** (gain_dB / 20)

    # Усиливаем или ослабляем только отфильтрованный сигнал
    filtered_audio_with_gain = filtered_audio * gain

    # Остальная часть сигнала (вне полосы частот) не изменяется
    # Объединяем усиленную полосу с остальным сигналом
    output_audio = audio_data + (filtered_audio_with_gain - filtered_audio)

    # Ограничиваем значения для предотвращения переполнения
    max_val = np.iinfo(np.int32).max
    min_val = np.iinfo(np.int32).min
    output_audio = np.clip(output_audio, min_val, max_val)

    # Приводим результат обратно к типу int32
    output_audio = output_audio.astype(np.int32)

    return output_audio

def bandstop_filter(audio_data: np.ndarray, central_freq: float, bandwidth: float, samp_rate: int) -> np.ndarray:
    """
    Ослабляет указанную полосу частот в аудиосигнале с использованием bandstop фильтра.
    
    :param audio_data: numpy массив с аудиоданными (int32, двухканальный сигнал).
    :param central_freq: Центральная частота полосы подавления в Гц.
    :param bandwidth: Ширина полосы частот в Гц.
    :param samp_rate: Частота дискретизации (samples per second) аудиофайла.
    :return: numpy массив с обработанным аудиосигналом с подавленной полосой частот.
    """
    # Расчет частот среза для bandstop
    lowcut = central_freq - bandwidth / 2
    highcut = central_freq + bandwidth / 2

    # Проектируем фильтр Баттерворта типа bandstop
    b, a = butter(3, [lowcut / (0.5 * samp_rate), highcut / (0.5 * samp_rate)], btype='bandstop')
    
    # Применяем фильтр к аудиоданным (по оси 0, так как каналы могут быть разные)
    filtered_audio = lfilter(b, a, audio_data, axis=0)

    # Ограничиваем значения для предотвращения переполнения
    max_val = np.iinfo(np.int32).max
    min_val = np.iinfo(np.int32).min
    output_audio = np.clip(filtered_audio, min_val, max_val)

    # Возвращаем отфильтрованный сигнал
    return output_audio.astype(np.int32)

def normalize_wav_bytes(wav_bytes: bytes, target_dBFS=-14.0) -> bytes:
    """
    Нормализует громкость WAV-файла.

    :param wav_bytes: WAV-файл в виде строки байтов.
    :param target_dBFS: Целевой уровень громкости (по умолчанию -14 дБ).
    :return: Обработанный WAV-файл в виде строки байтов.
    """
    try:
        # Создание аудиосегмента из строки байтов
        audio = AudioSegment.from_file(io.BytesIO(wav_bytes), format="wav")

        # Нормализация громкости
        change_in_dBFS = target_dBFS - audio.dBFS
        normalized_audio = audio.apply_gain(change_in_dBFS)

        # Экспорт обработанного аудио в строку байтов
        output_io = io.BytesIO()
        normalized_audio.export(output_io, format="wav")
        return output_io.getvalue()

    except Exception as e:
        print(f"Ошибка при обработке аудио: {e}")
        return None

def bytes_to_audiosegment(audio_bytes: bytes) -> AudioSegment:
    """Конвертирует байты в объект AudioSegment"""
    return AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")

def audiosegment_to_bytes(audio: AudioSegment) -> bytes:
    """Конвертирует объект AudioSegment обратно в байты"""
    buffer = io.BytesIO()
    audio.export(buffer, format="wav")
    return buffer.getvalue()

# 🎶 1. Реверберация (Reverb)
def apply_reverb(audio_bytes: bytes, decay: float = 0.4, delay_ms: int = 50) -> bytes:
    """
    Добавляет эффект реверберации (Reverb) к аудиофайлу.
    :param audio_bytes: Байтовая строка аудиофайла (WAV)
    :param decay: Степень затухания (0.2-0.8), чем выше, тем больше эхо.
    :param delay_ms: Задержка отражения (10-100 мс), влияет на размер помещения.
    :return: Обработанный аудиофайл в байтах
    """
    audio = bytes_to_audiosegment(audio_bytes)
    frame_rate = audio.frame_rate
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)

    # Преобразуем задержку из мс в количество сэмплов
    delay_samples = int(frame_rate * delay_ms / 1000)

    # Создаем пустой массив для отражений
    reverb_samples = np.zeros(len(samples) + delay_samples * 10)  # 10 отражений

    # Добавляем оригинальный сигнал
    reverb_samples[:len(samples)] += samples

    # Добавляем затухающие отражения
    for i in range(1, 10):
        reverb_samples[i * delay_samples:i * delay_samples + len(samples)] += samples * (decay ** i)

    # Обрезаем до оригинального размера
    reverb_samples = reverb_samples[:len(samples)]

    # Ограничиваем значения
    max_value = np.iinfo(np.int32).max
    reverb_samples = np.clip(reverb_samples, -max_value, max_value).astype(np.int32)

    # Преобразуем массив обратно в аудио
    processed_audio = audio._spawn(reverb_samples.tobytes())
    return audiosegment_to_bytes(processed_audio)

# 🎶 2. Дилей (Delay)
def apply_delay(audio_bytes: bytes, delay_ms: int = 300, decay: float = 0.5) -> bytes:
    # Преобразуем байты в объект AudioSegment
    audio = bytes_to_audiosegment(audio_bytes)
    # Вычисляем количество сэмплов для задержки
    delay_samples = int(audio.frame_rate * delay_ms / 1000)
    # Получаем сэмплы аудио как массив
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32) 
    # Создаем массив для задержанных сэмплов
    delayed_samples = np.zeros(len(samples) + delay_samples)
    # Копируем оригинальные сэмплы в начало
    delayed_samples[:len(samples)] = samples
    # Добавляем сэмплы с задержкой с учетом коэффициента затухания
    delayed_samples[delay_samples:] += samples * decay
    # Ограничиваем сэмплы в диапазоне допустимых значений для 16-битных аудиоформатов
    max_value = np.iinfo(np.int32).max
    delayed_samples = np.clip(delayed_samples, -max_value, max_value)
    # Преобразуем сэмплы обратно в целочисленные значения
    processed_samples = delayed_samples.astype(np.int32)
    # Создаем новый объект AudioSegment из обработанных сэмплов
    processed_audio = audio._spawn(processed_samples.tobytes())
    # Преобразуем аудио обратно в байты и возвращаем
    return audiosegment_to_bytes(processed_audio)

# 🎶 3. Сатурация (Saturation) – мягкое аналоговое насыщение
def apply_saturation(audio_bytes: bytes, amount: float = 0.5) -> bytes:
    audio = bytes_to_audiosegment(audio_bytes)
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    max_value = np.iinfo(np.int32).max  # Для 32-битного аудио
    samples /= max_value

    processed_samples = np.tanh(samples * amount)  # Сатурация через гиперболический тангенс
    saturated_samples = (processed_samples * np.iinfo(audio.array_type).max).astype(audio.array_type)

    samples *= max_value
    saturated_samples = np.clip(saturated_samples, -max_value, max_value)
    # Преобразуем сэмплы обратно в целочисленные значения
    processed_samples = saturated_samples.astype(np.int32)
    # Создаем новый объект AudioSegment из обработанных сэмплов
    processed_audio = audio._spawn(processed_samples.tobytes())
    # Преобразуем аудио обратно в байты и возвращаем
    return audiosegment_to_bytes(processed_audio)

def apply_distortion(audio_bytes: bytes, gain: float = 10) -> bytes:
    # Преобразуем байты в объект AudioSegment
    audio = bytes_to_audiosegment(audio_bytes)
    
    # Получаем сэмплы аудио как массив
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)

    max_value = np.iinfo(np.int32).max  # Для 32-битного аудио

    samples /= max_value
    #
    ## Применяем усиление (гейн)
    samples *= gain
    #print(samples)
    ## Применяем жесткое ограничение перегруза (ограничиваем в диапазоне [-1, 1])
    samples = np.clip(samples, -1, 1)
    samples *= max_value
    
    # Преобразуем сэмплы обратно в целочисленные значения с учетом максимума для 32-битного формата
    distorted_samples = np.clip(samples, -max_value, max_value)
    # Преобразуем сэмплы обратно в целочисленные значения
    processed_samples = distorted_samples.astype(np.int32)
    
    # Создаем новый объект AudioSegment из обработанных сэмплов
    processed_audio = audio._spawn(processed_samples.tobytes())
    
    # Возвращаем аудио в формате байтов
    return audiosegment_to_bytes(processed_audio)

# 🎶 5. Компрессия (Compression)
def apply_compression(audio_bytes: bytes, threshold: float = -20, ratio: float = 4) -> bytes:
    audio = bytes_to_audiosegment(audio_bytes)
    compressed_audio = effects.compress_dynamic_range(audio, threshold=threshold, ratio=ratio)
    return audiosegment_to_bytes(compressed_audio)

# 🎶 6. Модуляция – Хорус (Chorus)
def apply_chorus(audio_bytes: bytes, rate_hz: float = 1.5, depth_ms: int = 25) -> bytes:
    """
    Добавляет эффект хорус (chorus) к аудиофайлу.
    :param audio_bytes: Байтовая строка аудиофайла (WAV)
    :param rate_hz: Частота модуляции задержки (0.5 - 3 Гц)
    :param depth_ms: Глубина модуляции задержки (обычно 20-30 мс)
    :return: Обработанный аудиофайл в байтах
    """
    audio = bytes_to_audiosegment(audio_bytes)
    frame_rate = audio.frame_rate
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    
    # Переводим задержку в сэмплы
    max_delay_samples = int((depth_ms / 1000) * frame_rate)

    # Генерируем сигнал модуляции (синусоидальный LFO)
    time = np.arange(len(samples))
    lfo = np.sin(2 * np.pi * rate_hz * time / frame_rate)  # LFO-генератор (модулирует задержку)

    # Рассчитываем изменяющуюся задержку (LFO изменяет время задержки)
    modulated_delay = ((lfo + 1) / 2) * max_delay_samples  # Диапазон: [0, max_delay_samples]

    # Создаём новый массив с задержкой
    delayed_samples = np.zeros_like(samples)
    for i in range(len(samples)):
        delay = int(modulated_delay[i])  # Получаем текущую задержку в сэмплах
        if i - delay >= 0:
            delayed_samples[i] = samples[i - delay]  # Задержанный сигнал

    # Смешиваем оригинальный и задержанный сигнал (50/50)
    chorus_samples = (samples + delayed_samples) / 2

    # Ограничение значений
    max_value = np.iinfo(np.int32).max
    chorus_samples = np.clip(chorus_samples, -max_value, max_value).astype(np.int32)

    # Преобразуем массив обратно в аудио
    processed_audio = audio._spawn(chorus_samples.tobytes())
    return audiosegment_to_bytes(processed_audio)

# 🎶 7. Модуляция – Флэнджер (Flanger)
def apply_flanger(audio_bytes: bytes, rate_hz: float = 0.5, depth_ms: int = 10, feedback: float = 0.5) -> bytes:
    """
    Добавляет эффект флэнджер (flanger) к аудиофайлу.
    :param audio_bytes: Байтовая строка аудиофайла (WAV)
    :param rate_hz: Частота модуляции задержки (0.1 - 3 Гц)
    :param depth_ms: Глубина модуляции задержки (обычно 5-15 мс)
    :param feedback: Коэффициент обратной связи (0 - без обратной связи, 1 - сильный резонанс)
    :return: Обработанный аудиофайл в байтах
    """
    audio = bytes_to_audiosegment(audio_bytes)
    frame_rate = audio.frame_rate
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    
    # Переводим глубину задержки в сэмплы
    max_delay_samples = int((depth_ms / 1000) * frame_rate)

    # Генерируем сигнал модуляции (LFO) для изменения задержки
    time = np.arange(len(samples))
    lfo = np.sin(2 * np.pi * rate_hz * time / frame_rate)  # Генератор низкой частоты

    # Рассчитываем изменяющуюся задержку (LFO изменяет время задержки)
    modulated_delay = ((lfo + 1) / 2) * max_delay_samples  # Диапазон: [0, max_delay_samples]

    # Создаём массив для обработанных сэмплов
    delayed_samples = np.zeros_like(samples)
    
    # Применяем задержку и обратную связь
    for i in range(len(samples)):
        delay = int(modulated_delay[i])  # Текущее значение задержки в сэмплах
        if i - delay >= 0:
            delayed_samples[i] = samples[i - delay] + delayed_samples[i - delay] * feedback  # Задержанный сигнал с обратной связью

    # Смешиваем оригинальный и задержанный сигнал
    flanger_samples = (samples + delayed_samples) / 2

    # Ограничение значений
    max_value = np.iinfo(np.int32).max
    flanger_samples = np.clip(flanger_samples, -max_value, max_value).astype(np.int32)

    # Преобразуем массив обратно в аудио
    processed_audio = audio._spawn(flanger_samples.tobytes())
    return audiosegment_to_bytes(processed_audio)

# 🎶 8. Модуляция – Тремоло по громкости
def apply_tremolo(audio_bytes: bytes, rate_hz: float = 5, depth: float = 0.5) -> bytes:
    audio = bytes_to_audiosegment(audio_bytes)
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    mod_signal = 1 - (depth * (1 + np.sin(2 * np.pi * np.arange(len(samples)) * rate_hz / audio.frame_rate)) / 2)
    tremolo_samples = samples * mod_signal

    max_value = np.iinfo(np.int32).max
    tremolo_samples = np.clip(tremolo_samples, -max_value, max_value)
    # Преобразуем сэмплы обратно в целочисленные значения
    processed_samples = tremolo_samples.astype(np.int32)
    # Создаем новый объект AudioSegment из обработанных сэмплов
    processed_audio = audio._spawn(processed_samples.tobytes())
    # Преобразуем аудио обратно в байты и возвращаем
    return audiosegment_to_bytes(processed_audio)

# 🎶 9. Модуляция – Тремоло по высоте (Vibrato)
def apply_vibrato(audio_bytes: bytes, rate_hz: float = 5, depth_semitones: float = 0.5) -> bytes:
    """
    Добавляет эффект частотного вибрато (Frequency Vibrato) к аудиофайлу.
    :param audio_bytes: Байтовая строка аудиофайла (WAV)
    :param rate_hz: Частота модуляции вибрато (3-8 Гц)
    :param depth_semitones: Глубина модуляции (обычно 0.1 - 1.5 полутонов)
    :return: Обработанный аудиофайл в байтах
    """
    audio = bytes_to_audiosegment(audio_bytes)
    frame_rate = audio.frame_rate
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)

    # Генерируем сигнал модуляции (LFO) для изменения высоты звука
    time = np.arange(len(samples))
    vibrato_signal = np.sin(2 * np.pi * rate_hz * time / frame_rate) * depth_semitones

    # Преобразуем глубину модуляции в коэффициент изменения частоты
    pitch_factor = 2 ** (vibrato_signal / 12)  # Перевод полутонов в коэффициент частоты

    # Применяем изменение частоты с интерполяцией
    indices = np.arange(len(samples)) * pitch_factor
    indices = np.clip(indices, 0, len(samples) - 1)  # Ограничиваем диапазон индексов
    vibrato_samples = np.interp(indices, np.arange(len(samples)), samples)

    # Ограничение значений
    max_value = np.iinfo(np.int32).max
    vibrato_samples = np.clip(vibrato_samples, -max_value, max_value).astype(np.int32)

    # Преобразуем массив обратно в аудио
    processed_audio = audio._spawn(vibrato_samples.tobytes())
    return audiosegment_to_bytes(processed_audio)

# 🎵 Применение случайного эффекта с учетом сложности
def apply_random_effect(audio_bytes: bytes, difficulty: str = "medium") -> tuple[bytes, str]:
    """Применяет случайный эффект к аудиофайлу с разными уровнями сложности."""
    def apply_no_effect(audio_bytes: bytes) -> bytes:
        return audio_bytes

    difficulty_params = {
        "easy": {
            "reverb_decay": 0.8, "reverb_delay": 100,
            "delay_ms": 500, "delay_decay": 0.7,
            "distortion_gain": 3,
            "tremolo_rate": 5, "tremolo_depth": 0.8,
            "vibrato_rate": 1.0, "vibrato_depth": 0.08,
            "flanger_rate": 0.5, "flanger_depth": 8,
            "chorus_rate": 0.7, "chorus_depth": 7,
            "compression_th": -40, "compression_ratio" : 16,
            "saturation": 3
        },
        "medium": {
            "reverb_decay": 0.6, "reverb_delay": 75,
            "delay_ms": 300, "delay_decay": 0.5,
            "distortion_gain": 2,
            "tremolo_rate": 7, "tremolo_depth": 0.6,
            "vibrato_rate": 0.7, "vibrato_depth": 0.03,
            "flanger_rate": 0.3, "flanger_depth": 5,
            "chorus_rate": 0.5, "chorus_depth": 5,
            "compression_th": -20, "compression_ratio" : 8,
            "saturation": 2
        },
        "hard": {
            "reverb_decay": 0.4, "reverb_delay": 50,
            "delay_ms": 100, "delay_decay": 0.3,
            "distortion_gain": 1.5,
            "tremolo_rate": 10, "tremolo_depth": 0.3,
            "vibrato_rate": 0.5, "vibrato_depth": 0.01,
            "flanger_rate": 0.1, "flanger_depth": 2,
            "chorus_rate": 1, "chorus_depth": 2,
            "compression_th": -10, "compression_ratio" : 4,
            "saturation": 1
        }
    }
    
    params = difficulty_params.get(difficulty, difficulty_params["medium"])
    effects_list = [
        ("Reverb", apply_reverb, [params["reverb_decay"]]), #OK
        ("Delay", apply_delay, [params["delay_ms"], params["delay_decay"]]), #OK
        ("Distortion", apply_distortion, [params["distortion_gain"]]), #OK
        ("Tremolo", apply_tremolo, [params["tremolo_rate"], params["tremolo_depth"]]), #OK
        ("Flanger", apply_flanger, [params["flanger_rate"], params["flanger_depth"]]), #OK
        ("Chorus", apply_chorus, [params["chorus_rate"], params["chorus_depth"]]), #OK
        ("Vibrato", apply_vibrato, [params["vibrato_rate"], params["vibrato_depth"]]), #OK
        ("Compression", apply_compression, [params["compression_th"], params["compression_ratio"]]), #SUPER
        ("Saturation", apply_saturation, [params["saturation"]]), #OK
        ("No effect", apply_no_effect, [])
    ]
    
    effect_name, effect_func, effect_args = random.choice(effects_list)
    
    modified_audio = effect_func(audio_bytes, *effect_args)
    
    return modified_audio, effect_name

if __name__ == "__main__":
    # Пример использования
    #with open("D:/Универ/ДИПЛОМ/Project/fs/testing_tracks/full-1.wav", "rb") as f:
    #    wav_data = f.read()

    #processed_wav = one_band_eq(wav_data, 145, 150, 10)

    #with open("output.wav", "wb") as f:
    #    f.write(processed_wav)

    with open("D:/Универ/ДИПЛОМ/Project/chords.wav", "rb") as f:
        input_audio = f.read()

    # Применение реверберации
    processed_audio = apply_reverb(input_audio, decay=0.4)

    # Сохранение результата
    with open("output.wav", "wb") as f:
        f.write(processed_audio)
