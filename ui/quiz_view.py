import math
import pygame
from .shared import W, H, BG, DIM, GREEN, RED, YELLOW, Fonts
from quiz import QuizState, OPEN_NOTES


class QuizView:
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock, fonts: Fonts):
        self.screen = screen
        self.clock = clock
        self.fonts = fonts
        self.gain: float = 1.0
        self._dragging: bool = False
        self._drag_y: int = 0
        self._drag_gain: float = 1.0

    def draw(self, quiz: QuizState, now: float, rms: float = 0.0):
        self.screen.fill(BG)
        self._draw_stats(quiz)
        self._draw_magnitude_bar(rms)
        self._draw_gain_knob()

        if quiz.state == 'challenge':
            self._draw_challenge(quiz, now)
        else:
            self._draw_result(quiz)

        pygame.display.flip()
        self.clock.tick(60)

    def poll(self) -> bool:
        knob_cx, knob_cy = W - 46, H - 62
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
            if event.type == pygame.MOUSEWHEEL:
                self.gain = round(max(1.0, min(8.0, self.gain + event.y * 0.5)), 1)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if math.hypot(mx - knob_cx, my - knob_cy) <= 28:
                    self._dragging = True
                    self._drag_y = my
                    self._drag_gain = self.gain
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self._dragging = False
            if event.type == pygame.MOUSEMOTION and self._dragging:
                delta = (self._drag_y - event.pos[1]) / 60.0 * 7.0
                self.gain = round(max(1.0, min(8.0, self._drag_gain + delta)), 1)
        return True

    def _draw_stats(self, quiz: QuizState):
        surf = self.fonts.stats.render(
            f'Score: {quiz.score} / {quiz.total}     Avg time: {quiz.avg_time():.1f}s',
            True, DIM,
        )
        self.screen.blit(surf, (20, 18))

    def _draw_gain_knob(self):
        cx, cy = W - 46, H - 62
        r = 24
        t = (self.gain - 1.0) / 7.0
        angle = math.radians(225 - t * 270)
        rect = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
        pygame.draw.arc(self.screen, (50, 50, 65), rect, math.radians(-45), math.radians(225), 3)
        if t > 0:
            pygame.draw.arc(self.screen, YELLOW, rect, angle, math.radians(225), 3)
        pygame.draw.circle(self.screen, (45, 45, 60), (cx, cy), r - 5)
        ix = cx + int((r - 8) * math.cos(angle))
        iy = cy - int((r - 8) * math.sin(angle))
        pygame.draw.line(self.screen, YELLOW, (cx, cy), (ix, iy), 2)
        label = self.fonts.hint.render(f'GAIN  ×{self.gain:.1f}', True, DIM)
        self.screen.blit(label, label.get_rect(center=(cx, cy + r + 10)))

    def _draw_magnitude_bar(self, rms: float):
        from audio import SILENCE_RMS
        bar_w, bar_h = 200, 8
        x, y = W - bar_w - 20, 22
        filled_w = int(bar_w * min(1.0, rms / 0.1))
        color = GREEN if rms > SILENCE_RMS else DIM
        pygame.draw.rect(self.screen, (40, 40, 55), (x, y, bar_w, bar_h), border_radius=4)
        if filled_w > 0:
            pygame.draw.rect(self.screen, color, (x, y, filled_w, bar_h), border_radius=4)
        label = self.fonts.hint.render('INPUT', True, DIM)
        self.screen.blit(label, (x - label.get_width() - 8, y - 2))

    def _draw_challenge(self, quiz: QuizState, now: float):
        open_surf = self.fonts.note.render(OPEN_NOTES[quiz.target_string], True, DIM)
        note_surf = self.fonts.note.render(quiz.target_note, True, YELLOW)

        gap = 36
        total_w = open_surf.get_width() + gap * 2 + 2 + note_surf.get_width()
        start_x = (W - total_w) // 2
        center_y = H // 2 - 30

        self.screen.blit(open_surf, open_surf.get_rect(midleft=(start_x, center_y)))

        line_x = start_x + open_surf.get_width() + gap
        line_top = center_y - open_surf.get_height() // 2
        line_bot = center_y + open_surf.get_height() // 2
        pygame.draw.line(self.screen, DIM, (line_x, line_top), (line_x, line_bot), 2)

        self.screen.blit(note_surf, note_surf.get_rect(midleft=(line_x + gap, center_y)))

        timer = self.fonts.timer.render(f'{quiz.elapsed(now):.1f}s', True, DIM)
        self.screen.blit(timer, timer.get_rect(center=(W // 2, line_bot + 50)))

    def _draw_result(self, quiz: QuizState):
        color = GREEN if quiz.result_correct else RED
        note_surf = self.fonts.note.render(quiz.target_note, True, color)
        self.screen.blit(note_surf, note_surf.get_rect(center=(W // 2, 280)))
        msg = (
            f'✓   {quiz.result_time:.2f}s' if quiz.result_correct
            else f'✗   played {quiz.result_played}{quiz.result_played_octave},  expected {quiz.target_note}{quiz.target_octave}'
        )
        result_surf = self.fonts.result.render(msg, True, color)
        self.screen.blit(result_surf, result_surf.get_rect(center=(W // 2, 435)))
