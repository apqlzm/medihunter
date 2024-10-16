# medihunter

Інструмент призначено для автоматичного пошуку візитів до лікарів. Особливо корисно, коли візити важко знайти ;)

**Працює з Python версії 3.6+**

<p align="center">  
    <img src="https://apqlzm.github.io/theme/images/icons/search-every-minute.svg">  
</p>

## Вступ

Доступні дві версії скрипту

* **medihunter_pushover.py** - має функції pushover сповіщень, можливість шукати кілька клінік і кілька спеціалістів одночасно. Код потребує рефакторингу і тому не буде розвиватися. З часом планую його видалити.
* **medihunter.py** - тут додаються нові функціональності. Наразі (2021-07-11) можна встановити сповіщення pushover, у Telegram та через xmpp.

## Встановлення

Активуємо virtualenv (опціонально, але рекомендовано)

```bash  
source /path/to/my/virtualenv/bin/activate  
```  
або у Windows cmd з віртуальним середовищем, створеним бібліотекою venv

```  
SourceToVirtEnv\Scripts\activate.bat  
```

Переходимо до каталогу з джерелом і запускаємо

```bash  
pip install --editable .  
```

Тепер у нашому virtualenv доступна команда: `medihunter`

Якщо не хочемо кожного разу вводити логін і пароль і/або не хочемо вказувати їх відкрито в терміналі через `--user login --password пароль`, то можемо зберегти їх у файлі `.env`:  
```  
MEDICOVER_USER=логін  
MEDICOVER_PASS=пароль  
```

Найпростіше копіювати приклад файлу `.env.example` з головного каталогу як `.env` і заповнити в ньому дані.

## Доступні підкоманди

### show-params

Коли шукаємо візит, потрібно вказати місто, медичний заклад, спеціалізацію (який це має бути лікар), ідентифікатор лікаря (можливість обрати конкретного лікаря), дату візиту (візит розпочнеться не раніше цієї дати). Кожен з цих параметрів (крім дати) має присвоєний id номер. Щоб його дізнатися, використовуємо для цього команду *show-params*.

id міст

```bash  
medihunter show-params -f region  
```

id спеціалізації

```bash  
medihunter show-params -f specialization -r 204  
```

### find-appointment

Знайдемо ендокринолога

```bash  
medihunter find-appointment -s 27962  
```

Звичайно, знаходження візиту до ендокринолога не таке просте, тому встановімо, щоб пошуковик перевіряв чи є щось доступне кожні 5 хвилин

```bash  
medihunter find-appointment -s 27962 -i 5  
```

а може хочемо пошукати конкретних ендокринологів з ID: 12345 і 0987? **лише в medicover_pushover.py**

```bash  
medihunter find-appointment -s 27962 -o 12345 -o 0987  
```

а може просто шукаємо будь-якого терапевта в клініках зручно для нас в Атріумі та на Простій? **лише в medicover_pushover.py**

```bash  
medihunter find-appointment -s 9 -c 174 -c 49088  
```

а що якщо хочемо знайти візит до будь-якого ортопеда в Тримісті протягом наступних двох тижнів, а не за місяць? **без дати початку не працює**

```bash  
medihunter find-appointment -s 163 -d 2021-12-19 -f 2022-12-31 -r 200  
```

Або можна додати безпосередньо до Crontab як нижче **запис у crontab працює лише з medicover_pushover.py**

- буде запускатися між 6тою та 23тю кожні 5 хвилин  
- -s - шукає ортопеда для дорослих  
- -c 174 -c 6896 лише в центрі Варшави Атріум і Варшава Інфланцька  
Буде використовувати задані параметри користувача Medicover і Pushover для надсилання сповіщень  
- crontab збереже логи у /var/log/medihunter.log

```bash  
*/5 6-23 * * * /usr/bin/python3.7 /home/user/medihunter.py find-appointment -s 163 -c 174 -c 6896 --user MEDICOVER_USER --password MEDICOVER_PASS --pushover_msgtitle 'Ортопед Центр' --pushover_token PUSHOVER_TOKEN --pushover_user PUSHOVER_USER >> /var/log/medihunter.log 2>&1  
```

### my-plan

Завантажує і зберігає доступні послуги разом з інформацією про те, чи доступні вони в рамках придбаного пакету, а якщо ні, то чи маємо на них якісь знижки. Деякі послуги мають ліміти, це теж має бути тут видно. Вихідний файл має формат tsv (Tab-separated values). Приклад використання:

