# medihunter

Narzędzia służy do automatycznego wyszukiwania wizyt u lekarzy. Szczególnie przydaje się gdy wizyty są trudno dostępne ;)

**Działa z pythonem w wersji 3.6+**

<p align="center">
    <img src="https://apqlzm.github.io/theme/images/icons/search-every-minute.svg">
</p>

## Instalacja

Aktywujemy virtualenva (opcjonalnie choć zalecane)

```bash
source /path/to/my/virtualenv/bin/activate
```

Przechodzimy do katalogu ze źródłem i odpalamy

```bash
pip install --editable .
```

Od teraz mamy dostępną w virtualenvie komendę **medihunter**

## Dostępne subkomendy

### show-params

Gdy wyszukujemy wizyty musimy podać miasto, placówkę medyczną, specjalizację (jaki to ma być lekarz), identyfikator lekarza (możliwość wybrania konkretnego lekarza), datę wizyty (wizyta zacznie się nie wcześniej niż ta data). Każdy z tych parametrów (z wyjątkiem daty) ma przypisany nr id. Żeby go poznać używamy do tego komendy *show-params*.

id specjalizacji

```bash
medihunter show-params -f specialization
```

id miast

```bash
medihunter show-params -f region
```

### find-appointment

Poszukajmy endokrynologa

```bash
medihunter find-appointment -s 27962
```

Oczywiście znalezienie wizyty do endokrynologa nie jest takie proste, więc ustawmy żeby wyszukiwarka sprawdzała czy jest coś dostępne co 5 minut

```bash
medihunter find-appointment -s 27962 -i 1
```

## Wyświetlanie pomocy

Ogólna pomoc

```bash
medihunter --help
```

Poszczególne subkomendy

```bash
medihunter find-appointment --help
medihunter show-params --help
```

## Domyślne ustawienia

### show-params

domyślnie -f jest ustawiony na *specialization*

### find-appointment

opcja|domyślna wartość
-----|----------------
-r, --region|Warszawa 
-s, --specialization|Medicover Express - przeziębienie, grypa
-c, --clinic|wszystkie jakie są w regionie/mieście
-o, --doctor|wszuscy lekarze
-d, --start-date|data bieżąca
-i, --interval|brak
