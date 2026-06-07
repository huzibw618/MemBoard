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
    ('E  (1)',        [1]),
    ('B  (2)',        [2]),
    ('G  (3)',        [3]),
    ('D  (4)',        [4]),
    ('A  (5)',        [5]),
    ('e  (6)',        [6]),
]


def run_device_menu(renderer: Renderer) -> int | None:
    devices = get_input_devices()
    selected = 0
    renderer.draw_menu(devices, selected)
    while True:
        running, confirmed, delta = renderer.poll_menu_event(len(devices))
        if not running:
            return None
        selected = (selected + delta) % len(devices)
        if confirmed:
            return devices[selected]['index']
        renderer.draw_menu(devices, selected)


def run_string_menu(renderer: Renderer) -> list[int] | None:
    labels = [label for label, _ in STRING_OPTIONS]
    selected = 0
    renderer.draw_string_menu(labels, selected)
    while True:
        running, confirmed, delta = renderer.poll_menu_event(len(STRING_OPTIONS))
        if not running:
            return None
        selected = (selected + delta) % len(STRING_OPTIONS)
        if confirmed:
            return STRING_OPTIONS[selected][1]
        renderer.draw_string_menu(labels, selected)


def run_rounds_menu(renderer: Renderer, allowed_strings: list[int]) -> int | None:
    selected = 0
    best_scores = get_best_scores(allowed_strings, ROUND_OPTIONS)
    renderer.draw_rounds_menu(ROUND_OPTIONS, selected, best_scores)
    while True:
        running, confirmed, delta = renderer.poll_menu_event(len(ROUND_OPTIONS))
        if not running:
            return None
        selected = (selected + delta) % len(ROUND_OPTIONS)
        if confirmed:
            return ROUND_OPTIONS[selected]
        renderer.draw_rounds_menu(ROUND_OPTIONS, selected, best_scores)


def main():
    renderer = Renderer()

    device_index = run_device_menu(renderer)
    if device_index is None:
        renderer.quit()
        return

    allowed_strings = run_string_menu(renderer)
    if allowed_strings is None:
        renderer.quit()
        return

    max_rounds = run_rounds_menu(renderer, allowed_strings)
    if max_rounds is None:
        renderer.quit()
        return

    audio_module.DEVICE = device_index
    quiz = QuizState.start(max_rounds=max_rounds, allowed_strings=allowed_strings)

    logged = False
    with AudioStream() as stream:
        running = True
        while running:
            now = time.time()

            if quiz.state == 'finished':
                if not logged:
                    log_session(quiz)
                    logged = True
                renderer.draw_finished(quiz)
                running = renderer.poll_events()
                continue

            running = renderer.poll_events()

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
            renderer.draw(quiz, now)

    renderer.quit()


if __name__ == '__main__':
    main()
