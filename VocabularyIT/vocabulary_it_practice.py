"""Build reviewed spelling/picture practice metadata without changing vocabulary."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPELLING = Path(__file__).with_name('vocabulary_it_spelling.json')
DATA = ROOT / 'docs/data/vocabulary-it-v2.json'
OUTPUT = ROOT / 'docs/data/vocabulary-it-quiz.json'
# Conservative, editorial exclusions: related pictures must not compete.
CONFLICTS = {
    'young-woman': 'amica|fidanzata|figlia|ragazza|sorella|signorina|Giulia|Luisa|Margherita',
    'young-man': 'figlio|fratello|Giovanni|Luca',
    'female-relative': 'madre|zia|nonna',
    'male-relative': 'padre|zio|nonno',
    'niece-nephew': 'nipote|figlio|figlia',
    'doctor': 'dottore|medico|ospedale',
    'nationality': 'tedesco|francese|inglese|italiano|ceco|romano|russo|slovacco|straniero',
    'personal-pronoun': 'io|tu|lui|Lei|lei|voi|noi|loro|me|te|ci|gli',
    'possessive': 'mio|mia|tuo|tua',
    'indefinite-article': 'un|una',
    'demonstrative': 'questo|quelle',
    'near': 'vicino|vicino a|qua|ecco',
    'far': 'lontano|laggiù|là|lì',
    'now': 'ora|adesso|subito|già',
    'right': 'a destra|destro',
    'left': 'a sinistra|sinistro',
    'more-less': 'troppo|molto|quanto|quante|abbastanza|poco|meno',
    'little': "po'|un po’|poco|poco fa",
    'certainty': 'sicuro|certo|certamente|naturalmente|davvero|infatti|vero',
    'approval': 'bene|benissimo|bravo|perfetto|buono|bello',
    'unpleasant': 'male|cattivo|brutto|odiare|nemico',
    'interest': 'interessante|interessare|interessarsi di|piacere|voglia|desiderare|vorrei|preferire',
    'unwell': 'malato|ammalato|stanco|debole|fare male',
    'free-busy': 'libero|occupato|impegnato',
    'intensity': 'forte|forza|piano|lentamente',
    'time-unit': 'minuto|ora|giorno|settimana|mese|anno|tempo',
    'calendar': 'lunedì|martedì|mercoledì|giovedì|venerdì|sabato|domenica|tutti i giorni',
    'evening': 'stasera|buonanotte',
    'tomorrow': 'domani|domattina|dopodomani',
    'thank-you': 'grazie|Di niente.|per niente|niente',
    'congratulation': 'Congratulazioni!|congratulazione|auguri|compleanno|festa',
    'request': 'per favore|favore|permesso|pregare|aiuto',
    'sorry': 'scusare|scusarsi',
    'departure': 'a presto|arrivederci|andare|venire|vengo|tornare|uscita',
    'stay': 'stare|restare|trovarsi|abita',
    'start-end': 'cominciare|finire',
    'knowledge': 'conoscere|capire|comprendere|so|ricordare',
    'speaking': 'parlare|rispondere|chiamare|chiamarsi|mi chiamo',
    'hearing': 'sentire|sentirsi|ascoltare',
    'seeing': 'vedere|guardare',
    'teaching': 'lezione|insegnare|esercizio|corso|frequentare',
    'word-language': 'parola|vocabolo|lingua|dizionario|interprete',
    'walking': 'fare due passi|camminare|passo|gita|viaggio|vacanza, vacanze',
    'wash': 'lavare|lavarsi|bagno|asciugamano|pulito',
    'sport-race': 'gara|vinti|vincere|automobilismo|formula',
    'ball-sport': 'calcio|pallacanestro|pallavolo|giocare',
    'fish': 'pescare|pescato',
    'coat': 'giacca|cappotto',
    'neck-accessory': 'sciarpa|collana',
    'sweet-bakery': 'torta|brioche|éclair|biscotto|dolce',
    'citrus': 'pompelmo|arancia|limone|spremuta',
    'food-meal': 'cibo|cena|mangiare|carne',
    'cook': 'cucinare|cuoca|forno',
    'coffee-drink': 'caffè|vino|bicchiere|sete',
    'shop': 'mercato|negozio|panificio|libreria|comprare|vendere',
    'home': 'casa|camera|albergo|coinquilino',
    'road': 'strada|via|viale|piazza|quartiere|paese',
    'car': 'macchina|auto',
    'flying': 'aereo|volo',
    'book': 'libro|rivista|leggere|tascabile',
    'picture': 'foto|disegnare',
    'money': 'portafoglio|carta di credito|in contanti|pagare|costare|euro|stipendio|scontrino',
    'weather': 'coperto|piovere|cielo|grigio|freddo|caldo',
    'number': 'numero|zero|otto|nove',
}
COLORS = {'giallo', 'grigio', 'marrone', 'viola'}

# This reviewed content batch keeps picture exclusions next to its source meanings.
_LEDA_CHANGES = json.loads((Path(__file__).with_name('batches') / 'leda_20261116.json').read_text())['practiceChanges']
COLORS.update(_LEDA_CHANGES['colors'])
for _group, _words in _LEDA_CHANGES['extend'].items():
    CONFLICTS[_group] += '|' + _words
CONFLICTS.update(_LEDA_CHANGES['new'])

_LOOP_CHANGES = json.loads((Path(__file__).with_name('batches') / 'loop_refresh_20261118.json').read_text())['practiceChanges']
for _group, _words in _LOOP_CHANGES['extend'].items():
    CONFLICTS[_group] += '|' + _words
CONFLICTS.update(_LOOP_CHANGES['new'])




def build(data, spelling):
    items = data['items']
    if data.get('language') != 'it' or spelling.get('language') != 'it' or spelling.get('schemaVersion') != 1:
        raise ValueError('Cizí nebo neplatný jazykový podklad.')
    if set(spelling['entries']) != {i['uid'] for i in items}:
        raise ValueError('Slabikový katalog nepokrývá přesně současné karty.')
    known = {i['it'].casefold() for i in items}
    for group, words in CONFLICTS.items():
        if set(w.casefold() for w in words.split('|')) - known:
            raise ValueError('Neznámé heslo v obrazové skupině: ' + group)
    entries = {}
    homographs = {}
    for item in items:
        source = spelling['entries'][item['uid']]
        pieces = source.get('pieces')
        if (source.get('it') != item['it'] or source.get('cz') != item['cz']
                or not isinstance(pieces, list) or not 1 <= len(pieces) <= 120
                or any(not isinstance(p, str) or not p for p in pieces) or ''.join(pieces) != item['it']
                or type(source.get('reviewed')) is not bool):
            raise ValueError('Nepřesné slabiky nebo změněné heslo: ' + item['uid'])
        if not source['reviewed'] and pieces != [item['it']]:
            raise ValueError('Neověřené dělení se nesmí použít: ' + item['uid'])
        if item['it'] in homographs and homographs[item['it']] != pieces:
            raise ValueError('Stejné heslo má různá dělení.')
        homographs[item['it']] = pieces
        entries[item['uid']] = {
            'uid': item['uid'], 'it': item['it'], 'cz': item['cz'], 'image': item['image'], 'thumbnail': item['thumbnail'],
            'pieces': pieces, 'reviewed': source['reviewed'],
            'displayMode': 'syllables' if source['reviewed'] else 'whole-word',
            'format': 'colors' if item['it'] in COLORS else 'objects',
            'conflicts': [group for group, words in CONFLICTS.items() if item['it'].casefold() in {w.casefold() for w in words.split('|')}],
        }
    return {'schemaVersion': 1, 'language': 'it', 'kind': 'spelling-pictures',
            'description': 'Ověřený zápis a konzervativní vyloučení zaměnitelných obrázků. Dvě nejisté přejímky zobrazené celé.',
            'spellingSources': spelling.get('sources', []), 'entries': entries}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    data = json.loads(DATA.read_text()); spelling = json.loads(SPELLING.read_text())
    if spelling.get('sourceDataSha256') != hashlib.sha256(DATA.read_bytes()).hexdigest():
        raise ValueError('Slabiková revize vznikla z jiného exportu.')
    result = build(data, spelling)
    if args.write:
        # Use the existing atomic local writer; no synthesis is invoked.
        from vocabulary_it_audio import atomic
        atomic(OUTPUT, (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode())
    print(json.dumps({'cards': len(result['entries']), 'reviewed': sum(e['reviewed'] for e in result['entries'].values()), 'written': args.write}))


if __name__ == '__main__':
    main()
