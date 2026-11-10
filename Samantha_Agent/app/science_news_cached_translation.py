"""Registered, nonpaid transfer of one reviewed translation and explicit save."""
from __future__ import annotations

import hashlib

from app.science_news import ID, public_url


def attach_and_save(store, *, item_id, source_url, source_text, source_sha256,
                    translation, translation_sha256, permission, request_id, confirmed=False):
    if confirmed is not True:
        raise ValueError("Uložení konkrétního překladu vyžaduje souhlas.")
    if not ID.fullmatch(str(item_id)) or not ID.fullmatch(str(request_id)):
        raise ValueError("Neplatná identita zprávy nebo uložení.")
    if (not isinstance(source_text, str) or not 200 <= len(source_text) <= 50000
            or not isinstance(translation, str) or not .3 * len(source_text) <= len(translation) <= 4 * len(source_text)
            or hashlib.sha256(source_text.encode()).hexdigest() != source_sha256
            or hashlib.sha256(translation.encode()).hexdigest() != translation_sha256
            or permission not in ("cc-by", "cc-by-sa", "cc0", "public-domain", "user-provided")):
        raise ValueError("Zdroj, překlad nebo oprávnění nejsou ověřené.")
    source_url = public_url(source_url)
    with store.transaction() as state:
        item = state["items"].get(item_id)
        if not item or item["source_url"] != source_url:
            raise ValueError("Překlad patří jinému zdroji.")
        if item.get("decision") not in (None, "save"):
            raise ValueError("Vyřízenou zprávu neobnovuji.")
        if item.get("operation") not in (None, request_id):
            raise ValueError("Nejprve ověř předchozí operaci této zprávy.")
        if any(state["jobs"].get(prefix + item_id, {}).get("state") in ("running", "delivery_unknown", "attention")
               for prefix in ("translation_", "model_translation_")):
            raise ValueError("Předchozí překlad potřebuje ověření; nepřepisuji jej.")
        if item.get("translation") not in (None, "", translation) or item.get("source_text") not in (None, "", source_text):
            raise ValueError("Zpráva již obsahuje jiný zdroj nebo překlad.")
        if item.get("decision") == "save":
            if item.get("translation") != translation:
                raise ValueError("Existující uloženou kartu je nutné upravit samostatně.")
        else:
            article = store.archive_root / "articles" / ("science_" + item_id[3:]) / "article.txt"
            if any(p.is_symlink() for p in (article, *article.parents)) or (article.exists() and translation not in article.read_text()):
                raise ValueError("Existující kartu bez tohoto překladu nepřepisuji.")
            item.update(source_text=source_text, translation_permission=permission, translation=translation)
    # Existing durable archive protocol owns the actual save, follow and replay.
    return store.decide(item_id, "save", request_id)
