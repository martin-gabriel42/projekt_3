# main.py

Tento skript automatizuje stažení a zpracování volebních výsledků z webu ČSÚ pro parlamentní volby 2017.
Všechny územní celky, s kterýmy skript může pracovat se nachází na následujícím odkazu.

https://www.volby.cz/pls/ps2017nss/ps3?xjazyk=CZ

Skript stáhne volební data daného volebního okresu (případně všech okresů) a vytvoří csv soubor s výsledky.
Pro každý okres je vytvořen jeden soubor. Tento výsledný soubor obsahuje pro každou obec v okresu následující informace:

-kód obce (code)
-název obce (municipality)
-počet voličů v seznamu (registered voters)
-celkový počet hlasů (total votes)
-počet platných hlasů (valid votes)
-všechny strany, které v okresu kandidovaly a odpovídající počet hlasů pro tuto stranu

## požadavky na spuštění skriptu

Python 3.6+
Potřebné knihovny třetích stran jsou uvedené v souboru requirements.txt
Knihovny lze instalovat následujícím způsobem:

    pip install -r requirements.txt
    

## návod na spouštění skriptu a vstupní parametry

Skript lze spouštět pomocí dvou nebo jednoho argumentu, podle toho, čeho chce uživatel dosáhnout.
Skript dokáže stáhnout data buď jednoho konkrétního okresu, nebo všech okresů na výše uvedeném odkazu.

Pro stáhnutí dat jednoho okresu:

    Skript se spouští dvěma argumenty. Prvním argumentem je odkaz na daný okres. Druhým argumentem je jméno výstupního souboru.

    -vstupní parametry `<URL> <jméno_souboru>`: Skript stáhne výsledky pro konkrétní okres

    Příklad:
    
        python main.py "https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=2&xnumnuts=2101" výsledky

        -Skript vygeneruje soubor výsledky.csv, který bude obsahovat volební data z daného odkazu (v tomto případě okres Benešov).
        -Jméno výstupního souboru může nebo nemusí obsahovat příponu .csv, skript akceptuje obě možnosti.
        -Pokud je odkaz nebo jméno výstupního souboru neplatné, skript vypíše varování a ukončí se.

    !!! POZOR !!!
        Skript automaticky přepíše existující soubory se shodným jménem výstupního souboru.

Pro stáhnutí dat všech okresů:

    Skript se spouští jedním argumentem.

    -vstupní parametr `ALL`: Skript stáhne výsledky pro všechny okresy. Jakýkoliv jiný parametr je neplatný.

    Příklad:

        python main.py ALL

        -Skript vygeneruje pro každý okres samostatný soubor do právě používané složky (cwd).
        -Jména výstupních souborů mají formát {jméno okresu}_results.csv
        
    !!! POZOR !!!
        Skript automaticky přepíše existující soubory se shodným jménem výstupních souborů.
        Tato možnost spouštění obvykle bude trvat několik minut, než se stáhnou data ze všech okresů.