# HA-07 — Oprava pokračování po Stop


## 2026-11-15 21:26 CET — Oprava HA-07: pokračování ve vlastněné zastavené práci

Hotovo: Po potvrzeném Stop se u ověřené rozpracované práce nabízí Pokračovat
ve vývoji. Po jednorázovém potvrzení následující nový pokyn převezme zachované
změny stejného pracovního proudu. Původní přerušený tah zůstává přerušený;
nový tah má novou identitu a journal odkazuje na původní práci. Opakovaný
požadavek nezakládá druhý modelový tah. Znovupřipojení zachová i dirty workspace.
Rozhodnutí: Míla zadal odstranění chyby po Stop při aktivaci Vocabulary IT.
Oprava je v terminálovém main; nezahrnuje dokončení ani začlenění rozpracované
aktivace. Push a runtime nasazení vyžadují samostatné p+n podle AGENTS.md.
Další krok: Po cílené bráně vytvořit lokální commit opravy. Před nasazením
vyřešit registrovaným servisním postupem publikační blokaci zachovaného
profilového WIP; nic nepřeklasifikovat na hotové a nic nezahodit.
Navrhované další kroky: Po schváleném nasazení zkusit skutečné pokračování
aktivace jedním novým povoleným pokynem. HA-09 zůstává samostatný plán.
Technický důkaz: HTTP Stop → výslovné pokračování → další Stop zachovává
soubory a vlastnictví. Ověřený parent musí mít shodné workstream/thread/turn,
kanonický terminal_confirmed a trvalý interrupted záznam, odpovídající
ownership marker i seznam změn. Nesoulad, cizí WIP, nejisté doručení,
chybějící nové oprávnění a starý parent jsou odmítnuté před modelem.
Při známém selhání před dispatch se obnoví původní ownership. Po posunu main
se dirty clone nesynchronizuje; vývoj smí pokračovat na svém původním
základu s odloženou integrací. Běžné čistotní a integrační brány se nemění.
Finální lokální důkaz: data/private/ha07_resume_fix_20261115/completion.json.
Rizika: Pokračování není replay ani rollback. Rozpracované změny vyžadují
svůj dokončovací a integrační postup. Pád v nejistém okně zůstává fail-closed
pro servisní ověření. Podpora se vztahuje na ověřený primární Human–Adam WIP.
Živá UI/modelová přejímka následuje až po zvlášť schváleném nasazení.

Regrese: test původního HA-07 pokrýval nový poradní tah po Stop; skutečný
zapisovací tah ponechal dirty WIP a narazil na _assert_target_workspace.
Nový scénář ověřuje celý ProfileManager/Service/SessionHub/WorkController/HTTP
průchod. Server nabízí interrupted_work_continuation; POST work/start nese
continue_from_client_message_id spolu s write_intent=true. Neuděluje oprávnění
libovolnému dirty workspace. Ownership pokračování vzniká před modelovým
odesláním, předchozí výsledek není předstíraně dokončený a automatický
checkpoint přerušeného výsledku se nespouští.

Skutečný Vocabulary IT WIP obsahuje pět změněných souborů v soukromém profilu;
jejich výchozí SHA-256 jsou jen v private preserved_wip.json. Oprava se jich
nedotýká a nenasazuje nedokončenou aktivaci. Finální ověření porovná jejich
obsah i počet. Root main může být po commitu čistý a profil nadále dirty;
nejde o GitHub batch pending samotného profilu ani o ztracená data.
