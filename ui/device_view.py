import pygame
from .shared import W, H, BG, DIM, WHITE, YELLOW, Fonts, poll_menu


class DeviceView:
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock, fonts: Fonts):
        self.screen = screen
        self.clock = clock
        self.fonts = fonts

    def draw(self, devices: list[dict], selected: int):
        self.screen.fill(BG)

        title = self.fonts.title.render('MemBoard', True, YELLOW)
        self.screen.blit(title, title.get_rect(center=(W // 2, 70)))

        label = self.fonts.stats.render('Select input device:', True, WHITE)
        self.screen.blit(label, label.get_rect(center=(W // 2, 140)))

        row_h, start_y = 36, 175
        for i, device in enumerate(devices):
            is_sel = i == selected
            prefix = '▶  ' if is_sel else '    '
            surf = self.fonts.menu.render(f'{prefix}{device["name"][:55]}', True, WHITE if is_sel else DIM)
            rect = surf.get_rect(center=(W // 2, start_y + i * row_h))
            if is_sel:
                pygame.draw.rect(self.screen, (35, 35, 55), rect.inflate(20, 8), border_radius=4)
            self.screen.blit(surf, rect)

        hint = self.fonts.hint.render('↑ ↓  navigate     Enter  start', True, DIM)
        self.screen.blit(hint, hint.get_rect(center=(W // 2, H - 30)))

        pygame.display.flip()
        self.clock.tick(60)

    def poll(self) -> tuple[bool, bool, int, bool]:
        return poll_menu()
