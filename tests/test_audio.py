import numpy as np
import pytest
from audio import freq_to_note, PitchStabilizer, _detect_frequency, SAMPLE_RATE, FFT_SIZE


# ------------------------------------------------------------------ freq_to_note

@pytest.mark.parametrize('freq, expected_note, expected_octave', [
    (440.00, 'A',  4),   # A4 reference pitch
    (220.00, 'A',  3),   # A3 one octave down
    (880.00, 'A',  5),   # A5 one octave up
    (261.63, 'C',  4),   # middle C
    (329.63, 'E',  4),   # E4
    (246.94, 'B',  3),   # B3
    (196.00, 'G',  3),   # G3
    (164.81, 'E',  3),   # E3 (open low-e equivalent)
    (369.99, 'F#', 4),   # F#4
    (415.30, 'G#', 4),   # G#4 / Ab4
    (493.88, 'B',  4),   # B4
    (523.25, 'C',  5),   # C5
])
def test_freq_to_note(freq, expected_note, expected_octave):
    note, octave = freq_to_note(freq)
    assert note == expected_note
    assert octave == expected_octave


def test_freq_to_note_octave_boundary_up():
    # 932.33 Hz = A#5 / Bb5
    note, octave = freq_to_note(932.33)
    assert note == 'A#'
    assert octave == 5


def test_freq_to_note_octave_boundary_down():
    # 116.54 Hz = A#2 / Bb2
    note, octave = freq_to_note(116.54)
    assert note == 'A#'
    assert octave == 2


# ------------------------------------------------------------------ PitchStabilizer

def _feed(stab: PitchStabilizer, freq, n: int):
    for _ in range(n):
        stab.update(freq)


def test_stabilizer_no_reading_before_min_samples():
    stab = PitchStabilizer(min_samples=4)
    for _ in range(3):
        stab.update(440.0)
        assert stab.reading is None
    stab.update(440.0)
    assert stab.reading is not None


def test_stabilizer_steady_note():
    stab = PitchStabilizer()
    _feed(stab, 440.0, 10)
    note, octave, cents = stab.reading
    assert (note, octave) == ('A', 4)
    assert abs(cents) < 1.0


def test_stabilizer_reports_sharp_and_flat():
    sharp = PitchStabilizer()
    _feed(sharp, 445.0, 10)
    assert sharp.reading[0] == 'A' and sharp.reading[2] > 0

    flat = PitchStabilizer()
    _feed(flat, 435.0, 10)
    assert flat.reading[0] == 'A' and flat.reading[2] < 0


def test_stabilizer_rejects_single_octave_glitch():
    # One spurious octave reading in a steady note must not change the displayed note.
    stab = PitchStabilizer()
    _feed(stab, 440.0, 8)
    stab.update(880.0)          # glitch
    _feed(stab, 440.0, 4)
    assert stab.reading[:2] == ('A', 4)


def test_stabilizer_switches_to_genuinely_new_note():
    # A sustained move to B4 should eventually relabel.
    stab = PitchStabilizer()
    _feed(stab, 440.0, 10)
    assert stab.reading[:2] == ('A', 4)
    _feed(stab, 493.88, 12)     # B4 held
    assert stab.reading[:2] == ('B', 4)


def test_stabilizer_resets_on_sustained_silence():
    stab = PitchStabilizer(silence_tolerance=4)
    _feed(stab, 440.0, 10)
    assert stab.reading is not None
    _feed(stab, None, 4)
    assert stab.reading is None


def test_stabilizer_tolerates_brief_dropout():
    stab = PitchStabilizer(silence_tolerance=4)
    _feed(stab, 440.0, 10)
    stab.update(None)           # one dropped block
    stab.update(None)
    assert stab.reading is not None  # not enough silence to reset


# ------------------------------------------------------------------ _detect_frequency

def _sine(freq: float, amplitude: float = 0.8, length: int = FFT_SIZE) -> np.ndarray:
    """Pure sine — only use for silence/range tests; HPS needs harmonics."""
    t = np.arange(length) / SAMPLE_RATE
    return (np.sin(2 * np.pi * freq * t) * amplitude).astype('float32')


def _guitar(freq: float, amplitude: float = 0.8, length: int = FFT_SIZE) -> np.ndarray:
    """Sawtooth-like signal (fundamental + harmonics) that HPS can correctly analyse."""
    t = np.arange(length) / SAMPLE_RATE
    sig = (
        np.sin(2 * np.pi * freq * 1 * t) * 0.60 +
        np.sin(2 * np.pi * freq * 2 * t) * 0.25 +
        np.sin(2 * np.pi * freq * 3 * t) * 0.10 +
        np.sin(2 * np.pi * freq * 4 * t) * 0.05
    ) * amplitude
    return sig.astype('float32')


def test_detect_frequency_silence_returns_none():
    audio = np.zeros(FFT_SIZE, dtype='float32')
    assert _detect_frequency(audio) is None


def test_detect_frequency_detects_a4():
    audio = _guitar(440.0)
    freq = _detect_frequency(audio)
    assert freq is not None
    note, _ = freq_to_note(freq)
    assert note == 'A'


def test_detect_frequency_detects_e4():
    audio = _guitar(329.63)
    freq = _detect_frequency(audio)
    assert freq is not None
    note, octave = freq_to_note(freq)
    assert note == 'E'
    assert octave == 4


def test_detect_frequency_detects_b3():
    audio = _guitar(246.94)
    freq = _detect_frequency(audio)
    assert freq is not None
    note, octave = freq_to_note(freq)
    assert note == 'B'
    assert octave == 3


def test_detect_frequency_detects_low_e():
    audio = _guitar(164.81)  # E3 — open low-e on guitar
    freq = _detect_frequency(audio)
    assert freq is not None
    note, octave = freq_to_note(freq)
    assert note == 'E'
    assert octave == 3


def test_detect_frequency_rejects_below_range():
    # 30 Hz is below the 50 Hz floor in _detect_frequency
    audio = _sine(30.0)
    freq = _detect_frequency(audio)
    # Either None or mapped above 50 Hz — must not return 30 Hz
    if freq is not None:
        assert freq >= 50


def test_detect_frequency_within_guitar_range():
    # Any detected frequency should be within the search window (50-1400 Hz)
    for test_freq in [82.41, 110.0, 196.0, 392.0, 659.25, 1174.66]:
        audio = _sine(test_freq)
        freq = _detect_frequency(audio)
        if freq is not None:
            assert 50 <= freq <= 1400
