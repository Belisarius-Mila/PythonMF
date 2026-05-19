import queue
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import pygame


ROOT_DIR = Path(__file__).resolve().parent
BACKGROUND_PATH = ROOT_DIR / "NumCol1.JPG"

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60

BG_TOP = (230, 242, 247)
BG_BOTTOM = (245, 250, 252)
TEXT = (31, 44, 58)
TEXT_SOFT = (82, 97, 112)
PANEL = (255, 255, 255)
PANEL_SOFT = (248, 250, 253)
LINE = (126, 154, 182)
TAB_ACTIVE = (231, 240, 252)

IMAGE_WIDTH = 1024
IMAGE_HEIGHT = 559

NUMBER_WORDS = {
    1: "One",
    2: "Two",
    3: "Three",
    4: "Four",
    5: "Five",
}


@dataclass
class Hotspot:
    id: str
    word: str
    image_rect: pygame.Rect
    glow_color: tuple[int, int, int]
    label_center: tuple[int, int] | None = None
    group: str = ""


class SpeechManager:
    def __init__(self):
        self.items: queue.Queue[str | None] = queue.Queue()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def say_en(self, text: str):
        self.items.put(text)

    def close(self):
        self.items.put(None)

    def _worker(self):
        while True:
            item = self.items.get()
            if item is None:
                self.items.task_done()
                return
            try:
                subprocess.run(
                    ["say", "-v", "Samantha", item],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
            except Exception:
                pass
            finally:
                self.items.task_done()


class MMTXApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("MMTX")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        self.font_title = pygame.font.SysFont("arial", 34, bold=True)
        self.font_h1 = pygame.font.SysFont("arial", 26, bold=True)
        self.font_h2 = pygame.font.SysFont("arial", 22, bold=True)
        self.font_m = pygame.font.SysFont("arial", 18, bold=True)
        self.font_s = pygame.font.SysFont("arial", 16)
        self.font_num = pygame.font.SysFont("arial", 28, bold=True)

        self.background = self._load_background()
        self.speech = SpeechManager()

        self.mode = "colors"
        self.color_hotspots = [
            Hotspot("red", "Red", pygame.Rect(24, 120, 300, 290), (255, 89, 89)),
            Hotspot("blue", "Blue", pygame.Rect(220, 188, 182, 260), (86, 128, 255)),
            Hotspot("green", "Green", pygame.Rect(574, 300, 228, 210), (82, 214, 104)),
            Hotspot("orange", "Orange", pygame.Rect(742, 165, 246, 246), (255, 167, 67)),
        ]
        self.number_hotspots = [
            Hotspot("red_1", "", pygame.Rect(66, 164, 208, 112), (255, 89, 89), (160, 232), "red"),
            Hotspot("red_2", "", pygame.Rect(48, 344, 94, 84), (255, 89, 89), (74, 386), "red"),
            Hotspot("blue_1", "", pygame.Rect(270, 242, 92, 108), (86, 128, 255), (314, 286), "blue"),
            Hotspot("blue_2", "", pygame.Rect(304, 342, 64, 86), (86, 128, 255), (336, 405), "blue"),
            Hotspot("blue_3", "", pygame.Rect(240, 398, 52, 70), (86, 128, 255), (252, 426), "blue"),
            Hotspot("green_1", "", pygame.Rect(632, 364, 96, 86), (82, 214, 104), (672, 418), "green"),
            Hotspot("green_2", "", pygame.Rect(590, 438, 72, 78), (82, 214, 104), (613, 473), "green"),
            Hotspot("green_3", "", pygame.Rect(688, 438, 72, 76), (82, 214, 104), (715, 476), "green"),
            Hotspot("green_4", "", pygame.Rect(756, 476, 72, 66), (82, 214, 104), (782, 505), "green"),
            Hotspot("orange_1", "", pygame.Rect(768, 214, 110, 46), (255, 167, 67), (814, 236), "orange"),
            Hotspot("orange_2", "", pygame.Rect(882, 238, 74, 36), (255, 167, 67), (922, 254), "orange"),
            Hotspot("orange_3", "", pygame.Rect(770, 278, 112, 44), (255, 167, 67), (820, 298), "orange"),
            Hotspot("orange_4", "", pygame.Rect(894, 304, 92, 40), (255, 167, 67), (926, 326), "orange"),
            Hotspot("orange_5", "", pygame.Rect(770, 368, 170, 68), (255, 167, 67), (858, 391), "orange"),
        ]

        self.active_hotspot_id = ""
        self.active_word = ""
        self.active_until = 0.0
        self.hover_hotspot_id = ""
        self.revealed_numbers: dict[str, int] = {}
        self.group_counts = {"red": 0, "blue": 0, "green": 0, "orange": 0}

    def _load_background(self):
        if not BACKGROUND_PATH.exists():
            return None
        try:
            return pygame.image.load(str(BACKGROUND_PATH)).convert()
        except Exception:
            return None

    def image_area(self) -> pygame.Rect:
        scale = min(WINDOW_WIDTH / IMAGE_WIDTH, WINDOW_HEIGHT / IMAGE_HEIGHT)
        draw_w = int(IMAGE_WIDTH * scale)
        draw_h = int(IMAGE_HEIGHT * scale)
        x = (WINDOW_WIDTH - draw_w) // 2
        y = (WINDOW_HEIGHT - draw_h) // 2
        return pygame.Rect(x, y, draw_w, draw_h)

    def scale_rect(self, image_rect: pygame.Rect) -> pygame.Rect:
        area = self.image_area()
        sx = area.width / IMAGE_WIDTH
        sy = area.height / IMAGE_HEIGHT
        return pygame.Rect(
            int(area.x + image_rect.x * sx),
            int(area.y + image_rect.y * sy),
            max(1, int(image_rect.width * sx)),
            max(1, int(image_rect.height * sy)),
        )

    def active_hotspots(self) -> list[Hotspot]:
        return self.color_hotspots if self.mode == "colors" else self.number_hotspots

    def button_repeat(self) -> pygame.Rect:
        return pygame.Rect(26, 24, 96, 42)

    def button_exit(self) -> pygame.Rect:
        return pygame.Rect(136, 24, 96, 42)

    def button_colors(self) -> pygame.Rect:
        return pygame.Rect(910, 22, 150, 44)

    def button_numbers(self) -> pygame.Rect:
        return pygame.Rect(1074, 22, 180, 44)

    def draw_background(self):
        for y in range(WINDOW_HEIGHT):
            t = y / max(1, WINDOW_HEIGHT - 1)
            color = (
                int(BG_TOP[0] * (1 - t) + BG_BOTTOM[0] * t),
                int(BG_TOP[1] * (1 - t) + BG_BOTTOM[1] * t),
                int(BG_TOP[2] * (1 - t) + BG_BOTTOM[2] * t),
            )
            pygame.draw.line(self.screen, color, (0, y), (WINDOW_WIDTH, y))

        area = self.image_area()
        if self.background is not None:
            scaled = pygame.transform.smoothscale(self.background, area.size)
            self.screen.blit(scaled, area)
        else:
            pygame.draw.rect(self.screen, (210, 228, 210), area, border_radius=18)
            pygame.draw.rect(self.screen, LINE, area, 2, border_radius=18)
            txt = self.font_h1.render("Chybi NumCol1.JPG", True, TEXT)
            self.screen.blit(txt, txt.get_rect(center=area.center))

    def draw_top_ui(self):
        title_box = pygame.Rect(254, 20, 610, 50)
        pygame.draw.rect(self.screen, PANEL, title_box, border_radius=18)
        pygame.draw.rect(self.screen, LINE, title_box, 2, border_radius=18)
        title_text = "MMTX - Barevne houby" if self.mode == "colors" else "MMTX - Pocitani hub"
        title = self.font_title.render(title_text, True, TEXT)
        self.screen.blit(title, title.get_rect(center=title_box.center))

        self.draw_small_button(self.button_repeat(), "Znovu")
        self.draw_small_button(self.button_exit(), "Konec")
        self.draw_tab_button(self.button_colors(), "Barvy", self.mode == "colors")
        self.draw_tab_button(self.button_numbers(), "Cisla", self.mode == "numbers")

    def draw_small_button(self, rect: pygame.Rect, label: str):
        mouse_pos = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse_pos)
        fill = PANEL_SOFT if hover else PANEL
        pygame.draw.rect(self.screen, fill, rect, border_radius=16)
        pygame.draw.rect(self.screen, LINE, rect, 2, border_radius=16)
        txt = self.font_s.render(label, True, TEXT)
        self.screen.blit(txt, txt.get_rect(center=rect.center))

    def draw_tab_button(self, rect: pygame.Rect, label: str, is_active: bool):
        mouse_pos = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse_pos)
        fill = TAB_ACTIVE if is_active else (PANEL_SOFT if hover else PANEL)
        pygame.draw.rect(self.screen, fill, rect, border_radius=16)
        pygame.draw.rect(self.screen, LINE, rect, 2, border_radius=16)
        txt = self.font_m.render(label, True, TEXT)
        self.screen.blit(txt, txt.get_rect(center=rect.center))

    def draw_bottom_ui(self):
        box = pygame.Rect(28, WINDOW_HEIGHT - 110, 610, 72)
        pygame.draw.rect(self.screen, PANEL, box, border_radius=22)
        pygame.draw.rect(self.screen, LINE, box, 2, border_radius=22)
        if self.mode == "colors":
            line1 = "Klikni na houbu a ozve se barva."
            line2 = "Cil: Red, Blue, Green, Orange"
        else:
            line1 = "Klikni na jednotlive houby a uslysis cislo."
            line2 = "Kazda barva ma svou radu: one, two, three..."
        self.screen.blit(self.font_h2.render(line1, True, TEXT), (54, WINDOW_HEIGHT - 90))
        self.screen.blit(self.font_s.render(line2, True, TEXT_SOFT), (56, WINDOW_HEIGHT - 58))

        if self.active_word and time.time() < self.active_until:
            bubble = pygame.Rect(WINDOW_WIDTH - 290, WINDOW_HEIGHT - 122, 248, 84)
            pygame.draw.rect(self.screen, PANEL, bubble, border_radius=24)
            pygame.draw.rect(self.screen, LINE, bubble, 2, border_radius=24)
            txt = self.font_title.render(self.active_word, True, TEXT)
            self.screen.blit(txt, txt.get_rect(center=bubble.center))

    def draw_hotspot_feedback(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        for hotspot in self.active_hotspots():
            rect = self.scale_rect(hotspot.image_rect)
            is_hover = hotspot.id == self.hover_hotspot_id
            is_active = hotspot.id == self.active_hotspot_id and time.time() < self.active_until
            if not is_hover and not is_active:
                continue
            alpha = 120 if is_active else 70
            fill = (*hotspot.glow_color, alpha)
            pygame.draw.ellipse(overlay, fill, rect)
            pygame.draw.ellipse(overlay, (*hotspot.glow_color, 220), rect, 4)
        self.screen.blit(overlay, (0, 0))

    def draw_word_tag(self):
        if not self.active_word or time.time() >= self.active_until:
            return
        hotspot = next((item for item in self.active_hotspots() if item.id == self.active_hotspot_id), None)
        if hotspot is None:
            return
        rect = self.scale_rect(hotspot.image_rect)
        tag = pygame.Rect(rect.centerx - 92, rect.y - 52, 184, 44)
        tag.clamp_ip(pygame.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.draw.rect(self.screen, PANEL, tag, border_radius=18)
        pygame.draw.rect(self.screen, LINE, tag, 2, border_radius=18)
        txt = self.font_h2.render(self.active_word, True, TEXT)
        self.screen.blit(txt, txt.get_rect(center=tag.center))

    def draw_revealed_numbers(self):
        if self.mode != "numbers":
            return
        for hotspot in self.number_hotspots:
            number_value = self.revealed_numbers.get(hotspot.id)
            if number_value is None:
                continue
            if hotspot.label_center is None:
                rect = self.scale_rect(hotspot.image_rect)
                center_x, center_y = rect.center
            else:
                center_x, center_y = self.scale_point(hotspot.label_center)
            tag = pygame.Rect(center_x - 22, center_y - 20, 44, 40)
            pygame.draw.rect(self.screen, PANEL, tag, border_radius=16)
            pygame.draw.rect(self.screen, LINE, tag, 2, border_radius=16)
            txt = self.font_num.render(str(number_value), True, TEXT)
            self.screen.blit(txt, txt.get_rect(center=tag.center))

    def scale_point(self, image_point: tuple[int, int]) -> tuple[int, int]:
        area = self.image_area()
        sx = area.width / IMAGE_WIDTH
        sy = area.height / IMAGE_HEIGHT
        return (
            int(area.x + image_point[0] * sx),
            int(area.y + image_point[1] * sy),
        )

    def detect_hotspot(self, pos: tuple[int, int]) -> Hotspot | None:
        for hotspot in reversed(self.active_hotspots()):
            rect = self.scale_rect(hotspot.image_rect)
            if self.point_in_ellipse(pos, rect):
                return hotspot
        return None

    def point_in_ellipse(self, pos: tuple[int, int], rect: pygame.Rect) -> bool:
        if rect.width <= 0 or rect.height <= 0:
            return False
        cx = rect.centerx
        cy = rect.centery
        rx = rect.width / 2.0
        ry = rect.height / 2.0
        if rx <= 0 or ry <= 0:
            return False
        nx = (pos[0] - cx) / rx
        ny = (pos[1] - cy) / ry
        return (nx * nx + ny * ny) <= 1.0

    def speak_instruction(self):
        if self.mode == "colors":
            self.speech.say_en("Click a mushroom")
        else:
            self.speech.say_en("Click each mushroom and count")

    def activate_hotspot(self, hotspot: Hotspot):
        self.active_hotspot_id = hotspot.id
        self.active_until = time.time() + 1.5
        if self.mode == "numbers":
            number_value = self.revealed_numbers.get(hotspot.id)
            if number_value is None:
                next_number = self.group_counts[hotspot.group] + 1
                self.group_counts[hotspot.group] = next_number
                self.revealed_numbers[hotspot.id] = next_number
                number_value = next_number
            self.active_word = NUMBER_WORDS.get(number_value, str(number_value))
        else:
            self.active_word = hotspot.word
        self.speech.say_en(self.active_word)

    def switch_mode(self, mode: str):
        if self.mode == mode:
            return
        self.mode = mode
        self.active_hotspot_id = ""
        self.active_word = ""
        self.active_until = 0.0
        self.hover_hotspot_id = ""
        if mode == "numbers":
            self.revealed_numbers = {}
            self.group_counts = {"red": 0, "blue": 0, "green": 0, "orange": 0}
        self.speak_instruction()

    def handle_click(self, pos: tuple[int, int]) -> bool:
        if self.button_repeat().collidepoint(pos):
            self.speak_instruction()
            return True
        if self.button_exit().collidepoint(pos):
            return False
        if self.button_colors().collidepoint(pos):
            self.switch_mode("colors")
            return True
        if self.button_numbers().collidepoint(pos):
            self.switch_mode("numbers")
            return True
        hotspot = self.detect_hotspot(pos)
        if hotspot is not None:
            self.activate_hotspot(hotspot)
        return True

    def update_hover(self):
        hotspot = self.detect_hotspot(pygame.mouse.get_pos())
        self.hover_hotspot_id = hotspot.id if hotspot else ""

    def draw(self):
        self.draw_background()
        self.draw_hotspot_feedback()
        self.draw_revealed_numbers()
        self.draw_word_tag()
        self.draw_top_ui()
        self.draw_bottom_ui()
        pygame.display.flip()

    def run(self):
        running = True
        self.speak_instruction()
        while running:
            self.update_hover()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    running = self.handle_click(event.pos)
            self.draw()
            self.clock.tick(FPS)
        self.shutdown()

    def shutdown(self):
        self.speech.close()
        pygame.quit()


if __name__ == "__main__":
    MMTXApp().run()
