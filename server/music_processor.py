import io
import numpy as np
from scipy.signal import butter, lfilter
import wave

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
    Усиливает или ослабляет указанную полосу частот в аудиосигнале, как в эквалайзере.
    
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

if __name__ == "__main__":
    # Пример использования
    with open("D:/Универ/ДИПЛОМ/Project/fs/testing_tracks/full-1.wav", "rb") as f:
        wav_data = f.read()

    processed_wav = one_band_eq(wav_data, 145, 150, 10)

    with open("output.wav", "wb") as f:
        f.write(processed_wav)
