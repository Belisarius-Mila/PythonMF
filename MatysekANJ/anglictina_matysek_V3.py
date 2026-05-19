import json
import math
import queue
import random
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

import pygame


ROOT_DIR = Path(__file__).resolve().parent
OWL_PATH = ROOT_DIR / "oul.png"
PROGRESS_PATH = ROOT_DIR / "matysek_progress_v3.json"

WIDTH = 1280
HEIGHT = 720
FPS = 60

BG_TOP = (232, 245, 255)
BG_BOTTOM = (250, 252, 255)
CARD = (255, 255, 255)
CARD_ALT = (245, 249, 255)
TEXT = (33, 46, 63)
TEXT_SOFT = (92, 106, 122)
LINE = (128, 158, 196)
GREEN = (46, 160, 84)
RED = (196, 72, 72)
YELLOW = (255, 215, 90)
BLUE = (72, 126, 235)

PACK_META = {
    "colors": {"title": "Barvy", "place": "Duhova louka", "bg": (255, 239, 245)},
    "numbers": {"title": "Cisla", "place": "Jablecny sad", "bg": (255, 247, 214)},
    "animals": {"title": "Zvirata", "place": "Farma a les", "bg": (228, 247, 235)},
    "family": {"title": "Rodina", "place": "Domecek", "bg": (238, 241, 255)},
}

PACKS = {
    "colors": [
        {"id": "red", "en": "red", "cz": "cervenou", "kind": "color", "color": (242, 86, 86)},
        {"id": "blue", "en": "blue", "cz": "modrou", "kind": "color", "color": (72, 126, 235)},
        {"id": "yellow", "en": "yellow", "cz": "zlutou", "kind": "color", "color": (250, 209, 74)},
        {"id": "green", "en": "green", "cz": "zelenou", "kind": "color", "color": (62, 184, 108)},
    ],
    "numbers": [
        {"id": "one", "en": "one", "cz": "jednu", "kind": "count", "count": 1},
        {"id": "two", "en": "two", "cz": "dve", "kind": "count", "count": 2},
        {"id": "three", "en": "three", "cz": "tri", "kind": "count", "count": 3},
        {"id": "four", "en": "four", "cz": "ctyri", "kind": "count", "count": 4},
        {"id": "five", "en": "five", "cz": "pet", "kind": "count", "count": 5},
    ],
    "animals": [
        {"id": "dog", "en": "dog", "cz": "pejska", "kind": "animal", "animal": "dog"},
        {"id": "cat", "en": "cat", "cz": "kocku", "kind": "animal", "animal": "cat"},
        {"id": "duck", "en": "duck", "cz": "kachnu", "kind": "animal", "animal": "duck"},
        {"id": "fish", "en": "fish", "cz": "rybu", "kind": "animal", "animal": "fish"},
        {"id": "owl", "en": "owl", "cz": "sovu", "kind": "animal", "animal": "owl"},
    ],
    "family": [
        {"id": "mummy", "en": "mummy", "cz": "maminku", "kind": "family", "role": "mummy"},
        {"id": "daddy", "en": "daddy", "cz": "tatinka", "kind": "family", "role": "daddy"},
        {"id": "baby", "en": "baby", "cz": "miminko", "kind": "family", "role": "baby"},
        {"id": "brother", "en": "brother", "cz": "brasku", "kind": "family", "role": "brother"},
        {"id": "grandma", "en": "grandma", "cz": "babicku", "kind": "family", "role": "grandma"},
    ],
}

PRAISES_CZ = ["Vyborne!", "Parada!", "Skvele!"]
ENCOURAGE_CZ = ["Zkus to jeste jednou.", "Poslechni si to znovu.", "Nevadi, zkusime to jeste."]


