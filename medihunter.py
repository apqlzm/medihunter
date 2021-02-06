""" Base script without pushover notifications
this is a startpoint for adding new features
"""

import json
import time
from datetime import datetime, timedelta
from typing import Callable, List

import click

from medicover_session import (
    Appointment,
    MedicoverSession,
    load_available_search_params,
)
from medihunter_notifiers import pushover_notify, telegram_notify

now = datetime.now()
now_formatted = now.strftime("%Y-%m-%dT02:00:00.000Z")


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
    if notifier == "pushover":
        title = kwargs.get("notification_title")
        pushover_notify(message, title)
    elif notifier == "telegram":
        telegram_notify(message)


def process_appointments(
    appointments: List[Appointment], iteration_counter: int, notifier: str, **kwargs
):

    applen = len(appointments)
    click.echo(
        click.style(
            f"(iteration: {iteration_counter}) Found {applen} appointments",
            fg="green",
            blink=True,
        )
    )

    notification_message = ""

    for appointment in appointments:
        if duplicate_checker(appointment):
            echo_appointment(appointment)
            notification_message += f"{appointment.appointment_datetime} {appointment.doctor_name} {appointment.clinic_name}\n"

    if notification_message:
        notification_title = kwargs.get("notification_title")
        notify_external_device(
            notification_message, notifier, notification_title=notification_title
        )


def echo_appointment(appointment):
    click.echo(
        appointment.appointment_datetime
        + " "
        + click.style(appointment.doctor_name, fg="bright_green")
        + " "
        + appointment.clinic_name
        + " "
        + ("(Telefonicznie)" if appointment.is_phone_consultation else "(Stacjonarnie)")
    )


def validate_arguments(**kwargs) -> bool:
    if kwargs["service"] == -1 and kwargs["bookingtype"] == 1:
        click.echo("Service is required when bookingtype=1 (Diagnostic procedure)")
        return False

    if kwargs["specialization"] == -1 and kwargs["bookingtype"] == 2:
        click.echo("Specialization is required when bookingtype=2 (Consulting)")
        return False
    return True


@click.command()
@click.option("--region", "-r", required=True, show_default=True)
@click.option("--bookingtype", "-b", default=2, show_default=True)
@click.option("--specialization", "-s", default=-1)
@click.option("--clinic", "-c", default=-1)
@click.option("--doctor", "-o", default=-1)
@click.option("--start-date", "-d", default=now_formatted, show_default=True)
@click.option("--end-date", "-f")
@click.option("--start-time", "-a", default="0:00", show_default=True)
@click.option("--end-time", "-g", default="23:59", show_default=True)
@click.option("--service", "-e", default=-1)
@click.option("--interval", "-i", default=0, show_default=True)
@click.option("--days-ahead", "-j", default=1, show_default=True)
@click.option("--enable-notifier", "-n", type=click.Choice(["pushover", "telegram"]))
@click.option("--notification-title", "-t")
@click.option("--user", prompt=True)
@click.password_option(confirmation_prompt=False)
@click.option("--disable-phone-search", is_flag=True)
def find_appointment(
    user,
    password,
    region,
    bookingtype,
    specialization,
    clinic,
    doctor,
    start_date,
    end_date,
    start_time,
    end_time,
    service,
    interval,
    days_ahead,
    enable_notifier,
    notification_title,
    disable_phone_search,
):

    if end_date:
        start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")
        diff = end_date_dt - start_date_dt
        days_ahead = diff.days

    valid = validate_arguments(
        bookingtype=bookingtype, specialization=specialization, service=service
    )

    if not valid:
        return

    iteration_counter = 1
    med_session = MedicoverSession(username=user, password=password)

    try:
        med_session.log_in()
    except Exception:
        click.secho("Unsuccessful logging in", fg="red")
        return

    click.echo("Logged in")

    med_session.load_search_form()

    while interval > 0 or iteration_counter < 2:
        appointments = []
        start_date_param = start_date
        for _ in range(days_ahead):
            found_appointments = med_session.search_appointments(
                region=region,
                bookingtype=bookingtype,
                specialization=specialization,
                clinic=clinic,
                doctor=doctor,
                start_date=start_date_param,
                end_date=end_date,
                start_time=start_time,
                end_time=end_time,
                service=service,
                disable_phone_search=disable_phone_search
            )

            if not found_appointments:
                break

            appointment_datetime = found_appointments[-1].appointment_datetime
            appointment_datetime = datetime.strptime(
                appointment_datetime, "%Y-%m-%dT%H:%M:%S"
            )
            appointment_datetime = appointment_datetime + timedelta(days=1)
            start_date_param = appointment_datetime.date().isoformat()
            appointments.extend(found_appointments)

        if not appointments:
            click.echo(
                click.style(
                    f"(iteration: {iteration_counter}) No results found", fg="yellow"
                )
            )
        else:
            process_appointments(
                appointments,
                iteration_counter,
                notifier=enable_notifier,
                notification_title=notification_title,
            )

        iteration_counter += 1
        time.sleep(interval * 60)


FIELD_NAMES = ["specialization", "region", "clinic", "doctor"]


@click.command()
@click.option(
    "-f", "--field-name", type=click.Choice(FIELD_NAMES), default="specialization"
)
def show_params(field_name):
    params = load_available_search_params(field_name)
    for p in params:
        text = p["text"]
        id_ = p["id"]
        print(f" {text} (id={id_})")


@click.command()
@click.option("--user", prompt=True)
@click.password_option(confirmation_prompt=False)
def my_plan(user, password):
    med_session = MedicoverSession(username=user, password=password)
    try:
        med_session.log_in()
    except Exception:
        click.secho("Unsuccessful logging in", fg="red")
        return
    click.echo("Logged in")
    plan = med_session.get_plan()

    with open("plan.tsv", mode="wt", encoding="utf-8") as f:
        f.write(plan)


@click.command()
@click.option("--user", prompt=True)
@click.password_option(confirmation_prompt=False)
def my_appointments(user, password):
    med_session = MedicoverSession(username=user, password=password)
    try:
        med_session.log_in()
    except Exception:
        click.secho("Unsuccessful logging in", fg="red")
        return
    click.echo("Logged in")
    appointments = med_session.get_appointments()

    planned_appointments = list(filter(lambda a: datetime.strptime(
        a.appointment_datetime, "%Y-%m-%dT%H:%M:%S"
    ) >= now, appointments))
    if planned_appointments:
        click.echo("Showing only planned appointments:")
        for planned_appointment in planned_appointments:
            echo_appointment(planned_appointment)
    else:
        click.echo("No planned appointments.")


@click.group()
def medihunter():
    pass


medihunter.add_command(show_params)
medihunter.add_command(find_appointment)
medihunter.add_command(my_plan)
medihunter.add_command(my_appointments)


if __name__ == "__main__":
    medihunter()
