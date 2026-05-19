import json
import math
import random
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from pathlib import Path

import pygame

ROOT_DIR = Path(__file__).resolve().parent
PICT_DIR = ROOT_DIR / "Pict"
ANIMALS_DIR = ROOT_DIR / "Animals"
OWL_PATH = ROOT_DIR / "oul.png"
PROGRESS_PATH = ROOT_DIR / "matysek_progress.json"

FPS = 60
WIDTH = 1280
HEIGHT = 780

BG = (242, 249, 255)
CARD = (255, 255, 255)
TEXT = (25, 36, 52)
GREEN = (30, 150, 65)
RED = (190, 45, 45)
BLUE = (35, 102, 240)

COLOR_WORDS = {
    "red": (255, 77, 77),
    "blue": (59, 130, 246),
    "green": (34, 197, 94),
    "yellow": (250, 204, 21),
    "orange": (251, 146, 60),
    "black": (34, 34, 34),
    "white": (255, 255, 255),
    "pink": (236, 72, 153),
    "brown": (139, 90, 43),
    "gray": (156, 163, 175),
    "purple": (168, 85, 247),
}

NUMBER_WORDS = {
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
}

PRAISES = [
    "Great job, Matysek!",
    "Excellent!",
    "Super!",
    "Well done!",
    "You are amazing!",
]

ENCOURAGEMENTS = [
    "Zkus to znovu, Matysku.",
    "Skoro! Zkusime to znovu.",
    "Zkus to znovu.",
]

ANIMAL_CZ_MAP = {
    "dog": "pes",
    "cat": "kocka",
    "fish": "ryba",
    "horse": "kun",
    "duck": "kachna",
    "rabbit": "kralik",
    "parrot": "papousek",
    "eagle": "orel",
    "bird": "ptak",
    "deer": "jelen",
    "elephant": "slon",
    "lion": "lev",
    "camel": "velbloud",
    "turkey": "krocan",
    "zebra": "zebra",
    "sheep": "ovce",
    "tortoise": "zelva",
    "cow": "krava",
    "hippopotamus": "hroch",
    "hippo": "hroch",
    "wolf": "vlk",
    "mouse": "mys",
    "monkey": "opice",
    "giraffe": "zirafa",
    "fox": "liska",
    "pig": "prase",
    "snake": "had",
    "bear": "medved",
    "goat": "koza",
    "goose": "husa",
    "rhinoceros": "nosorozec",
    "rhino": "nosorozec",
    "owl": "sova",
}

ANIMAL_EMOJI_MAP = {
    "dog": "D",
    "cat": "C",
    "fish": "F",
    "horse": "H",
    "duck": "K",
    "rabbit": "R",
    "parrot": "P",
    "eagle": "E",
    "bird": "B",
    "deer": "J",
    "elephant": "S",
    "lion": "L",
    "camel": "V",
    "turkey": "T",
    "zebra": "Z",
    "sheep": "O",
    "tortoise": "Q",
    "cow": "W",
    "hippopotamus": "Y",
    "hippo": "Y",
    "wolf": "U",
    "mouse": "M",
    "monkey": "N",
    "giraffe": "G",
    "fox": "X",
    "pig": "I",
    "snake": "A",
    "bear": "R",
    "goat": "T",
    "goose": "H",
    "rhinoceros": "O",
    "rhino": "O",
    "owl": "O",
}


def _normalize_animal_stem(stem: str) -> tuple[str, list[str]]:
    s = stem.strip().lower()
    aliases: list[str] = []
    main = s
    if "(" in s and ")" in s:
        before = s.split("(", 1)[0].strip()
        inside = s.split("(", 1)[1].split(")", 1)[0].strip()
        main = before or inside or s
        if before:
            aliases.append(before)
        if inside:
            aliases.extend([x.strip() for x in inside.split("/") if x.strip()])
    aliases.append(main)
    uniq: list[str] = []
    seen = set()
    for a in aliases:
        if a not in seen:
            seen.add(a)
            uniq.append(a)
    display = min(uniq, key=len) if uniq else stem.lower()
    return display, uniq


