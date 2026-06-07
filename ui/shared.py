import pygame

W, H = 900, 700

BG     = (15,  15,  25)
DIM    = (80,  80, 100)
WHITE  = (220, 220, 235)
GREEN  = (50,  220, 100)
RED    = (220,  70,  70)
YELLOW = (240, 200,  50)


class Fonts:
    def __init__(self):
        self.title  = pygame.font.SysFont('dejavusans', 52, bold=True)
        self.stats  = pygame.font.SysFont('dejavusans', 24)
        self.note   = pygame.font.SysFont('dejavusans', 210, bold=True)
        self.timer  = pygame.font.SysFont('dejavusans', 38)
        self.result = pygame.font.SysFont('dejavusans', 42, bold=True)
        self.menu   = pygame.font.SysFont('dejavusans', 22)
        self.hint   = pygame.font.SysFont('dejavusans', 18)


def draw_back_button(screen: pygame.Surface, fonts: Fonts) -> pygame.Rect:
    surf = fonts.menu.render('← Back', True, DIM)
    rect = surf.get_rect(midleft=(20, H - 30))
    bg = rect.inflate(24, 10)
    pygame.draw.rect(screen, (35, 35, 55), bg, border_radius=4)
    screen.blit(surf, rect)
    return bg


def draw_action_button(screen: pygame.Surface, fonts: Fonts,
                       text: str, cx: int, cy: int,
                       color: tuple, selected: bool = False) -> pygame.Rect:
    surf = fonts.result.render(text, True, color)
    rect = surf.get_rect(center=(cx, cy))
    bg = rect.inflate(48, 20)
    pygame.draw.rect(screen, (50, 50, 70) if selected else (30, 30, 45), bg, border_radius=8)
    pygame.draw.rect(screen, color, bg, 3 if selected else 2, border_radius=8)
    screen.blit(surf, rect)
    return bg


def poll_menu(back_btn: pygame.Rect | None = None) -> tuple[bool, bool, int, bool]:
    """Shared event loop for all menu screens. Returns (running, confirmed, delta, back)."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False, False, 0, False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False, False, 0, False
            if event.key == pygame.K_RETURN:
                return True, True, 0, False
            if event.key == pygame.K_UP:
                return True, False, -1, False
            if event.key == pygame.K_DOWN:
                return True, False, 1, False
            if back_btn is not None and event.key == pygame.K_BACKSPACE:
                return True, False, 0, True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if back_btn is not None and back_btn.collidepoint(event.pos):
                return True, False, 0, True
    return True, False, 0, False
