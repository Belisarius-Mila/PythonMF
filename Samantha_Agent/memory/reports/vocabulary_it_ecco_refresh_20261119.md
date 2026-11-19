## 2026-11-19 09:30 CET — Schválené delší věty bez Ecco a nové větné audio

Hotovo: Zapracovaných90 náhrad bez Ecco a jedna rozšířená nabídka ručníku;
přesně dvě věty s Ecco zůstávají (#0215 a #0282). Všech91 upravených vět má
6–9 slov a3–5 různých stávajících ilustrací.1116 hesel/2631 obrazových vazeb.
182 nových větných IT/CZ MP3 (Elsa/Vlasta,-10 %), všech4422 starších MP3
bajtově zachovaných. Samostatné slovní audio, identity, ilustrace, původní
CSV, ostatních1025 vět a osobní A–D zachované; žádné nové heslo/obrázek.

Rozhodnutí: Míla schválil celý návrh z Downloads a zadal „OK, vše p+n“.
Publikaci provede jediná registrovaná role release_executor/Terra pro
project-vocabulary-it na GitHub Pages. Předchozí společné vydání d2a42b9a
je dokončené a neopakuje se; nynější vydání má vlastní stabilní identitu.

Další krok: Dokončit programovou bránu, jediný lokální commit a registrované
submit_release(wait=True). Přesný finální SHA, brána a výsledek publikace
jsou výhradně v private/vocabulary_it_ecco_20261119/completion.json a původní
release_result.json. Tento zápis před zmrazením vydání není potvrzení push.

Navrhované další kroky: Mílův poslech a fyzická iPhone přejímka. LEDA1–2
zůstávají samostatně odložené. Při nejistém vydání ověřit stejný job bez retry.

Technický důkaz:182/182 nových nahrávek plně dekódovaných FFmpeg,187/187
místních HTTP souborů přesných; před/po všechny4422 starší MP3 shodné.
Safari Mac: nové IT/CZ věty a obrázky čistého stolu a ručníku, přehrání,
pauza/stop a návrat velké slovní karty. Tři obsahové regrese navíc chrání
přesný rozsah91, dvojici Ecco, homografy a audio; historické šedesátkové
kontroly obnovují předchozí stav pouze přes schválené změny. Finální bránu
vybírá program, její výsledek je v completion.json. HTTP/JS/Safari Mac nejsou
fyzická iPhone ani úplná lidská akustická přejímka. Cockpit se nerestartuje.

Schválený návrh: Vocabulary_IT_navrh_nahrad_vet_Ecco_2026-11-19.txt.
Úplná implementovaná změna vět, původních znění a obrazových vazeb:
VocabularyIT/batches/ecco_refresh_20261119.json.
