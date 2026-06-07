import queue
import threading
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 44100
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


def _detect_frequency(audio_block: np.ndarray) -> float | None:
    windowed = audio_block * np.hanning(len(audio_block))
    fft_magnitudes = np.abs(np.fft.rfft(windowed))
    freqs = np.fft.rfftfreq(len(windowed), 1 / SAMPLE_RATE)

    hps = fft_magnitudes.copy()
    for h in range(2, 6):
        downsampled = fft_magnitudes[::h]
        hps[:len(downsampled)] *= downsampled

    lo = np.searchsorted(freqs, 50)
    hi = np.searchsorted(freqs, 1400)
    hps_r, freqs_r = hps[lo:hi], freqs[lo:hi]

    threshold = np.max(hps_r) * 0.3
    for i in range(1, len(hps_r) - 1):
        if hps_r[i] > hps_r[i - 1] and hps_r[i] > hps_r[i + 1] and hps_r[i] >= threshold:
            return float(freqs_r[i])
    return None


class AudioStream:
    def __init__(self):
        self._ring = np.zeros(FFT_SIZE, dtype='float32')
        self._lock = threading.Lock()
        self._queue: queue.Queue = queue.Queue(maxsize=1)
        self._stream = None

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
        chunk = indata[:, 0]
        with self._lock:
            self._ring = np.roll(self._ring, -len(chunk))
            self._ring[-len(chunk):] = chunk
        rms = float(np.sqrt(np.mean(chunk ** 2)))
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
