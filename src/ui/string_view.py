import pygame
from .shared import W, H, BG, DIM, YELLOW, Fonts, draw_back_button, poll_menu


class StringView:
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock, fonts: Fonts):
        self.screen = screen
        self.clock = clock
        self.fonts = fonts
        self._back_btn: pygame.Rect | None = None

    def draw(self, options: list[str], selected: int):
        self.screen.fill(BG)

        title = self.fonts.title.render('MemBoard', True, YELLOW)
        self.screen.blit(title, title.get_rect(center=(W // 2, 70)))

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

        self._back_btn = draw_back_button(self.screen, self.fonts)
        hint = self.fonts.hint.render('↑ ↓  navigate     Enter  confirm', True, DIM)
        self.screen.blit(hint, hint.get_rect(center=(W // 2 + 60, H - 30)))

        pygame.display.flip()
        self.clock.tick(60)

    def poll(self) -> tuple[bool, bool, int, bool]:
        return poll_menu(self._back_btn)
