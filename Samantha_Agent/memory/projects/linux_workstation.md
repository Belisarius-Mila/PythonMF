# Linux / instalace a konfigurace

## Cíl

Samostatný konzultační projekt pro bezpečnou instalaci Linuxu, následnou
konfiguraci a běžnou práci na starším stolním počítači.

## Výchozí hardware

- Intel Pentium G4560, Kaby Lake, 2 jádra / 4 vlákna, 64 bitů
- 8 GB RAM
- původní klasický HDD
- integrovaná grafika Intel HD Graphics
- samostatná AMD Radeon R5 435
- zapnutá hardwarová virtualizace
- připravovaný Kingston A400 480 GB, 2,5 palce, SATA SSD

## Dosavadní rozhodnutí

- Největší praktické zrychlení přinese nový SSD.
- Linux se má nejprve instalovat samostatně na nový SSD.
- Původní HDD s Windows se při první instalaci fyzicky odpojí a zachová beze
  změny jako bezpečná návratová cesta.
- Po ověření Linuxu se HDD znovu připojí; o případném odstranění Windows se
  rozhodne až později a pouze výslovně.
- Předběžný vhodný kandidát pro tento hardware je Linux Mint Xfce, ale konečný
  výběr se potvrdí až před vytvořením instalačního USB.

## Bezpečnostní hranice

- Před instalací zálohovat uživatelská data a ověřit, který fyzický disk je SSD.
- Windows ani původní HDD nemazat bez výslovného potvrzení Míly.
- Při první instalaci držet původní HDD fyzicky odpojený, aby instalátor nemohl
  změnit jeho oddíly ani zavaděč.
- Než se odstraní návratová cesta, ověřit grafiku, síť, zvuk, tiskárnu a všechny
  potřebné programy v Linuxu.

## Nejbližší krok

Po dodání SSD připravit ověřené živé USB, spustit Linux bez instalace a otestovat
základní hardware. Teprve potom instalovat na nový SSD.
