import json
import os
from collections import namedtuple
from datetime import datetime, timedelta

import requests
import appdirs
import pickle
from bs4 import BeautifulSoup


BASE_HOST = "mol.medicover.pl"
BASE_URL = "https://"+BASE_HOST

BASE_OAUTH_URL = "https://oauth.medicover.pl"

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0"

Appointment = namedtuple(
    "Appointment",
    ["doctor_name", "clinic_name", "appointment_datetime", "is_phone_consultation"],
)


class MedicoverSession:
    """
    Creating (log_in) and killing (log_out) session.
    """

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pl,en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        self.cookies_path = appdirs.user_cache_dir("medihunter", "medihunter") + "/cookies"

    def save_cookies(self):
        os.makedirs(os.path.dirname(self.cookies_path), exist_ok=True)
        with open(self.cookies_path, 'wb') as f:
            pickle.dump(self.session.cookies, f)

    def load_cookies(self):
        try:
            with open(self.cookies_path, 'rb') as f:
                self.session.cookies.update(pickle.load(f))
        except:
            pass

    def extract_data_from_login_form(self, page_text: str):
        """ Extract values from input fields and prepare data for login request. """
        data = {"UserName": self.username, "Password": self.password}
        soup = BeautifulSoup(page_text, "html.parser")
        for input_tag in soup.find_all("input"):
            if input_tag["name"] == "ReturnUrl":
                data["ReturnUrl"] = input_tag["value"]
            elif input_tag["name"] == "__RequestVerificationToken":
                data["__RequestVerificationToken"] = input_tag["value"]
        return data

    def extract_data_from_mfa_form(self, page_text: str, code: str):
        """ Extract values from mfa form fields. """
        data = {"Code": code, "IsDeviceTrusted": "true"}
        soup = BeautifulSoup(page_text, "html.parser")
        for input_tag in soup.find_all("input"):
            if input_tag["name"] == "__RequestVerificationToken":
                data["__RequestVerificationToken"] = input_tag["value"]
        return data

    def form_to_dict(self, page_text):
        """ Extract values from input fields. """
        data = {}
        soup = BeautifulSoup(page_text, "html.parser")
        for input_tag in soup.find_all("input"):
            if input_tag["name"] == "code":
                data["code"] = input_tag["value"]
            elif input_tag["name"] == "id_token":
                data["id_token"] = input_tag["value"]
            elif input_tag["name"] == "scope":
                data["scope"] = input_tag["value"]
            elif input_tag["name"] == "state":
                data["state"] = input_tag["value"]
            elif input_tag["name"] == "session_state":
                data["session_state"] = input_tag["value"]
        return data

    def oauth_sign_in(self, page_text):
        """
        Helper function allowing to extract oauth link from page content
        """
        soup = BeautifulSoup(page_text, "html.parser")
        return soup.form["action"]

    def log_in(self):
        """Login to Medicover website"""
        self.load_cookies()

        # Check whether a previous session is still valid
        # 0. GET https://mol.medicover.pl/
        response = self.session.get(
            "https://mol.medicover.pl/",
            headers=self.headers,
            allow_redirects=False)

        if response.status_code == 200:
            return response

        # 1. GET https://mol.medicover.pl/Users/Account/LogOn?ReturnUrl=%2F
        response = self.session.get(
            BASE_URL + "/Users/Account/LogOn?ReturnUrl=%2F",
            headers=self.headers,
            allow_redirects=False,
        )
        next_url = response.headers["Location"]

        # 2. GET
        # https://oauth.medicover.pl/connect/authorize?client_id=Mcov_Mol&response_type=code+id_token&scope=openid&redirect_uri=https%3A%2F%2Fmol...
        response = self.session.get(
            next_url, headers=self.headers, allow_redirects=False
        )
        next_url = response.headers["Location"]

        # 3. GET
        # https://oauth.medicover.pl/login?signin=5512f89689e74ce9d5515f6a84d76
        response = self.session.get(
            next_url, headers=self.headers, allow_redirects=False
        )
        next_referer = next_url

        # 4. GET
        # https://oauth.medicover.pl/external?provider=IS3&signin=944f8051df4165a710e592dd7f8a&owner=Mcov_Mol&ui_locales=pl-PL

        response = self.session.get(
            f"{BASE_OAUTH_URL}/external",
            headers=self.headers.update({"Referer": next_referer}),
            params={
                "provider": "IS3",
                "signin": next_url.split("=")[-1],
                "owner": "Mcov_Mol",
                "ui_locales": "pl-PL",
            },
            allow_redirects=False,
        )
        next_url = response.headers["Location"]

        # 5. GET
        # https://login.medicover.pl/connect/authorize?client_id=is3&redirect_uri=https%3a%2f%2foauth.medicover.pl...

        response = self.session.get(
            next_url,
            headers=self.headers.update({"Referer": next_referer}),
        )

        data = self.extract_data_from_login_form(response.text)
        login_url = response.url

        # 6. POST
        # https://login.medicover.pl/Account/Login?ReturnUrl=%2Fconnect%2Fauthorize%2Fcallback%3Fclient_id%3Dis3...
        response = self.session.post(login_url, headers=self.headers, data=data)

        if '/Account/mfa?' in response.url:
            # 6a. POST
            # https://login.medicover.pl/Account/mfa?ReturnUrl=%2Fconnect%2Fauthorize%2Fcallback%3Fclient_id%3Dis3...
            code = input("Enter the code received by SMS: ")
            mfa_url = response.url
            data = self.extract_data_from_mfa_form(response.text, code)
            response = self.session.post(mfa_url, headers=self.headers, data=data)

        data = self.form_to_dict(response.text)
        if not data:
             raise RuntimeError("Cannot log in. Probably invalid user/pass and/or account locked (for e.g. 15 minutes)")

        # 7. POST
        response = self.session.post(
            f"{BASE_OAUTH_URL}/signin-oidc",
            headers=self.headers,
            data=data
            # , allow_redirects=False
        )
        data = self.form_to_dict(response.text)
        next_referer = response.url

        self.headers.update(
            {
                "Referer": f"{BASE_OAUTH_URL}/",
                "Origin": f"{BASE_OAUTH_URL}/",
                "Host": BASE_HOST,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        # 8 POST
        response = self.session.post(
            BASE_URL+"/Medicover.OpenIdConnectAuthentication/Account/OAuthSignIn",
            headers=self.headers,
            data=data,
        )

        del self.headers["Origin"]
        del self.headers["Content-Type"]
        self.headers.update(
            {
                "Referer": BASE_URL+"/Medicover.OpenIdConnectAuthentication/Account/OAuthSignIn",
            }
        )
        # 9. GET
        response = self.session.get(BASE_URL+"/", headers=self.headers)
        response.raise_for_status()
        self.save_cookies()
        return response

    def _parse_search_results(self, result):
        """
        take search results in json format end transporm it to list of namedtuples
        """

        result = result.json()
        result = result["items"]
        appointments = []

        for r in result:
            appointments.append(self.convert_search_result_to_appointment(r))

        return appointments

    def convert_search_result_to_appointment(self, r):
        appointment = Appointment(
            doctor_name=r["doctorName"],
            clinic_name=r["clinicName"],
            appointment_datetime=r["appointmentDate"],
            is_phone_consultation=r["isPhoneConsultation"],
        )
        return appointment

    def search_appointments(self, *args, **kwargs):

        if not (
            "clinic" in kwargs
            and "region" in kwargs
            and "start_date" in kwargs
            and "bookingtype" in kwargs
            and "specialization" in kwargs
            and "doctor" in kwargs
        ):
            return



        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Host": BASE_HOST,
            "Origin": BASE_URL,
            "User-Agent": USER_AGENT,
        }

        region_id = int(kwargs["region"])
        service_ids = (
            [int(kwargs["specialization"])]
            if kwargs["bookingtype"] == 2
            else [int(kwargs["service"])]
        )
        clinic_ids = [kwargs["clinic"]] if kwargs["clinic"] > 0 else []
        doctor_ids = [kwargs["doctor"]] if kwargs["doctor"] > 0 else []

        disable_phone_search = (
            kwargs["disable_phone_search"]
            if "disable_phone_search" in kwargs
            else False
        )

        search_params = {
            "regionIds": [region_id],
            "serviceTypeId": kwargs["bookingtype"],
            "serviceIds": service_ids,
            "clinicIds": clinic_ids,
            "doctorLanguagesIds": [],
            "doctorIds": doctor_ids,
            "searchSince": kwargs["start_date"] + "T00:00:00.000Z",
            "startTime": kwargs["start_time"],
            "endTime": kwargs["end_time"],
            "selectedSpecialties": None,
            "visitType": "center" if kwargs["bookingtype"] == 1 else 2,
            "disablePhoneSearch": disable_phone_search,
        }

        result = self.session.post(
            f"{BASE_URL}/api/MyVisits/SearchFreeSlotsToBook",
            json=search_params,
            params={"language": "pl-PL"},
            headers=headers,
        )

        try:
            appointments = self._parse_search_results(result)
        except KeyError as exc:
            return []
        if kwargs.get("end_date") is not None:

            def is_appointment_before_date(
                appointment: Appointment, date: datetime
            ) -> bool:
                def parse_appointment_datetime_to_datetime(iso_date: str) -> datetime:
                    return datetime.strptime(iso_date, "%Y-%m-%dT%H:%M:%S")

                def get_end_of_day(dt: datetime) -> datetime:
                    return dt + timedelta(days=1, microseconds=-1)

                return parse_appointment_datetime_to_datetime(
                    appointment.appointment_datetime
                ) <= get_end_of_day(date)

            end_date = datetime.strptime(kwargs["end_date"], "%Y-%m-%d")
            appointments = [
                a for a in appointments if is_appointment_before_date(a, end_date)
            ]

        return appointments

    def load_search_form(self):
        return self.session.get(
            BASE_URL + "/MyVisits",
            params={"bookingTypeId": 2, "mex": "True", "pfm": 1},
        )

    def log_out(self):
        """Logout from Medicover website"""
        next_url = BASE_URL+"/Users/Account/LogOff"
        self.headers.update({"Referer": BASE_URL + "/"})
        self.headers.update(self.session.headers)
        response = self.session.get(next_url, headers=self.headers)
        self.session.close()
        self.save_cookies()
        return response

    def get_plan(self):
        """Download Medicover plan"""
        output = ""
        medical_services_website = self.session.get(
            BASE_URL + "/Medicover.MedicalServices/MedicalServices", headers={
                "Host": BASE_HOST,
                "Origin": BASE_URL,
                "User-Agent": USER_AGENT,
            }
        )
        medical_services_website.raise_for_status()
        soup = BeautifulSoup(medical_services_website.content, "lxml")
        drop_down = soup.find("select")
        drop_down_options = drop_down.find_all("option")
        for option in drop_down_options:
            option_id = option["value"]
            if option_id == "":
                continue
            option_html = self.session.get(
                f"{BASE_URL}/MedicalServices/MedicalServices/ShowResults?serviceId={option_id}"
                , headers={
                    "Host": BASE_HOST,
                    "Origin": BASE_URL,
                    "User-Agent": USER_AGENT,
                }
            )
            option_html.raise_for_status()
            soup2 = BeautifulSoup(option_html.content, "lxml")
            option_header = soup2.find("h4").text
            option_header = option_header.replace("\r\n", "").replace("\n", "")
            option_texts = []
            for p_tag in soup2.find_all("p"):
                option_texts.append(
                    p_tag.text.strip().replace("\r\n", "").replace("\n", "")
                )
            option_text = "\t|".join(option_texts)
            option_result = f"{option_id}\t{option_header}\t{option_text}"
            print(option_result)
            output = output + option_result + "\n"

        return output

    def get_appointments(self):
        """Download all past and future appointments."""
        appointments = []
        page = 1
        while True:
            response = self.session.post(
                BASE_URL + "/api/MyVisits/SearchVisitsToView",
                headers={
                    # Makes the response come as json.
                    "X-Requested-With": "XMLHttpRequest",
                    "Host": BASE_HOST,
                    "Origin": BASE_URL,
                    "User-Agent": USER_AGENT,
                },
                data={
                    "Page": page,
                    "PageSize": 12,
                },
            )
            response.raise_for_status()
            response_json = response.json()
            for r in response_json["items"]:
                appointments.append(self.convert_search_result_to_appointment(r))
            if len(appointments) >= response_json["totalCount"]:
                break
            # Just in case the condition above fails for some reason.
            if not len(response_json["items"]):
                break
            page += 1
        return appointments


def load_available_search_params(field_name):
    FIELDS_NAMES = {
        "specialization": "availableSpecializations",
        "region": "availableRegions",
        "clinic": "availableClinics",
        "doctor": "availableDoctors",
    }

    if field_name not in FIELDS_NAMES:
        return

    field_name = FIELDS_NAMES[field_name]

    params_file_content = ""

    params_path = os.path.join(os.path.dirname(__file__), "ids/params.json")

    with open(params_path, encoding="utf-8") as f:
        params_file_content = f.read()

    params = json.loads(params_file_content)

    return params[field_name]
