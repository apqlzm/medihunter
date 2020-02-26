import json
import os
import re
from collections import namedtuple
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

from errors import IdsrvXsrfNotFound

Appointment = namedtuple(
    "Appointment", ["doctor_name", "clinic_name", "appointment_datetime"]
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
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pl,en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    def login_form_data(self, page_text):
        """
            Helper function allowing to extract xsref hash and prepare data for login.
        """

        data = {"username": self.username, "password": self.password}
        if "idsrv.xsrf" in page_text:
            for line in page_text.split("\n"):
                if "idsrv.xsrf" in line:
                    line = line.replace("&quot;", '"')
                    line = line.replace("</script>", "")
                    line = re.sub(r"<script.*?>", "", line)
                    dzej_son = json.loads(line)
                    xsrf = dzej_son["antiForgery"]["value"]
                    data["idsrv.xsrf"] = xsrf
                    break
        else:
            raise IdsrvXsrfNotFound
        return data

    def oauth_sign_in(self, page_text):
        """
            Helper function allowing to extract oauth link from page content
        """
        soup = BeautifulSoup(page_text, "html.parser")
        return soup.form["action"]

    def token_form_data(self, page_text):
        """
            Helper function allowing to extract code, token, scope, state and session_state from
            page content
        """
        o = dict()
        soup = BeautifulSoup(page_text, "html.parser")
        for descet in soup.form.descendants:
            if descet.name == "input":
                if descet["name"] == "code":
                    o["code"] = descet["value"]
                elif descet["name"] == "id_token":
                    o["id_token"] = descet["value"]
                elif descet["name"] == "scope":
                    o["scope"] = descet["value"]
                elif descet["name"] == "session_state":
                    o["session_state"] = descet["value"]
                elif descet["name"] == "state":
                    o["state"] = descet["value"]
        return o

    def log_in(self):
        """
            Login to Medicover website
        """
        # TODO: this method needs to be cleaned

        # 1. GET https://mol.medicover.pl/Users/Account/LogOn?ReturnUrl=%2F
        response = self.session.get(
            "https://mol.medicover.pl/Users/Account/LogOn?ReturnUrl=%2F",
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
        # https://oauth.medicover.pl/login?signin=5512f89689e74ce9d5515f6a84d2b176
        response = self.session.get(
            next_url, headers=self.headers, allow_redirects=False
        )
        login_url = response.url
        data = self.login_form_data(response.text)

        # 4. POST
        # https://oauth.medicover.pl/login?signin=5512f89689e74ce9d5515f6a84d2b176
        next_url = login_url
        self.session.headers.update(
            {"Content-Type": "application/x-www-form-urlencoded"}
        )
        self.session.headers.update({"Origin": "https://oauth.medicover.pl"})
        self.session.headers.update({"Referer": login_url})
        response = self.session.post(
            next_url, headers=self.headers, data=data, allow_redirects=False
        )

        # 5. GET
        # https://oauth.medicover.pl/connect/authorize?client_id=Mcov_Mol&response_type=code%20id_token&scope=openid&redirect_uri=h...
        next_url = response.headers["Location"]
        response = self.session.get(
            next_url, headers=self.headers, allow_redirects=False
        )
        self.session.headers.update({"Referer": next_url})
        next_url = self.oauth_sign_in(response.text)
        data = self.token_form_data(response.text)
        self.session.headers.update(
            {"Content-Type": "application/x-www-form-urlencoded"}
        )

        # 6. POST
        # https://mol.medicover.pl/Medicover.OpenIdConnectAuthentication/Account/OAuthSignIn
        response = self.session.post(
            next_url, headers=self.headers, data=data, allow_redirects=False
        )
        self.session.headers.pop("Content-Type")
        next_url = "https://mol.medicover.pl/"
        self.session.headers.update({"Referer": login_url})

        # 7. GET https://mol.medicover.pl/
        response = self.session.get(
            next_url, headers=self.headers, data=data, allow_redirects=False
        )

        # 8. GET https://mol.medicover.pl/
        response = self.session.get(
            next_url, headers=self.headers, data=data, allow_redirects=False
        )
        return response

    def _parse_search_results(self, result):
        """
        take search results in json format end transporm it to list of namedtuples
        """

        result = result.json()
        result = result["items"]
        appointments = []

        for r in result:
            appointment = Appointment(
                doctor_name=r["doctorName"],
                clinic_name=r["clinicName"],
                appointment_datetime=r["appointmentDate"],
            )
            appointments.append(appointment)

        return appointments

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

        BASE_URL = "mol.medicover.pl"
        headers = self.session.headers
        headers.update(
            {
                "Host": BASE_URL,
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.5",
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://mol.medicover.pl/MyVisits",
            }
        )

        region_id = int(kwargs["region"])
        service_ids = (
            [int(kwargs["specialization"])]
            if kwargs["bookingtype"] == 2
            else [int(kwargs["service"])]
        )
        clinic_ids = [kwargs["clinic"]] if kwargs["clinic"] > 0 else []
        doctor_ids = [kwargs["doctor"]] if kwargs["doctor"] > 0 else []

        search_params = {
            "regionIds": [region_id],
            "serviceTypeId": kwargs["bookingtype"],
            "serviceIds": service_ids,
            "clinicIds": clinic_ids,
            "doctorLanguagesIds": [],
            "doctorIds": doctor_ids,
            "searchSince": kwargs["start_date"],
            "startTime": kwargs["start_time"],
            "endTime": kwargs["end_time"],
        }

        result = self.session.post(
            f"https://{BASE_URL}/api/MyVisits/SearchFreeSlotsToBook",
            json=search_params,
            params={"language": "pl-PL"},
            headers=headers,
        )

        appointments = self._parse_search_results(result)

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
            "https://mol.medicover.pl/MyVisits",
            params={"bookingTypeId": 2, "mex": "True", "pfm": 1},
        )

    def log_out(self):
        """
            Logout from Medicover website
            Session lasts 10 minutes anyway
        """
        next_url = "https://mol.medicover.pl/Users/Account/LogOff"
        self.headers.update({"Referer": "https://mol.medicover.pl/"})
        self.headers.update(self.session.headers)
        # print(self.headers)
        response = self.session.get(next_url, headers=self.headers)
        self.session.close()
        return response

    def get_plan(self):
        """ Download Medicover plan """
        output = ""
        medical_services_website = self.session.get(
            "https://mol.medicover.pl/Medicover.MedicalServices/MedicalServices"
        )
        soup = BeautifulSoup(medical_services_website.content, "lxml")
        drop_down = soup.find("select")
        drop_down_options = drop_down.find_all("option")
        for option in drop_down_options:
            option_id = option["value"]
            if option_id == "":
                continue
            option_html = self.session.get(
                f"https://mol.medicover.pl/MedicalServices/MedicalServices/ShowResults?serviceId={option_id}"
            )
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

    with open(params_path, encoding='utf-8') as f:
        params_file_content = f.read()

    params = json.loads(params_file_content)

    return params[field_name]
