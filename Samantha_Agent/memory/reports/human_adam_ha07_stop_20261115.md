# HA-07 — Zastavení přesné běžící práce


## 2026-11-15 19:39 CET — HA-07: zastavení přesné běžící práce, místně

Hotovo: Human–Adam má tlačítko Zastavit tuto práci. Přijetí žádosti je
oddělené od potvrzeného přerušení, dokončení, odmítnutí a neověřeného
výsledku. Rozepsaný další pokyn i upřesnění zůstávají; po žádosti se
obnoví ze sessionStorage pouze ve stejném rozsahu původní práce.
Potvrzené přerušení přežije reload i čtení novým serverovým vlastníkem.
Rozpracované soubory a jejich ownership zůstávají zachované.
Rozhodnutí: Míla schválil zahájení implementace HA-07. HA-08 je navazující
krok. Toto zadání nepovoluje push, runtime deploy ani placený živý pilot.
Další krok: Po cílené programové bráně lokální commit; samostatně schválené
p+n a omezená živá přejímka na Macu/iPhonu. Konečný lokální důkaz, přesné
počty a commit jsou v data/private/ha07_stop_20261115/completion.json.
Navrhované další kroky: HA-08 — spotřeba celé práce; dosud otevřené živé
ověření HA-06 a ergonomie telefonu. Žádné automatické rozšíření oprávnění.
Technický důkaz: Jediný turn/interrupt na původním klientovi, přesný
thread/turn/operation, původní scope/owner/generace/politika. Trvalá bariéra
před RPC, stabilní ID ha07-operation, žádný retry při ztrátě ACK/restartu.
Samotné ACK není zastavení; terminalita vyžaduje původní vstupní důkaz
a odpovídající turn/completed interrupted, uložené v kanonické relaci.
Přerušení nepředává částečný výsledek automatickému checkpointu/publikaci
ani importu médií. Nový výslovný pokyn po potvrzeném Stop funguje.
Testy pokrývají dokončení vítězící v závodu, dvojklik, odpojení, pád
volajícího, cizí scope/turn, drift oprávnění, chybějící journal, čtecí
recover, zachování zapisovacího WIP a skutečný izolovaný Unix/WebSocket.
Node osm scénářů; skutečný Edge nad kartou320/390/1280 bez přetékání,
tlačítko přibližně170×45px, zachování draftů/fokusu. Bez modelového tahu.
Rizika: Žádost není rollback už provedených účinků. Navazující checkpoint
nebo publikace mají vlastní běh; nemají bezpečné obecné přerušení a Stop
se pro ně neaktivuje. Nepodporovaný peer či ztracený vlastník nic neodesílá.
Syntetické ověření není živé převzetí sdíleného modelového tahu/iPhonu.

Protokolový vstup byl ověřen z místního CLI0.169.0 generate-json-schema:
TurnInterruptParams obsahuje threadId a turnId, odpověď je prázdný objekt.
Surové schema zůstává privátně pod ha07_stop_20261115/schema/.
