import pygame
from .shared import W, H, BG, DIM, GREEN, YELLOW, Fonts, draw_back_button, poll_menu


class RoundsView:
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock, fonts: Fonts):
        self.screen = screen
        self.clock = clock
        self.fonts = fonts
        self._back_btn: pygame.Rect | None = None

    def draw(self, options: list[int], selected: int, best_scores: dict):
        self.screen.fill(BG)

        title = self.fonts.title.render('MemBoard', True, YELLOW)
        self.screen.blit(title, title.get_rect(center=(W // 2, 70)))

        label = self.fonts.menu.render('How many rounds?', True, DIM)
        self.screen.blit(label, label.get_rect(center=(W // 2, 150)))

        row_h, start_y = 68, 210
        for i, count in enumerate(options):
            is_sel = i == selected
            color = YELLOW if is_sel else DIM

            count_surf = self.fonts.result.render(str(count), True, color)
            count_rect = count_surf.get_rect(center=(W // 2, start_y + i * row_h))

            best = best_scores.get(count)
            best_str = f'PB  {best}' if best is not None else 'no data'
            best_surf = self.fonts.hint.render(best_str, True, GREEN if best is not None else DIM)
            best_rect = best_surf.get_rect(midleft=(count_rect.right + 24, count_rect.centery))

            if is_sel:
                highlight = count_rect.union(best_rect).inflate(28, 10)
                pygame.draw.rect(self.screen, (35, 35, 55), highlight, border_radius=6)

            self.screen.blit(count_surf, count_rect)
            self.screen.blit(best_surf, best_rect)

        self._back_btn = draw_back_button(self.screen, self.fonts)
        hint = self.fonts.hint.render('↑ ↓:  navigate     Enter:  confirm', True, DIM)
        self.screen.blit(hint, hint.get_rect(center=(W // 2 + 60, H - 30)))

        pygame.display.flip()
        self.clock.tick(60)

    def poll(self) -> tuple[bool, bool, int, bool]:
        return poll_menu(self._back_btn)
