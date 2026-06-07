import pygame
from quiz import QuizState, STRING_NAMES, OPEN_NOTES

W, H = 900, 700

BG     = (15,  15,  25)
DIM    = (80,  80, 100)
WHITE  = (220, 220, 235)
GREEN  = (50,  220, 100)
RED    = (220,  70,  70)
YELLOW = (240, 200,  50)


class Renderer:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption('MemBoard')
        self.clock = pygame.time.Clock()
        self.font_title  = pygame.font.SysFont('dejavusans', 52, bold=True)
        self.font_stats  = pygame.font.SysFont('dejavusans', 24)
        self.font_string = pygame.font.SysFont('dejavusans', 36)
        self.font_note   = pygame.font.SysFont('dejavusans', 210, bold=True)
        self.font_timer  = pygame.font.SysFont('dejavusans', 38)
        self.font_result = pygame.font.SysFont('dejavusans', 42, bold=True)
        self.font_menu   = pygame.font.SysFont('dejavusans', 22)
        self.font_hint   = pygame.font.SysFont('dejavusans', 18)

    def draw_menu(self, devices: list[dict], selected: int):
        self.screen.fill(BG)

        title_surf = self.font_title.render('MemBoard', True, YELLOW)
        self.screen.blit(title_surf, title_surf.get_rect(center=(W // 2, 70)))

        label_surf = self.font_menu.render('Select input device:', True, DIM)
        self.screen.blit(label_surf, label_surf.get_rect(center=(W // 2, 140)))

        row_h = 36
        start_y = 175
        for i, device in enumerate(devices):
            is_selected = i == selected
            color = WHITE if is_selected else DIM
            prefix = '▶  ' if is_selected else '    '
            name = device['name'][:55]  # truncate long names
            surf = self.font_menu.render(f'{prefix}{name}', True, color)
            rect = surf.get_rect(center=(W // 2, start_y + i * row_h))
            if is_selected:
                pygame.draw.rect(self.screen, (35, 35, 55), rect.inflate(20, 8), border_radius=4)
            self.screen.blit(surf, rect)

        hint_surf = self.font_hint.render('↑ ↓  navigate     Enter  start', True, DIM)
        self.screen.blit(hint_surf, hint_surf.get_rect(center=(W // 2, H - 30)))

        pygame.display.flip()
        self.clock.tick(60)

    def draw_string_menu(self, options: list[str], selected: int):
        self.screen.fill(BG)

        title_surf = self.font_title.render('MemBoard', True, YELLOW)
        self.screen.blit(title_surf, title_surf.get_rect(center=(W // 2, 70)))

        label_surf = self.font_menu.render('Which strings do you want to practice?', True, DIM)
        self.screen.blit(label_surf, label_surf.get_rect(center=(W // 2, 150)))

        row_h = 52
        start_y = 210
        for i, label in enumerate(options):
            is_selected = i == selected
            color = YELLOW if is_selected else DIM
            surf = self.font_result.render(label, True, color)
            rect = surf.get_rect(center=(W // 2, start_y + i * row_h))
            if is_selected:
                pygame.draw.rect(self.screen, (35, 35, 55), rect.inflate(40, 10), border_radius=6)
            self.screen.blit(surf, rect)

        hint_surf = self.font_hint.render('↑ ↓  navigate     Enter  confirm', True, DIM)
        self.screen.blit(hint_surf, hint_surf.get_rect(center=(W // 2, H - 30)))

        pygame.display.flip()
        self.clock.tick(60)

    def draw_rounds_menu(self, options: list[int], selected: int, best_scores: dict):
        self.screen.fill(BG)

        title_surf = self.font_title.render('MemBoard', True, YELLOW)
        self.screen.blit(title_surf, title_surf.get_rect(center=(W // 2, 70)))

        label_surf = self.font_menu.render('How many rounds?', True, DIM)
        self.screen.blit(label_surf, label_surf.get_rect(center=(W // 2, 150)))

        row_h = 68
        start_y = 210
        for i, count in enumerate(options):
            is_selected = i == selected
            color = YELLOW if is_selected else DIM

            count_surf = self.font_result.render(str(count), True, color)
            count_rect = count_surf.get_rect(center=(W // 2, start_y + i * row_h))

            best = best_scores.get(count)
            best_str = f'PB  {best}' if best is not None else 'no data'
            best_surf = self.font_hint.render(best_str, True, GREEN if best is not None else DIM)
            best_rect = best_surf.get_rect(midleft=(count_rect.right + 24, count_rect.centery))

            if is_selected:
                highlight = count_rect.union(best_rect).inflate(28, 10)
                pygame.draw.rect(self.screen, (35, 35, 55), highlight, border_radius=6)

            self.screen.blit(count_surf, count_rect)
            self.screen.blit(best_surf, best_rect)

        hint_surf = self.font_hint.render('↑ ↓  navigate     Enter  confirm', True, DIM)
        self.screen.blit(hint_surf, hint_surf.get_rect(center=(W // 2, H - 30)))

        pygame.display.flip()
        self.clock.tick(60)

    def draw_finished(self, quiz: QuizState):
        self.screen.fill(BG)

        done_surf = self.font_title.render('Session Complete', True, YELLOW)
        self.screen.blit(done_surf, done_surf.get_rect(center=(W // 2, 180)))

        score_surf = self.font_result.render(
            f'{quiz.score} / {quiz.total} correct', True, WHITE
        )
        self.screen.blit(score_surf, score_surf.get_rect(center=(W // 2, 290)))

        avg_surf = self.font_result.render(
            f'Avg time:  {quiz.avg_time():.2f}s', True, DIM
        )
        self.screen.blit(avg_surf, avg_surf.get_rect(center=(W // 2, 350)))

        mem_surf = self.font_title.render(
            f'MemScore:  {quiz.memscore()}', True, YELLOW
        )
        self.screen.blit(mem_surf, mem_surf.get_rect(center=(W // 2, 430)))

        hint_surf = self.font_hint.render('Escape  quit', True, DIM)
        self.screen.blit(hint_surf, hint_surf.get_rect(center=(W // 2, H - 30)))

        pygame.display.flip()
        self.clock.tick(60)

    def poll_menu_event(self, num_devices: int) -> tuple[bool, bool, int]:
        """Returns (running, confirmed, new_selected_index)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False, False, 0
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False, False, 0
                if event.key == pygame.K_RETURN:
                    return True, True, 0
                if event.key == pygame.K_UP:
                    return True, False, -1
                if event.key == pygame.K_DOWN:
                    return True, False, 1
        return True, False, 0

    def poll_events(self) -> bool:
        """Returns False when the user quits."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
        return True

    def draw(self, quiz: QuizState, now: float):
        self.screen.fill(BG)
        self._draw_stats(quiz)

        if quiz.state == 'challenge':
            self._draw_challenge(quiz, now)
        else:
            self._draw_result(quiz)

        pygame.display.flip()
        self.clock.tick(60)

    def quit(self):
        pygame.quit()

    def _draw_stats(self, quiz: QuizState):
        surf = self.font_stats.render(
            f'Score: {quiz.score} / {quiz.total}     Avg time: {quiz.avg_time():.1f}s',
            True, DIM,
        )
        self.screen.blit(surf, (20, 18))

    def _draw_challenge(self, quiz: QuizState, now: float):
        open_surf = self.font_note.render(OPEN_NOTES[quiz.target_string], True, DIM)
        note_surf = self.font_note.render(quiz.target_note, True, YELLOW)

        gap = 36
        total_w = open_surf.get_width() + gap * 2 + 2 + note_surf.get_width()
        start_x = (W - total_w) // 2
        center_y = H // 2 - 30

        open_rect = open_surf.get_rect(midleft=(start_x, center_y))
        self.screen.blit(open_surf, open_rect)

        line_x = start_x + open_surf.get_width() + gap
        line_top = center_y - open_surf.get_height() // 2
        line_bot = center_y + open_surf.get_height() // 2
        pygame.draw.line(self.screen, DIM, (line_x, line_top), (line_x, line_bot), 2)

        note_rect = note_surf.get_rect(midleft=(line_x + gap, center_y))
        self.screen.blit(note_surf, note_rect)

        timer_surf = self.font_timer.render(f'{quiz.elapsed(now):.1f}s', True, DIM)
        self.screen.blit(timer_surf, timer_surf.get_rect(center=(W // 2, line_bot + 50)))

    def _draw_result(self, quiz: QuizState):
        color = GREEN if quiz.result_correct else RED

        note_surf = self.font_note.render(quiz.target_note, True, color)
        self.screen.blit(note_surf, note_surf.get_rect(center=(W // 2, 280)))

        msg = (
            f'✓   {quiz.result_time:.2f}s'
            if quiz.result_correct
            else f'✗   played {quiz.result_played}{quiz.result_played_octave},  expected {quiz.target_note}{quiz.target_octave}'
        )
        result_surf = self.font_result.render(msg, True, color)
        self.screen.blit(result_surf, result_surf.get_rect(center=(W // 2, 435)))
