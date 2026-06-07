import pygame
from .shared import W, H, Fonts, GainKnob
from .device_view import DeviceView
from .string_view import StringView
from .rounds_view import RoundsView
from .quiz_view import QuizView
from .finished_view import FinishedView
from .tuner_view import TunerView
from quiz import QuizState


class Renderer:
    def __init__(self):
        pygame.init()
        screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption('MemBoard')
        clock = pygame.time.Clock()
        fonts = Fonts()
        self._knob = GainKnob()  # one global gain shared by the quiz and tuner

        self._device   = DeviceView(screen, clock, fonts)
        self._strings  = StringView(screen, clock, fonts, self._knob)
        self._rounds   = RoundsView(screen, clock, fonts)
        self._quiz     = QuizView(screen, clock, fonts, self._knob)
        self._finished = FinishedView(screen, clock, fonts)
        self._tuner    = TunerView(screen, clock, fonts, self._knob)

    @property
    def gain(self) -> float:
        return self._knob.gain

    def draw_menu(self, devices: list[dict], selected: int):
        self._device.draw(devices, selected)

    def draw_string_menu(self, options: list[str], selected: int, rms: float = 0.0):
        self._strings.draw(options, selected, rms)

    def draw_rounds_menu(self, options: list[int], selected: int, best_scores: dict):
        self._rounds.draw(options, selected, best_scores)

    def draw(self, quiz: QuizState, now: float, rms: float = 0.0):
        self._quiz.draw(quiz, now, rms)

    def draw_finished(self, quiz: QuizState):
        self._finished.draw(quiz)

    def update_tuner(self, freq: float | None):
        self._tuner.update(freq)

    def draw_tuner(self, rms: float = 0.0):
        self._tuner.draw(rms)

    def poll_device_event(self) -> tuple[bool, bool, int, bool]:
        return self._device.poll()

    def poll_string_event(self) -> tuple[bool, bool, int, bool, bool]:
        return self._strings.poll()

    def poll_rounds_event(self) -> tuple[bool, bool, int, bool]:
        return self._rounds.poll()

    def poll_events(self) -> tuple[bool, bool]:
        return self._quiz.poll()

    def poll_finished_event(self) -> tuple[bool, bool, bool]:
        return self._finished.poll()

    def poll_tuner_event(self) -> tuple[bool, bool]:
        return self._tuner.poll()

    def quit(self):
        pygame.quit()
