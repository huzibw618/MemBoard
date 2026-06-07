import pygame
from .shared import W, H, BG, DIM, WHITE, GREEN, YELLOW, Fonts, GainKnob, draw_back_button, draw_input_bar
from audio import PitchStabilizer


class TunerView:
    IN_TUNE_CENTS = 5.0

    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock, fonts: Fonts, knob: GainKnob):
        self.screen = screen
        self.clock = clock
        self.fonts = fonts
        self._back_btn: pygame.Rect | None = None
        self._knob = knob
        self._stab = PitchStabilizer()

    def update(self, freq: float | None):
        """Feed one detection (Hz) or None for silence. Called per audio block."""
        self._stab.update(freq)

    def draw(self, rms: float = 0.0):
        self.screen.fill(BG)
        title = self.fonts.title.render('Tuner', True, YELLOW)
        self.screen.blit(title, title.get_rect(center=(W // 2, 80)))
        draw_input_bar(self.screen, self.fonts, rms)
        self._knob.draw(self.screen, self.fonts)

        reading = self._stab.reading
        if reading is not None:
            note, octave, cents = reading
            in_tune = abs(cents) <= self.IN_TUNE_CENTS
            color = GREEN if in_tune else WHITE

            note_surf = self.fonts.note.render(note, True, color)
            self.screen.blit(note_surf, note_surf.get_rect(center=(W // 2, H // 2 - 40)))

            info = self.fonts.stats.render(f'octave {octave}     {self._stab.freq:.1f} Hz', True, DIM)
            self.screen.blit(info, info.get_rect(center=(W // 2, H // 2 + 80)))

            self._draw_meter(cents, in_tune)
        else:
            dash = self.fonts.note.render('—', True, DIM)
            self.screen.blit(dash, dash.get_rect(center=(W // 2, H // 2 - 40)))
            msg = self.fonts.stats.render('play a note…', True, DIM)
            self.screen.blit(msg, msg.get_rect(center=(W // 2, H // 2 + 80)))

        self._back_btn = draw_back_button(self.screen, self.fonts)
        hint = self.fonts.hint.render('Esc  back', True, DIM)
        self.screen.blit(hint, hint.get_rect(center=(W // 2, H - 25)))

        pygame.display.flip()
        self.clock.tick(60)

    def _draw_meter(self, cents: float, in_tune: bool):
        bar_w = 500
        x = (W - bar_w) // 2
        y = H // 2 + 160
        cx = x + bar_w // 2

        pygame.draw.line(self.screen, DIM, (x, y), (x + bar_w, y), 2)
        pygame.draw.line(self.screen, GREEN if in_tune else DIM, (cx, y - 18), (cx, y + 18), 2)

        flat = self.fonts.hint.render('♭ flat', True, DIM)
        sharp = self.fonts.hint.render('sharp ♯', True, DIM)
        self.screen.blit(flat, flat.get_rect(midleft=(x, y - 32)))
        self.screen.blit(sharp, sharp.get_rect(midright=(x + bar_w, y - 32)))

        clamped = max(-50.0, min(50.0, cents))
        nx = cx + int(clamped / 50.0 * (bar_w // 2))
        color = GREEN if in_tune else YELLOW
        pygame.draw.circle(self.screen, color, (nx, y), 9)

        sign = '+' if cents >= 0 else ''
        label = self.fonts.stats.render(f'{sign}{cents:.0f}¢', True, color)
        self.screen.blit(label, label.get_rect(center=(cx, y + 46)))

    def poll(self) -> tuple[bool, bool]:
        """Returns (running, back). running=False quits the app; back=True returns to the strings menu."""
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