def _build_animal_words() -> list[dict]:
    items: list[dict] = []
    if ANIMALS_DIR.exists():
        for f in sorted(ANIMALS_DIR.iterdir()):
            if not f.is_file() or f.suffix.lower() not in (".png", ".jpg", ".jpeg", ".gif"):
                continue
            display, aliases = _normalize_animal_stem(f.stem)
            items.append(
                {
                    "word": display,
                    "cz": ANIMAL_CZ_MAP.get(display, display),
                    "image": f,
                    "emoji": ANIMAL_EMOJI_MAP.get(display, "?"),
                    "animal_aliases": aliases,
                }
            )
    items.append({"word": "owl", "cz": "sova", "image": OWL_PATH, "emoji": "O", "animal_aliases": ["owl"]})
    out: list[dict] = []
    seen = set()
    for item in items:
        w = item["word"]
        if w in seen:
            continue
        seen.add(w)
        out.append(item)
    return out


def _find_edge_tts_bin() -> str | None:
    candidates = [
        shutil.which("edge-tts"),
        str(Path.home() / "Library/Python/3.11/bin/edge-tts"),
        str(Path.home() / "Library/Python/3.12/bin/edge-tts"),
        "/opt/homebrew/bin/edge-tts",
        "/usr/local/bin/edge-tts",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    return None


def _say_voice_exists(voice_name: str) -> bool:
    try:
        out = subprocess.check_output(["say", "-v", "?"], text=True, stderr=subprocess.DEVNULL)
        return any(line.startswith(voice_name + " ") for line in out.splitlines())
    except Exception:
        return False


def speak_english(text: str, voice: str = "Samantha"):
    try:
        subprocess.Popen(["say", "-v", voice, text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def _play_mp3(path: Path):
    afplay_bin = shutil.which("afplay")
    if not afplay_bin:
        return
    try:
        subprocess.run([afplay_bin, str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except Exception:
        pass


def _speak_czech_male_edge_async(text: str) -> bool:
    edge_tts_bin = _find_edge_tts_bin()
    if not edge_tts_bin:
        return False

    def worker():
        out_path = Path(tempfile.gettempdir()) / f"matysek_owl_{uuid.uuid4().hex}.mp3"
        try:
            subprocess.run(
                [
                    edge_tts_bin,
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
        except Exception:
            _speak_old_man_czech_fallback(text)
        finally:
            try:
                out_path.unlink(missing_ok=True)
            except Exception:
                pass

    threading.Thread(target=worker, daemon=True).start()
    return True


def _speak_old_man_czech_fallback(text: str):
    for voice in ("Alex", "Zuzana"):
        try:
            if voice == "Alex" and not _say_voice_exists("Alex"):
                continue
            if voice == "Zuzana" and not _say_voice_exists("Zuzana"):
                continue
            subprocess.Popen(["say", "-v", voice, text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        except Exception:
            continue


def owl_speak_czech(text: str):
    if _speak_czech_male_edge_async(text):
        return
    _speak_old_man_czech_fallback(text)


class AssetStore:
    def __init__(self):
        self.cache: dict[tuple[str, tuple[int, int]], pygame.Surface] = {}

    def image(self, path: Path, size: tuple[int, int]) -> pygame.Surface | None:
        key = (str(path), size)
        if key in self.cache:
            return self.cache[key]
        if not path.exists():
            return None
        try:
            original = pygame.image.load(str(path)).convert_alpha()
            src_w, src_h = original.get_size()
            dst_w, dst_h = max(1, size[0]), max(1, size[1])
            if src_w <= 0 or src_h <= 0:
                return None

            # Preserve aspect ratio: scale to fit into the target box, then center.
            scale = min(dst_w / src_w, dst_h / src_h)
            out_w = max(1, int(src_w * scale))
            out_h = max(1, int(src_h * scale))
            scaled = pygame.transform.smoothscale(original, (out_w, out_h))

            canvas = pygame.Surface((dst_w, dst_h), pygame.SRCALPHA)
            x = (dst_w - out_w) // 2
            y = (dst_h - out_h) // 2
            canvas.blit(scaled, (x, y))

            self.cache[key] = canvas
            return canvas
        except Exception:
            return None


class Button:
    def __init__(self, rect: pygame.Rect, text: str, bg: tuple[int, int, int], fg: tuple[int, int, int] = TEXT):
        self.rect = rect
        self.text = text
        self.bg = bg
        self.fg = fg

    def draw(self, screen: pygame.Surface, font: pygame.font.Font, mouse_pos: tuple[int, int]):
        hover = self.rect.collidepoint(mouse_pos)
        shade = 18 if hover else 0
        color = tuple(min(255, c + shade) for c in self.bg)
        pygame.draw.rect(screen, color, self.rect, border_radius=14)
        pygame.draw.rect(screen, (35, 55, 80), self.rect, width=2, border_radius=14)
        txt = font.render(self.text, True, self.fg)
        screen.blit(txt, txt.get_rect(center=self.rect.center))


class AnglictinaMatysekApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Anglictina Matysek - Pygame Edition")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()

        self.font_big = pygame.font.SysFont("arial", 50, bold=True)
        self.font_h1 = pygame.font.SysFont("arial", 40, bold=True)
        self.font_h2 = pygame.font.SysFont("arial", 30, bold=True)
        self.font_m = pygame.font.SysFont("arial", 24, bold=True)
        self.font_s = pygame.font.SysFont("arial", 20)

        self.assets = AssetStore()
        self.animal_words = _build_animal_words()

        self.score = 0
        self.stars = 0
        self.correct_total = 0
        self.round_total = 0
        self.streak = 0
        self._load_progress()

        self.scene = "home"
        self.feedback = ""
        self.feedback_color = TEXT
        self.scheduled_next_time = 0.0
        self.scheduled_next_fn = None
        self.sparkles = [{"x": random.randint(20, WIDTH - 20), "y": random.randint(20, HEIGHT - 20)} for _ in range(42)]

        self.color_round: dict = {}
        self.number_round: dict = {}
        self.mix_round: dict = {}
        self.animal_round: dict = {}

    def _load_progress(self):
        if not PROGRESS_PATH.exists():
            return
        try:
            data = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
            self.score = int(data.get("score", 0))
            self.stars = int(data.get("stars", 0))
            self.correct_total = int(data.get("correct_total", 0))
            self.round_total = int(data.get("round_total", 0))
            self.streak = int(data.get("streak", 0))
        except Exception:
            pass

    def _save_progress(self):
        data = {
            "score": int(self.score),
            "stars": int(self.stars),
            "correct_total": int(self.correct_total),
            "round_total": int(self.round_total),
            "streak": int(self.streak),
        }
        try:
            PROGRESS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _queue_next(self, delay: float, fn):
        self.scheduled_next_time = time.time() + delay
        self.scheduled_next_fn = fn

    def _tick_queue(self):
        if self.scheduled_next_fn and time.time() >= self.scheduled_next_time:
            fn = self.scheduled_next_fn
            self.scheduled_next_fn = None
            self.scheduled_next_time = 0.0
            fn()

    def _draw_header(self, w: int):
        bar = pygame.Rect(0, 0, w, 74)
        pygame.draw.rect(self.screen, (213, 232, 250), bar)
        pygame.draw.line(self.screen, (130, 166, 206), (0, 73), (w, 73), 2)
        self.screen.blit(self.font_h2.render("Anglictina pro Matyska", True, TEXT), (20, 18))
        right = f"Skore: {self.score}   Hvezdy: {self.stars}   Streak: {self.streak}"
        txt = self.font_m.render(right, True, (15, 30, 50))
        self.screen.blit(txt, (w - txt.get_width() - 20, 22))

    def _draw_background(self, w: int, h: int):
        for y in range(h):
            t = y / max(1, h)
            c = (
                int(BG[0] + t * 8),
                int(BG[1] + t * 3),
                int(BG[2] - t * 5),
            )
            pygame.draw.line(self.screen, c, (0, y), (w, y))
        for s in self.sparkles:
            s["x"] += random.randint(-1, 1)
            s["y"] += random.randint(-1, 1)
            s["x"] = max(5, min(w - 5, s["x"]))
            s["y"] = max(80, min(h - 5, s["y"]))
            pygame.draw.circle(self.screen, random.choice([(255, 213, 102), (142, 202, 230), (255, 175, 204)]), (s["x"], s["y"]), 3)

    def _home_buttons(self, w: int, h: int) -> list[tuple[Button, str]]:
        x = w * 0.62
        y = 150
        bw = int(w * 0.28)
        bh = 64
        gap = 14
        items = [
            ("Barvy", "colors", (255, 224, 239)),
            ("Cisla", "numbers", (255, 247, 191)),
            ("Zvirata", "animals", (220, 248, 255)),
            ("Mix hra", "mix", (224, 248, 222)),
            ("Odmema", "reward", (214, 237, 255)),
        ]
        out = []
        for i, (title, scene, bgc) in enumerate(items):
            rect = pygame.Rect(int(x), int(y + i * (bh + gap)), bw, bh)
            out.append((Button(rect, title, bgc), scene))
        out.append((Button(pygame.Rect(int(x), int(y + 5 * (bh + gap) + 16), bw, 52), "Sova promluv", CARD), "owl"))
        return out

    def _switch_scene(self, new_scene: str):
        self.feedback = ""
        self.feedback_color = TEXT
        self.scene = new_scene
        if new_scene == "colors":
            self.colors_new_round()
            owl_speak_czech("Teď budeme hledat barvy.")
        elif new_scene == "numbers":
            self.numbers_new_round()
            owl_speak_czech("Teď budeme počítat.")
        elif new_scene == "animals":
            self.animals_new_round()
            owl_speak_czech("Teď budeme hledat zvířata.")
        elif new_scene == "mix":
            self.mix_new_round()
            owl_speak_czech("Najdi správnou kartičku podle počtu a barvy.")

    def _draw_back_button(self, w: int) -> Button:
        return Button(pygame.Rect(w - 180, 84, 150, 46), "Domu", CARD)

    def _draw_feedback(self, y: int):
        if self.feedback:
            t = self.font_h2.render(self.feedback, True, self.feedback_color)
            self.screen.blit(t, (40, y))

    def colors_new_round(self):
        options = random.sample(list(COLOR_WORDS.keys()), 4)
        target = random.choice(options)
        self.color_round = {"options": options, "target": target}
        self.feedback = ""
        speak_english(target)

    def numbers_new_round(self):
        count = random.randint(1, 10)
        choices = {count}
        while len(choices) < 4:
            choices.add(random.randint(1, 10))
        options = list(choices)
        random.shuffle(options)
        color_name = random.choice(["blue", "green", "yellow", "red", "orange", "pink"])
        self.number_round = {"count": count, "options": options, "color": color_name}
        self.feedback = ""
        speak_english("How many")
        speak_english(NUMBER_WORDS[count])

    def mix_new_round(self):
        cards = []
        used = set()
        colors = ["blue", "green", "yellow", "red", "orange", "pink"]
        for _ in range(4):
            while True:
                cnt = random.randint(1, 6)
                col = random.choice(colors)
                if (cnt, col) not in used:
                    used.add((cnt, col))
                    cards.append({"count": cnt, "color": col})
                    break
        target_idx = random.randrange(4)
        self.mix_round = {"cards": cards, "target_idx": target_idx}
        self.feedback = ""
        t = cards[target_idx]
        speak_english("Find")
        speak_english(NUMBER_WORDS[t["count"]])
        speak_english(t["color"])

    def animals_new_round(self):
        if len(self.animal_words) >= 4:
            options = random.sample(self.animal_words, 4)
        else:
            options = [random.choice(self.animal_words) for _ in range(4)]
        target_idx = random.randrange(4)
        self.animal_round = {"options": options, "target_idx": target_idx}
        self.feedback = ""
        target = options[target_idx]
        speak_english("Click")
        speak_english(target["word"])

    def _answer(self, correct: bool, success_points: int, fail_penalty: int, good_msg: str, bad_msg: str, next_fn):
        self.round_total += 1
        if correct:
            self.correct_total += 1
            self.score += success_points
            self.stars += 1
            self.streak += 1
            self.feedback = good_msg
            self.feedback_color = GREEN
            owl_speak_czech(random.choice(["Výborně!", "Paráda!", "Skvěle!"]))
            self._queue_next(1.1, next_fn)
        else:
            self.score = max(0, self.score - fail_penalty)
            self.streak = 0
            self.feedback = bad_msg
            self.feedback_color = RED
            owl_speak_czech(random.choice(ENCOURAGEMENTS))
        self._save_progress()

    def _draw_star(self, cx: int, cy: int, r: int, fill: tuple[int, int, int]):
        pts = []
        for i in range(10):
            a = math.radians(-90 + i * 36)
            rr = r if i % 2 == 0 else max(8, int(r * 0.45))
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        pygame.draw.polygon(self.screen, fill, pts)
        pygame.draw.polygon(self.screen, (40, 55, 80), pts, 2)

    def draw_home(self, w: int, h: int, mouse_pos: tuple[int, int]):
        self._draw_background(w, h)
        title = self.font_big.render("Sova uci Matyska", True, (39, 64, 96))
        self.screen.blit(title, (36, 110))
        subtitle = self.font_h2.render("Vyber si hru", True, TEXT)
        self.screen.blit(subtitle, (42, 176))

        owl = self.assets.image(OWL_PATH, (420, 420))
        if owl:
            self.screen.blit(owl, (52, 220))
        else:
            pygame.draw.circle(self.screen, (230, 240, 255), (240, 430), 120)
            self.screen.blit(self.font_big.render("OWL", True, BLUE), (165, 405))

        buttons = self._home_buttons(w, h)
        for btn, _ in buttons:
            btn.draw(self.screen, self.font_m, mouse_pos)
        return buttons

    def draw_colors(self, w: int, h: int, mouse_pos: tuple[int, int]):
        self.screen.blit(self.font_h1.render("Hra: Barvy", True, TEXT), (40, 92))
        target = self.color_round["target"]
        self.screen.blit(self.font_h2.render(f"Klikni na: {target.upper()}", True, COLOR_WORDS[target]), (40, 140))
        self._draw_feedback(185)

        area = pygame.Rect(40, 240, int(w * 0.5), int(h * 0.6))
        pygame.draw.rect(self.screen, CARD, area, border_radius=18)
        pygame.draw.rect(self.screen, (150, 190, 220), area, 2, border_radius=18)
        sample = pygame.Rect(area.x + 40, area.y + 55, area.width - 80, area.height - 110)
        pygame.draw.rect(self.screen, COLOR_WORDS[target], sample, border_radius=20)
        pygame.draw.rect(self.screen, (40, 55, 80), sample, 2, border_radius=20)

        rects = []
        bx = int(w * 0.6)
        bw = int(w * 0.16)
        bh = 84
        for i, word in enumerate(self.color_round["options"]):
            row = i // 2
            col = i % 2
            rect = pygame.Rect(bx + col * (bw + 26), 280 + row * (bh + 24), bw, bh)
            fg = (25, 25, 25) if word in ("yellow", "white", "gray") else (250, 250, 250)
            Button(rect, word.upper(), COLOR_WORDS[word], fg).draw(self.screen, self.font_m, mouse_pos)
            rects.append((rect, i))
        return rects

    def draw_numbers(self, w: int, h: int, mouse_pos: tuple[int, int]):
        self.screen.blit(self.font_h1.render("Hra: Cisla", True, TEXT), (40, 92))
        self.screen.blit(self.font_h2.render("How many?", True, TEXT), (40, 140))
        self._draw_feedback(185)

        area = pygame.Rect(40, 240, int(w * 0.56), int(h * 0.6))
        pygame.draw.rect(self.screen, (255, 253, 242), area, border_radius=18)
        pygame.draw.rect(self.screen, (230, 210, 120), area, 2, border_radius=18)

        count = self.number_round["count"]
        cols = min(5, max(2, int(math.ceil(math.sqrt(count)))))
        rows = int(math.ceil(count / cols))
        sx = (area.width - 80) / cols
        sy = (area.height - 90) / max(1, rows)
        fill = COLOR_WORDS[self.number_round["color"]]
        for i in range(count):
            rr = i // cols
            cc = i % cols
            cx = int(area.x + 40 + (cc + 0.5) * sx)
            cy = int(area.y + 45 + (rr + 0.6) * sy)
            self._draw_star(cx, cy, max(14, int(min(sx, sy) * 0.24)), fill)

        rects = []
        bx = int(w * 0.68)
        bw = int(w * 0.12)
        bh = 90
        for i, n in enumerate(self.number_round["options"]):
            row = i // 2
            col = i % 2
            rect = pygame.Rect(bx + col * (bw + 24), 290 + row * (bh + 24), bw, bh)
            Button(rect, f"{n}", CARD).draw(self.screen, self.font_h2, mouse_pos)
            small = self.font_s.render(NUMBER_WORDS[n].upper(), True, (70, 80, 95))
            self.screen.blit(small, small.get_rect(center=(rect.centerx, rect.centery + 24)))
            rects.append((rect, i))
        return rects

    def draw_mix(self, w: int, h: int, mouse_pos: tuple[int, int]):
        t = self.mix_round["cards"][self.mix_round["target_idx"]]
        self.screen.blit(self.font_h1.render("Mix hra", True, TEXT), (40, 92))
        self.screen.blit(
            self.font_h2.render(f"Find: {NUMBER_WORDS[t['count']].upper()} {t['color'].upper()}", True, TEXT),
            (40, 140),
        )
        self._draw_feedback(185)

        rects = []
        margin = 60
        gap = 20
        card_w = int((w - margin * 2 - gap) / 2)
        card_h = int((h - 300 - gap) / 2)
        for i, card in enumerate(self.mix_round["cards"]):
            row = i // 2
            col = i % 2
            rect = pygame.Rect(margin + col * (card_w + gap), 240 + row * (card_h + gap), card_w, card_h)
            pygame.draw.rect(self.screen, CARD, rect, border_radius=14)
            pygame.draw.rect(self.screen, (145, 203, 160), rect, 2, border_radius=14)
            title = self.font_s.render(f"CARD {i + 1}", True, (80, 100, 120))
            self.screen.blit(title, (rect.x + 14, rect.y + 10))

            cnt = card["count"]
            colname = card["color"]
            fill = COLOR_WORDS[colname]
            cols = 3
            rows = int(math.ceil(cnt / cols))
            sx = (card_w - 50) / cols
            sy = (card_h - 80) / max(1, rows)
            for j in range(cnt):
                rr = j // cols
                cc = j % cols
                cx = int(rect.x + 25 + (cc + 0.5) * sx)
                cy = int(rect.y + 40 + (rr + 0.6) * sy)
                pygame.draw.circle(self.screen, fill, (cx, cy), max(8, int(min(sx, sy) * 0.18)))
                pygame.draw.circle(self.screen, (45, 58, 78), (cx, cy), max(8, int(min(sx, sy) * 0.18)), 2)

            foot = self.font_s.render(f"{NUMBER_WORDS[cnt].upper()} - {colname.upper()}", True, (50, 62, 82))
            self.screen.blit(foot, (rect.x + 16, rect.y + card_h - 32))
            if rect.collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, (70, 120, 180), rect, 3, border_radius=14)
            rects.append((rect, i))
        return rects

    def draw_animals(self, w: int, h: int, mouse_pos: tuple[int, int]):
        target = self.animal_round["options"][self.animal_round["target_idx"]]
        self.screen.blit(self.font_h1.render("Hra: Zvirata", True, TEXT), (40, 92))
        self.screen.blit(self.font_h2.render(f"Click: {target['word'].upper()}", True, TEXT), (40, 140))
        self._draw_feedback(185)

        rects = []
        margin = 60
        gap = 20
        card_w = int((w - margin * 2 - gap) / 2)
        card_h = int((h - 300 - gap) / 2)
        for i, item in enumerate(self.animal_round["options"]):
            row = i // 2
            col = i % 2
            rect = pygame.Rect(margin + col * (card_w + gap), 240 + row * (card_h + gap), card_w, card_h)
            pygame.draw.rect(self.screen, CARD, rect, border_radius=14)
            pygame.draw.rect(self.screen, (145, 203, 230), rect, 2, border_radius=14)

            img = self.assets.image(item["image"], (int(card_w * 0.72), int(card_h * 0.62))) if isinstance(item["image"], Path) else None
            if img:
                img_rect = img.get_rect(center=(rect.centerx, rect.y + int(card_h * 0.43)))
                self.screen.blit(img, img_rect)
            else:
                ph = pygame.Rect(rect.x + 40, rect.y + 35, card_w - 80, int(card_h * 0.58))
                pygame.draw.rect(self.screen, (230, 239, 248), ph, border_radius=12)
                letter = self.font_big.render(item["emoji"], True, (80, 98, 120))
                self.screen.blit(letter, letter.get_rect(center=ph.center))

            label = self.font_m.render(item["word"].upper(), True, (45, 58, 78))
            self.screen.blit(label, label.get_rect(center=(rect.centerx, rect.y + card_h - 26)))
            if rect.collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, (64, 120, 190), rect, 3, border_radius=14)
            rects.append((rect, i))
        return rects

    def draw_reward(self, w: int, h: int):
        self.screen.blit(self.font_h1.render("Odmema pro Matyska", True, TEXT), (40, 92))
        summary = f"Spravne: {self.correct_total}/{self.round_total}   Skore: {self.score}   Hvezdy: {self.stars}"
        self.screen.blit(self.font_m.render(summary, True, (70, 80, 95)), (40, 142))
        for _ in range(80):
            x = random.randint(0, w - 1)
            y = random.randint(220, h - 20)
            c = random.choice([(255, 107, 107), (255, 209, 102), (78, 205, 196), (95, 168, 255), (199, 125, 255)])
            pygame.draw.circle(self.screen, c, (x, y), random.randint(2, 6))

        owl = self.assets.image(OWL_PATH, (320, 320))
        if owl:
            self.screen.blit(owl, owl.get_rect(center=(w // 2, h // 2 + 60)))
        txt = self.font_big.render("BRAVO!", True, (120, 45, 18))
        self.screen.blit(txt, txt.get_rect(center=(w // 2, 220)))

    def run(self):
        running = True
        clickables: list[tuple[pygame.Rect, str, int | None]] = []
        while running:
            self.clock.tick(FPS)
            self._tick_queue()
            w, h = self.screen.get_size()
            mouse_pos = pygame.mouse.get_pos()
            self._draw_background(w, h)
            self._draw_header(w)
            clickables = []

            if self.scene == "home":
                home_buttons = self.draw_home(w, h, mouse_pos)
                for btn, action in home_buttons:
                    clickables.append((btn.rect, action, None))
            else:
                back = self._draw_back_button(w)
                back.draw(self.screen, self.font_s, mouse_pos)
                clickables.append((back.rect, "home", None))
                if self.scene == "colors":
                    for rect, idx in self.draw_colors(w, h, mouse_pos):
                        clickables.append((rect, "color_pick", idx))
                elif self.scene == "numbers":
                    for rect, idx in self.draw_numbers(w, h, mouse_pos):
                        clickables.append((rect, "number_pick", idx))
                elif self.scene == "mix":
                    for rect, idx in self.draw_mix(w, h, mouse_pos):
                        clickables.append((rect, "mix_pick", idx))
                elif self.scene == "animals":
                    for rect, idx in self.draw_animals(w, h, mouse_pos):
                        clickables.append((rect, "animal_pick", idx))
                elif self.scene == "reward":
                    self.draw_reward(w, h)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((max(980, event.w), max(680, event.h)), pygame.RESIZABLE)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.scene == "home":
                            running = False
                        else:
                            self.scene = "home"
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    for rect, action, idx in clickables:
                        if not rect.collidepoint((mx, my)):
                            continue
                        if action in ("home", "colors", "numbers", "animals", "mix", "reward"):
                            self._switch_scene(action)
                        elif action == "owl":
                            owl_speak_czech("Matysku, vyber si hru. Jsem pripraveny.")
                        elif action == "color_pick" and idx is not None:
                            options = self.color_round["options"]
                            target = self.color_round["target"]
                            picked = options[idx]
                            if picked == target:
                                speak_english(target)
                                self._answer(True, 10, 2, random.choice(PRAISES), "", self.colors_new_round)
                            else:
                                speak_english(target)
                                self._answer(False, 10, 2, "", f"To byla {picked.upper()}. Hledame {target.upper()}.", self.colors_new_round)
                        elif action == "number_pick" and idx is not None:
                            picked = self.number_round["options"][idx]
                            correct = self.number_round["count"]
                            if picked == correct:
                                speak_english(NUMBER_WORDS[correct])
                                self._answer(True, 12, 2, random.choice(PRAISES), "", self.numbers_new_round)
                            else:
                                speak_english(NUMBER_WORDS[correct])
                                self._answer(False, 12, 2, "", f"Spravne je {NUMBER_WORDS[correct].upper()}.", self.numbers_new_round)
                        elif action == "mix_pick" and idx is not None:
                            ok = idx == self.mix_round["target_idx"]
                            if ok:
                                self._answer(True, 15, 3, random.choice(PRAISES), "", self.mix_new_round)
                            else:
                                self._answer(False, 15, 3, "", "Zkus znovu, stejne karty zustavaji.", self.mix_new_round)
                        elif action == "animal_pick" and idx is not None:
                            target_idx = self.animal_round["target_idx"]
                            target = self.animal_round["options"][target_idx]
                            if idx == target_idx:
                                speak_english(target["word"])
                                self._answer(True, 14, 2, random.choice(PRAISES), "", self.animals_new_round)
                            else:
                                picked = self.animal_round["options"][idx]
                                self._answer(False, 14, 2, "", f"To je {picked['cz']}. Zkus to znovu.", self.animals_new_round)
                        break

            pygame.display.flip()

        self._save_progress()
        pygame.quit()


if __name__ == "__main__":
    app = AnglictinaMatysekApp()
    app.run()
