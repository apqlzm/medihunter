import json
import time
import shelve
from datetime import datetime
from pushover import Client

import click

from medicover_session import MedicoverSession, load_available_search_params


now = datetime.now()
now_formatted = now.strftime('%Y-%m-%dT02:00:00.000Z')


@click.command()
@click.option('--user', prompt=True)
@click.password_option(confirmation_prompt=False)
@click.option('--region', '-r', default=204)
@click.option('--specialization', '-s', default=16234)
@click.option('--clinic', '-c', multiple=True, default='0')
@click.option('--doctor', '-o', multiple=True, default='0')
@click.option('--start-date', '-d', default=now_formatted)
@click.option('--interval', '-i', default=0)
@click.option('--pushover_token', default="")
@click.option('--pushover_user', default="")
@click.option('--pushover_device', default=None)
@click.option('--pushover_msgtitle', default="")
def find_appointment(user, password, region, specialization, clinic, doctor, start_date, interval, pushover_token, pushover_user,pushover_device,pushover_msgtitle):
    counter = 0
    med_session = MedicoverSession(username=user, password=password)

    # TODO: Workaround as for some reasons when they were defaulted to -1 in click.option this was casuing tuple error in click and for loops
    if clinic[0]=='0': 
        clinic = list(clinic)
        clinic[0]='-1'
    if doctor[0]=='0': 
        doctor = list(doctor)
        doctor[0]='-1'
    # END of TO DO

    if (pushover_user != "") and (pushover_token != ""):
        try :
            client = Client(user_key=pushover_user, api_token=pushover_token)
            pushover_notification = True
        except Exception:
            click.secho('Pushover not initialized correctly', fg='red')
            return
    else :
        pushover_notification = False

    try :
        r = med_session.log_in()
    except Exception:
        click.secho('Unsuccessful logging in', fg='red')
        return

    click.echo(datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S') + ': Logged in ' + pushover_msgtitle)

    med_session.load_search_form()  # TODO: can I get rid of it?

    while interval > 0 or counter < 1:
        notification = ""
        notificationcounter = 0
        for c in clinic:
            for d in doctor:
                appointments = med_session.search_appointments(
                    region=region, specialization=specialization, clinic=c, doctor=d, start_date=start_date)

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
                        if pushover_notification :
                            try :
                                # TODO: replace shelves with SQL as concurency will fail
                                visistshelve = shelve.open('./visits.db', flag='r')
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

        if pushover_notification and notificationcounter > 0 :
            if len(notification) > 1020 : notification = notification [0:960] + '<b><font color="#ff0000"> + more appointments online</font></b>'
            if len(pushover_msgtitle) > 0 : pushover_msgtitle = pushover_msgtitle + ': '
            client.send_message(notification, title=pushover_msgtitle + "Found " + str(notificationcounter) + " appointments", device=pushover_device,html=1)

        counter += 1
        time.sleep(interval*60)


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
