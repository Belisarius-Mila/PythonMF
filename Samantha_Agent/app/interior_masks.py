"""Native-pixel masks and lossless local composition. No model or network."""
from __future__ import annotations

import hashlib
import io
import math

from PIL import Image, ImageChops, ImageDraw, ImageFilter

MODES = ("PIXEL_LOCK", "GEOMETRY_LOCK", "EDITABLE", "FREE_DESIGN", "CONTEXT_ONLY")
SIZE = (1000, 650)


def png(image):
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def sample_image():
    image = Image.new("RGB", SIZE, "#ded6c8")
    draw = ImageDraw.Draw(image)
    draw.polygon([(0, 0), (100, 60), (100, 510), (0, 650)], fill="#b5aa96")
    draw.polygon([(1000, 0), (900, 60), (900, 510), (1000, 650)], fill="#c7bba5")
    draw.polygon([(0, 650), (100, 510), (900, 510), (1000, 650)], fill="#a18a70")
    draw.rectangle((100, 60, 900, 510), fill="#e6dece")
    draw.rectangle((390, 145, 610, 380), fill="#534d43")
    draw.rectangle((400, 155, 600, 370), fill="#efeee5")
    draw.rectangle((409, 164, 492, 359), fill="#b5cbd0")
    draw.rectangle((507, 164, 590, 359), fill="#b5cbd0")
    draw.rectangle((380, 381, 620, 394), fill="#f4f0e6")
    return png(image)


def validate_layers(layers, size):
    if not isinstance(layers, list) or len(layers) > 64:
        raise ValueError("Neplatný počet oblastí.")
    points_total = 0
    ids = set()
    for layer in layers:
        if not isinstance(layer, dict) or set(layer) != {"id", "name", "mode", "visible", "strokes"}:
            raise ValueError("Neplatná oblast.")
        if not isinstance(layer["id"], str) or not 1 <= len(layer["id"]) <= 64 or layer["id"] in ids:
            raise ValueError("Neplatná identita oblasti.")
        ids.add(layer["id"])
        if not isinstance(layer["name"], str) or not 1 <= len(layer["name"].strip()) <= 100:
            raise ValueError("Doplň název oblasti.")
        if layer["mode"] not in MODES or type(layer["visible"]) is not bool:
            raise ValueError("Neplatný režim oblasti.")
        if not isinstance(layer["strokes"], list) or len(layer["strokes"]) > 1000:
            raise ValueError("Příliš mnoho tahů.")
        for stroke in layer["strokes"]:
            if not isinstance(stroke, dict) or set(stroke) != {"tool", "erase", "width", "points"}:
                raise ValueError("Neplatný tah.")
            tool, points, width = stroke["tool"], stroke["points"], stroke["width"]
            if tool not in ("rect", "polygon", "brush") or type(stroke["erase"]) is not bool:
                raise ValueError("Neplatný nástroj.")
            if type(width) not in (int, float) or not math.isfinite(width) or not 1 <= width <= 200:
                raise ValueError("Neplatná šířka štětce.")
            if not isinstance(points, list) or not 1 <= len(points) <= 5000:
                raise ValueError("Neplatné body.")
            if (tool == "rect" and len(points) != 2) or (tool == "polygon" and len(points) < 3):
                raise ValueError("Nedokončený tvar.")
            points_total += len(points)
            if points_total > 50000:
                raise ValueError("Příliš mnoho bodů.")
            for point in points:
                if not isinstance(point, list) or len(point) != 2:
                    raise ValueError("Neplatný bod.")
                for value, limit in zip(point, size):
                    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value < limit:
                        raise ValueError("Bod leží mimo pracovní obrázek.")


def rasterize(layers, size):
    validate_layers(layers, size)
    allowed = Image.new("L", size)
    protected = Image.new("L", size)
    geometry = Image.new("L", size)
    for layer in layers:
        mask = Image.new("L", size)
        draw = ImageDraw.Draw(mask)
        for stroke in layer["strokes"]:
            points = [tuple(round(v) for v in point) for point in stroke["points"]]
            fill = 0 if stroke["erase"] else 255
            radius = stroke["width"] / 2
            if stroke["tool"] == "rect":
                a, b = points
                draw.rectangle((min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])), fill=fill)
            elif stroke["tool"] == "polygon":
                draw.polygon(points, fill=fill)
            else:
                draw.line(points, fill=fill, width=round(stroke["width"]))
                for x, y in points:
                    draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=fill)
        mode = layer["mode"]
        if mode in ("EDITABLE", "FREE_DESIGN"):
            allowed = ImageChops.lighter(allowed, mask)
        elif mode == "GEOMETRY_LOCK":
            # A surface-only geometry validator is not available in the first milestone.
            geometry = ImageChops.lighter(geometry, mask)
        else:
            protected = ImageChops.lighter(protected, mask)
    blocked = ImageChops.lighter(protected, geometry)
    conflict = ImageChops.multiply(allowed, blocked)
    effective = ImageChops.subtract(allowed, blocked)
    return effective, conflict, geometry


def composite(base_bytes, candidate_bytes, layers, feather=0):
    if type(feather) is not int or not 0 <= feather <= 20:
        raise ValueError("Neplatné vyhlazení okraje.")
    with Image.open(io.BytesIO(base_bytes)) as source:
        base = source.convert("RGBA" if "A" in source.getbands() else "RGB")
    with Image.open(io.BytesIO(candidate_bytes)) as source:
        if source.size != base.size:
            raise ValueError("Kandidát má jiné rozměry. Vyber stejný pohled.")
        candidate = source.convert(base.mode)
    allowed, conflict, geometry = rasterize(layers, base.size)
    alpha = allowed
    if feather:
        alpha = ImageChops.multiply(allowed, allowed.filter(ImageFilter.GaussianBlur(feather)))
    result = png(Image.composite(candidate, base, alpha))
    with Image.open(io.BytesIO(result)) as decoded:
        diff = ImageChops.difference(base, decoded.convert(base.mode))
        changed = Image.new("L", base.size)
        for channel in diff.split():
            changed = ImageChops.lighter(changed, channel)
        changed = changed.point(lambda value: 255 if value else 0)
        outside = ImageChops.multiply(changed, ImageChops.invert(allowed))
        count = outside.histogram()[255]
    if count:
        raise ValueError("Výsledek porušuje ochranu pixelů.")
    return result, {
        "pixel_integrity": "verified", "protected_changed_pixels": count,
        "geometry": "unverified", "geometry_reason": "Geometrie fotografie vyžaduje vlastní ověření.",
        "conflict_pixels": conflict.histogram()[255], "geometry_locked_pixels": geometry.histogram()[255],
        "base_sha256": hashlib.sha256(base_bytes).hexdigest(), "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(), "result_sha256": hashlib.sha256(result).hexdigest(),
        "mask_sha256": hashlib.sha256(allowed.tobytes()).hexdigest(),
        "width": base.width, "height": base.height, "adapter": "local_color",
    }
