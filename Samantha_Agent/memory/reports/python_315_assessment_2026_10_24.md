# Python 3.15 — posouzení 2026-10-24 09:48 CEST

Doporučení: Python 3.15.1 je vhodný pro samostatný paralelní pilot.
Běžící Samanthu/Camino zatím nepřepínat. V tomto kroku nebyl instalován
Python, balíčky ani změněné .venv, PATH, LaunchAgents nebo konfigurace služeb.

## Zjištěný stav

Oficiální [Python 3.15.1](https://www.python.org/downloads/release/python-3151/)
vyšel 21. 10. 2026 jako první údržbové a bezpečnostní vydání. Verze 3.15.0
vyšla 9. 10.; řídit se aktuálním vydáním, nikoli starším plánem PEP 790.
[Přehled změn a portování](https://docs.python.org/3.15/whatsnew/3.15.html).

Místní .venv skutečně používá Python 3.12.0rc3, tedy předprodukční sestavení.
Python 3.15 zde nenalezen. Není důvod zachovávat RC navždy, migrace ale
zahrnuje prostředí všech služeb a závislosti, nikoli jen spuštění instalátoru.

Metadata z oficiálního PyPI byla ověřena pro 18 relevantních položek.
Šest přesných místních verzí nemá kompatibilní hotový wheel pro pravidelný
CPython 3.15 na tomto arm64 Macu. Novější vydání jej mají:

| Balíček | Místní verze bez odpovídajícího wheelu | Ověřená novější verze s wheelem |
| --- | --- | --- |
| pydantic-core | [2.46.4](https://pypi.org/project/pydantic-core/2.46.4/#files) | [2.50.1](https://pypi.org/project/pydantic-core/2.50.1/#files) |
| Pillow | [12.2.0](https://pypi.org/project/Pillow/12.2.0/#files) | [13.0.0](https://pypi.org/project/Pillow/13.0.0/#files) |
| pillow-heif | [1.3.0](https://pypi.org/project/pillow-heif/1.3.0/#files) | [1.8.1](https://pypi.org/project/pillow-heif/1.8.1/#files) |
| numpy | [2.4.6](https://pypi.org/project/numpy/2.4.6/#files) | [2.5.4](https://pypi.org/project/numpy/2.5.4/#files) |
| jiter | [0.14.0](https://pypi.org/project/jiter/0.14.0/#files) | [0.18.0](https://pypi.org/project/jiter/0.18.0/#files) |
| cffi | [2.0.0](https://pypi.org/project/cffi/2.0.0/#files) | [2.1.1](https://pypi.org/project/cffi/2.1.1/#files) |

Zdrojem každého řádku je veřejné https://pypi.org/pypi/NAZEV/VERZE/json;
konkrétní URL a tagy jsou v soukromém technickém dokladu. Requires-Python
samo není důkaz binární ani runtime kompatibility.

Binární dry-run resolveru pro oba requirements soubory, CPython 3.15.1,
GIL a kompatibilní macOS/arm64 tagy prošel: 50 balíčků, bez kompilace
nebo instalace. Neomezené requirements ovšem vybraly také OpenAI SDK 3.37.0
namísto místního 2.36.0 a Agents 0.24.0 namísto 0.17.2. To není nutná
vlastnost Pythonu 3.15; pro úzký pilot mají tyto změny zůstat oddělené.
Druhý binární dry-run s výslovným zachováním OpenAI 2.36.0 a Agents
0.17.2 také prošel (50 balíčků). Pilot tedy nemusí měnit hlavní AI SDK.
Nativní závislosti však vyžadují novější kompatibilní vydání a skutečné testy.

## Smysluplný pilot

1. Případně instalovat oficiální stabilní 3.15.1 vedle stávajícího Pythonu;
   zachovat starý interpreter, .venv i explicitní cesty běžících služeb.
2. Vytvořit nové oddělené testovací prostředí s běžným GIL interpreterem,
   nikoli python3.15t/free-threaded variantou. Uložit přesný seznam závislostí
   a držet OpenAI/Agents SDK beze změny, pokud resolver i testy dovolí.
3. Spustit plnou bránu a izolované HTTP/SQLite/media/FFmpeg testy, přenos
   dvou projektů a start/stop nové testovací instance. Ověřit kódování UTF-8
   a nativní moduly. Dry-run neověřuje skutečný běh na novém interpreteru.
4. Teprve po této přejímce a samostatném schválení naplánovat přepnutí
   konkrétních služeb s novou zálohou a možností vrátit původní prostředí.

Novější Python nevyřeší sám přepínání projektů ani nevytvoří rychlejší
FFmpeg export. Toto posouzení nepovoluje změnu provozu ani systémový upgrade.
Důkazy: data/private/camino_projects_20261024/python315_*.json a *.log.
