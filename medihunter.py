""" Base script without pushover notifications 
this is a startpoint for adding new features
"""

import json
import time
from datetime import datetime
from typing import Callable, List

import click

from medicover_session import (Appointment, MedicoverSession,
                               load_available_search_params)
from medihunter_notifiers import pushover_notify, telegram_notify

now = datetime.now()
now_formatted = now.strftime('%Y-%m-%dT02:00:00.000Z')


def make_duplicate_checker() -> Callable[[Appointment], bool]:
    """Closure which checks if appointment was already found before 

    Returns:
        True if appointment ocurred first time
        False otherwise
    """
    found_appointments: List[Appointment] = []

    def duplicate_checker(appointment: Appointment) -> bool:
        if appointment in found_appointments:
            return False
        found_appointments.append(appointment)
        return True

    return duplicate_checker


duplicate_checker = make_duplicate_checker()

def notify_external_device(message: str, notifier: str, **kwargs):
    # TODO: add more notification providers
    if notifier == 'pushover':
        title = kwargs.get('notification_title')
        pushover_notify(message, title)
    elif notifier == 'telegram':
        telegram_notify(message)


def process_appointments(appointments: List[Appointment], iteration_counter: int, notifier: str, **kwargs):

    applen = len(appointments)
    click.echo(click.style(
        f'(iteration: {iteration_counter}) Found {applen} appointments', fg='green', blink=True))
    
    notification_message = ''

    for appointment in appointments:
        if duplicate_checker(appointment):
            click.echo(
                appointment.appointment_datetime + ' ' +
                click.style(appointment.doctor_name, fg='bright_green') + ' ' +
                appointment.clinic_name
            )
            notification_message += f'{appointment.appointment_datetime} {appointment.doctor_name} {appointment.clinic_name}\n'
    
    if notification_message:
        notification_title = kwargs.get('notification_title')
        notify_external_device(notification_message, notifier, notification_title=notification_title)


def validate_arguments(**kwargs) -> bool:
    if kwargs['service'] == -1 and kwargs['bookingtype'] == 1:
        click.echo(
            'Service is required when bookingtype=1 (Diagnostic procedure)')
        return False

    if kwargs['specialization'] == -1 and kwargs['bookingtype'] == 2:
        click.echo(
            'Specialization is required when bookingtype=2 (Consulting)')
        return False
    return True


@click.command()
@click.option('--region', '-r', required=True, show_default=True)
@click.option('--bookingtype', '-b', default=2, show_default=True)
@click.option('--specialization', '-s', default=-1)
@click.option('--clinic', '-c', default=-1)
@click.option('--doctor', '-o', default=-1)
@click.option('--start-date', '-d', default=now_formatted, show_default=True)
@click.option('--service', '-e', default=-1)
@click.option('--interval', '-i', default=0, show_default=True)
@click.option('--enable-notifier', '-n', type=click.Choice(['pushover', 'telegram']))
@click.option('--notification-title', '-t')
@click.option('--user', prompt=True)
@click.password_option(confirmation_prompt=False)
def find_appointment(user,
                     password,
                     region,
                     bookingtype,
                     specialization,
                     clinic,
                     doctor,
                     start_date,
                     service,
                     interval,
                     enable_notifier,
                     notification_title):
    
    valid = validate_arguments(
        bookingtype=bookingtype,
        specialization=specialization,
        service=service
    )

    if not valid:
        return

    iteration_counter = 1
    med_session = MedicoverSession(username=user, password=password)

    try:
        med_session.log_in()
    except Exception:
        click.secho('Unsuccessful logging in', fg='red')
        return

    click.echo('Logged in')

    med_session.load_search_form()

    while interval > 0 or iteration_counter < 2:
        appointments = med_session.search_appointments(
            region=region, 
            bookingtype=bookingtype,
            specialization=specialization, 
            clinic=clinic, 
            doctor=doctor,
            start_date=start_date,
            service=service)

        if not appointments:
            click.echo(click.style(
                f'(iteration: {iteration_counter}) No results found', fg='yellow'))
        else:
            process_appointments(
                appointments, iteration_counter, notifier=enable_notifier, notification_title=notification_title)

        iteration_counter += 1
        time.sleep(interval*60)


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
