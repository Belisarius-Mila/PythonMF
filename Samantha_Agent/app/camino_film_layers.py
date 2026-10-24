"""Photo text layout shared by validation and MP4 rendering; no source mutation."""
from __future__ import annotations

import math
from PIL import Image, ImageDraw, ImageFont

from camino.film.media import FONT
from camino.film.project import FilmError

MAX_TEXT = 6000
MODES = ("none", "static", "scroll", "narration")


def reading_ms(text):
    return max(5000, math.ceil(max(len(text.split()) / 2.5, len(text) / 15)) * 1000)


def layout(text, size):
    width, height = size
    pixels = round(height * .035)
    font = ImageFont.truetype(str(FONT), pixels)
    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lines = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split():
            candidate = (line + " " + word).strip()
            if line and draw.textlength(candidate, font=font) > width * .80:
                lines.append(line); line = ""
            if draw.textlength(word, font=font) > width * .80:
                # Only split an unbroken token (for example a URL), preserving every character.
                for char in word:
                    if draw.textlength(line + char, font=font) > width * .80:
                        lines.append(line); line = ""
                    line += char
            else:
                line = (line + " " + word).strip()
        lines.append(line)
    return font, lines, round(pixels * 1.45)


def validate_layer(layer, *, exact, identifier, integer, text_reference):
    exact(layer, "text mode text_source narration")
    text = layer["text"]
    if (not isinstance(text, str) or len(text) > MAX_TEXT
            or any(ord(c) < 32 and c != "\n" for c in text)):
        raise FilmError("Text fotografie může mít nejvýše 6000 znaků; nový řádek je povolený.")
    if layer["mode"] not in MODES or layer["mode"] != "none" and not text.strip():
        raise FilmError("Vyber režim a vyplň text fotografie.")
    if layer["text_source"] is not None:
        text_reference(layer["text_source"])
    narration = layer["narration"]
    if narration is not None:
        exact(narration, "id duration_ms sha256 included")
        identifier(narration["id"]); integer(narration["duration_ms"], 1, 3_600_000)
        if (not isinstance(narration["sha256"], str) or len(narration["sha256"]) != 64
                or any(c not in "0123456789abcdef" for c in narration["sha256"])
                or type(narration["included"]) is not bool):
            raise FilmError("Neplatný uložený hlasový komentář fotografie.")


def validate_display(shot):
    layer = shot.get("photo_text")
    if not layer or not shot["included"]:
        return
    mode, text = layer["mode"], layer["text"]
    if mode == "static":
        for size in ((1280, 720), (1920, 1080)):
            _, lines, spacing = layout(text, size)
            if len(lines) * spacing > size[1] * .38:
                raise FilmError("Statický text se do okna čitelně nevejde. Vyber úryvek nebo plynulý text.")
    if mode == "scroll" and shot["out_ms"] < reading_ms(text):
        raise FilmError("Plynulý text potřebuje delší zobrazení. U fotografie použij Prodloužit pro celý text.")
    narration = layer["narration"]
    if mode == "narration" and (not narration or not narration["included"]):
        raise FilmError("Čtení zatím není zařazené do filmu. Vytvoř ho, poslechni a použij, nebo vyber jiný režim textu.")
    if mode == "narration" and narration and narration["included"] and narration["duration_ms"] > shot["out_ms"]:
        raise FilmError("Čtení přesahuje fotografii. Prodluž ji podle komentáře nebo vyber kratší text.")


def layer_image(target, text, size, mode):
    """Transparent full-frame static panel or opaque scroll strip."""
    width, height = size
    font, lines, spacing = layout(text, size)
    if mode == "static":
        image = Image.new("RGBA", size)
        draw = ImageDraw.Draw(image)
        top = round(height * .92 - len(lines) * spacing - height * .05)
        draw.rectangle((round(width * .07), top, round(width * .93), height * .92), fill=(12, 18, 28, 215))
        for i, line in enumerate(lines):
            draw.text((width * .10, top + height * .025 + i * spacing), line, font=font, fill="white")
    else:
        image = Image.new("RGBA", (round(width * .86), len(lines) * spacing + spacing), (12, 18, 28, 235))
        draw = ImageDraw.Draw(image)
        for i, line in enumerate(lines):
            draw.text((width * .03, i * spacing), line, font=font, fill="white")
    with target.open("xb") as handle:
        image.save(handle, "PNG")
    target.chmod(0o600)
    return image.height