```bash  
medihunter my-plan --user mylogin --password mypassword  
```

## Відображення довідки

Загальна довідка

```bash  
medihunter --help  
```

Окремі підкоманди

```bash  
medihunter find-appointment --help  
medihunter show-params --help  
```

## Сповіщення Pushover

стосується **medicover_pushover.py**

За допомогою встановлення параметрів для сповіщень Poshover https://pushover.net/ можливо передавати сповіщення про візит прямо до додатку. Як мінімум потрібно вказати параметри --pushover_token та --pushover_user

## Стандартні налаштування

### show-params

за замовчуванням -f встановлено на *specialization*

### find-appointment

TODO: _Наступні опції актуальні лише для medihunter_pushover.py_

опція|стандартне значення  
-----|----------------  
-r, --region|Варшава  
-b, --bookingtype|2, Тип візиту 2 = Консультація (за замовчуванням), 1 = Діагностичне обстеження  
-s, --specialization|немає Спеціалізація, вказати у випадку, якщо Тип візиту - Консультація (bookingtype = 2 за замовчуванням)  
-e, --service|немає, Тип/ідентифікатор послуги, вказати у випадку, якщо Тип візиту - послуга (bookingtype = 1), працює аналогічно до спеціалізації  
-c, --clinic|всі, що є в регіоні/місті, можна використовувати параметр багатократно для пошуку візитів у конкретних клініках  
-o, --doctor|всі лікарі, можна використовувати параметр багатократно для перевірки кількох лікарів  
-d, --start-date|поточна дата (формат: YYYY-mm-dd)  
-f, --end-date|немає (формат: YYYY-mm-dd), доступна лише в medihunter.py  
-a, --start-time|"0:00" (формат: hh:mm), доступна лише в medihunter.py  
-g, --end-time|"23:59" (формат: hh:mm), доступна лише в medihunter.py  
-j, --days-ahead| 1 = показує візити на перший знайдений день, доступна лише в medihunter.py  
-i, --interval|немає  
--disable-phone-search|немає, Дозволяє пропустити телефонні візити в пошуку, доступна лише в medihunter.py  
--pushover_token|немає, Pushover Application Token  
--pushover_user|немає, Pushover user Token  
--pushover_device|немає, None назва пристрою в Pushover за замовчуванням пуста=всі  
--pushover_msgtitle|немає - префікс додається перед заголовком сповіщення  
-t, --notification-title|немає, доступна лише в medihunter.py, підтримується лише Pushover, Telegram і Gotify

## Pushbullet у medihunter.py

Для роботи сповіщень pushbullet потрібно виконати експорт (задаємо свої значення):

```shell  
# bash  
export NOTIFIERS_PUSHBULLET_TOKEN=avykwnqc8ohyk73mo1bsuggsm3r4qf  
```

або

```shell  
# fish  
set -x NOTIFIERS_PUSHBULLET_TOKEN avykwnqc8ohyk73mo1bsuggsm3r4qf  
```

Тепер можемо шукати візити, наприклад, так:

```shell  
medihunter find-appointment -n pushbullet -r 204 -s 4798 --user 00000 --password psw1234 -i 1 -d 2019-05-15  
```

## Pushover у medihunter.py

Для роботи сповіщень pushover потрібно виконати експорт (задаємо свої значення):

```shell  
# bash  
export NOTIFIERS_PUSHOVER_TOKEN=avykwnqc8ohyk73mo1bsuggsm3r4qf  
export NOTIFIERS_PUSHOVER_USER=s4g1zoewbzseogp4knrapx23k9yi95  
```

або

```shell  
# fish  
set -x NOTIFIERS_PUSHOVER_TOKEN avykwnqc8ohyk73mo1bsuggsm3r4qf  
set -x NOTIFIERS_PUSHOVER_USER s4g1zoewbzseogp4knrapx23k9yi95  
```

Тепер можемо шукати візити, наприклад, так:

```shell  
medihunter find-appointment -n pushover -r 204 -s 4798 --user 00000 --password psw1234 -i 1 -d 2019-05-15  
```

## Telegram у medihunter.py

Потрібно створити бота для сповіщень і канал, на який будуть відправлятися сповіщення. Деталі, як це зробити, можна знайти за адресою https://core.telegram.org/bots

Як тільки маємо це готове, достатньо виконати експорт двох змінних (задаємо свої значення):

