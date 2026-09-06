Spojíme seznam, cyklus, podmínku a kreslení. Každé číslo v seznamu body je výsledek jednoho pokusu. Za alespoň 10 bodů získá pokus zelený kruh, jinak oranžový.

Podmínka hodnota >= 10 znamená „hodnota je větší nebo rovna deseti“. Proměnná splneno začíná nulou. U úspěšného pokusu ji zvětšíme o jedna pomocí splneno = splneno + 1.

Proměnná x určuje vodorovnou polohu kruhu. Po každém kreslení ji zvětšíme o 150, takže další pokus bude vedle. Kruh i posun patří do cyklu, ale až za celé if/else.

Závěrečný print() je mimo cyklus a vypíše součet úspěšných pokusů.
