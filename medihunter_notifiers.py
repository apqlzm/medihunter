from notifiers import get_notifier
from notifiers.exceptions import BadArguments

pushover = get_notifier('pushover')

def pushover_notify(message):
    try:
        r = pushover.notify(message=message)
    except BadArguments as e:
        print(f'Pushover failed {e}')
        return

    if r.status != 'Success':
        print(f'Pushover notification failed {r.errors}')

