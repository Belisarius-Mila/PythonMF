Text "12" a číslo 12 nejsou stejný typ hodnoty. Z textu udělá celé číslo funkce int(): int("12") vrátí 12. int("ahoj") ale vyvolá chybu ValueError, protože tento text celé číslo nepředstavuje.

try označí blok, ve kterém očekávaná chyba může nastat. Pokud chyba nastane, Python přeskočí zbytek tohoto bloku a hledá odpovídající except. except ValueError zachytí právě tuto chybu, nikoli všechny možné problémy.

Pro vstup "12" převod uspěje a vypíše se Číslo: 12. Pro "ahoj" se řádek s výpisem čísla už neprovede; místo něj se vypíše zpráva v except. Cyklus potom pokračuje vstupem "5".

try a except jsou odsazené stejně. Jejich vnitřní řádky mají další čtyři mezery. Po try i except je dvojtečka.

Hodnoty dodáváme seznamem, protože učebna zatím nepodporuje interaktivní input(). U příkladu s ošetřenou chybou se celá úloha nezastaví červenou chybou.

DO DÍLNY
Přidej "-3", " 8 " a "3.5". První dva texty int převede; "3.5" není zápis celého čísla a vyvolá ValueError. Nevkládej obecné except bez uvedení chyby — mohlo by schovat i jinou programátorskou chybu.
