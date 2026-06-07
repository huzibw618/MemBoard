import time
import random
from dataclasses import dataclass, field

STABILITY          = 4
RESULT_HOLD        = 5.0

# (note, octave) for frets 1-11 on each string
STRING_NOTES = {
    1: [('F',4),('F#',4),('G',4),('G#',4),('A',4),('A#',4),('B',4),('C',5),('C#',5),('D',5),('D#',5)],
    2: [('C',4),('C#',4),('D',4),('D#',4),('E',4),('F',4),('F#',4),('G',4),('G#',4),('A',4),('A#',4)],
    3: [('G#',3),('A',3),('A#',3),('B',3),('C',4),('C#',4),('D',4),('D#',4),('E',4),('F',4),('F#',4)],
    4: [('D#',3),('E',3),('F',3),('F#',3),('G',3),('G#',3),('A',3),('A#',3),('B',3),('C',4),('C#',4)],
    5: [('A#',2),('B',2),('C',3),('C#',3),('D',3),('D#',3),('E',3),('F',3),('F#',3),('G',3),('G#',3)],
    6: [('F',2),('F#',2),('G',2),('G#',2),('A',2),('A#',2),('B',2),('C',3),('C#',3),('D',3),('D#',3)],
}

STRING_NAMES = {1: 'e', 2: 'B', 3: 'G', 4: 'D', 5: 'A', 6: 'E'}
OPEN_NOTES   = {1: 'e', 2: 'B', 3: 'G', 4: 'D', 5: 'A', 6: 'E'}


def _new_challenge(allowed: list[int], last: tuple | None = None) -> tuple[int, str, int]:
    while True:
        s = random.choice(allowed)
        n, o = random.choice(STRING_NOTES[s])
        if last is None or (s, n, o) != last:
            return s, n, o


@dataclass
class QuizState:
    target_string:   int   = 1
    target_note:     str   = 'F'
    target_octave:   int   = 4
    challenge_start: float = 0.0
    state:           str   = 'challenge'
    result_correct:  bool  = False
    result_time:     float = 0.0
    result_played:   str   = ''
    result_played_octave: int = 0
    result_until:    float = 0.0
    score:           int   = 0
    total:           int   = 0
    max_rounds:      int   = 25
    allowed_strings: list  = field(default_factory=lambda: [1,2,3,4,5,6])
    times:           list  = field(default_factory=list)
    correct_times:   list  = field(default_factory=list)
    _note_history:   list  = field(default_factory=list, repr=False)

    @classmethod
    def start(cls, max_rounds: int, allowed_strings: list[int]) -> 'QuizState':
        s, n, o = _new_challenge(allowed_strings)
        return cls(target_string=s, target_note=n, target_octave=o,
                   challenge_start=time.time(), max_rounds=max_rounds,
                   allowed_strings=allowed_strings)

    def feed_note(self, note: str | None, octave: int | None):
        if note and octave is not None:
            candidate = (note, octave)
            self._note_history.append(candidate)
            if len(self._note_history) > STABILITY:
                self._note_history.pop(0)
            if self.state == 'challenge' and self._note_history.count(candidate) >= STABILITY:
                self._commit_result(note, octave)
        else:
            self._note_history.clear()

    def tick(self, now: float):
        if self.state == 'result' and now >= self.result_until:
            if self.total >= self.max_rounds:
                self.state = 'finished'
            else:
                s, n, o = _new_challenge(self.allowed_strings, last=(self.target_string, self.target_note, self.target_octave))
                self.target_string, self.target_note, self.target_octave = s, n, o
                self.challenge_start = time.time()
                self._note_history.clear()
                self.state = 'challenge'

    def elapsed(self, now: float) -> float:
        return now - self.challenge_start

    def avg_time(self) -> float:
        return sum(self.times) / len(self.times) if self.times else 0.0

    def memscore(self, target_time: float = 3.0) -> float:
        if self.total == 0 or not self.correct_times:
            return 0.0
        accuracy = self.score / self.total
        avg_correct = sum(self.correct_times) / len(self.correct_times)
        speed = min(1.0, target_time / avg_correct)
        return round(accuracy * speed * 100, 1)

    def _commit_result(self, note: str, octave: int):
        now = time.time()
        elapsed = now - self.challenge_start
        self.result_correct = (note == self.target_note and octave == self.target_octave)
        self.result_time         = elapsed
        self.result_played       = note
        self.result_played_octave = octave
        self.result_until   = now + RESULT_HOLD
        self.total         += 1
        self.times.append(elapsed)
        if self.result_correct:
            self.score += 1
            self.correct_times.append(elapsed)
        self.state = 'result'
