# Kompaktní hlídání a akce e-mailů

Stav: místně hotové a cíleně ověřené; bez nového push/nasazení. 2026-11-14 21:03 CET.
Proud: UI pošty v Cockpitu; existující Cockpit handoff/TVBCP a e-mailová paměť.

Míla schválil dvě řady akcí (Odpovědět/Uložit do archivu, Hlídat záležitost/
Do kalendáře) a doplnil sbalení hlídaného velkého UI na název a Hlídáno.
Implementace zachovává původní handlery, digesty, potvrzení, čekání a obnovu.
Ignorovat, Příště nedůležité a Smazat z Cockpitu jsou pod Další akce.

Po potvrzeném založení se sbalí původní e-mailová karta i aktivní záležitost.
Nativní details/summary lze otevřít dotykem a klávesnicí. Pravidelný refresh
uchová ruční rozbalení/sbalení i Další akce. Po vyřízení se původní karta
zobrazí celá; obnovená generace začne znovu kompaktně. Neověřený zápis se
neprohlašuje za založené hlídání. DOM stav neukládá texty do localStorage.

Souhrnný řádek ukazuje Ke kontrole při nové zprávě, návrhu, termínu, neověřené
zdrojové vazbě či nerozhodnutém přiřazení. Nečerstvý běh a nejasné odeslání/uložení
jsou také viditelné ve stručném štítku. Běžný stav je jen název + Hlídáno.
Původní obsah, zdroj, historie, úprava i Vyřízeno zůstávají pod rozbalením.

Ověření:51 frontendových/HTTP testů PASS, včetně původních ochran odeslání,
konfliktů, obnovy, dvojího klepnutí a nových regresí sbalení/pollingu/stavů.
Browser320/390/1280 přes celé skutečné místní HTML a bezpečnostní hlavičky:
obě sbalené karty70px, žádné přetékání. Mezerník i klepnutí otevřou obsah;
create sbalí, refresh uchová, complete obnoví plnou kartu; koncept beze změny.
Jen2 syntetické POST (create/complete),0 produkčních POST/výjimek.
Screenshot390 vizuálně prohlédnutý. Finální statická brána před commitem.
Log email_compact_targeted_20261114.log; private email_compact_ui_20261114/.

Poslední doplnění štítku neověřeného uložení má novou Node i browserovou
regresi; finálních26 frontendových testů a nová statická brána PASS. Backend
souvisejících HTTP testů zůstává beze změny.

Runtime knihovny64e9897a se tímto místním vývojem nemění. UI má samostatně
čekající commity; nové p+n ani fyzická iPhone přejímka nejsou provedené.
Samostatný e-mailový TVBCP nebyl dohodnutý a nevzniká; celý e-mailový projekt
zůstává otevřený, A+C je stále po UI. Žádný IMAP/SMTP/model, aktivace nebo
hromadná změna živých zpráv není součástí této práce.
