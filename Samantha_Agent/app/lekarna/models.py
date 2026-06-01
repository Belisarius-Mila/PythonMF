from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DomaciLek:
    nazev: str
    ucinna_latka: str
    forma: str
    sila: str
    kategorie: str
    pouziti: str
    pro_koho: str
    nevhodne_pro_koho: str
    expirace: str
    mnozstvi: str
    umisteni: str
    overeno_z_letaku: str
    stav_obalu: str
    jistota_cteni: str
    nutno_overit: str
    zdroj: str
    poznamky: str
    PIL_Short: str
    PIL_Source: str
    PIL_Checked_Date: str
    PIL_Match_Status: str
    Search_Tags: str


@dataclass(frozen=True)
class DomaciLekMatch:
    lek: DomaciLek
    score: int
    reasons: tuple[str, ...]
    warnings: tuple[str, ...]
