# medihunter

This tool is designed for automatic searching of medical appointments with doctors. It's especially useful when appointments are hard to come by ;)

**Works with Python version 3.6+**

<p align="center">  
    <img src="https://apqlzm.github.io/theme/images/icons/search-every-minute.svg">  
</p>

## Introduction

There are two versions of the script available:

* **medihunter_pushover.py** - includes pushover notifications functionality, the ability to search multiple clinics and several specialists at the same time. This code needs refactoring and therefore won't be developed further. I plan to remove it eventually.
* **medihunter.py** - new features are being added here. As of now (2021-07-11), you can set pushover, telegram, and xmpp notifications.

## Installation

Activate virtualenv (optional but recommended)

```bash  
source /path/to/my/virtualenv/bin/activate  
```  
or in Windows cmd with a virtual environment created by venv library

```  
SourceToVirtEnv\Scripts\activate.bat  
```

Navigate to the source directory and run

```bash  
pip install --editable .  
```

Now you have the `medihunter` command available in virtualenv.

If you don't want to be asked every time for login and password and/or don't want to openly provide them in the terminal through `--user login --password password`, you can save them in the `.env` file:  
```  
MEDICOVER_USER=login  
MEDICOVER_PASS=password  
```

The easiest way is to copy the sample `.env.example` file from the main directory as `.env` and fill in the data.

## Available Subcommands

### show-params

When searching for an appointment, you need to provide the city, medical facility, specialization (what kind of doctor it should be), doctor's ID (with the possibility to choose a specific doctor), and date of visit (the visit will start no sooner than this date). Each of these parameters (except for the date) has an assigned ID number. To find it out, use the *show-params* command.

city IDs

```bash  
medihunter show-params -f region  
```

specialization IDs

```bash  
medihunter show-params -f specialization -r 204  
```

### find-appointment

Let's look for an endocrinologist

```bash  
medihunter find-appointment -s 27962  
```

Of course, finding an appointment with an endocrinologist is not that easy, so let's set the searcher to check for availability every 5 minutes

```bash  
medihunter find-appointment -s 27962 -i 5  
```

or maybe we want to search for specific endocrinologists with IDs: 12345 and 0987? **only in medihunter_pushover.py**

```bash  
medihunter find-appointment -s 27962 -o 12345 -o 0987  
```

or perhaps we're just looking for any internist in clinics close to us at Atrium and on Prosta street? **only in medihunter_pushover.py**

```bash  
medihunter find-appointment -s 9 -c 174 -c 49088  
```

and what if we want to find an appointment with any orthopedist in the Tricity area within the next two weeks, not in a month? **doesn't work without a start date**

```bash  
medihunter find-appointment -s 163 -d 2021-12-19 -f 2022-12-31 -r 200  
```

Or, you can add it directly to Crontab as below **entry in cron works only with medihunter_pushover.py**

- will be run between 6 am and 11 pm every 5 minutes  
- -s - looks for an Orthopedist for adults  
- -c 174 -c 6896 only in the center Warsaw Atrium and Warsaw Inflancka  
Will use the provided Medicover user parameters and Pushover for sending notifications  
- crontab will save logs in /var/log/medihunter.log

```bash  
*/5 6-23 * * * /usr/bin/python3.7 /home/user/medihunter.py find-appointment -s 163 -c 174 -c 6896 --user MEDICOVER_USER --password MEDICOVER_PASS --pushover_msgtitle 'Orthopedist Center' --pushover_token PUSHOVER_TOKEN --pushover_user PUSHOVER_USER >> /var/log/medihunter.log 2>&1  
```

### my-plan

Downloads and saves available services along with information on whether they are available as part of the purchased package, and if not, whether there are any discounts on them. Some services have limits, which should also be visible here. The output file is in tsv (Tab-separated_values) format. Example usage:

```bash  
medihunter my-plan --user mylogin --password mypassword  
```

## Displaying Help

General help

```bash  
medihunter --help  
```

Individual subcommands

```bash  
medihunter find-appointment --help  
medihunter show-params --help  
```

## Pushover Notifications

pertains to **medihunter_pushover.py**

By providing parameters for Pushover notifications https://pushover.net/, it is possible to transmit notifications about an appointment directly to the app. You must provide at least the --pushover_token and --pushover_user parameters.

## Default Settings

### show-params

by default, -f is set to *specialization*

### find-appointment

TODO: _The following options are only current for medihunter_pushover.py_

option|default value  
-----|----------------  
-r, --region|Warsaw  
-b, --bookingtype|2, Consultation type 2 = Consultation (by default), 1 = Diagnostic examination  
-s, --specialization|none, Specify in case of Consultation type (bookingtype = 2 by default)  
-e, --service|none, Type/service identifier, specify in case of service type booking (bookingtype = 1), works similarly to specialization  
-c, --clinic|all in the region/city, can use this parameter multiple times to search for appointments in specific clinics  
-o, --doctor|all doctors, can use this parameter multiple times to check several doctors  
-d, --start-date|current date (format: YYYY-mm-dd)  
-f, --end-date|None (format: YYYY-mm-dd), available only in medihunter.py  
-a, --start-time|"0:00" (format: hh:mm), available only in medihunter.py  
-g, --end-time|"23:59" (format: hh:mm), available only in medihunter.py  
-j, --days-ahead| 1 = displays appointments for the first found day, available only in medihunter.py  
-i, --interval|None  
--disable-phone-search|None, Allows skipping telephone appointments in the search, available only in medihunter.py  
--pushover_token|None, Pushover Application Token  
--pushover_user|None, Pushover user Token  
--pushover_device|None, None device name in Pushover by default empty=all  
--pushover_msgtitle|none - prefix added before the notification title  
-t, --notification-title|none, available only in medihunter.py, supported only by Pushover, Telegram, and Gotify

