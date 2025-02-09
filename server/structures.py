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