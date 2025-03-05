import random

class Note:
    NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    OCTAVES = ["субконтроктава", "контроктава", "большая", "малая", "первая", "вторая", "третья", "четвертая", "пятая"]

    def __init__(self, name: str, octave: str):
        if name not in self.NOTES or octave not in self.OCTAVES:
            raise ValueError("Некорректные нота или октава")
        self.name = name
        self.octave = octave

    def __repr__(self):
        return f"{self.name} ({self.octave})"

    def transpose(self, semitones: int):
        """Сдвигает ноту на заданное количество полутонов."""
        index = self.NOTES.index(self.name) + semitones
        octave_index = self.OCTAVES.index(self.octave) + index // 12
        index %= 12

        if 0 <= octave_index < len(self.OCTAVES):
            return Note(self.NOTES[index], self.OCTAVES[octave_index])
        else:
            raise ValueError("Транспозиция выходит за допустимый диапазон октав")

class Chord:
    def __init__(self, root: Note, intervals: list[int]):
        """Создает аккорд на основе основной ноты и списка интервалов (в полутонах)."""
        self.notes = [root] + [root.transpose(interval) for interval in intervals]

    def __repr__(self):
        return " - ".join(map(str, self.notes))

    def transpose(self, semitones: int):
        """Транспонирует аккорд на указанное число полутонов."""
        self.notes = [note.transpose(semitones) for note in self.notes]
        return self
    
def get_key_chords(root: Note, scale_type: str) -> list[Chord]:
    """
    Возвращает 6 аккордов, входящих в заданную тональность.

    :param root: Основная нота тональности.
    :param scale_type: "M" для мажора, "m" для минора.
    :return: Список объектов Chord.
    """
    if scale_type not in ("M", "m"):
        raise ValueError("Тональность должна быть 'M' (мажор) или 'm' (минор).")

    # Мажорные и минорные ступени (в полутонах)
    major_steps = [0, 2, 4, 5, 7, 9]  # I, ii, iii, IV, V, vi
    minor_steps = [0, 3, 5, 7, 8, 10]  # i, III, iv, v, VI, vii

    # Правильные трезвучия в тональности:
    major_chords = [[4, 7], [3, 7], [3, 7], [4, 7], [4, 7], [3, 7]]
    minor_chords = [[3, 7], [4, 7], [3, 7], [3, 7], [4, 7], [4, 7]]

    steps = major_steps if scale_type == "M" else minor_steps
    chords_intervals = major_chords if scale_type == "M" else minor_chords

    # Определяем октаву, чтобы аккорды были в средней тесситуре
    middle_octave = "малая" if root.octave in Note.OCTAVES[:4] else "первая"

    # Создаём список аккордов
    chords = []
    for step, intervals in zip(steps, chords_intervals):
        chord_root = root.transpose(step)
        chord_root.octave = middle_octave  # Переводим в среднюю тесситуру
        chords.append(Chord(chord_root, intervals))

    return chords

def generate_random_interval() -> tuple[Note, Note, int]:
    """
    Генерирует две случайные ноты в средней тесситуре и интервал между ними.
    
    :return: Кортеж (первая нота, вторая нота, интервал в полутонах)
    """
    # Средняя тесситура (малая и первая октавы)
    middle_octaves = ["малая", "первая"]

    # Выбираем случайную ноту в средней тесситуре
    root_note = Note(random.choice(Note.NOTES), random.choice(middle_octaves))

    # Выбираем случайный интервал от 0 (прима) до 24 (квинтдецима)
    semitones = random.randint(0, 24)

    try:
        # Получаем вторую ноту путем транспозиции
        second_note = root_note.transpose(semitones)
        return [root_note, second_note], semitones
    except ValueError:
        # Если транспозиция выходит за пределы октав, пробуем снова
        return generate_random_interval()

def generate_chord_progression(n: int) -> tuple[list[Chord], list[int]]:
    """
    Генерирует последовательность из `n` аккордов в одной случайной тональности.
    
    :param n: Количество аккордов (не менее 2)
    :return: Кортеж (список аккордов, список ступеней)
    """
    if n < 2:
        raise ValueError("Количество аккордов должно быть >= 2.")

    # Выбираем случайный корень тональности и мажор/минор
    root_note = Note(random.choice(Note.NOTES), octave="малая")
    scale_type = random.choice(["M", "m"])  # Мажор или минор

    # Получаем аккорды этой тональности
    chords = get_key_chords(root_note, scale_type)

    # Первая и последняя ступени - тоника (I ступень)
    chord_sequence = [chords[0]]  # Начинаем с I ступени
    step_sequence = [1]  # Ступень первой ноты (I)

    # Выбираем случайные аккорды для промежуточных шагов
    available_steps = [2, 3, 4, 5, 6]  # Возможные ступени
    for _ in range(n - 2):
        step = random.choice(available_steps)
        chord_sequence.append(chords[step - 1])  # Индексация с 0
        step_sequence.append(step)

    # Завершаем тоникой
    chord_sequence.append(chords[0])
    step_sequence.append(1)

    return chord_sequence, step_sequence

if __name__ == "__main__":
    # До мажор (C major)
    key = get_key_chords(Note("D", "малая"), "m")
    print("Key:")
    for chord in key:
        print(chord)

    print(generate_random_interval())
