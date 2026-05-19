# Matýsek: koncept anglické hry pro pětileté dítě

## Stav

V projektu `MatysekANJ` existovaly nebo vznikly různé verze anglické výukové aplikace:

- `anglictina_matysek.py`
- `anglictina_matysek_V2.py`
- `anglictina_matysek_V3.py`

Původní verze byla příliš textová a školní. Bylo rozhodnuto, že pro Matýska, kterému je 5 let, neumí číst a neumí anglicky, není vhodné stavět aplikaci jako klasické menu miniher nebo testů.

Úvodní promluva byla upravena tak, aby nezačínala automaticky po startu aplikace, ale jen po kliknutí na tlačítko sovy.

## Cíl

Cílem je vytvořit anglickou hru pro pětiletého kluka, která učí přirozeně přes obrázky, klikání, hlas a příběh.

Hra nemá být školní test. Má být dobrodružství.

## Důležité poznatky

Zásadní principy:

- dítě neumí číst, takže hlavní komunikace musí být hlasem, obrázkem a akcí,
- co nejméně textu,
- žádné dlouhé instrukce,
- vždy jen jeden jasný cíl,
- maximálně několik voleb najednou,
- žádné trestání za chybu,
- při chybě jen jemně navést a zopakovat,
- odměnou má být objevování, hvězdičky, samolepky, rozsvícený svět, ne školní skóre,
- angličtina má být krátká a opakovaná v kontextu.

Původní návrh s oblastmi:

- barvy,
- čísla,
- zvířata,
- rodina,
- později jídlo, tělo, oblečení, hračky, dopravní prostředky.

První slovní zásoba:

- barvy: `red`, `blue`, `yellow`, `green`
- čísla: `one` až `five`
- zvířata: `dog`, `cat`, `duck`, `fish`, `horse`
- rodina: `mummy`, `daddy`, `baby`, `brother`, `grandma`
- hračky/věci: `ball`, `teddy`, `car`, `book`
- jídlo: `apple`, `banana`, `milk`, `cake`
- tělo: `eyes`, `nose`, `hands`, `feet`
- oblečení: `hat`, `shoes`, `T-shirt`

Odložit:

- složitější barvy jako `gray`, `brown`, `purple`, `white`,
- čísla 6 až 10,
- abstraktní mix úlohy,
- textové zadání typu `How many?`,
- skóre a streak jako hlavní motivaci.

## Rozhodnutí

Bylo navrženo nepřepisovat vše najednou. Nejprve vznikla stabilní jednoduchá verze `anglictina_matysek_V3.py`.

Technicky jednoduchý V3 model:

- pevné okno,
- jeden hlavní loop,
- jedna aktivní scéna,
- scény `home`, `lesson`, `reward`,
- univerzální typ kola pro všechny oblasti,
- maximálně 3 volby,
- žádný drag-and-drop v první verzi,
- žádné složité animace,
- žádný resizable layout,
- žádné odečítání bodů.

Datový princip:

- každá lekce generuje jen `RoundData`,
- renderer neřeší typ hry,
- barvy, čísla, zvířata a rodina jsou stejný mechanismus s jinými daty.

Doporučené datové třídy:

```python
@dataclass
class Choice:
    id: str
    label: str
    image_path: str | None = None
    color: tuple[int, int, int] | None = None
    count: int | None = None

@dataclass
class RoundData:
    pack: str
    prompt_cz: str
    prompt_en: str
    choices: list[Choice]
    correct_id: str

@dataclass
class AppState:
    scene: str = "home"
    current_pack: str | None = None
    round_data: RoundData | None = None
    stars: int = 0
    stickers: int = 0
    pending_next_at: float = 0.0
```

## Otevřené otázky

Později se ukázalo, že ani V3 se scénami a výběrem oblastí není dostatečně originální. Míla chce spíš příběhový obraz, ve kterém se kliká na objekty, ne obrazovky s výběrem her.

Proto vznikl nový směr `MMTX.py`, který má být samostatná jiná aplikace.

## Další kroky pro Codex

- Nepovažovat V3 za konečný směr.
- `anglictina_matysek_V3.py` nechat jako stabilní experiment, pokud Míla neřekne jinak.
- Nový hlavní směr je `MMTX.py`: příběhové scény, pozadí, klikací objekty, hotspoty.
- U Matýska vždy myslet na dítě 5 let, bez čtení.
- Zachovat technickou jednoduchost, protože projekt MultiLO měl v minulosti problémy se stabilitou.

## Zdroj

Souhrn ChatGPT/Codex konverzace k redesignu anglické hry pro Matýska, brainstorming vzdělávacích oblastí, návrh V3 a rozhodnutí směřovat k příběhovým scénám.

