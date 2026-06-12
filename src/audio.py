import queue
import threading
from collections import deque
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 48000
BLOCK_SIZE  = 2048
FFT_SIZE    = 16384
SILENCE_RMS = 0.008
DEVICE      = None  # None = system default; set to device index from sd.query_devices()

NOTE_NAMES = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']


def get_input_devices() -> list[dict]:
    devices = sd.query_devices()
    return [
        {'index': i, 'name': d['name']}
        for i, d in enumerate(devices)
        if d['max_input_channels'] > 0
    ]


def freq_to_note(freq: float) -> tuple[str, int]:
    semitones_from_a4 = 12 * np.log2(freq / 440.0)
    nearest = round(semitones_from_a4)
    note = NOTE_NAMES[nearest % 12]
    octave = 4 + (nearest + 9) // 12
    return note, octave


def _index_to_note(idx: int) -> tuple[str, int]:
    """Semitone index relative to A4 -> (note, octave)."""
    return NOTE_NAMES[idx % 12], 4 + (idx + 9) // 12


class PitchStabilizer:
    """Turns a noisy stream of per-block detections into a steady tuner reading.

    - A median over the recent window rejects single-frame outliers (e.g. octave jumps).
    - The displayed note changes once the pitch crosses the ~50-cent boundary into
      a neighbour and stays there for ``confirm`` readings (a little hysteresis), so
      a sustained note never flickers yet the label still matches the nearest note
      like any other tuner.
    - Both the note and the cents needle are derived from one lightly smoothed
      frequency, so the label and the needle never disagree.
    """

    def __init__(self, window: int = 5, min_samples: int = 3,
                 switch_cents: float = 50.0, confirm: int = 2,
                 ema: float = 0.4, silence_tolerance: int = 4):
        self._window = window
        self._min = min_samples
        self._switch = switch_cents
        self._confirm = confirm
        self._ema = ema
        self._silence_tol = silence_tolerance
        self.reset()

    def reset(self):
        self._history: deque = deque(maxlen=self._window)
        self._idx: int | None = None      # held note, semitones from A4
        self._display: float | None = None  # EMA frequency
        self._cand: int | None = None
        self._cand_count = 0
        self._silence = 0

    def update(self, freq: float | None):
        """Feed one detection in Hz, or None for silence/no-detection."""
        if not freq:
            self._silence += 1
            if self._silence >= self._silence_tol:
                self.reset()
            return
        self._silence = 0
        self._history.append(freq)
        if len(self._history) < self._min:
            return

        med = float(np.median(self._history))
        self._display = med if self._display is None else (1 - self._ema) * self._display + self._ema * med

        semis = 12 * np.log2(self._display / 440.0)
        if self._idx is None:
            self._idx = int(round(semis))
            return

        if abs(semis - self._idx) * 100.0 > self._switch:
            cand = int(round(semis))
            self._cand_count = self._cand_count + 1 if cand == self._cand else 1
            self._cand = cand
            if self._cand_count >= self._confirm:
                self._idx = cand
                self._cand = None
                self._cand_count = 0
        else:
            self._cand = None
            self._cand_count = 0

    @property
    def freq(self) -> float | None:
        return self._display

    @property
    def reading(self) -> tuple[str, int, float] | None:
        """Stable (note, octave, cents) or None when there's no confident pitch."""
        if self._idx is None or self._display is None:
            return None
        note, octave = _index_to_note(self._idx)
        cents = (12 * np.log2(self._display / 440.0) - self._idx) * 100.0
        return note, octave, cents


def _parabolic_peak(mags: np.ndarray, i: int) -> float:
    """Sub-bin offset of the peak at bin ``i`` via parabolic interpolation.

    The raw FFT bin width (~3 Hz here) is far too coarse for cents-accurate
    tuning, so we fit a parabola to the peak and its two neighbours to recover
    a fractional-bin position. Returns an offset in ``(-0.5, 0.5)``.
    """
    if i <= 0 or i >= len(mags) - 1:
        return 0.0
    a, b, c = mags[i - 1], mags[i], mags[i + 1]
    denom = a - 2.0 * b + c
    if denom == 0:
        return 0.0
    return max(-0.5, min(0.5, 0.5 * (a - c) / denom))


def _detect_frequency(audio_block: np.ndarray) -> float | None:
    windowed = audio_block * np.hanning(len(audio_block))
    fft_magnitudes = np.abs(np.fft.rfft(windowed))
    freqs = np.fft.rfftfreq(len(windowed), 1 / SAMPLE_RATE)

    # Harmonic product spectrum to favour the fundamental over its harmonics.
    # Deliberately few harmonics: with too many, a subharmonic (whose partials
    # all line up) can out-score the true fundamental whose upper harmonics are
    # weak, making low notes read an octave flat.
    hps = fft_magnitudes.copy()
    for h in range(2, 4):
        downsampled = fft_magnitudes[::h]
        hps[:len(downsampled)] *= downsampled

    lo = int(np.searchsorted(freqs, 50))
    hi = int(np.searchsorted(freqs, 1400))
    if hi <= lo:
        return None

    peak = lo + int(np.argmax(hps[lo:hi]))
    if hps[peak] <= 0:
        return None

    # Octave guard: HPS can still latch onto a subharmonic, whose bin carries
    # almost no real spectral energy. If the bin an octave up is far stronger in
    # the raw spectrum, that is the true fundamental.
    upper = peak * 2
    if upper < len(fft_magnitudes) and fft_magnitudes[upper] > fft_magnitudes[peak] * 4.0:
        peak = upper

    refined = peak + _parabolic_peak(fft_magnitudes, peak)
    return float(refined * SAMPLE_RATE / len(windowed))


class AudioStream:
    def __init__(self):
        self._ring = np.zeros(FFT_SIZE, dtype='float32')
        self._lock = threading.Lock()
        self._queue: queue.Queue = queue.Queue(maxsize=1)
        self._stream = None
        self.rms: float = 0.0
        self.gain: float = 1.0

    def __enter__(self):
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            channels=1,
            dtype='float32',
            device=DEVICE,
            callback=self._callback,
        )
        self._stream.__enter__()
        return self

    def __exit__(self, *args):
        self._stream.__exit__(*args)

    def _callback(self, indata, frames, time, status):
        chunk = indata[:, 0] * self.gain
        with self._lock:
            self._ring = np.roll(self._ring, -len(chunk))
            self._ring[-len(chunk):] = chunk
        rms = float(np.sqrt(np.mean(chunk ** 2)))
        self.rms = rms
        if rms > SILENCE_RMS:
            with self._lock:
                window = self._ring.copy()
            freq = _detect_frequency(window)
        else:
            freq = None
        try:
            self._queue.put_nowait(freq)
        except queue.Full:
            pass

    def get_freq(self) -> float | None:
        """Returns detected frequency or None for silence. Raises queue.Empty if no new data."""
        return self._queue.get_nowait()
