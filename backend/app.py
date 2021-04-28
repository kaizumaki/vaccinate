from flask import Flask, render_template
import csv
import sys
from typing import TypedDict, Tuple, Dict
from enum import Enum
import requests
from bs4 import BeautifulSoup
from backend.hospital_types import Hospital, HospitalID, AppointmentAvailability

# Parsers
from backend.Parsers.ntu_taipei import *
from backend.Parsers.ntu_hsinchu import *
from backend.Parsers.ntu_yunlin import *


app = Flask(
    __name__,
    static_url_path="",
    static_folder="../dist",
    template_folder="../dist",
)


PARSERS = [parseNTUH, parseNTUHHsinchu, parseNTUHYunlin]


@app.route("/")
def index() -> str:
    availability: Dict[HospitalID, AppointmentAvailability] = dict(
        [f() for f in PARSERS]
    )
    with open("data/hospitals.csv") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = []
        for row in reader:
            hospital_id = int(row["編號"])
            hospital_availability = (
                availability[hospital_id].value
                if hospital_id in availability
                else AppointmentAvailability.NO_DATA.value
            )
            hospital: Hospital = {
                "address": row["地址"],
                "availability": hospital_availability,
                "department": row["科別"],
                "hospital_id": int(row["編號"]),
                "location": row["縣市"],
                "name": row["醫院名稱"],
                "phone": row["電話"],
                "website": row["Website"],
            }
            rows.append(hospital)
        return render_template("./index.html", rows=rows)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
