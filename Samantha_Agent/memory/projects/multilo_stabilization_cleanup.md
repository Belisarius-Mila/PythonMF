# MultiLO: stabilizace návratu do kokpitu a cleanup screenů

## Stav

V projektu `MultiLO` se opakovaně řešilo zamrzání aplikace při návratu z výukových modulů zpět do kokpitu, hlavně v režimech s editací textu.

Soubory dotčené v této části práce:

- `MultiLO/step2_cockpit.py`
- `MultiLO/screen_frames.py`

Během práce bylo nutné opakovaně shodit zamrzlé okno aplikace a spustit cockpit znovu.

## Cíl

Cílem bylo stabilizovat návrat z jednotlivých screenů zpět do kokpitu a snížit riziko zamrzání, hlavně při práci s textovými vstupy ve screens jako:

- Dny v týdnu,
- Měsíce,
- Psaní režimy.

## Důležité poznatky

### CTkEntry byl pravděpodobný zdroj zamrzání

Opakovaný problém se vracel při aktivní editaci textu a návratu do kokpitu.

Závěr:

- `CTkEntry` v psacích režimech je rizikový,
- pro stabilitu návratu je bezpečnější použít obyčejné `tk.Entry`.

Provedená změna:

- v `Dny v týdnu -> Psaní` byly `CTkEntry` nahrazeny za `tk.Entry`,
- stejně v `Měsíce -> Psaní`.

Tento zásah byl pravděpodobně stabilnější než předchozí kosmetické nebo timing workaroundy.

### Navigace v horní liště

V modulu `Dny v týdnu` bylo tlačítko `Zpět do kokpitu` přesunuto nahoru na stejnou vizuální úroveň jako:

- Uživatel,
- Jazyk,
- Režim,
- Soubor.

Následně bylo graficky doladěno, aby sedělo ve stejném rytmu a výškové logice jako ostatní bloky.

### Lifecycle screenů byl křehký

Původní stabilizační review našlo tato rizika:

1. `retired_screens` v kokpitu mohly akumulovat staré screeny.
2. `FlashcardsScreen` při návratu do kokpitu nerušil naplánované `after(...)` callbacky.
3. Testy nekryly lifecycle návratu screenů.

Bylo potvrzeno, že workaround bez explicitního `destroy()` je časovaná bomba, protože v procesu mohou zůstávat celé widget stromy, obrázky, TTS objekty a interní stav starých screenů.

## Rozhodnutí

### Stabilizační patch

Byl proveden stabilizační patch před další prací na Step 8.

Patch:

- odstranil akumulaci `retired_screens`,
- zavedl jednotné `cleanup()` API pro screeny,
- upravil `_defer_show_cockpit()`,
- doplnil cleanup do `FlashcardsScreen`,
- sjednotil cleanup wrappery u dalších screenů.

### Cockpit

V `step2_cockpit.py` byla upravena logika návratu:

- `_defer_show_cockpit()` zavolá `cleanup()` na aktivním screenu, pokud existuje,
- potom screen schová,
- postaví kokpit,
- starý screen zničí až potom.

Pořadí bylo vyhodnoceno jako správné:

```text
cleanup -> pack_forget -> after_idle(_show_cockpit) -> after_idle(destroy)
```

Použit byl defensivní přístup:

```python
getattr(old_screen, "cleanup", None)
```

To umožní fungování i v případě, že někdy přibude screen bez `cleanup()`.

### FlashcardsScreen

Do `FlashcardsScreen` bylo doplněno `cleanup()`.

Důležité:

- ruší `quiz_advance_job`,
- `destroy()` volá `cleanup()`,
- tlačítko `Zpět do kokpitu` už nejde přímo na `on_back`,
- návrat jde přes `_back()`, který cleanup spustí.

Tím byla uzavřena regrese kolem pending `after(...)` callbacků ve flashcards.

### Ostatní screeny

Sjednocené `cleanup()` wrappery byly doplněny nebo sjednoceny u:

- `ColorsScreen`,
- `NumbersScreen`,
- `WeekdaysScreen`,
- `MonthsScreen`.

`destroy()` nyní používá `cleanup()` místo duplicitního teardown kódu.

### WeekdaysScreen

U `WeekdaysScreen._back()` bylo doplněno přesnější ukončení editace před odchodem:

- `entry.selection_clear()`,
- `entry.icursor("end")`,
- `state=disabled`,
- přesun focusu.

Použití `after(50)` bylo vyhodnoceno jako konzervativnější než `after(1)` a méně agresivní vůči Tk event handlerům.

### MonthsScreen follow-up

Byla zachycena připomínka, že `MonthsScreen._back()` sice nepřímo cleanup dostane přes kokpit, ale je lepší, aby byl cleanup lokální.

Byl doplněn drobný fix:

- `MonthsScreen._back()` volá vlastní `cleanup()` přímo lokálně,
- není závislý jen na kokpitu.

## Ověření

Po stabilizačním patchi proběhlo:

```bash
python3 -m py_compile MultiLO/screen_frames.py
```

A testy:

```text
Ran 8 tests, OK
```

Po drobném fixu `MonthsScreen._back()`:

- `py_compile` prošel.

Doporučený ruční retest:

1. Zvířata -> Vyber 1 ze 3 -> odpověď -> Zpět do kokpitu
2. Barvy -> autoplay -> Zpět do kokpitu
3. Číslovky -> autoplay -> Zpět do kokpitu
4. Dny v týdnu -> Sekvence -> Zpět do kokpitu
5. Dny v týdnu -> Psaní -> editace -> Zpět do kokpitu
6. Měsíce -> Psaní -> editace -> Zpět do kokpitu

Nejproblematičtější historicky byl bod 5.

## Otevřené otázky

- Doplnit lifecycle smoke testy až jako samostatný krok.
- Headless Tk lifecycle testy jsou možné, ale nejsou malý rychlý patch.
- Nepokračovat v rozsáhlých zásazích do navigace, dokud se stabilita nepotvrdí ručním retestem.
- Při budoucím přidání nových screenů vyžadovat `cleanup()` API od začátku.
- U nových psacích režimů raději používat `tk.Entry` místo `CTkEntry`.

## Další kroky pro Codex

Před úpravami MultiLO vždy přečíst:

- `MultiLO/step2_cockpit.py`
- `MultiLO/screen_frames.py`
- tento memory soubor

Dávat pozor na lifecycle screenů.

Nepřidávat nové `after(...)` callbacky bez možnosti jejich zrušení v `cleanup()`.

U každého nového screenu nebo režimu zkontrolovat:

- zda má `cleanup`,
- zda `destroy` volá `cleanup`,
- zda back cesta neobchází `cleanup`.

Pokud se řeší zamrzání při návratu, nejdříve zkontrolovat:

- Entry,
- focus,
- pending callbacks,
- destroy lifecycle.

Nepoužívat `retired_screens` jako nekonečný sklad starých screenů.

Nemíchat stabilizační patch s většími UX změnami.

Po změnách spustit minimálně:

```bash
python3 -m py_compile MultiLO/screen_frames.py
```

A dostupné testy MultiLO plus ruční retest návratu do kokpitu.

## Zdroj

Souhrn ChatGPT/Codex konverzace k MultiLO, stabilizaci zamrzání při návratu do kokpitu, přesunu tlačítka návratu, nahrazení `CTkEntry` za `tk.Entry`, review lifecycle screenů, zavedení `cleanup()` API a opravě `MonthsScreen._back()`.

