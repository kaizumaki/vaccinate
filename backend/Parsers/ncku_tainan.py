from typing import Tuple
import requests
import bs4
from hospital_types import (
    HospitalID,
    AppointmentAvailability,
    HospitalAvailabilitySchema,
    ScrapedData,
)

CERT: str = "../data/hosp-ncku-edu-tw-chain.pem"
URL_SELF_PAID = "https://service.hosp.ncku.edu.tw/Tandem/MainUI.aspx?Lang=&skv=EzNec8%2bb3OYprHkqM83gBiNJ2d6GNAz2gvscJU0dxqw%3d"
URL_GOV_PAID = "https://service.hosp.ncku.edu.tw/Tandem/MainUI.aspx?Lang=&skv=EzNec8%2bb3ObBGuEQakq0QawPuiWkTewUO9FjEuW3Njo%3d"


def parse_ncku_tainan() -> ScrapedData:
    availability: HospitalAvailabilitySchema = {
        "self_paid": parse_ncku_tainan_self_paid(),
        "government_paid": parse_ncku_tainan_gov_paid(),
    }
    return (
        22,
        availability,
    )


def parse_ncku_tainan_self_paid() -> AppointmentAvailability:
    return (
        AppointmentAvailability.AVAILABLE
        if check_available_ncku_tainan(URL_SELF_PAID)
        else AppointmentAvailability.UNAVAILABLE
    )


def parse_ncku_tainan_gov_paid() -> AppointmentAvailability:
    return (
        AppointmentAvailability.AVAILABLE
        if check_available_ncku_tainan(URL_GOV_PAID)
        else AppointmentAvailability.UNAVAILABLE
    )


def check_available_ncku_tainan(url: str) -> bool:
    # Initial data_dict for POST method later.
    post_data = {
        "__EVENTTARGET": "ctl00$MainContent$ddlWeeks",
        "__EVENTARGUMENT": "",
        "__LASTFOCUS": "",
        "__VIEWSTATE": "",
        "__VIEWSTATEGENERATOR": "",
        "__SCROLLPOSITIONX": "0",
        "__SCROLLPOSITIONY": "0",
        "__EVENTVALIDATION": "",
        "ctl00$MainContent$ddlWeeks": "",
        "ctl00$MainContent$ddlNoons": "",
        "ctl00$MainContent$ddlWeeks_02": "",
    }

    # First request is GET.
    r = requests.get(url, verify=CERT, timeout=5)
    soup = bs4.BeautifulSoup(r.text, "html.parser")

    # Get first day of each weekly appointments list.
    selectTag = soup.find("select", {"id": "ctl00_MainContent_ddlWeeks"})
    optionValues = list(map(lambda x: x.get("value"), selectTag.find_all("option")))

    for i, date in enumerate(optionValues):
        # Check if there is an available appointment.
        table = soup.find("table", {"id": "tRegSchedule"})
        appointments = list(
            map(
                lambda x: x.text,
                filter(
                    filter_appointments_ncku_tainan,
                    table.find_all("td", {"class": "p-0"}),
                ),
            )
        )

        if bool(appointments):
            return True

        if i != len(optionValues) - 1:
            # Prepare data_dict next POST request
            post_data["__VIEWSTATE"] = soup.find("input", {"id": "__VIEWSTATE"}).get(
                "value"
            )
            post_data["__VIEWSTATEGENERATOR"] = soup.find(
                "input", {"id": "__VIEWSTATEGENERATOR"}
            ).get("value")
            post_data["__EVENTVALIDATION"] = soup.find(
                "input", {"id": "__EVENTVALIDATION"}
            ).get("value")
            post_data["ctl00$MainContent$ddlWeeks"] = optionValues[i + 1]
            post_data["ctl00$MainContent$ddlWeeks_02"] = date

            # Launch POST request
            r = requests.post(url, verify=CERT, data=post_data, timeout=5)
            soup = bs4.BeautifulSoup(r.text, "html.parser")

    return False


def filter_appointments_ncku_tainan(element: bs4.element.Tag) -> bool:
    sub_strs = ["預約", "轉掛", "停診"]
    return (
        all(sub_str not in element.text for sub_str in sub_strs) and element.text != ""
    )
