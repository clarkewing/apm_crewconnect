from datetime import date, datetime
import json
from typing import Any

import jsonpickle
from apm import Apm
from token_manager import TokenManager


apm = Apm("https://crewmobile.to.aero", TokenManager())

flights = apm.get_flight_schedule(date(2024, 6, 24))

flights_with_missing_crew_members = [
    flight
    for flight in flights
    if flight.is_missing_crew_members("OPL") and flight.aircraft_type == "73H"
]

with open(".storage/schedule.json", "w+") as file:
    file.write(jsonpickle.encode(flights_with_missing_crew_members))
