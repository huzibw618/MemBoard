import pygame
from .shared import W, H, BG, DIM, GREEN, RED, YELLOW, Fonts, GainKnob, draw_back_button, draw_input_bar
from quiz import QuizState, OPEN_NOTES


class QuizView:
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock, fonts: Fonts, knob: GainKnob):
        self.screen = screen
        self.clock = clock
        self.fonts = fonts
        self._knob = knob
        self._back_btn: pygame.Rect | None = None

    def draw(self, quiz: QuizState, now: float, rms: float = 0.0):
        self.screen.fill(BG)
        self._draw_stats(quiz)
        draw_input_bar(self.screen, self.fonts, rms)
        self._knob.draw(self.screen, self.fonts)

        if quiz.state == 'challenge':
            self._draw_challenge(quiz, now)
        else:
            self._draw_result(quiz)

        self._back_btn = draw_back_button(self.screen, self.fonts)
        hint = self.fonts.hint.render('Esc  back to menu', True, DIM)
        self.screen.blit(hint, hint.get_rect(center=(W // 2, H - 25)))

        pygame.display.flip()
        self.clock.tick(60)

    def poll(self) -> tuple[bool, bool]:
        """Returns (running, back). running=False quits the app; back=True returns to the previous menu."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False, False
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                return True, True
            if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                    and self._back_btn and self._back_btn.collidepoint(event.pos)):
                return True, True
            self._knob.handle_event(event)
        return True, False

    def _draw_stats(self, quiz: QuizState):
        surf = self.fonts.stats.render(
            f'Score: {quiz.score} / {quiz.total}     Avg time: {quiz.avg_time():.1f}s',
            True, DIM,
        )
        self.screen.blit(surf, (20, 18))

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
