import pygame
from .shared import W, H, BG, DIM, WHITE, YELLOW, Fonts, draw_action_button
from quiz import QuizState


class FinishedView:
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock, fonts: Fonts):
        self.screen = screen
        self.clock = clock
        self.fonts = fonts
        self._sel: int = 0  # 0 = Rerun, 1 = Back
        self._rerun_btn: pygame.Rect | None = None
        self._back_btn: pygame.Rect | None = None

    def draw(self, quiz: QuizState):
        self.screen.fill(BG)

        done = self.fonts.title.render('Session Complete', True, YELLOW)
        self.screen.blit(done, done.get_rect(center=(W // 2, 150)))

        score = self.fonts.result.render(f'{quiz.score} / {quiz.total} correct', True, WHITE)
        self.screen.blit(score, score.get_rect(center=(W // 2, 255)))

        avg = self.fonts.result.render(f'Avg time:  {quiz.avg_time():.2f}s', True, DIM)
        self.screen.blit(avg, avg.get_rect(center=(W // 2, 315)))

        mem = self.fonts.title.render(f'MemScore:  {quiz.memscore()}', True, YELLOW)
        self.screen.blit(mem, mem.get_rect(center=(W // 2, 395)))

        self._rerun_btn = draw_action_button(self.screen, self.fonts, '↺   Rerun', W // 2, 490, YELLOW, self._sel == 0)
        self._back_btn  = draw_action_button(self.screen, self.fonts, '←   Back',  W // 2, 560, DIM,    self._sel == 1)

        hint = self.fonts.hint.render('↑ ↓  select     Enter  confirm     Escape  quit', True, DIM)
        self.screen.blit(hint, hint.get_rect(center=(W // 2, H - 25)))

        pygame.display.flip()
        self.clock.tick(60)

    def poll(self) -> tuple[bool, bool, bool]:
        """Returns (running, rerun, back)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False, False, False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False, False, False
                if event.key in (pygame.K_UP, pygame.K_DOWN):
                    self._sel = 1 - self._sel
                if event.key == pygame.K_RETURN:
                    return (True, True, False) if self._sel == 0 else (True, False, True)
                if event.key == pygame.K_r:
                    return True, True, False
                if event.key == pygame.K_BACKSPACE:
                    return True, False, True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._rerun_btn and self._rerun_btn.collidepoint(event.pos):
                    return True, True, False
                if self._back_btn and self._back_btn.collidepoint(event.pos):
                    return True, False, True
        return True, False, False
