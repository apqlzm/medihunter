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
from medihunter_notifiers import pushover_notify

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

def notify_external_device(message: str, notifier: str):
    # TODO: add more notification providiers
    if notifier == 'pushover':
        pushover_notify(message)


def process_appointments(appointments: List[Appointment], iteration_counter: int, notifier: str):

    applen = len(appointments)
    click.echo(click.style(
        f'(iteration: {iteration_counter}) Found {applen} appointments', fg='green', blink=True))
        
    for appointment in appointments:
        if duplicate_checker(appointment):
            click.echo(
                appointment.appointment_datetime + ' ' +
                click.style(appointment.doctor_name, fg='bright_green') + ' ' +
                appointment.clinic_name
            )
            notify_external_device(
                f'{appointment.appointment_datetime} {appointment.doctor_name} {appointment.clinic_name}', notifier)


@click.command()
@click.option('--region', '-r', required=True, show_default=True)
@click.option('--bookingtype', '-b', default=2, show_default=True)
@click.option('--specialization', '-s', required=True, show_default=True)
@click.option('--clinic', '-c', default=-1)
@click.option('--doctor', '-o', default=-1)
@click.option('--start-date', '-d', default=now_formatted, show_default=True)
@click.option('--interval', '-i', default=0, show_default=True)
@click.option('--enable-notifier', '-n', type=click.Choice(['pushover', 'gmail']))
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
                     interval,
                     enable_notifier):
    iteration_counter = 1
    med_session = MedicoverSession(username=user, password=password)

    try:
        med_session.log_in()
    except Exception:
        click.secho('Unsuccessful logging in', fg='red')
        return

    click.echo('Logged in')

    med_session.load_search_form()  # TODO: can I get rid of it?

    while interval > 0 or iteration_counter < 2:
        appointments = med_session.search_appointments(
            region=region, 
            bookingtype=bookingtype,
            specialization=specialization, 
            clinic=clinic, 
            doctor=doctor,
            start_date=start_date)

        if not appointments:
            click.echo(click.style(
                f'(iteration: {iteration_counter}) No results found', fg='yellow'))
        else:
            process_appointments(
                appointments, iteration_counter, notifier=enable_notifier)

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
