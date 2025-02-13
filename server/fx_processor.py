import io
import numpy as np
from scipy.signal import butter, lfilter
from pydub import AudioSegment, effects
import wave
import numpy as np
import scipy.signal as signal
import soundfile as sf

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
    print(audio_data)
    print(audio_data[0][0].dtype)
    if gain > 0:
        processed_data = bandpass_gain(audio_data, filter_freq, filter_width, gain, framerate)
    else:
        processed_data = bandstop_filter(audio_data, filter_freq, filter_width, framerate)
    print(processed_data)
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
def apply_reverb(audio_bytes: bytes, decay: float = 0.3) -> bytes:
    audio = bytes_to_audiosegment(audio_bytes)
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32) / np.iinfo(audio.array_type).max
    reverb_filter = np.exp(-np.linspace(0, decay, len(samples)))
    processed_samples = np.convolve(samples, reverb_filter, mode='same')
    processed_samples = np.clip(processed_samples, -1, 1) * np.iinfo(audio.array_type).max
    processed_audio = audio._spawn(processed_samples.astype(audio.array_type).tobytes())
    return audiosegment_to_bytes(processed_audio)

# 🎶 2. Дилей (Delay)
def apply_delay(audio_bytes: bytes, delay_ms: int = 300, decay: float = 0.5) -> bytes:
    audio = bytes_to_audiosegment(audio_bytes)
    delay_samples = int(audio.frame_rate * delay_ms / 1000)
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    delayed_samples = np.zeros(len(samples) + delay_samples)
    delayed_samples[:len(samples)] = samples
    delayed_samples[delay_samples:] += samples * decay
    processed_audio = audio._spawn((delayed_samples[:len(samples)] * np.iinfo(audio.array_type).max).astype(audio.array_type).tobytes())
    return audiosegment_to_bytes(processed_audio)

# 🎶 3. Сатурация (Saturation) – мягкое аналоговое насыщение
def apply_saturation(audio_bytes: bytes, amount: float = 0.5) -> bytes:
    audio = bytes_to_audiosegment(audio_bytes)
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    processed_samples = np.tanh(samples * amount)  # Сатурация через гиперболический тангенс
    processed_samples = (processed_samples * np.iinfo(audio.array_type).max).astype(audio.array_type)
    processed_audio = audio._spawn(processed_samples.tobytes())
    return audiosegment_to_bytes(processed_audio)

# 🎶 4. Перегруз (Distortion) – жесткое цифровое ограничение
def apply_distortion(audio_bytes: bytes, gain: float = 10) -> bytes:
    audio = bytes_to_audiosegment(audio_bytes)
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32) * gain
    samples = np.clip(samples, -1, 1)  # Жесткое ограничение перегруза
    processed_samples = (samples * np.iinfo(audio.array_type).max).astype(audio.array_type)
    processed_audio = audio._spawn(processed_samples.tobytes())
    return audiosegment_to_bytes(processed_audio)

# 🎶 5. Компрессия (Compression)
def apply_compression(audio_bytes: bytes, threshold: float = -20, ratio: float = 4) -> bytes:
    audio = bytes_to_audiosegment(audio_bytes)
    compressed_audio = effects.compress_dynamic_range(audio, threshold=threshold, ratio=ratio)
    return audiosegment_to_bytes(compressed_audio)

# 🎶 6. Модуляция – Хорус (Chorus)
def apply_chorus(audio_bytes: bytes, rate_hz: float = 1.5, depth: int = 25) -> bytes:
    audio = bytes_to_audiosegment(audio_bytes)
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    mod_signal = np.sin(2 * np.pi * np.arange(len(samples)) * rate_hz / audio.frame_rate) * depth
    modulated_samples = np.interp(np.arange(len(samples)) + mod_signal, np.arange(len(samples)), samples)
    processed_audio = audio._spawn((modulated_samples * np.iinfo(audio.array_type).max).astype(audio.array_type).tobytes())
    return audiosegment_to_bytes(processed_audio)

# 🎶 7. Модуляция – Флэнджер (Flanger)
def apply_flanger(audio_bytes: bytes, rate_hz: float = 0.25, depth: int = 5) -> bytes:
    audio = bytes_to_audiosegment(audio_bytes)
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    mod_signal = np.sin(2 * np.pi * np.arange(len(samples)) * rate_hz / audio.frame_rate) * depth
    flanged_samples = (samples + np.interp(np.arange(len(samples)) - mod_signal, np.arange(len(samples)), samples)) / 2
    processed_audio = audio._spawn((flanged_samples * np.iinfo(audio.array_type).max).astype(audio.array_type).tobytes())
    return audiosegment_to_bytes(processed_audio)

# 🎶 8. Модуляция – Тремоло по громкости
def apply_tremolo(audio_bytes: bytes, rate_hz: float = 5, depth: float = 0.5) -> bytes:
    audio = bytes_to_audiosegment(audio_bytes)
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    mod_signal = 1 - (depth * (1 + np.sin(2 * np.pi * np.arange(len(samples)) * rate_hz / audio.frame_rate)) / 2)
    tremolo_samples = samples * mod_signal
    processed_audio = audio._spawn((tremolo_samples * np.iinfo(audio.array_type).max).astype(audio.array_type).tobytes())
    return audiosegment_to_bytes(processed_audio)

# 🎶 9. Модуляция – Тремоло по высоте (Vibrato)
def apply_vibrato(audio_bytes: bytes, rate_hz: float = 5, depth: float = 10) -> bytes:
    audio = bytes_to_audiosegment(audio_bytes)
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    mod_signal = np.sin(2 * np.pi * np.arange(len(samples)) * rate_hz / audio.frame_rate) * depth
    vibrato_samples = np.interp(np.arange(len(samples)) + mod_signal, np.arange(len(samples)), samples)
    processed_audio = audio._spawn((vibrato_samples * np.iinfo(audio.array_type).max).astype(audio.array_type).tobytes())
    return audiosegment_to_bytes(processed_audio)


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