## Pushbullet in medihunter.py

To operate Pushbullet notifications, you need to set the export (with your own values):

```shell  
# bash  
export NOTIFIERS_PUSHBULLET_TOKEN=avykwnqc8ohyk73mo1bsuggsm3r4qf  
```

or

```shell  
# fish  
set -x NOTIFIERS_PUSHBULLET_TOKEN avykwnqc8ohyk73mo1bsuggsm3r4qf  
```

Now you can search for appointments like this:

```shell  
medihunter find-appointment -n pushbullet -r 204 -s 4798 --user 00000 --password psw1234 -i 1 -d 2019-05-15  
```

## Pushover in medihunter.py

To operate Pushover notifications, you need to set the export (with your own values):

```shell  
# bash  
export NOTIFIERS_PUSHOVER_TOKEN=avykwnqc8ohyk73mo1bsuggsm3r4qf  
export NOTIFIERS_PUSHOVER_USER=s4g1zoewbzseogp4knrapx23k9yi95  
```

or

```shell  
# fish  
set -x NOTIFIERS_PUSHOVER_TOKEN avykwnqc8ohyk73mo1bsuggsm3r4qf  
set -x NOTIFIERS_PUSHOVER_USER s4g1zoewbzseogp4knrapx23k9yi95  
```

Now you can search for appointments like this:

```shell  
medihunter find-appointment -n pushover -r 204 -s 4798 --user 00000 --password psw1234 -i 1 -d 2019-05-15  
```

## Telegram in medihunter.py

You need to create a bot for notifications and a channel where they will be sent. You can find details on how to do this at https://core.telegram.org/bots

Once you have that ready, you just need to export two variables (with your own values):

```shell  
# bash  
export NOTIFIERS_TELEGRAM_CHAT_ID=avykwnqc8ohyk73mo1bsuggsm3r4qf  
export NOTIFIERS_TELEGRAM_TOKEN=740885363:AdFRNFTIFTc4hC1flAuXE-dyik_Udm6Ma3o  
```

or

```shell  
# fish  
set -x NOTIFIERS_TELEGRAM_CHAT_ID avykwnqc8ohyk73mo1bsuggsm3r4qf  
set -x NOTIFIERS_TELEGRAM_TOKEN 740885363:AdFRNFTIFTc4hC1flAuXE-dyik_Udm6Ma3o  
```

or in Windows with venv  
```shell  
set NOTIFIERS_TELEGRAM_CHAT_ID=avykwnqc8ohyk73mo1bsuggsm3r4qf  
set NOTIFIERS_TELEGRAM_TOKEN=740885363:AdFRNFTIFTc4hC1flAuXE-dyik_Udm6Ma3o  
```

Now you can search for appointments and receive notifications in Telegram:

```shell  
medihunter find-appointment -r 204 -s 4798 --user 00000 --password psw1234 -i 1 -d 2019-05-22 -n telegram  
```

## XMPP in medihunter.py

You need to have 2 registered XMPP accounts:
- the first for sending messages, in case of finding appointments matching the search criteria,
- the second for receiving notification messages, on which you will be logged in with any client that supports XMPP (e.g., on a computer/mobile device).

Export the names of both XMPP accounts and the login password for the first account (with your own values):

```shell  
# bash  
export NOTIFIERS_XMPP_JID='sender_of_notifications@example.com'  
export NOTIFIERS_XMPP_PASSWORD='password_of_sender_of_notifications'  
export NOTIFIERS_XMPP_RECEIVER='receiver_of_notifications@example.com'  
```

or

```shell  
# fish  
set -x NOTIFIERS_XMPP_JID 'sender_of_notifications@example.com'  
set -x NOTIFIERS_XMPP_PASSWORD 'password_of_sender_of_notifications'  
set -x NOTIFIERS_XMPP_RECEIVER 'receiver_of_notifications@example.com'  
```

Now you can search for appointments and receive notifications via XMPP:

```shell  
medihunter find-appointment -r 204 -s 4798 --user 00000 --password psw1234 -i 1 -d 2019-05-22 -n xmpp  
```

## Gotify in medihunter.py

[Gotify](https://gotify.net/) is a simple service for sending push notifications mainly to Android devices. It differs from other such applications in that it is fully open source and intended for hosting on your own server.

To use this notification method, you need to set a few environment variables:

```shell  
# bash  
export GOTIFY_TOKEN=AbCDeFg2yvapfPA  
export GOTIFY_HOST=https://gotify.my-server.com  
```

or

```shell  
# fish  
set -x GOTIFY_TOKEN 'AbCDeFg2yvapfPA'  
set -x GOTIFY_HOST 'https://gotify.my-server.com'  
```

or in Windows with venv  
```shell  
set GOTIFY_TOKEN=AbCDeFg2yvapfPA  
set GOTIFY_HOST=https://gotify.my-server.com  
```

There's also an optional `GOTIFY_PRIORITY` variable which allows setting the notification priority (default `5`).

Now you can search for appointments and receive notifications via Gotify:

```shell  
medihunter find-appointment -r 204 -s 4798 --user 00000 --password psw1234 -i 1 -d 2019-05-22 -n gotify  
```

## Docker  
To run the application in a container, you first need to build the image

```shell  
docker build -t medihunter .  
```

Then launch the container using the run command  
```shell  
docker run -it medihunter find-appointment --user 00000 --password psw1234 -r 204 -s 4798  
```

It is also possible to use environment variables or an .env file  
```shell  
docker run -it  -e MEDICOVER_USER=00000 -e MEDICOVER_PASS=psw1234 medihunter find-appointment -r 204 -s 4798

docker run -it --env-file=.env medihunter find-appointment -r 204 -s 4798  
```