```shell  
# bash  
export NOTIFIERS_TELEGRAM_CHAT_ID=avykwnqc8ohyk73mo1bsuggsm3r4qf  
export NOTIFIERS_TELEGRAM_TOKEN=740885363:AdFRNFTIFTc4hC1flAuXE-dyik_Udm6Ma3o  
```

або

```shell  
# fish  
set -x NOTIFIERS_TELEGRAM_CHAT_ID avykwnqc8ohyk73mo1bsuggsm3r4qf  
set -x NOTIFIERS_TELEGRAM_TOKEN 740885363:AdFRNFTIFTc4hC1flAuXE-dyik_Udm6Ma3o  
```

або у Windows з venv  
```shell  
set NOTIFIERS_TELEGRAM_CHAT_ID=avykwnqc8ohyk73mo1bsuggsm3r4qf  
set NOTIFIERS_TELEGRAM_TOKEN=740885363:AdFRNFTIFTc4hC1flAuXE-dyik_Udm6Ma3o  
```

Тепер можемо шукати візити і отримувати сповіщення в Telegram:

```shell  
medihunter find-appointment -r 204 -s 4798 --user 00000 --password psw1234 -i 1 -d 2019-05-22 -n telegram  
```

## XMPP у medihunter.py

Потрібно мати 2 зареєстровані акаунти XMPP:  
- перший для надсилання повідомлень, у випадку знаходження візитів, що відповідають заданим критеріям пошуку,  
- другий для отримання повідомлень із сповіщеннями, на якому будемо залогінені в будь-якому клієнті, що підтримує XMPP (наприклад, на комп'ютері/мобільному пристрої).

Експортуємо назви обох акаунтів XMPP і пароль для логіна до першого з акаунтів (задаємо свої значення):

```shell  
# bash  
export NOTIFIERS_XMPP_JID='sender_notifications@example.com'  
export NOTIFIERS_XMPP_PASSWORD='password_sender_notifications'  
export NOTIFIERS_XMPP_RECEIVER='receiver_notifications@example.com'  
```

або

```shell  
# fish  
set -x NOTIFIERS_XMPP_JID 'sender_notifications@example.com'  
set -x NOTIFIERS_XMPP_PASSWORD 'password_sender_notifications'  
set -x NOTIFIERS_XMPP_RECEIVER 'receiver_notifications@example.com'  
```

Тепер можемо шукати візити і отримувати сповіщення через XMPP:

```shell  
medihunter find-appointment -r 204 -s 4798 --user 00000 --password psw1234 -i 1 -d 2019-05-22 -n xmpp  
```

## Gotify у medihunter.py

[Gotify](https://gotify.net/) є простим сервісом для відправлення сповіщень push головним чином на пристрої з системою Android.  
Відрізняється від інших подібних програм тим, що є повністю відкритим кодом та призначений для хостингу на власному сервері.

Для використання цього методу сповіщень, потрібно встановити декілька змінних оточення:

```shell  
# bash  
export GOTIFY_TOKEN=AbCDeFg2yvapfPA  
export GOTIFY_HOST=https://gotify.my-server.com  
```

або

```shell  
# fish  
set -x GOTIFY_TOKEN 'AbCDeFg2yvapfPA'  
set -x GOTIFY_HOST 'https://gotify.my-server.com'  
```

або у Windows з venv  
```shell  
set GOTIFY_TOKEN=AbCDeFg2yvapfPA  
set GOTIFY_HOST=https://gotify.my-server.com  
```

В також існує опціональна змінна `GOTIFY_PRIORITY`, яка дозволяє встановити пріоритет сповіщення (за замовчуванням `5`).

Тепер можемо шукати візити і отримувати сповіщення через Gotify:

```shell  
medihunter find-appointment -r 204 -s 4798 --user 00000 --password psw1234 -i 1 -d 2019-05-22 -n gotify  
```

## Docker  
Для запуску програми в контейнері спочатку потрібно побудувати образ

```shell  
docker build -t medihunter .  
```

Далі запускаємо контейнер за допомогою команди run  
```shell  
docker run -it medihunter find-appointment --user 00000 --password psw1234 -r 204 -s 4798  
```

Можливо також використати змінні оточення чи файл .env  
```shell  
docker run -it  -e MEDICOVER_USER=00000 -e MEDICOVER_PASS=psw1234 medihunter find-appointment -r 204 -s 4798d

docker run -it --env-file=.env medihunter find-appointment -r 204 -s 4798  
```