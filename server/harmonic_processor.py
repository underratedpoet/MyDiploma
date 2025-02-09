import io
import pretty_midi
import subprocess
import soundfile as sf

from server.structures import Note, Chord  # Импортируем Note и Chord

SF2_PATH = "/server/FluidR3_GM.sf2"  # Путь к soundfont

def midi_to_wav(midi_data: bytes) -> bytes:
    """Конвертирует MIDI (bytes) в WAV (bytes)."""
    midi_file = "temp.mid"
    wav_file = "temp.wav"

    with open(midi_file, "wb") as f:
        f.write(midi_data)

    subprocess.run([
        "fluidsynth", "-ni", SF2_PATH, midi_file, "-F", wav_file, "-r", "44100"
    ], check=True)

    wav_bytes = io.BytesIO()
    data, samplerate = sf.read(wav_file, dtype="int16")
    sf.write(wav_bytes, data, samplerate, format="WAV")

    return wav_bytes.getvalue()

def get_notes_wav(notes: list[Note]) -> bytes:
    """
    Создаёт WAV-файл из массива нот (все звучат одновременно 2 секунды).
    """
    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)  # Grand Piano

    for note in notes:
        midi_note = note_to_midi(note)
        instrument.notes.append(pretty_midi.Note(
            velocity=100, pitch=midi_note, start=0.0, end=2.0
        ))

    midi.instruments.append(instrument)
    midi_bytes = io.BytesIO()
    midi.write(midi_bytes)
    return midi_to_wav(midi_bytes.getvalue())

def get_chords_wav(chords: list[Chord]) -> bytes:
    """
    Создаёт WAV-файл из массива аккордов (каждый звучит 1 секунду).
    """
    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)  # Grand Piano
    start_time = 0.0

    for chord in chords:
        for note in chord.notes:
            midi_note = note_to_midi(note)
            instrument.notes.append(pretty_midi.Note(
                velocity=100, pitch=midi_note, start=start_time, end=start_time + 1.0
            ))
        start_time += 1.0

    midi.instruments.append(instrument)
    midi_bytes = io.BytesIO()
    midi.write(midi_bytes)
    return midi_to_wav(midi_bytes.getvalue())

def note_to_midi(note: Note) -> int:
    """Конвертирует объект Note в MIDI-номер."""
    note_map = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
    octave_index = Note.OCTAVES.index(note.octave)
    return 12 * (octave_index + 1) + note_map[note.name]


if __name__ == "__main__":
    notes = [Note("C", "первая"), Note("E", "первая"), Note("G", "первая")]
    chords = [Chord(Note("C", "первая"), [4, 7]), Chord(Note("D", "первая"), [3, 7])]

    with open("notes.wav", "wb") as f:
        f.write(get_notes_wav(notes))

    with open("chords.wav", "wb") as f:
        f.write(get_chords_wav(chords))
