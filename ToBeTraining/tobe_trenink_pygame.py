import csv
import random
import sys
from pathlib import Path

import pygame

CSV_BASENAME = "tobevety.csv"
COLUMN_LESSON = "Lekce"
COLUMN_QUESTION = "Otázka"
COLUMN_POSITIVE = "Kladná odpověď"
COLUMN_NEGATIVE = "Záporná odpověď"

LESSONS = (
    ("to be", "be"),
    ("to have", "have"),
    ("to go", "go"),
)

BG = (246, 239, 229)
PANEL = (255, 250, 244)
HEADER = (31, 60, 74)
ACCENT = (204, 90, 46)
TEAL = (44, 122, 123)
GOLD = (217, 164, 65)
TEXT = (31, 41, 51)
MUTED = (82, 96, 109)
GREEN_BG = (223, 243, 228)
GREEN_FG = (33, 98, 58)
RED_BG = (253, 232, 232)
RED_FG = (138, 28, 28)
SCENE_BG = (255, 247, 236)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)

WIDTH = 1400
HEIGHT = 860
FPS = 60


class Button:
    def __init__(self, rect, text, callback, bg, fg, border, active_bg=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.bg = bg
        self.fg = fg
        self.border = border
        self.active_bg = active_bg or bg
        self.is_active = False

    def draw(self, surface, font):
        bg = self.active_bg if self.is_active else self.bg
        pygame.draw.rect(surface, bg, self.rect, border_radius=16)
        pygame.draw.rect(surface, self.border, self.rect, 2, border_radius=16)
        label = font.render(self.text, True, self.fg)
        surface.blit(label, label.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()
                return True
        return False


class TrainerApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("ToBeTraining pygame prototype")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.font_title = pygame.font.SysFont("arial", 36, bold=True)
        self.font_subtitle = pygame.font.SysFont("arial", 20, bold=True)
        self.font_question = pygame.font.SysFont("arial", 42, bold=True)
        self.font_answer = pygame.font.SysFont("arial", 32)
        self.font_button = pygame.font.SysFont("arial", 22, bold=True)
        self.font_small = pygame.font.SysFont("arial", 18, bold=True)

        self.csv_path = self.find_csv_path()
        self.all_rows = self.load_csv(self.csv_path)
        self.current_lesson = "be"
        self.lesson_rows = []
        self.indices = []
        self.current_pos = -1
        self.current_row = None
        self.show_positive = False
        self.show_negative = False

        self.lesson_buttons = []
        self.action_buttons = []
        self.build_buttons()
        self.set_lesson(self.current_lesson)

    def find_csv_path(self):
        path = Path(__file__).resolve().parent / CSV_BASENAME
        if not path.exists():
            raise FileNotFoundError(f"Missing CSV: {path}")
        return path

    def load_csv(self, path):
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter=";"))
        return [row for row in rows if row.get(COLUMN_LESSON) and row.get(COLUMN_QUESTION)]

    def build_buttons(self):
        x = WIDTH - 360
        y = 20
        for idx, (label, key) in enumerate(LESSONS):
            rect = (x + idx * 112, y, 104, 44)
            self.lesson_buttons.append(
                Button(rect, label, lambda lesson=key: self.set_lesson(lesson), PANEL, HEADER, GOLD, ACCENT)
            )

        base_y = HEIGHT - 92
        specs = [
            ("New", self.show_new_sentence, ACCENT, WHITE),
            ("Begin", self.begin_from_start, GOLD, TEXT),
            ("Yes", self.reveal_positive, (119, 178, 85), WHITE),
            ("No", self.reveal_negative, (199, 81, 70), WHITE),
        ]
        x = 220
        for label, callback, bg, fg in specs:
            self.action_buttons.append(Button((x, base_y, 180, 54), label, callback, bg, fg, HEADER))
            x += 210

    def set_lesson(self, lesson):
        self.current_lesson = lesson
        self.lesson_rows = [row for row in self.all_rows if row[COLUMN_LESSON] == lesson]
        self.indices = list(range(len(self.lesson_rows)))
        random.shuffle(self.indices)
        self.current_pos = -1
        self.update_button_states()
        self.show_new_sentence()

    def update_button_states(self):
        for button, (_, lesson) in zip(self.lesson_buttons, LESSONS):
            button.is_active = lesson == self.current_lesson

    def get_current_row(self):
        if self.current_pos < 0 or self.current_pos >= len(self.indices):
            return None
        return self.lesson_rows[self.indices[self.current_pos]]

    def begin_from_start(self):
        if not self.lesson_rows:
            return
        self.current_pos = 0
        self.current_row = self.get_current_row()
        self.show_positive = False
        self.show_negative = False

    def show_new_sentence(self):
        if not self.lesson_rows:
            return
        self.current_pos += 1
        if self.current_pos >= len(self.indices):
            random.shuffle(self.indices)
            self.current_pos = 0
        self.current_row = self.get_current_row()
        self.show_positive = False
        self.show_negative = False

    def reveal_positive(self):
        if self.current_row:
            self.show_positive = True

    def reveal_negative(self):
        if self.current_row:
            self.show_negative = True

    def wrap_text(self, text, font, max_width):
        words = text.split()
        lines = []
        current = []
        for word in words:
            test = " ".join(current + [word])
            if font.size(test)[0] <= max_width or not current:
                current.append(word)
            else:
                lines.append(" ".join(current))
                current = [word]
        if current:
            lines.append(" ".join(current))
        return lines

    def draw_multiline(self, surface, text, font, color, rect, align="center"):
        lines = self.wrap_text(text, font, rect.width - 20)
        total_h = len(lines) * font.get_linesize()
        y = rect.y + (rect.height - total_h) // 2
        for line in lines:
            rendered = font.render(line, True, color)
            line_rect = rendered.get_rect()
            if align == "center":
                line_rect.centerx = rect.centerx
            else:
                line_rect.x = rect.x + 12
            line_rect.y = y
            surface.blit(rendered, line_rect)
            y += font.get_linesize()

    def draw_scene(self, surface, row):
        scene_rect = pygame.Rect(70, 430, WIDTH - 140, 250)
        pygame.draw.rect(surface, PANEL, scene_rect, border_radius=26)
        pygame.draw.rect(surface, (212, 195, 163), scene_rect, 2, border_radius=26)
        label = self.font_small.render("SCENE", True, MUTED)
        surface.blit(label, (scene_rect.x + 18, scene_rect.y + 14))

        canvas = scene_rect.inflate(-30, -50)
        canvas.y += 24
        pygame.draw.rect(surface, SCENE_BG, canvas, border_radius=18)
        pygame.draw.rect(surface, (212, 195, 163), canvas, 1, border_radius=18)

        if not row:
            return

        text = row[COLUMN_QUESTION].lower()
        center_y = canvas.centery
        if "school" in text:
            pygame.draw.rect(surface, (242, 242, 242), (canvas.x + 80, center_y - 40, 160, 110), border_radius=8)
            pygame.draw.polygon(surface, (211, 107, 107), [(canvas.x + 70, center_y - 40), (canvas.x + 160, center_y - 110), (canvas.x + 250, center_y - 40)])
        if "home" in text or "house" in text:
            pygame.draw.rect(surface, (247, 237, 226), (canvas.x + 280, center_y - 30, 150, 100), border_radius=8)
            pygame.draw.polygon(surface, (201, 124, 93), [(canvas.x + 270, center_y - 30), (canvas.x + 355, center_y - 90), (canvas.x + 440, center_y - 30)])
        if "dog" in text:
            pygame.draw.ellipse(surface, (193, 154, 107), (canvas.x + 520, center_y + 10, 110, 40))
            pygame.draw.circle(surface, (193, 154, 107), (canvas.x + 625, center_y + 20), 18)
        if "cat" in text:
            pygame.draw.ellipse(surface, (180, 180, 180), (canvas.x + 660, center_y + 8, 90, 36))
            pygame.draw.polygon(surface, (180, 180, 180), [(canvas.x + 680, center_y + 8), (canvas.x + 690, center_y - 12), (canvas.x + 700, center_y + 8)])
        if "car" in text or "bike" in text:
            pygame.draw.rect(surface, (69, 123, 157), (canvas.x + 820, center_y + 5, 150, 44), border_radius=12)
            pygame.draw.circle(surface, BLACK, (canvas.x + 850, center_y + 52), 16)
            pygame.draw.circle(surface, BLACK, (canvas.x + 930, center_y + 52), 16)
        if "prague" in text or "city" in text or "work" in text:
            for i, h in enumerate((110, 140, 95, 125)):
                pygame.draw.rect(surface, (217, 217, 217), (canvas.right - 260 + i * 45, center_y - h // 2, 34, h), border_radius=4)

        badges = []
        for keyword in ("lesson", "garden", "book", "teacher", "fast", "today", "now"):
            if keyword in text:
                badges.append(keyword.upper())
        bx = canvas.x + 20
        by = canvas.bottom - 34
        for badge in badges:
            label = self.font_small.render(badge, True, TEXT)
            rect = label.get_rect()
            rect.topleft = (bx + 12, by + 8)
            box = pygame.Rect(bx, by, rect.width + 24, 34)
            pygame.draw.rect(surface, (255, 239, 176), box, border_radius=16)
            pygame.draw.rect(surface, GOLD, box, 1, border_radius=16)
            surface.blit(label, rect)
            bx += box.width + 10

    def draw(self):
        self.screen.fill(BG)
        pygame.draw.rect(self.screen, HEADER, (0, 0, WIDTH, 86))
        self.screen.blit(self.font_title.render("English Trainer", True, WHITE), (28, 20))
        self.screen.blit(self.font_subtitle.render("pygame prototype", True, (216, 231, 234)), (32, 56))

        for button in self.lesson_buttons:
            button.draw(self.screen, self.font_button)

        question_rect = pygame.Rect(70, 110, WIDTH - 140, 130)
        pygame.draw.rect(self.screen, PANEL, question_rect, border_radius=28)
        pygame.draw.rect(self.screen, GOLD, question_rect, 3, border_radius=28)
        self.screen.blit(self.font_small.render("QUESTION", True, ACCENT), (question_rect.x + 20, question_rect.y + 14))
        question = self.current_row[COLUMN_QUESTION] if self.current_row else ""
        self.draw_multiline(self.screen, question, self.font_question, TEXT, question_rect.inflate(-40, -30))

        yes_rect = pygame.Rect(70, 270, WIDTH - 140, 64)
        no_rect = pygame.Rect(70, 348, WIDTH - 140, 64)
        pygame.draw.rect(self.screen, GREEN_BG, yes_rect, border_radius=20)
        pygame.draw.rect(self.screen, (123, 196, 127), yes_rect, 2, border_radius=20)
        pygame.draw.rect(self.screen, RED_BG, no_rect, border_radius=20)
        pygame.draw.rect(self.screen, (242, 159, 159), no_rect, 2, border_radius=20)
        self.screen.blit(self.font_small.render("YES", True, GREEN_FG), (yes_rect.x + 18, yes_rect.y + 8))
        self.screen.blit(self.font_small.render("NO", True, RED_FG), (no_rect.x + 18, no_rect.y + 8))
        if self.show_positive and self.current_row:
            self.draw_multiline(self.screen, self.current_row[COLUMN_POSITIVE], self.font_answer, GREEN_FG, yes_rect.inflate(-30, -10), align="left")
        if self.show_negative and self.current_row:
            self.draw_multiline(self.screen, self.current_row[COLUMN_NEGATIVE], self.font_answer, RED_FG, no_rect.inflate(-30, -10), align="left")

        self.draw_scene(self.screen, self.current_row)

        lesson_name = next(label for label, key in LESSONS if key == self.current_lesson)
        footer = self.font_small.render(f"Active lesson: {lesson_name}", True, MUTED)
        self.screen.blit(footer, (70, HEIGHT - 34))
        for button in self.action_buttons:
            button.draw(self.screen, self.font_button)

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key in (pygame.K_SPACE, pygame.K_n):
                        self.show_new_sentence()
                    elif event.key == pygame.K_y:
                        self.reveal_positive()
                    elif event.key == pygame.K_x:
                        self.reveal_negative()
                for button in self.lesson_buttons + self.action_buttons:
                    button.handle_event(event)
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()


def main():
    app = TrainerApp()
    app.run()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise
