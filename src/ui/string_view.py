import pygame
from .shared import (W, H, BG, DIM, YELLOW, Fonts, GainKnob,
                     draw_back_button, draw_tuner_button, draw_input_bar, poll_menu)


class StringView:
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock, fonts: Fonts, knob: GainKnob):
        self.screen = screen
        self.clock = clock
        self.fonts = fonts
        self._knob = knob
        self._back_btn: pygame.Rect | None = None
        self._tuner_btn: pygame.Rect | None = None

    def draw(self, options: list[str], selected: int, rms: float = 0.0):
        self.screen.fill(BG)

        title = self.fonts.title.render('MemBoard', True, YELLOW)
        self.screen.blit(title, title.get_rect(center=(W // 2, 70)))

        draw_input_bar(self.screen, self.fonts, rms)
        self._knob.draw(self.screen, self.fonts)

        label = self.fonts.menu.render('Which strings do you want to practice?', True, DIM)
        self.screen.blit(label, label.get_rect(center=(W // 2, 150)))

        row_h, start_y = 52, 210
        for i, opt in enumerate(options):
            is_sel = i == selected
            surf = self.fonts.result.render(opt, True, YELLOW if is_sel else DIM)
            rect = surf.get_rect(center=(W // 2, start_y + i * row_h))
            if is_sel:
                pygame.draw.rect(self.screen, (35, 35, 55), rect.inflate(40, 10), border_radius=6)
            self.screen.blit(surf, rect)

        self._tuner_btn = draw_tuner_button(self.screen, self.fonts)
        self._back_btn = draw_back_button(self.screen, self.fonts)
        hint = self.fonts.hint.render('↑ ↓  navigate     Enter  confirm     T  tuner', True, DIM)
        self.screen.blit(hint, hint.get_rect(center=(W // 2 + 60, H - 30)))

        pygame.display.flip()
        self.clock.tick(60)

    def poll(self) -> tuple[bool, bool, int, bool, bool]:
        return poll_menu(self._back_btn, self._tuner_btn, self._knob)
