""" This script contains pushover notification + all basic functionalities """

import json
import time
import shelve
from datetime import datetime
from pushover import Client

import click

from medicover_session import MedicoverSession, load_available_search_params


now = datetime.now()
now_formatted = now.strftime('%Y-%m-%dT02:00:00.000Z')
now_formatted_logging = now.strftime('%Y-%m-%d %H:%M:%S')

@click.command()
@click.option('--user', prompt=True)
@click.password_option(confirmation_prompt=False)
@click.option('--region', '-r', default=204, show_default=True)
@click.option('--bookingtype', '-b', default=2, show_default=True)
@click.option('--specialization', '-s', required=True)
@click.option('--service', '-e', default="")
@click.option('--clinic', '-c', multiple=True, default=['-1'])
@click.option('--doctor', '-o', multiple=True, default=['-1'])
@click.option('--start-date', '-d', default=now_formatted, show_default=True)
@click.option('--interval', '-i', default=0)
@click.option('--pushover_token')
@click.option('--pushover_user')
@click.option('--pushover_device')
@click.option('--pushover_msgtitle')
def find_appointment(
    user,
    password,
    region,
    bookingtype,
    specialization,
    service,
    clinic,
    doctor,
    start_date,
    interval,
    pushover_token,
    pushover_user,
    pushover_device,
    pushover_msgtitle
):

    counter = 0
    med_session = MedicoverSession(username=user, password=password)

    # Checking if pushover is enabled and notifications should be send later
    if pushover_user and pushover_token:
        try :
            client = Client(user_key=pushover_user, api_token=pushover_token)
            pushover_notification = True
        except Exception:
            click.secho('Pushover not initialized correctly', fg='red')
            return
    else :
        pushover_notification = False

    try :
        med_session.log_in()
    except Exception:
        click.secho('Unsuccessful logging in', fg='red')
        return

    click.echo(f'{now_formatted_logging}: Logged in {pushover_msgtitle}')

    med_session.load_search_form()  # TODO: can I get rid of it?

    while interval > 0 or counter < 1:
        notification = ""
        notificationcounter = 0
        for c in clinic:
            for d in doctor:
                appointments = med_session.search_appointments(
                    region=region, bookingtype=bookingtype, specialization=specialization, service=service, clinic=c, doctor=d, start_date=start_date)

                if not appointments:
                    click.echo(click.style(
                        f'(iteration: {counter}) No results found ' + pushover_msgtitle, fg='yellow'))
                else:
                    applen = len(appointments)                    
                    click.echo(click.style(f'(iteration: {counter}) Found {applen} appointments ' + pushover_msgtitle, fg='green', blink=True))
                    for appointment in appointments:
                        appointmentcheck = user + appointment.appointment_datetime + appointment.doctor_name
                        click.echo(
                            appointment.appointment_datetime + ' ' +
                            click.style(appointment.doctor_name, fg='bright_green') + ' ' +
                            appointment.clinic_name
                        )
                        #Pusover notifications message generation - will be generated only for newly found appointements
                        if pushover_notification :
                            try :
                                # TODO: replace shelves with SQL as concurency will fail
                                # TODO: crude workaround to create shelve if not existing 
                                visistshelve = shelve.open('./visits.db')
                                alreadynotified = appointmentcheck in list(visistshelve.values())
                                visistshelve.close()
                            except Exception:
                                click.secho('Problem in Reading stored appointments', fg='red')
                                return

                            if not alreadynotified:
                                notificationcounter += 1
                                notification = notification + '<b>' + appointment.appointment_datetime + '</b> <font color="#0000ff">' + appointment.doctor_name + '</font> ' + appointment.clinic_name + '\n'
                                try:
                                    visistshelve = shelve.open('./visits.db')
                                    visistshelve[appointmentcheck] = appointmentcheck
                                    visistshelve.close()
                                except Exception:
                                    click.secho('Problem in Writing appointments to storage', fg='red')
                                    return

        #Pushover notification final trim (max 1024 chars) and delivery
        if pushover_notification and notificationcounter > 0 :
            if len(notification) > 1020 : notification = notification [0:960] + '<b><font color="#ff0000"> + more appointments online</font></b>'
            if len(pushover_msgtitle) > 0 : pushover_msgtitle = pushover_msgtitle + ': '
            client.send_message(notification, title=pushover_msgtitle + "Found " + str(notificationcounter) + " appointments", device=pushover_device,html=1)

        counter += 1
        # TODO: Time to sleep should not be over 10 minutes as this is maximum time for Medicover session
        time.sleep(interval*60)

    # Leveraging existing function as if it's running i.e. via Cron ther may be too many sessions left open
    try :
        r = med_session.log_out()
    except Exception:
        click.secho('Logout problems', fg='red')
        return


def is_empty(any_structure):
    if any_structure:
        return False
    else:
        return True

FIELD_NAMES = ['specialization', 'region', 'clinic', 'doctor']

@click.command()
@click.option('-f', '--field-name', type=click.Choice(FIELD_NAMES), default='specialization')
def show_params(field_name):
    params = load_available_search_params(field_name)
    for p in params:
        text = p['text']
        id_ = p['id']
        print(f' {text} (id={id_})')


@click.group()
def medihunter():
    pass

medihunter.add_command(show_params)
medihunter.add_command(find_appointment)


if __name__ == '__main__':
    medihunter()
