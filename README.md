# medihunter

Narzędzia służy do automatycznego wyszukiwania wizyt u lekarzy. Szczególnie przydaje się gdy wizyty są trudno dostępne ;)

**Działa z pythonem w wersji 3.6+**

<p align="center">
    <img src="https://apqlzm.github.io/theme/images/icons/search-every-minute.svg">
</p>

## Wstęp

Dostępne są dwie wersje skryptu

* **medihunter_pushover.py** - ma funkcje powiadomień pushover, możliwość wyszukiwania kilku klinik i kilku specjalistów jednocześnie. Kod wymaga refaktoru i w związku z tym nie będzie rozwijany. Z czasem planuje go usunąć.  
* **medihunter.py** - tu dodawane są nowe funkcjonalności. Na chwilę obecną (2019-05-22) można ustawić powiadomienia pushover i w telegramie.

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

a może chcemy poszukać konkretnych endokrynolgów o ID: 12345 i 0987? **tylko w medicover_pushover.py**

```bash
medihunter find-appointment -s 27962 -o 12345 -o 0987
```

a może po prostu szukamy dowolnego internisty w przychodniach blisko nas w Atrium i na Prostej? **tylko w medicover_pushover.py**

```bash
medihunter find-appointment -s 9 -c 174 -c 49088
```

Lub można dodać bezpośrednio do Crontaba jak poniżej **wpis w cronie działa tylko z medicover_pushover.py**

- będzie uruchamiany między 6tą a 23cią co 5 minut
- -s - szuka Ortopedy dla dorosłych
- -c 174 -c 6896 tylko w centrum Warszawa Atrium i Warszawa Inflancka
Będzie korzystał z podanych parametrów użytkownika Medicoveru i Pushover do wysyłania powiadomień
- crontab zapisze logi w /var/log/medihunter.log

```bash
*/5 6-23 * * * /usr/bin/python3.7 /home/user/medihunter.py find-appointment -s 163 -c 174 -c 6896 --user MEDICOVER_USER --password MEDICOVER_PASS --pushover_msgtitle 'Ortopeda Centrum' --pushover_token PUSHOVER_TOKEN --pushover_user PUSHOVER_USER >> /var/log/medihunter.log 2>&1
```

### my-plan

Ściąga i zapisuje dostępne usługi wraz z informacjami na temat tego czy są dostępne w ramach wykupionego pakietu, a jeśli nie to czy mamy na nie jakieś zniżki. Niektóre usługi mają limity, to też powinno być tu widoczne. Plik wynikowy ma format  tsv (Tab-separated_values). Przykład użycia:

```bash
medihunter my-plan --user mylogin --password mypassword
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

dotyczy **medicover_pushover.py**

Poprzez podanie parametrów do powiadomień Poshover https://pushover.net/ możliwe jest przekazywanie powiadomień na wizytę bezpośrednio do aplikacji. Należy podać minimalnie parametry --pushover_token oraz --pushover_user

## Domyślne ustawienia

### show-params

domyślnie -f jest ustawiony na *specialization*

### find-appointment

TODO: _Poniższe opcje aktualne tylko dla medihunter_pushover.py_

opcja|domyślna wartość
-----|----------------
-r, --region|Warszawa
-b, --bookingtype|2, Typ wizyty 2 = Konsultacja (domyślnie), 1 = Badanie diagnostyczne
-s, --specialization|brak Specjalizacja, podać w przypadku gdy Typ wizyty to Konsultacja (bookingtype = 2 domyślnie)
-e, --service|brak, Typ/identyfikator usługi, podać w przypadku gdy Typ wizyty to usługa (bookingtype = 1), działa analogicznie do specjalizacji 
-c, --clinic|wszystkie jakie są w regionie/mieście, można użyć parametru wielokrotnie w celu szukania wizyt w konkretnych klinikach
-o, --doctor|wszyscy lekarze, można użyć parametru wielokrotnie w celu sprawdzenie kilku lekarzy
-d, --start-date|data bieżąca (format: YYYY-mm-dd)
-f, --end-date|brak (format: YYYY-mm-dd), dostępna tylko w medihunter.py
-a, --start-time|"0:00" (format: hh:mm), dostępna tylko w medihunter.py
-g, --end-time|"23:59" (format: hh:mm), dostępna tylko w medihunter.py
-j, --days-ahead| 1 = pokazuje wizyty dla pierwszego znalezionego dnia, dostępna tylko w medihunter.py
-i, --interval|brak
--disable-phone-search|brak, Pozwala pominąć wizyty telefoniczne w wyszukiwaniu, dostępna tylko w medihunter.py
--pushover_token|brak, Pushover Application Token
--pushover_user|brak, Pushover user Token
--pushover_device|brak, None nazwa device w Pushover domyślnie pusta=wszystkie
--pushover_msgtitle|brak - prefix dodawany przed tytułem powiadomienia
-t, --notification-title|brak, dostępna tylko w medihunter.py, wspierana tylko przez Pushover

## Pushover w medihunter.py

Żeby działały powiadomienia pushover trzeba zrobić eksport (wartości ustawiamy swoje):

```shell
# bash
export NOTIFIERS_PUSHOVER_TOKEN=avykwnqc8ohyk73mo1bsuggsm3r4qf
export NOTIFIERS_PUSHOVER_USER=s4g1zoewbzseogp4knrapx23k9yi95
```

lub

```shell
# fish
set -x NOTIFIERS_PUSHOVER_TOKEN avykwnqc8ohyk73mo1bsuggsm3r4qf
set -x NOTIFIERS_PUSHOVER_USER s4g1zoewbzseogp4knrapx23k9yi95
```

Teraz możemy wyszukać wizyty np. tak:

```shell
medihunter find-appointment -n pushover -r 204 -s 4798 --user 00000 --password psw1234 -i 1 -d 2019-05-15
```

## Telegram w medihunter.py

Musimy utworzyć bota do powiadomień i kanał na który będą przesyłane powiadomienia. Szczegóły jak to zrobić można znaleźć pod adresem https://core.telegram.org/bots

Jak już mamy to gotowe to wystarczy zrobić eksport dwóch zmiennych (wartości ustawiamy swoje):

```shell
# bash
export NOTIFIERS_TELEGRAM_CHAT_ID=avykwnqc8ohyk73mo1bsuggsm3r4qf
export NOTIFIERS_TELEGRAM_TOKEN=740885363:AdFRNFTIFTc4hC1flAuXE-dyik_Udm6Ma3o
```

lub

```shell
# fish
set -x NOTIFIERS_TELEGRAM_CHAT_ID avykwnqc8ohyk73mo1bsuggsm3r4qf
set -x NOTIFIERS_TELEGRAM_TOKEN 740885363:AdFRNFTIFTc4hC1flAuXE-dyik_Udm6Ma3o
```

Teraz możemy wyszukać wizyty i otrzymać notyfikacje w Telegramie:

```shell
medihunter find-appointment -r 204 -s 4798 --user 00000 --password psw1234 -i 1 -d 2019-05-22 -n telegram
```