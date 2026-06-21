import queue
import time
import audio as audio_module
from audio import AudioStream, freq_to_note, get_input_devices
from quiz import QuizState
from ui import Renderer
from logger import log_session, get_best_scores

ROUND_OPTIONS = [5, 25, 50, 75, 100]

STRING_ROWS = [
    ('e  (1)', 1), ('B  (2)', 2), ('G  (3)', 3),
    ('D  (4)', 4), ('A  (5)', 5), ('E  (6)', 6),
]


def run_device_menu(renderer: Renderer) -> int | None:
    devices = get_input_devices()
    selected = 0
    renderer.draw_menu(devices, selected)
    while True:
        running, confirmed, delta, _back = renderer.poll_device_event()
        if not running:
            return None
        selected = (selected + delta) % len(devices)
        if confirmed:
            return devices[selected]['index']
        renderer.draw_menu(devices, selected)


def run_tuner(renderer: Renderer, stream: AudioStream) -> str | None:
    """Live tuner screen, reusing an already-open audio stream.

    Returns 'back' when dismissed, or None to quit the app.
    """
    while True:
        running, back = renderer.poll_tuner_event()
        if not running:
            return None
        if back:
            return 'back'
        stream.gain = renderer.gain
        try:
            renderer.update_tuner(stream.get_freq())
        except queue.Empty:
            pass
        renderer.draw_tuner(stream.rms)


def run_string_menu(renderer: Renderer, device_index: int) -> list[int] | str | None:
    audio_module.DEVICE = device_index
    selected: set[int] = {1, 2, 3, 4, 5, 6}
    cursor = 0
    rows = ['All Strings'] + [label for label, _ in STRING_ROWS]
    with AudioStream() as stream:
        checked = [len(selected) == 6] + [idx in selected for _, idx in STRING_ROWS]
        renderer.draw_string_menu(rows, checked, cursor, bool(selected), stream.rms)
        while True:
            stream.gain = renderer.gain
            running, confirmed, delta, toggle, back, tuner = renderer.poll_string_event()
            if not running:
                return None
            if back:
                return 'back'
            if tuner:
                if run_tuner(renderer, stream) is None:
                    return None
                checked = [len(selected) == 6] + [idx in selected for _, idx in STRING_ROWS]
                renderer.draw_string_menu(rows, checked, cursor, bool(selected), stream.rms)
                continue
            cursor = (cursor + delta) % len(rows)
            if toggle:
                if cursor == 0:
                    if len(selected) == 6:
                        selected.clear()
                    else:
                        selected = {1, 2, 3, 4, 5, 6}
                else:
                    idx = STRING_ROWS[cursor - 1][1]
                    if idx in selected:
                        selected.discard(idx)
                    else:
                        selected.add(idx)
            if confirmed and selected:
                return sorted(selected)
            checked = [len(selected) == 6] + [idx in selected for _, idx in STRING_ROWS]
            renderer.draw_string_menu(rows, checked, cursor, bool(selected), stream.rms)


def run_rounds_menu(renderer: Renderer, allowed_strings: list[int]) -> int | str | None:
    selected = 0
    best_scores = get_best_scores(allowed_strings, ROUND_OPTIONS)
    renderer.draw_rounds_menu(ROUND_OPTIONS, selected, best_scores)
    renderer.flush_events()
    while True:
        running, confirmed, delta, back = renderer.poll_rounds_event()
        if not running:
            return None
        if back:
            return 'back'
        selected = (selected + delta) % len(ROUND_OPTIONS)
        if confirmed:
            return ROUND_OPTIONS[selected]
        renderer.draw_rounds_menu(ROUND_OPTIONS, selected, best_scores)


def run_countdown(renderer: Renderer) -> bool:
    """Counts down 5…1. Returns False if the user quits during countdown."""
    for n in range(5, 0, -1):
        start = time.time()
        while time.time() - start < 1.0:
            renderer.draw_countdown(n)
            if not renderer.poll_countdown():
                return False
    return True


def run_quiz(renderer: Renderer, device_index: int,
             allowed_strings: list[int], max_rounds: int) -> str | None:
    """Returns 'rerun', 'back', or None (quit)."""
    audio_module.DEVICE = device_index
    if not run_countdown(renderer):
        return None
    quiz = QuizState.start(max_rounds=max_rounds, allowed_strings=allowed_strings)
    logged = False

    with AudioStream() as stream:
        while True:
            now = time.time()

            if quiz.state == 'finished':
                if not logged:
                    log_session(quiz)
                    logged = True
                renderer.draw_finished(quiz)
                running, rerun, back = renderer.poll_finished_event()
                if not running:
                    return None
                if rerun:
                    return 'rerun'
                if back:
                    return 'back'
                continue

            running, back = renderer.poll_events()
            if not running:
                return None
            if back:
                return 'back'
            stream.gain = renderer.gain

            try:
                freq = stream.get_freq()
                if freq:
                    note, octave = freq_to_note(freq)
                    quiz.feed_note(note, octave)
                else:
                    quiz.feed_note(None, None)
            except queue.Empty:
                pass

            quiz.tick(now)
            renderer.draw(quiz, now, stream.rms)


def main():
    renderer = Renderer()
    state = 'device'
    device_index = None
    allowed_strings = None
    max_rounds = None

    while True:
        if state == 'device':
            result = run_device_menu(renderer)
            if result is None:
                break
            device_index = result
            state = 'strings'

        elif state == 'strings':
            result = run_string_menu(renderer, device_index)
            if result is None:
                break
            if result == 'back':
                state = 'device'
            else:
                allowed_strings = result
                state = 'rounds'

        elif state == 'rounds':
            result = run_rounds_menu(renderer, allowed_strings)
            if result is None:
                break
            if result == 'back':
                state = 'strings'
            else:
                max_rounds = result
                state = 'quiz'

        elif state == 'quiz':
            result = run_quiz(renderer, device_index, allowed_strings, max_rounds)
            if result is None:
                break
            if result == 'back':
                state = 'rounds'
            # 'rerun' keeps state == 'quiz', loops back with same settings

    renderer.quit()


if __name__ == '__main__':
    main()
