Benzi voice test

Tato slozka obsahuje lokalni testovaci sadu ceskych ukazek pro Benziho.

Duvod:
- na tomto Macu je dostupny jen hlas Zuzana
- neni zde edge-tts ani dalsi lokalni ceske hlasy
- proto porovnavame ruzne rychlosti a ruzne formulace vet

Obsah:
- generate_samples.sh : znovu vygeneruje vsechny audio ukazky
- index.html : jednoducha stranka pro poslech
- audio/*.m4a : vygenerovane ukazky

Pouziti:
1. Spust generovani: ./generate_samples.sh
2. Otevri index.html pres jednoduchy lokalni server nebo v prohlizeci
3. Vyber, ktera varianta je nejprijatelnejsi

Doporuceni:
- pokud nebude Zuzana dost dobra, dalsi krok je prejit na predgenerovane audio
  z cloudove sluzby nebo na rucne namluvene vety
