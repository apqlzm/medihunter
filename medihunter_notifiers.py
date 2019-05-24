from notifiers import get_notifier
from notifiers.exceptions import BadArguments

pushover = get_notifier('pushover')
telegram = get_notifier('telegram')

def pushover_notify(message):
    try:
        r = pushover.notify(message=message)
    except BadArguments as e:
        print(f'Pushover failed\n{e}')
        return

    if r.status != 'Success':
        print(f'Pushover notification failed:\n{r.errors}')


def telegram_notify(message):
    try:
        r = telegram.notify(message=message,
                            parse_mode='html')
    except BadArguments as e:
        print(f'Telegram notifications require NOTIFIERS_TELEGRAM_CHAT_ID'
              f' and NOTIFIERS_TELEGRAM_TOKEN environments to be exported. Detailed exception:\n{e}')
        return

    if r.status != 'Success':
        print(f'Telegram notification failed\n{r.errors}')