def _find_edge_tts_bin() -> str | None:
    candidates = [
        shutil.which("edge-tts"),
        str(Path.home() / "Library/Python/3.11/bin/edge-tts"),
        str(Path.home() / "Library/Python/3.12/bin/edge-tts"),
        "/opt/homebrew/bin/edge-tts",
        "/usr/local/bin/edge-tts",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def _play_mp3(path: Path):
    afplay_bin = shutil.which("afplay")
    if not afplay_bin:
        return
    try:
        subprocess.run([afplay_bin, str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except Exception:
        pass


class SpeechManager:
    def __init__(self):
        self.edge_tts_bin = _find_edge_tts_bin()
        self.items: queue.Queue[tuple[str, str] | None] = queue.Queue()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def say_cz(self, text: str):
        self.items.put(("cz", text))

    def say_en(self, text: str):
        self.items.put(("en", text))

    def close(self):
        self.items.put(None)

    def _worker(self):
        while True:
            item = self.items.get()
            if item is None:
                self.items.task_done()
                return
            lang, text = item
            try:
                if lang == "cz":
                    self._speak_cz(text)
                else:
                    subprocess.run(
                        ["say", "-v", "Samantha", text],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False,
                    )
            except Exception:
                pass
            finally:
                self.items.task_done()

    def _speak_cz(self, text: str):
        if self.edge_tts_bin:
            out_path = Path(tempfile.gettempdir()) / f"matysek_v3_{uuid.uuid4().hex}.mp3"
            try:
                subprocess.run(
                    [
                        self.edge_tts_bin,
                        "--voice",
                        "cs-CZ-AntoninNeural",
                        "--rate=-8%",
                        "--text",
                        text,
                        "--write-media",
                        str(out_path),
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                )
                _play_mp3(out_path)
                return
            except Exception:
                pass
            finally:
                try:
                    out_path.unlink(missing_ok=True)
                except Exception:
                    pass
        for voice in ("Zuzana", "Alex"):
            try:
                result = subprocess.run(
                    ["say", "-v", voice, text],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
                if result.returncode == 0:
                    return
            except Exception:
                continue
        try:
            subprocess.run(["say", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        except Exception:
            pass


@dataclass
class Choice:
    id: str
    label: str
    kind: str
    color: tuple[int, int, int] | None = None
    count: int = 0
    animal: str = ""
    role: str = ""


@dataclass
class RoundData:
    pack: str
    prompt_cz: str
    prompt_en: str
    choices: list[Choice]
    correct_id: str


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    fill: tuple[int, int, int]
    action: str


class AnglictinaMatysekV3:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Anglictina Matysek V3")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.font_title = pygame.font.SysFont("arial", 42, bold=True)
        self.font_h1 = pygame.font.SysFont("arial", 32, bold=True)
        self.font_h2 = pygame.font.SysFont("arial", 24, bold=True)
        self.font_m = pygame.font.SysFont("arial", 20, bold=True)
        self.font_s = pygame.font.SysFont("arial", 16)

        self.owl_image = self._load_owl()
        self.speech = SpeechManager()

        self.scene = "home"
        self.current_pack = ""
        self.round_data: RoundData | None = None
        self.feedback = ""
        self.feedback_color = TEXT
        self.pending_action_at = 0.0
        self.pending_action = None
        self.input_locked = False

        self.progress = {
            "stars": 0,
            "pack_progress": {pack: 0 for pack in PACKS},
        }
        self._load_progress()

    def _load_owl(self):
        if not OWL_PATH.exists():
            return None
        try:
            return pygame.image.load(str(OWL_PATH)).convert_alpha()
        except Exception:
            return None

    def _load_progress(self):
        if not PROGRESS_PATH.exists():
            return
        try:
            data = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return
        self.progress["stars"] = int(data.get("stars", 0))
        pack_progress = data.get("pack_progress", {})
        for pack in PACKS:
            self.progress["pack_progress"][pack] = int(pack_progress.get(pack, 0))

    def _save_progress(self):
        try:
            PROGRESS_PATH.write_text(json.dumps(self.progress, indent=2), encoding="utf-8")
        except Exception:
            pass

    def queue_action(self, delay_sec: float, fn):
        self.pending_action_at = time.time() + delay_sec
        self.pending_action = fn

    def tick_pending(self):
        if self.pending_action and time.time() >= self.pending_action_at:
            fn = self.pending_action
            self.pending_action = None
            self.pending_action_at = 0.0
            fn()

    def start_pack(self, pack: str):
        self.scene = "lesson"
        self.current_pack = pack
        self.feedback = ""
        self.feedback_color = TEXT
        self.speech.say_cz(f"Jdeme na {PACK_META[pack]['place']}.")
        self.next_round()

    def next_round(self):
        self.round_data = self.build_round(self.current_pack)
        self.feedback = ""
        self.feedback_color = TEXT
        self.input_locked = False
        self.play_prompt()

    def play_prompt(self):
        if not self.round_data:
            return
        self.speech.say_cz(self.round_data.prompt_cz)
        self.speech.say_en(self.round_data.prompt_en)
        self.speech.say_en(self.round_data.prompt_en)

    def build_round(self, pack: str) -> RoundData:
        source = PACKS[pack]
        correct_item = random.choice(source)
        others = [item for item in source if item["id"] != correct_item["id"]]
        distractors = random.sample(others, 2)
        raw_choices = distractors + [correct_item]
        random.shuffle(raw_choices)
        choices = [
            Choice(
                id=item["id"],
                label=item["en"],
                kind=item["kind"],
                color=item.get("color"),
                count=item.get("count", 0),
                animal=item.get("animal", ""),
                role=item.get("role", ""),
            )
            for item in raw_choices
        ]
        prompt_cz = f"Najdi {correct_item['cz']}."
        prompt_en = correct_item["en"]
        if pack == "numbers":
            prompt_cz = f"Najdi {correct_item['cz']} jablka."
            prompt_en = f"{correct_item['en']} apples"
        return RoundData(
            pack=pack,
            prompt_cz=prompt_cz,
            prompt_en=prompt_en,
            choices=choices,
            correct_id=correct_item["id"],
        )

    def handle_choice(self, choice_id: str):
        if self.input_locked or not self.round_data:
            return
        self.input_locked = True
        if choice_id == self.round_data.correct_id:
            self.feedback = random.choice(PRAISES_CZ)
            self.feedback_color = GREEN
            self.progress["stars"] += 1
            self.progress["pack_progress"][self.current_pack] += 1
            self._save_progress()
            self.speech.say_cz(self.feedback)
            if self.progress["stars"] % 5 == 0:
                self.queue_action(1.0, self.open_reward)
            else:
                self.queue_action(1.0, self.next_round)
        else:
            self.feedback = random.choice(ENCOURAGE_CZ)
            self.feedback_color = RED
            self.speech.say_cz(self.feedback)
            self.queue_action(1.0, self._unlock_after_error)

    def _unlock_after_error(self):
        self.input_locked = False
        self.play_prompt()

    def open_reward(self):
        self.scene = "reward"
        self.feedback = ""
        self.feedback_color = TEXT
        self.input_locked = False
        self.speech.say_cz("Mas novou odmenu. Podivej se, jak se rozsvitil tvuj ostrov.")

    def draw(self):
        self.draw_background()
        if self.scene == "home":
            self.draw_home()
        elif self.scene == "lesson":
            self.draw_lesson()
        else:
            self.draw_reward()
        pygame.display.flip()

    def draw_background(self):
        for y in range(HEIGHT):
            t = y / max(1, HEIGHT - 1)
            color = (
                int(BG_TOP[0] * (1 - t) + BG_BOTTOM[0] * t),
                int(BG_TOP[1] * (1 - t) + BG_BOTTOM[1] * t),
                int(BG_TOP[2] * (1 - t) + BG_BOTTOM[2] * t),
            )
            pygame.draw.line(self.screen, color, (0, y), (WIDTH, y))
        pygame.draw.circle(self.screen, (255, 250, 214), (1120, 110), 64)
        pygame.draw.ellipse(self.screen, (255, 255, 255), (130, 55, 180, 70))
        pygame.draw.ellipse(self.screen, (255, 255, 255), (260, 70, 210, 80))
        pygame.draw.ellipse(self.screen, (255, 255, 255), (880, 80, 220, 85))

    def draw_home(self):
        self.screen.blit(self.font_title.render("Sovi ostrov", True, TEXT), (46, 34))
        self.screen.blit(self.font_h2.render("Klikni, kam pujdes.", True, TEXT_SOFT), (48, 82))

        self.draw_owl(130, 170, 260, 310)

        bubble = pygame.Rect(70, 500, 360, 110)
        pygame.draw.rect(self.screen, CARD, bubble, border_radius=28)
        pygame.draw.rect(self.screen, LINE, bubble, 2, border_radius=28)
        self.screen.blit(self.font_h2.render("Sova pomuze s anglictinou.", True, TEXT), (96, 530))
        self.screen.blit(self.font_s.render("Cteni neni potreba. Staci poslouchat a klikat.", True, TEXT_SOFT), (96, 567))

        for button in self.home_buttons():
            self.draw_button(button)
            self.draw_home_icon(button)

        self.draw_icon_button(pygame.Rect(1020, 30, 96, 48), "Sova", CARD_ALT)
        self.draw_icon_button(pygame.Rect(1132, 30, 112, 48), "Odmeny", CARD_ALT)

    def draw_lesson(self):
        if not self.round_data:
            return
        meta = PACK_META[self.current_pack]
        header = pygame.Rect(34, 26, 1212, 90)
        pygame.draw.rect(self.screen, meta["bg"], header, border_radius=26)
        pygame.draw.rect(self.screen, LINE, header, 2, border_radius=26)
        self.screen.blit(self.font_h1.render(meta["place"], True, TEXT), (58, 44))
        self.screen.blit(self.font_s.render("Matysek posloucha a vybira kliknutim.", True, TEXT_SOFT), (60, 80))

        self.draw_icon_button(pygame.Rect(1042, 47, 94, 40), "Znovu", CARD)
        self.draw_icon_button(pygame.Rect(1148, 47, 72, 40), "Domu", CARD)

        prompt_box = pygame.Rect(68, 150, 1144, 90)
        pygame.draw.rect(self.screen, CARD, prompt_box, border_radius=24)
        pygame.draw.rect(self.screen, LINE, prompt_box, 2, border_radius=24)
        self.screen.blit(self.font_h2.render("Sova rika:", True, TEXT_SOFT), (96, 172))
        self.screen.blit(self.font_h1.render(self.round_data.prompt_cz, True, TEXT), (96, 198))

        if self.feedback:
            color = self.feedback_color
            feedback_box = pygame.Rect(426, 258, 430, 52)
            pygame.draw.rect(self.screen, CARD, feedback_box, border_radius=20)
            pygame.draw.rect(self.screen, color, feedback_box, 2, border_radius=20)
            text = self.font_h2.render(self.feedback, True, color)
            self.screen.blit(text, text.get_rect(center=feedback_box.center))

        self.draw_owl(65, 280, 180, 220)
        for rect, choice in self.choice_buttons():
            self.draw_choice(rect, choice)

        stars = self.progress["stars"]
        self.screen.blit(self.font_h2.render(f"Hvezdicky: {stars}", True, TEXT), (54, 644))

    def draw_reward(self):
        title = self.font_title.render("Police odmen", True, TEXT)
        self.screen.blit(title, (44, 36))
        self.screen.blit(self.font_h2.render("Kazda spravna odpoved rozsviti kus ostrova.", True, TEXT_SOFT), (46, 82))

        board = pygame.Rect(60, 140, 1160, 510)
        pygame.draw.rect(self.screen, CARD, board, border_radius=30)
        pygame.draw.rect(self.screen, LINE, board, 2, border_radius=30)

        packs = list(PACKS.keys())
        for idx, pack in enumerate(packs):
            x = 104 + idx * 285
            self.draw_reward_card(pack, pygame.Rect(x, 200, 220, 330))

        total_stars = self.progress["stars"]
        self.screen.blit(self.font_h1.render(f"Celkem hvezdicek: {total_stars}", True, TEXT), (86, 590))
        self.screen.blit(self.font_s.render("Klikni kamkoli nebo na Domu.", True, TEXT_SOFT), (88, 626))
        self.draw_icon_button(pygame.Rect(1092, 42, 112, 44), "Domu", CARD_ALT)

    def home_buttons(self) -> list[Button]:
        return [
            Button(pygame.Rect(520, 140, 300, 170), "Duhova louka", (255, 235, 242), "pack:colors"),
            Button(pygame.Rect(860, 140, 300, 170), "Jablecny sad", (255, 247, 214), "pack:numbers"),
            Button(pygame.Rect(520, 350, 300, 170), "Farma a les", (228, 247, 235), "pack:animals"),
            Button(pygame.Rect(860, 350, 300, 170), "Domecek", (236, 239, 255), "pack:family"),
        ]

    def choice_buttons(self) -> list[tuple[pygame.Rect, Choice]]:
        if not self.round_data:
            return []
        out = []
        x0 = 270
        y = 360
        w = 280
        h = 250
        gap = 36
        for idx, choice in enumerate(self.round_data.choices):
            out.append((pygame.Rect(x0 + idx * (w + gap), y, w, h), choice))
        return out

    def draw_button(self, button: Button):
        mouse_pos = pygame.mouse.get_pos()
        hover = button.rect.collidepoint(mouse_pos)
        fill = tuple(min(255, c + 10) for c in button.fill) if hover else button.fill
        pygame.draw.rect(self.screen, fill, button.rect, border_radius=30)
        pygame.draw.rect(self.screen, LINE, button.rect, 2, border_radius=30)
        label = self.font_h2.render(button.label, True, TEXT)
        self.screen.blit(label, label.get_rect(center=(button.rect.centerx, button.rect.bottom - 24)))

    def draw_icon_button(self, rect: pygame.Rect, label: str, fill: tuple[int, int, int]):
        mouse_pos = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse_pos)
        draw_fill = tuple(min(255, c + 8) for c in fill) if hover else fill
        pygame.draw.rect(self.screen, draw_fill, rect, border_radius=18)
        pygame.draw.rect(self.screen, LINE, rect, 2, border_radius=18)
        text = self.font_s.render(label, True, TEXT)
        self.screen.blit(text, text.get_rect(center=rect.center))

    def draw_home_icon(self, button: Button):
        cx = button.rect.centerx
        cy = button.rect.y + 70
        if button.action.endswith("colors"):
            for i, color in enumerate([(255, 97, 97), (255, 198, 63), (78, 191, 117), (89, 136, 237)]):
                pygame.draw.arc(
                    self.screen,
                    color,
                    pygame.Rect(cx - 70 + i * 4, cy - 22 + i * 3, 140 - i * 8, 90 - i * 6),
                    math.pi,
                    math.tau,
                    8,
                )
        elif button.action.endswith("numbers"):
            pygame.draw.rect(self.screen, (143, 94, 55), (cx - 18, cy - 20, 36, 88), border_radius=10)
            pygame.draw.circle(self.screen, (101, 177, 88), (cx, cy - 38), 52)
            for dx, dy in [(-22, -48), (16, -54), (-10, -24), (24, -22)]:
                pygame.draw.circle(self.screen, (227, 48, 48), (cx + dx, cy + dy), 12)
        elif button.action.endswith("animals"):
            self.draw_animal_icon("dog", pygame.Rect(cx - 54, cy - 60, 108, 108))
        else:
            house = pygame.Rect(cx - 62, cy - 42, 124, 92)
            pygame.draw.rect(self.screen, (255, 236, 198), house, border_radius=14)
            pygame.draw.polygon(self.screen, (221, 111, 111), [(cx - 72, cy - 2), (cx, cy - 74), (cx + 72, cy - 2)])
            pygame.draw.rect(self.screen, (184, 122, 76), (cx - 15, cy + 6, 30, 44), border_radius=6)
            pygame.draw.rect(self.screen, (173, 214, 255), (cx - 48, cy - 12, 26, 22), border_radius=4)
            pygame.draw.rect(self.screen, (173, 214, 255), (cx + 22, cy - 12, 26, 22), border_radius=4)

    def draw_choice(self, rect: pygame.Rect, choice: Choice):
        mouse_pos = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse_pos)
        fill = (252, 253, 255) if hover else CARD
        pygame.draw.rect(self.screen, fill, rect, border_radius=26)
        pygame.draw.rect(self.screen, LINE, rect, 2, border_radius=26)

        art = pygame.Rect(rect.x + 22, rect.y + 18, rect.width - 44, rect.height - 70)
        if choice.kind == "color" and choice.color:
            pygame.draw.rect(self.screen, choice.color, art, border_radius=30)
            pygame.draw.circle(self.screen, (255, 255, 255), art.center, 28)
        elif choice.kind == "count":
            self.draw_count_icon(art, choice.count)
        elif choice.kind == "animal":
            self.draw_animal_icon(choice.animal, art)
        else:
            self.draw_family_icon(choice.role, art)

        label = self.font_s.render(choice.label, True, TEXT_SOFT)
        self.screen.blit(label, label.get_rect(center=(rect.centerx, rect.bottom - 24)))

    def draw_count_icon(self, rect: pygame.Rect, count: int):
        pygame.draw.rect(self.screen, (255, 251, 232), rect, border_radius=24)
        pygame.draw.rect(self.screen, (238, 212, 129), rect, 2, border_radius=24)
        cols = min(3, count)
        rows = int(math.ceil(count / cols))
        step_x = rect.width / (cols + 1)
        step_y = rect.height / (rows + 1)
        drawn = 0
        for row in range(rows):
            for col in range(cols):
                if drawn >= count:
                    return
                cx = int(rect.x + step_x * (col + 1))
                cy = int(rect.y + step_y * (row + 1))
                self.draw_apple(cx, cy, 20)
                drawn += 1

    def draw_apple(self, cx: int, cy: int, r: int):
        pygame.draw.circle(self.screen, (231, 70, 70), (cx, cy), r)
        pygame.draw.circle(self.screen, (198, 55, 55), (cx - 8, cy - 4), r - 6)
        pygame.draw.line(self.screen, (104, 71, 43), (cx, cy - r), (cx + 2, cy - r - 14), 4)
        pygame.draw.ellipse(self.screen, (68, 170, 92), (cx + 2, cy - r - 14, 18, 10))

    def draw_animal_icon(self, animal: str, rect: pygame.Rect):
        pygame.draw.rect(self.screen, (240, 248, 255), rect, border_radius=24)
        pygame.draw.rect(self.screen, (182, 203, 228), rect, 2, border_radius=24)
        cx, cy = rect.center
        if animal == "dog":
            pygame.draw.circle(self.screen, (191, 145, 100), (cx, cy), 52)
            pygame.draw.ellipse(self.screen, (144, 96, 61), (cx - 58, cy - 32, 30, 70))
            pygame.draw.ellipse(self.screen, (144, 96, 61), (cx + 28, cy - 32, 30, 70))
            pygame.draw.ellipse(self.screen, (235, 218, 196), (cx - 26, cy - 6, 52, 42))
            pygame.draw.circle(self.screen, (30, 30, 30), (cx - 18, cy - 10), 5)
            pygame.draw.circle(self.screen, (30, 30, 30), (cx + 18, cy - 10), 5)
            pygame.draw.circle(self.screen, (70, 45, 34), (cx, cy + 5), 7)
        elif animal == "cat":
            pygame.draw.circle(self.screen, (224, 173, 95), (cx, cy), 50)
            pygame.draw.polygon(self.screen, (224, 173, 95), [(cx - 42, cy - 22), (cx - 22, cy - 62), (cx - 8, cy - 18)])
            pygame.draw.polygon(self.screen, (224, 173, 95), [(cx + 42, cy - 22), (cx + 22, cy - 62), (cx + 8, cy - 18)])
            pygame.draw.circle(self.screen, (30, 30, 30), (cx - 16, cy - 8), 5)
            pygame.draw.circle(self.screen, (30, 30, 30), (cx + 16, cy - 8), 5)
            pygame.draw.circle(self.screen, (217, 113, 122), (cx, cy + 6), 6)
            pygame.draw.line(self.screen, (80, 80, 80), (cx - 12, cy + 10), (cx - 38, cy + 4), 2)
            pygame.draw.line(self.screen, (80, 80, 80), (cx + 12, cy + 10), (cx + 38, cy + 4), 2)
        elif animal == "duck":
            pygame.draw.circle(self.screen, (252, 219, 84), (cx, cy), 52)
            pygame.draw.circle(self.screen, (30, 30, 30), (cx - 10, cy - 10), 5)
            pygame.draw.ellipse(self.screen, (245, 136, 52), (cx + 6, cy + 2, 44, 20))
            pygame.draw.circle(self.screen, (252, 219, 84), (cx - 28, cy - 42), 28)
        elif animal == "fish":
            pygame.draw.ellipse(self.screen, (75, 164, 220), (cx - 58, cy - 34, 116, 68))
            pygame.draw.polygon(self.screen, (75, 164, 220), [(cx + 52, cy), (cx + 88, cy - 28), (cx + 88, cy + 28)])
            pygame.draw.circle(self.screen, (255, 255, 255), (cx - 26, cy - 8), 9)
            pygame.draw.circle(self.screen, (25, 25, 25), (cx - 26, cy - 8), 4)
        else:
            pygame.draw.circle(self.screen, (184, 152, 106), (cx, cy), 52)
            pygame.draw.circle(self.screen, (235, 224, 199), (cx, cy + 8), 28)
            pygame.draw.circle(self.screen, (235, 224, 199), (cx - 48, cy - 8), 18)
            pygame.draw.circle(self.screen, (235, 224, 199), (cx + 48, cy - 8), 18)
            pygame.draw.circle(self.screen, (30, 30, 30), (cx - 18, cy - 8), 5)
            pygame.draw.circle(self.screen, (30, 30, 30), (cx + 18, cy - 8), 5)

    def draw_family_icon(self, role: str, rect: pygame.Rect):
        pygame.draw.rect(self.screen, (246, 244, 255), rect, border_radius=24)
        pygame.draw.rect(self.screen, (196, 190, 228), rect, 2, border_radius=24)
        cx, cy = rect.centerx, rect.centery + 6

        if role == "baby":
            head_r = 34
            body_color = (248, 218, 122)
        else:
            head_r = 40
            body_color = {
                "mummy": (233, 137, 167),
                "daddy": (101, 155, 233),
                "brother": (105, 186, 109),
                "grandma": (171, 146, 204),
            }.get(role, (180, 180, 200))

        pygame.draw.circle(self.screen, (247, 217, 189), (cx, cy - 18), head_r)
        pygame.draw.rect(self.screen, body_color, (cx - 38, cy + 18, 76, 54), border_radius=20)
        pygame.draw.circle(self.screen, (30, 30, 30), (cx - 13, cy - 24), 4)
        pygame.draw.circle(self.screen, (30, 30, 30), (cx + 13, cy - 24), 4)
        pygame.draw.arc(self.screen, (120, 82, 73), (cx - 15, cy - 10, 30, 18), math.pi, math.tau, 2)

        if role == "mummy":
            pygame.draw.polygon(self.screen, (233, 92, 139), [(cx - 10, cy - 64), (cx - 34, cy - 86), (cx - 18, cy - 50)])
            pygame.draw.polygon(self.screen, (233, 92, 139), [(cx + 10, cy - 64), (cx + 34, cy - 86), (cx + 18, cy - 50)])
        elif role == "daddy":
            pygame.draw.rect(self.screen, (73, 106, 171), (cx - 40, cy - 70, 80, 18), border_radius=9)
            pygame.draw.line(self.screen, (79, 55, 45), (cx - 16, cy - 4), (cx + 16, cy - 4), 3)
        elif role == "brother":
            pygame.draw.rect(self.screen, (84, 160, 86), (cx - 36, cy - 68, 72, 16), border_radius=8)
            pygame.draw.line(self.screen, (84, 160, 86), (cx + 18, cy - 56), (cx + 34, cy - 42), 5)
        elif role == "grandma":
            pygame.draw.arc(self.screen, (160, 160, 160), (cx - 42, cy - 72, 84, 40), math.pi, math.tau, 7)
            pygame.draw.circle(self.screen, (100, 100, 100), (cx - 14, cy - 24), 10, 2)
            pygame.draw.circle(self.screen, (100, 100, 100), (cx + 14, cy - 24), 10, 2)
            pygame.draw.line(self.screen, (100, 100, 100), (cx - 4, cy - 24), (cx + 4, cy - 24), 2)
        elif role == "baby":
            pygame.draw.circle(self.screen, (245, 160, 180), (cx, cy - 6), 8)

    def draw_owl(self, x: int, y: int, w: int, h: int):
        area = pygame.Rect(x, y, w, h)
        if self.owl_image:
            scaled = pygame.transform.smoothscale(self.owl_image, (w, h))
            self.screen.blit(scaled, area)
            return
        cx = area.centerx
        cy = area.centery + 8
        pygame.draw.ellipse(self.screen, (164, 124, 82), area)
        pygame.draw.ellipse(self.screen, (235, 222, 202), (x + 44, y + 62, w - 88, h - 96))
        pygame.draw.circle(self.screen, (255, 255, 255), (cx - 42, y + 110), 36)
        pygame.draw.circle(self.screen, (255, 255, 255), (cx + 42, y + 110), 36)
        pygame.draw.circle(self.screen, (41, 41, 41), (cx - 42, y + 110), 13)
        pygame.draw.circle(self.screen, (41, 41, 41), (cx + 42, y + 110), 13)
        pygame.draw.polygon(self.screen, (242, 174, 59), [(cx, y + 132), (cx - 16, y + 154), (cx + 16, y + 154)])
        pygame.draw.polygon(self.screen, (132, 95, 63), [(x + 34, y + 54), (x + 80, y + 4), (x + 108, y + 74)])
        pygame.draw.polygon(self.screen, (132, 95, 63), [(x + w - 34, y + 54), (x + w - 80, y + 4), (x + w - 108, y + 74)])

    def draw_reward_card(self, pack: str, rect: pygame.Rect):
        meta = PACK_META[pack]
        pygame.draw.rect(self.screen, meta["bg"], rect, border_radius=24)
        pygame.draw.rect(self.screen, LINE, rect, 2, border_radius=24)
        title = self.font_h2.render(meta["title"], True, TEXT)
        self.screen.blit(title, title.get_rect(center=(rect.centerx, rect.y + 28)))

        completed = self.progress["pack_progress"][pack]
        big_stars = completed // 4
        small_stars = completed % 4
        for idx in range(4):
            cx = rect.x + 48 + idx * 42
            cy = rect.y + 90
            color = YELLOW if idx < small_stars else (228, 232, 240)
            self.draw_star(cx, cy, 14, color)
        for idx in range(min(3, big_stars)):
            cx = rect.centerx
            cy = rect.y + 160 + idx * 56
            self.draw_star(cx, cy, 24, YELLOW)
        self.screen.blit(self.font_s.render(f"Spravne: {completed}", True, TEXT_SOFT), (rect.x + 18, rect.bottom - 30))

    def draw_star(self, cx: int, cy: int, radius: int, fill: tuple[int, int, int]):
        points = []
        for idx in range(10):
            angle = math.radians(-90 + idx * 36)
            r = radius if idx % 2 == 0 else max(6, int(radius * 0.45))
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        pygame.draw.polygon(self.screen, fill, points)
        pygame.draw.polygon(self.screen, (87, 79, 60), points, 2)

    def handle_click(self, pos: tuple[int, int]):
        if self.scene == "home":
            for button in self.home_buttons():
                if button.rect.collidepoint(pos):
                    self.start_pack(button.action.split(":", 1)[1])
                    return
            if pygame.Rect(1020, 30, 96, 48).collidepoint(pos):
                self.speech.say_cz("Vyber, kam pujdete. Muze to byt duha, sad, farma nebo domecek.")
                return
            if pygame.Rect(1132, 30, 112, 48).collidepoint(pos):
                self.open_reward()
                return
        elif self.scene == "lesson":
            if pygame.Rect(1042, 47, 94, 40).collidepoint(pos):
                self.play_prompt()
                return
            if pygame.Rect(1148, 47, 72, 40).collidepoint(pos):
                self.scene = "home"
                self.input_locked = False
                return
            for rect, choice in self.choice_buttons():
                if rect.collidepoint(pos):
                    self.handle_choice(choice.id)
                    return
        else:
            if pygame.Rect(1092, 42, 112, 44).collidepoint(pos):
                self.scene = "home"
            else:
                self.scene = "home"

    def run(self):
        running = True
        self.speech.say_cz("Ahoj. Vyber, kam pujdeme.")
        while running:
            self.tick_pending()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_click(event.pos)
            self.draw()
            self.clock.tick(FPS)
        self.shutdown()

    def shutdown(self):
        self._save_progress()
        self.speech.close()
        pygame.quit()


if __name__ == "__main__":
    AnglictinaMatysekV3().run()
