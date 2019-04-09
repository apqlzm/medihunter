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

a może chcemy poszukać konkretnych endokrynolgów o ID: 12345 i 0987 ?

```bash
medihunter find-appointment -s 27962 -o 12345 -o 0987
```

a może po prostu szukamy dowolnego internisty w przychodniach blisko nas w Atrium i na Prostej ?

```bash
medihunter find-appointment -s 9 -c 174 -c 49088
```

Lub można dodać bezpośrednio do Crontaba jak poniżej
- będzie uruchamiany między 6tą a 23cią co 5 minut
- -s - szuka Ortopedy dla dorosłych
- -c 174 -c 6896 tylko w centrum Warszawa Atrium i Warszawa Inflancka
Będzie korzystał z podanych parametrów użytkownika Medicoveru i Pushover do wysyłania powiadomień
- crontab zapisze logi w /var/log/medihunter.log

```bash
*/5 6-23 * * * /usr/bin/python3.7 /home/user/medihunter.py find-appointment -s 163 -c 174 -c 6896 --user MEDICOVER_USER --password MEDICOVER_PASS --pushover_msgtitle 'Ortopeda Centrum' --pushover_token PUSHOVER_TOKEN --pushover_user PUSHOVER_USER >> /var/log/medihunter.log 2>&1
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

## Powiadomienia Pushover

Poprzez podanie parametrów do powiadomień Poshover https://pushover.net/ możliwe jest przekazywanie powiadomień na wizytę bezpośrednio do aplikacji. Należy podać minimalnie parametry --pushover_token oraz --pushover_user


## Domyślne ustawienia

### show-params

domyślnie -f jest ustawiony na *specialization*

### find-appointment

opcja|domyślna wartość
-----|----------------
-r, --region|Warszawa 
-b, --bookingtype|2, Typ wizyty 2 = Konsultacja (domyślnie), 1 = Badanie diagnostyczne
-s, --specialization|brak Specjalizacja, podać w przypadku gdy Typ wizyty to Konsultacja (bookingtype = 2 domyślnie)
-e, --service|brak, Typ/identyfikator usługi, podać w przypadku gdy Typ wizyty to usługa (bookingtype = 1), działa analogicznie do specjalizacji 
-c, --clinic|wszystkie jakie są w regionie/mieście, można użyć parametru wielokrotnie w celu szukania wizyt w konkretnych klinikach
-o, --doctor|wszyscy lekarze, można użyć parametru wielokrotnie w celu sprawdzenie kilku lekarzy
-d, --start-date|data bieżąca (format: YYYY-mm-dd)
-i, --interval|brak
--pushover_token|brak, Pushover Application Token
--pushover_user|brak, Pushover user Token
--pushover_device|brak, None nazwa device w Pushover domyślnie pusta=wszystkie
--pushover_msgtitle|brak - prefix dodawany przed tytułem powiadomienia
