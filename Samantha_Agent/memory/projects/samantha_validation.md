# Samantha — ověření a rychlost vydání

Proud: `project-samantha-infrastructure`. Kanonické provedení a hranice:
`../technical/validation_policy.md`; rozhodovací historie v existujícím
`../tvbcp/workstreams/project-samantha-infrastructure.md`.

2026-11-15: Míla schválil implementaci jediné programové politiky místo
modelového rozhodování, zda zopakovat všechny testy. Terminál, checkpoint,
GitHub batch, Luna i deploy sdílejí runner a místní podepsané účtenky.
Plná brána chrání neznámý/rizikový kód; pevná úzká mapa dovoluje cílené testy
dokumentů/UI pouze nad ověřeným základem. Platnost původní plné brány24h.
Zápis checkpointového handoffu nesmí sám opakovat již ověřený kód.

Místní diagnostika před změnou: poslední Vocabulary p+n16:38, z toho brána14:28;
poslední celá unit sada780s. Čtyři Git/workspace moduly190,8s. Verzovaný strom
1,573GiB, samotný Python13,1MiB. Média se v tomto kroku nepřesouvají.

Vývoj je místní; runtime vyžaduje samostatně povolené vydání. Závěrečný
testovací důkaz a délky jsou v soukromé účtence `data/private/validation_policy_20261115/completion.json`
a v metadatech Gitu. Publikační, živé a fyzické přejímky tento vývoj nenahrazuje.
