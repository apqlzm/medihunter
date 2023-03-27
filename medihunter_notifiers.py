from notifiers import get_notifier
from notifiers.exceptions import BadArguments
from os import environ
from xmpp import *
import requests

pushbullet = get_notifier('pushbullet')
pushover = get_notifier('pushover')
telegram = get_notifier('telegram')

def pushbullet_notify(message, title: str = None):
    try:
        if title is None:
            r = pushbullet.notify(message=message)
        else:
            r = pushbullet.notify(message=message, title=title)
    except BadArguments as e:
        print(f'Pushbullet failed\n{e}')
        return

    if r.status != 'Success':
        print(f'Pushbullet notification failed:\n{r.errors}')

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

def gotify_notify(message, title: str = None):
    try:
        host = environ['GOTIFY_HOST']
        token = environ['GOTIFY_TOKEN']
    except KeyError as e:
        print(f'GOTIFY notifications require GOTIFY_HOST (base url with port),'
              f' GOTIFY_TOKEN to be exported. Detailed exception:\n{e}')
        return

    try:
        prio = int(environ['GOTIFY_PRIORITY'])
    except (KeyError, ValueError):
        prio = 5

    if title is None:
        title = "medihunter"

    try:
        resp = requests.post(host+'/message?token='+token, json={
            "message": message,
            "priority": int(prio),
            "title": title
        })

    except requests.exceptions.RequestException as e:
        print(f'GOTIFY notification failed:\n{e}')
