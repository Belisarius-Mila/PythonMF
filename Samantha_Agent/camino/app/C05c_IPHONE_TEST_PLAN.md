# C05c — fyzický plán stavového UX na iPhonu

Aktuální příprava: Camino 0.1.0 (4) je podepsané, strict ověřené, nainstalované
bez odinstalace a spuštěné na iPhonu 14 Plus.

Aktualizace 2026-09-25: Míla potvrdil po SideStore importu bez kabelu spuštění
původního Camina, dostupnost starých dat a přehrávání — tato část A je PASS.
Čtyři stavové sekce a části B/C nejsou tímto nově ověřené. Podle
[cestovního plánu](../docs/TRAVEL_MVP_PLAN.md) je spojíme do krátkého průchodu
M2/M4; neblokují lokální vývoj Vieweru a data netestujeme znovu bez důvodu.

## Předpoklady

- Podepsaná aktualizace stejného bundle ID je nainstalovaná bez odinstalace.
- Před fyzickým průchodem musí být zastavené pořizování i přehrávání.
- C05b session-owned server zůstává vypnutý. Jeho nový start, URL a token mají
  vlastní náhled a potvrzení; pro základní C05c průchod nejsou potřeba.

## A — zachování dat a čtyři sekce

1. Otevři po aktualizaci dnešní i starší Momenty a potvrď, že data zůstala.
2. Otevři **Uložení a přenosy**.
3. Potvrď samostatné sekce **Telefon**, **Mac**, **Další záloha** a **AI**.
4. Telefon musí uvést počet místních Momentů. Mac nesmí tento počet vydávat za
   počet souborů nebo segmentů.
5. **Další záloha** musí uvést, že zatím není ověřená. **AI** musí uvést, že
   zatím není zapnutá a že přepis není záloha.

Výsledek: `PASS / FAIL`, případně přesný odlišný text.

## B — nezávislost místního záznamu

1. Bez spouštění serveru vytvoř krátkou neutrální značku nebo textový Moment.
2. Potvrď, že se okamžitě zvýší nebo zachová pravdivý stav Telefonu.
3. Mac smí čekat nebo být nedostupný; Další záloha ani AI se nesmějí samy
   změnit na ověřené.

Výsledek: `PASS / FAIL`.

## C — regresní pause

1. Zapni **Pozastavit přenosy**, ukonči aplikaci a znovu ji otevři.
2. Potvrď, že pause drží, ale nový místní záznam lze dál vytvořit a číst.
3. Obnov přenosy a potvrď, že se změnila pouze osa Macu; Další záloha a AI
   zůstaly nezávislé.

Výsledek: `PASS / FAIL`.

## Hranice T054/T055

Produkční fyzický build nesmí používat syntetické stavové fixture. Proto lze
nyní fyzicky potvrdit oddělené výchozí osy a jejich UX, ale ne skutečnou
variantu „AI hotová bez zálohy“ ani ověřený snapshot další zálohy. T054 a T055
zůstávají na fyzickém zařízení otevřené do C06b/C07; automatické scénáře se
nezapisují jako produkční PASS.
