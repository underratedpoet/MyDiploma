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


if __name__ == "__main__":
    # До мажор (C major)
    key = get_key_chords(Note("D", "малая"), "m")
    print("Key:")
    for chord in key:
        print(chord)
