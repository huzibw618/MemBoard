import math
import os
import sys
import pygame
from audio import SILENCE_RMS

W, H = 900, 700


def _font_path(filename: str) -> str:
    """Locate a bundled font, both in dev and inside a PyInstaller bundle."""
    base = getattr(sys, '_MEIPASS', None)
    if base is None:  # running from source: src/ui/shared.py -> project root
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, 'assets', filename)

BG     = (15,  15,  25)
DIM    = (80,  80, 100)
WHITE  = (220, 220, 235)
GREEN  = (50,  220, 100)
RED    = (220,  70,  70)
YELLOW = (240, 200,  50)


class Fonts:
    def __init__(self):
        self.title  = self._load(52, bold=True)
        self.stats  = self._load(24)
        self.note   = self._load(210, bold=True)
        self.timer  = self._load(38)
        self.result = self._load(42, bold=True)
        self.menu   = self._load(22)
        self.hint   = self._load(18)

    @staticmethod
    def _load(size: int, bold: bool = False) -> pygame.font.Font:
        # Bundle DejaVu Sans so symbol glyphs (✓ ✗ ▶ ↺ ♪ …) render on every platform;
        # Windows lacks DejaVu, so SysFont would silently fall back and show tofu boxes.
        path = _font_path('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')
        if os.path.exists(path):
            return pygame.font.Font(path, size)
        return pygame.font.SysFont('dejavusans', size, bold=bold)


def draw_back_button(screen: pygame.Surface, fonts: Fonts) -> pygame.Rect:
    surf = fonts.menu.render('← Back', True, DIM)
    rect = surf.get_rect(midleft=(20, H - 30))
    bg = rect.inflate(24, 10)
    pygame.draw.rect(screen, (35, 35, 55), bg, border_radius=4)
    screen.blit(surf, rect)
    return bg


def draw_tuner_button(screen: pygame.Surface, fonts: Fonts) -> pygame.Rect:
    surf = fonts.menu.render('♪ Tuner', True, WHITE)
    rect = surf.get_rect(topleft=(32, 25))
    bg = rect.inflate(24, 12)
    pygame.draw.rect(screen, (35, 35, 55), bg, border_radius=4)
    pygame.draw.rect(screen, DIM, bg, 1, border_radius=4)
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


def draw_input_bar(screen: pygame.Surface, fonts: Fonts, rms: float):
    """Top-right INPUT level meter. Green once the signal clears the detection floor."""
    bar_w, bar_h = 200, 8
    x, y = W - bar_w - 20, 22
    filled_w = int(bar_w * min(1.0, rms / 0.1))
    color = GREEN if rms > SILENCE_RMS else DIM
    pygame.draw.rect(screen, (40, 40, 55), (x, y, bar_w, bar_h), border_radius=4)
    if filled_w > 0:
        pygame.draw.rect(screen, color, (x, y, filled_w, bar_h), border_radius=4)
    label = fonts.hint.render('INPUT', True, DIM)
    screen.blit(label, (x - label.get_width() - 8, y - 2))


class GainKnob:
    """Bottom-right gain dial (×1.0–×8.0). Owns its value and its drag/wheel interaction."""
    CX, CY, R = W - 46, H - 62, 24
    MIN, MAX = 1.0, 8.0

    def __init__(self):
        self.gain: float = 1.0
        self._dragging = False
        self._drag_y = 0
        self._drag_gain = 1.0

    def _clamp(self, value: float) -> float:
        return round(max(self.MIN, min(self.MAX, value)), 1)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Apply one pygame event to the knob. Returns True if it was a knob interaction."""
        if event.type == pygame.MOUSEWHEEL:
            self.gain = self._clamp(self.gain + event.y * 0.5)
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if math.hypot(event.pos[0] - self.CX, event.pos[1] - self.CY) <= self.R + 4:
                self._dragging = True
                self._drag_y = event.pos[1]
                self._drag_gain = self.gain
                return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = False
        if event.type == pygame.MOUSEMOTION and self._dragging:
            delta = (self._drag_y - event.pos[1]) / 60.0 * 7.0
            self.gain = self._clamp(self._drag_gain + delta)
            return True
        return False

    def draw(self, screen: pygame.Surface, fonts: Fonts):
        cx, cy, r = self.CX, self.CY, self.R
        t = (self.gain - self.MIN) / (self.MAX - self.MIN)
        angle = math.radians(225 - t * 270)
        rect = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
        pygame.draw.arc(screen, (50, 50, 65), rect, math.radians(-45), math.radians(225), 3)
        if t > 0:
            pygame.draw.arc(screen, YELLOW, rect, angle, math.radians(225), 3)
        pygame.draw.circle(screen, (45, 45, 60), (cx, cy), r - 5)
        ix = cx + int((r - 8) * math.cos(angle))
        iy = cy - int((r - 8) * math.sin(angle))
        pygame.draw.line(screen, YELLOW, (cx, cy), (ix, iy), 2)
        label = fonts.hint.render(f'GAIN  ×{self.gain:.1f}', True, DIM)
        screen.blit(label, label.get_rect(center=(cx, cy + r + 10)))


def poll_menu(back_btn: pygame.Rect | None = None,
              tuner_btn: pygame.Rect | None = None,
              knob: 'GainKnob | None' = None) -> tuple[bool, bool, int, bool, bool]:
    """Shared event loop for all menu screens. Returns (running, confirmed, delta, back, tuner).

    Any event not consumed for navigation is offered to ``knob`` (wheel/drag gain control).
    """
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False, False, 0, False, False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False, False, 0, False, False
            if event.key == pygame.K_RETURN:
                return True, True, 0, False, False
            if event.key == pygame.K_UP:
                return True, False, -1, False, False
            if event.key == pygame.K_DOWN:
                return True, False, 1, False, False
            if back_btn is not None and event.key == pygame.K_BACKSPACE:
                return True, False, 0, True, False
            if tuner_btn is not None and event.key == pygame.K_t:
                return True, False, 0, False, True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if back_btn is not None and back_btn.collidepoint(event.pos):
                return True, False, 0, True, False
            if tuner_btn is not None and tuner_btn.collidepoint(event.pos):
                return True, False, 0, False, True
        if knob is not None:
            knob.handle_event(event)
    return True, False, 0, False, False
