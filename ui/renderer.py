import pygame
from .shared import W, H, Fonts
from .device_view import DeviceView
from .string_view import StringView
from .rounds_view import RoundsView
from .quiz_view import QuizView
from .finished_view import FinishedView
from quiz import QuizState


class Renderer:
    def __init__(self):
        pygame.init()
        screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption('MemBoard')
        clock = pygame.time.Clock()
        fonts = Fonts()

        self._device   = DeviceView(screen, clock, fonts)
        self._strings  = StringView(screen, clock, fonts)
        self._rounds   = RoundsView(screen, clock, fonts)
        self._quiz     = QuizView(screen, clock, fonts)
        self._finished = FinishedView(screen, clock, fonts)

    @property
    def gain(self) -> float:
        return self._quiz.gain

    def draw_menu(self, devices: list[dict], selected: int):
        self._device.draw(devices, selected)

    def draw_string_menu(self, options: list[str], selected: int):
        self._strings.draw(options, selected)

    def draw_rounds_menu(self, options: list[int], selected: int, best_scores: dict):
        self._rounds.draw(options, selected, best_scores)

    def draw(self, quiz: QuizState, now: float, rms: float = 0.0):
        self._quiz.draw(quiz, now, rms)

    def draw_finished(self, quiz: QuizState):
        self._finished.draw(quiz)

    def poll_device_event(self) -> tuple[bool, bool, int, bool]:
        return self._device.poll()

    def poll_string_event(self) -> tuple[bool, bool, int, bool]:
        return self._strings.poll()

    def poll_rounds_event(self) -> tuple[bool, bool, int, bool]:
        return self._rounds.poll()

    def poll_events(self) -> bool:
        return self._quiz.poll()

    def poll_finished_event(self) -> tuple[bool, bool, bool]:
        return self._finished.poll()

    def quit(self):
        pygame.quit()
