from notifiers import get_notifier
from notifiers.exceptions import BadArguments
from os import environ
from xmpp import *

pushover = get_notifier('pushover')
telegram = get_notifier('telegram')

def pushover_notify(message, title: str = None):
    try:
        if title is None:
            r = pushover.notify(message=message)
        else:
            r = pushover.notify(message=message, title=title)
    except BadArguments as e:
        print(f'Pushover failed\n{e}')
        return

    if r.status != 'Success':
        print(f'Pushover notification failed:\n{r.errors}')


def telegram_notify(message, title: str = None):
    try:
        if title:
            message = f"<b>{title}</b>\n{message}"

        r = telegram.notify(message=message,
                            parse_mode='html')
    except BadArguments as e:
        print(f'Telegram notifications require NOTIFIERS_TELEGRAM_CHAT_ID'
              f' and NOTIFIERS_TELEGRAM_TOKEN environments to be exported. Detailed exception:\n{e}')
        return

    if r.status != 'Success':
        print(f'Telegram notification failed\n{r.errors}')

def xmpp_notify(message):
    try:
        jid = environ['NOTIFIERS_XMPP_JID']
        password = environ['NOTIFIERS_XMPP_PASSWORD']
        receiver = environ['NOTIFIERS_XMPP_RECEIVER']

        r = xmpp.protocol.JID(jid)
        conn = xmpp.Client(server = r.getDomain(), debug = False)
        if (
            (not conn.connect()) or
            (not conn.auth(user = r.getNode(), password = password, resource = r.getResource())) or
            (not conn.send(xmpp.protocol.Message(to = receiver, body = message)))
           ):
            print(f'XMPP notification failed')
    except KeyError as e:
        print(f'XMPP notifications require NOTIFIERS_XMPP_JID, NOTIFIERS_XMPP_PASSWORD'
              f' and NOTIFIERS_XMPP_RECEIVER to be exported. Detailed exception:\n{e}')
