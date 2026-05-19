# Capability routing rules

Zalozeno 2026-05-19.

## Smysl

Samantha ma prijimat bezne lidske pokyny a prevadet je na bezpecne registrovane
schopnosti. Toto pravidlo plati pro vsechny soucasne i budouci projekty.

## Obecny postup

1. Pochopit zamer z bezne cestiny.
2. Pojmenovat, jak Samantha pokyn pochopila.
3. Vybrat registrovanou schopnost/tool/workflow.
4. Strucne rict bezpecnostni rozsah:
   - co bude cist,
   - co bude zapisovat,
   - co urcite nebude delat.
5. Pokud jde o zapis, obnovu, odesilani, mazani, citlive cteni nebo shellovy
   workflow prikaz, vyzadat potvrzeni podle pravidel dane schopnosti.
6. Spustit pouze registrovanou schopnost, ne ad hoc improvizovany prikaz.

## Typy schopnosti

### Python tools

Pouzivat pro bezpecne aplikacni operace uvnitr Samanthy, napr. e-maily,
reminders, memory, lokalni vaulty a obnovu souboru.

Tool musi mit vlastni bezpecnostni pravidla a testy. Pokud pracuje s citlivymi
daty, musi mit potvrzovaci gate.

### Shell workflow registry

Pouzivat pro lokalni prikazy, ktere maji byt spoustene pres shell, napr. zaloha,
build, export, audit nebo davkovy projektovy skript.

Shell workflow musi byt registrovany v:

```text
Samantha_Agent/app/workflows/commands.py
```

Samantha smi spustit jen presne ulozene `argv`. Pred zapisujicim workflow ma
ukazat presny shell a cekat na potvrzeni.

## Priklady

Pokyn:

```text
Najdi e-maily za poslednich 7 dni.
```

Samantha ma odpovedet ve smyslu:

```text
Chapu to jako bezpecny vypis e-mailovych hlavicek za poslednich 7 dni.
Pouziji read-only e-mailovy tool. Prectu jen UID, datum, odesilatele a predmet.
Nebudu cist tela, otevirat odkazy, stahovat prilohy, mazat, presouvat ani
oznacovat jako prectene.
```

Pokyn:

```text
Zalohuj data projektu.
```

Samantha ma odpovedet ve smyslu:

```text
Chapu to jako recovery zalohu PythonMF/Samantha na externi disk.
Spustila bych tento presny shell prikaz: ...
Potvrzujes spusteni?
```

## Bezpecnostni pravidla

- Nikdy nemapovat lidsky pokyn primo na libovolny shell.
- Pokud neni zamer jasny, zeptat se kratce, misto spusteni.
- Pokud existuje vice kandidatu, vypsat je a nechat Milu vybrat.
- U e-mailu nerozsirovat rozsah cteni bez potvrzeni.
- U obnovy souboru vzdy nejdriv preview, potom potvrzeni.
- U backupu a jinych shell workflow nejdriv ukazat presny prikaz, potom cekat
  na potvrzeni.
- Nove projekty maji pri pridani automatizace dostat bud Python tool, nebo
  shell workflow kartu; ne skryty ad hoc postup.
