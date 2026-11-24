"""Clean room references plus one explicitly separate drawing guide."""
from __future__ import annotations

import io

from PIL import Image, ImageDraw

IMAGE_INPUT_PROTOCOL = "interior-images-v2"
MAX_SOURCE_IMAGES = 6

DRAWING_INPUT_INSTRUCTIONS = """
Obrazové vstupy mají v images očíslované role. working_clean je čistý pracovní
obrázek a určuje vzhled prostoru i úhel pohledu. drawing_guide je pouze jeho
kopie s kreslenými pokyny; clean_image_number odkazuje na čistý originál.
Pro obrazovou úpravu vycházej z čistého pracovního obrázku. Kopii s kresbou
používej jen k pochopení zamýšlených změn, ne jako další fotografii prostoru.
Značky nepatří do místnosti ani výsledku a nejsou přesnou maskou úprav.
Ostatní reference a společný půdorys si zachovávají vlastní význam; kresba je
nenahrazuje. Pracovní obrázek může být současně půdorysem (room_plan=true).
"""


def has_drawing_guide(draft):
    return bool(draft["image_source_id"] and draft["annotations"])


def prepare_image_inputs(store, project_id, room_id, room, draft, selected):
    """Preserve clean bytes and reference order; append the guide last."""
    inputs, manifest = [], []
    plan_id = room.get("room_basis", {}).get("plan_source_id", "")
    for index, source_id in enumerate(selected, 1):
        raw, _ = store.asset(project_id, room_id, source_id, "preview")
        working = source_id == draft["image_source_id"]
        inputs.append((source_id, raw))
        manifest.append({"number": index, "kind": room["sources"][source_id]["kind"],
                         "working_image": working, "room_plan": source_id == plan_id,
                         "role": "working_clean" if working else "room_plan" if source_id == plan_id else "reference"})
    if has_drawing_guide(draft):
        clean_index = selected.index(draft["image_source_id"])
        with Image.open(io.BytesIO(inputs[clean_index][1])) as source:
            image = source.convert("RGB")
        draw = ImageDraw.Draw(image)
        for stroke in draft["annotations"]:
            draw.line([(round(x * image.width), round(y * image.height)) for x, y in stroke],
                      fill="#d16d39", width=4)
        output = io.BytesIO()
        image.save(output, format="PNG")
        inputs.append((draft["image_source_id"], output.getvalue()))
        manifest.append({"number": len(inputs), "kind": manifest[clean_index]["kind"],
                         "working_image": False, "room_plan": False,
                         "role": "drawing_guide", "clean_image_number": clean_index + 1})
    return inputs, manifest
