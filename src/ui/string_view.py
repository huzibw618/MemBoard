import pygame
from .shared import (W, H, BG, DIM, YELLOW, Fonts, GainKnob,
                     draw_back_button, draw_tuner_button, draw_input_bar)


class StringView:
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock, fonts: Fonts, knob: GainKnob):
        self.screen = screen
        self.clock = clock
        self.fonts = fonts
        self._knob = knob
        self._back_btn: pygame.Rect | None = None
        self._tuner_btn: pygame.Rect | None = None

    def draw(self, options: list[str], checked: list[bool], cursor: int,
             can_start: bool, rms: float = 0.0):
        self.screen.fill(BG)

        title = self.fonts.title.render('MemBoard', True, YELLOW)
        self.screen.blit(title, title.get_rect(center=(W // 2, 70)))

        draw_input_bar(self.screen, self.fonts, rms)
        self._knob.draw(self.screen, self.fonts)

        label = self.fonts.menu.render('Which strings do you want to practice?', True, DIM)
        self.screen.blit(label, label.get_rect(center=(W // 2, 150)))

        row_h, start_y = 52, 210
        for i, opt in enumerate(options):
            is_cursor = i == cursor
            check_mark = '[x] ' if checked[i] else '[ ] '
            row_text = check_mark + opt
            surf = self.fonts.result.render(row_text, True, YELLOW if is_cursor else DIM)
            rect = surf.get_rect(center=(W // 2, start_y + i * row_h))
            if is_cursor:
                pygame.draw.rect(self.screen, (35, 35, 55), rect.inflate(40, 10), border_radius=6)
            self.screen.blit(surf, rect)

        self._tuner_btn = draw_tuner_button(self.screen, self.fonts)
        self._back_btn = draw_back_button(self.screen, self.fonts)
        hint_color = DIM if can_start else (50, 50, 65)
        hint = self.fonts.hint.render('↑↓ navigate   Space toggle   Enter start   T tuner', True, hint_color)
        self.screen.blit(hint, hint.get_rect(center=(W // 2, H - 30)))

        pygame.display.flip()
        self.clock.tick(60)

    def poll(self) -> tuple[bool, bool, int, bool, bool, bool]:
        """Returns (running, confirmed, delta, toggle, back, tuner)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False, False, 0, False, False, False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False, False, 0, False, False, False
                if event.key == pygame.K_RETURN:
                    return True, True, 0, False, False, False
                if event.key == pygame.K_UP:
                    return True, False, -1, False, False, False
                if event.key == pygame.K_DOWN:
                    return True, False, 1, False, False, False
                if event.key == pygame.K_SPACE:
                    return True, False, 0, True, False, False
                if self._back_btn is not None and event.key == pygame.K_BACKSPACE:
                    return True, False, 0, False, True, False
                if self._tuner_btn is not None and event.key == pygame.K_t:
                    return True, False, 0, False, False, True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._back_btn is not None and self._back_btn.collidepoint(event.pos):
                    return True, False, 0, False, True, False
                if self._tuner_btn is not None and self._tuner_btn.collidepoint(event.pos):
                    return True, False, 0, False, False, True
            if self._knob is not None:
                self._knob.handle_event(event)
        return True, False, 0, False, False, False
