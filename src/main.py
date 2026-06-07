import queue
import time
import audio as audio_module
from audio import AudioStream, freq_to_note, get_input_devices
from quiz import QuizState
from ui import Renderer
from logger import log_session, get_best_scores

ROUND_OPTIONS = [5, 25, 50, 75, 100]

STRING_OPTIONS = [
    ('All Strings',  [1, 2, 3, 4, 5, 6]),
    ('e  (1)',        [1]),
    ('B  (2)',        [2]),
    ('G  (3)',        [3]),
    ('D  (4)',        [4]),
    ('A  (5)',        [5]),
    ('E  (6)',        [6]),
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


def run_string_menu(renderer: Renderer) -> list[int] | str | None:
    labels = [label for label, _ in STRING_OPTIONS]
    selected = 0
    renderer.draw_string_menu(labels, selected)
    while True:
        running, confirmed, delta, back = renderer.poll_string_event()
        if not running:
            return None
        if back:
            return 'back'
        selected = (selected + delta) % len(STRING_OPTIONS)
        if confirmed:
            return STRING_OPTIONS[selected][1]
        renderer.draw_string_menu(labels, selected)


def run_rounds_menu(renderer: Renderer, allowed_strings: list[int]) -> int | str | None:
    selected = 0
    best_scores = get_best_scores(allowed_strings, ROUND_OPTIONS)
    renderer.draw_rounds_menu(ROUND_OPTIONS, selected, best_scores)
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


def run_quiz(renderer: Renderer, device_index: int,
             allowed_strings: list[int], max_rounds: int) -> str | None:
    """Returns 'rerun', 'back', or None (quit)."""
    audio_module.DEVICE = device_index
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

            if not renderer.poll_events():
                return None
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
            result = run_string_menu(renderer)
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
